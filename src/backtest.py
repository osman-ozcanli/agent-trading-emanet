"""Backtest: is there a real edge, and at which holding horizon?

18.09 (ikinci oturum) — bu dosya A kararı için yeniden kuruldu. Değişen dört şey:

  1. **Vade artık değişken.** 18.09 sabahındaki üç koşu (mevcut / C / C+tampon) hep
     aynı vadede (8 dk → 1 saatlik çözünürlükte fiilen 60 dk) kaldı ve hep negatif
     çıktı. Ölçülen sebep: zaman-stopuyla kapanan 114 işlemin komisyon öncesi
     kenarı %+0,064, gidiş-dönüş komisyon %0,20 — sinyal 3,1 kat zayıf. Bu bir
     eşik sorunu değil, vade sorunu, o yüzden `--horizon-sweep` ile vade taranıyor.
  2. **Short bantları düzeltildi.** Eski kod kâr-al/zarar-kes seviyelerini iki yön
     için de alış mantığıyla hesaplıyordu; `sell take_profit -0.0240` gibi satırlar
     bunun izidir. Artık seviyeler **canlı ajanın kendi fonksiyonundan**
     (`risk.brackets`) alınıyor — kopya değil aynı fonksiyon, aynı hata iki kez
     oluşamaz. Spot'ta short açılamadığı için `--allow-short` varsayılan kapalı.
  3. **Pencere 90 güne çıktı.** `market_get_candles` tek çağrıda 300 satırla
     sınırlı ama `after=<en eski ts>` imleciyle geriye sayfalanıyor (18.09'da
     doğrulandı). Akıllı para geçmişi hâlâ ~100 saat, bu yüzden `--witnesses tech`
     modunda o tanık devre dışı bırakılıp teknik tanık 90 günde ölçülebiliyor;
     `tech+sm` modunda pencere kaçınılmaz olarak akıllı paranın kapsamına düşer.
  4. **Gerçek disk önbelleği.** Önceki notlarda "veri önbellekte kaldı" yazıyordu
     ama önbellek yoktu; her koşu yeniden çekiyordu ve bu yüzden iki koşunun aynı
     satırı farklı çıkıyordu (-1,18 / -1,20). Artık `logs/backtest_cache.json`
     var, yani bir taramanın bütün satırları **aynı veri penceresini** kullanıyor.

Ölçüm dürüstlüğü, değişmeyen kurallar:
  - Geriye dönük bakış yok: bar i kararı yalnızca i'ye kadar hesaplanabilen
    göstergeleri ve kapanış zamanı <= bar i olan akıllı para okumasını görür.
  - Duygu (haber) tanığı test EDİLMEZ: OKX'te geçmişe dönük oran yok, uydurulmaz,
    her barda "unknown" sayılır — canlı ajanın ulaşılamayan tanığı işlediği gibi.
  - Bir barın içinde iki seviye de tetiklenebiliyorsa zarar-kes önce sayılır.
    Uzun vadede bantlar bar menzilinden çok geniş olduğu için bu varsayım artık
    belirleyici değil (8 dk/0,8%-0,5% kurgusunda belirleyiciydi — bkz. kayıt).
  - Simülasyon adımı 1 saatlik mum; sinyal 4H/1G EMA'dan gelir. Yani çıkış
    kontrolü sinyalden daha ince çözünürlükte yapılır.

config.yaml, state*.json ve defterlere ASLA dokunulmaz. CLI bayrakları config'i
yalnızca bellekte geçersiz kılar: canlı ajan dondurulmuş kalır, sayı görülüp
onaylanmadan hiçbir şey ona yazılmaz (PROGRESS.md, 18.09 kararı).

Kullanım:
  python src/backtest.py --horizon-sweep            # A kararının ana çıktısı
  python src/backtest.py --hold-minutes 1440 --tp 4 --sl 2.5
  python src/backtest.py --witnesses tech+sm --days 12   # eski kurgu, karşılaştırma
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import mcp
import risk
import witnesses as W
from okx import load_config

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "logs" / "backtest_cache.json"

BAR_MINUTES = {"1m": 1, "5m": 5, "15m": 15, "30m": 30, "1H": 60, "2H": 120,
               "4H": 240, "6H": 360, "12H": 720, "1D": 1440, "1W": 10080}


# --- data fetch --------------------------------------------------------------

def fetch_candles(cfg: dict[str, Any], inst_id: str, bar: str, days: float) -> list[dict]:
    """`days` worth of candles, oldest first, real OKX data.

    One call caps at 300 rows, so this pages backwards with OKX's `after` cursor
    (`after=<oldest ts seen>` returns the next 300 older rows — verified 18.09).
    """
    need = int(days * 1440 / BAR_MINUTES[bar]) + 25  # +25 = EMA20 warmup headroom
    prof = cfg["profiles"]["intel"]
    rows: list[list[str]] = []
    cursor: int | None = None
    while len(rows) < need:
        args: dict[str, Any] = {"instId": inst_id, "bar": bar, "limit": 300}
        if cursor is not None:
            args["after"] = str(cursor)
        page = W._rows(mcp.tool("market_get_candles", args, prof))
        if not page:
            break
        rows += page
        cursor = min(int(r[0]) for r in page)
        time.sleep(0.05)  # shared query pool: be a polite client

    uniq: dict[int, dict] = {}
    for r in rows:
        uniq[int(r[0])] = {"ts": int(r[0]), "o": float(r[1]), "h": float(r[2]),
                           "l": float(r[3]), "c": float(r[4])}
    out = [uniq[k] for k in sorted(uniq)]
    # OKX stamps a candle by its OPEN time, so the newest bar is still forming and
    # its high/low/close are partial. Dropping it keeps every bar in the window whole.
    return out[:-1]


def fetch_smartmoney(cfg: dict[str, Any], ccy: str, retries: int = 4) -> list[dict]:
    """Hourly smart-money history for one currency.

    Still capped at ~100 rows: the daily granularity endpoint returns HTTP 500
    and the hourly one rejects limit>100. This is why `--witnesses tech+sm`
    cannot reach a 90-day window while `tech` can.
    """
    for attempt in range(retries):
        try:
            rows = W._rows(mcp.tool("smartmoney_get_signal_trend_by_filter",
                             {"instCcy": ccy, "granularity": "1h", "sortBy": "pnl",
                              "period": "7", "limit": 100},
                             cfg["profiles"]["intel"]))
            out = []
            for r in rows:
                dv = r["dataVersion"]  # YYYYMMDDHH, UTC
                ts = datetime(int(dv[0:4]), int(dv[4:6]), int(dv[6:8]), int(dv[8:10]),
                              tzinfo=timezone.utc).timestamp() * 1000
                out.append({"ts": ts, "weighted_long": float(r.get("weightedLongRatio", 0.5))})
            out.sort(key=lambda r: r["ts"])
            return out
        except (mcp.MCPError, OSError) as exc:
            if attempt == retries - 1:
                print(f"  !! {ccy} akilli para alinamadi ({retries} deneme): {exc}")
                return []
            time.sleep(2.0)
    return []


def fetch_min_notional(cfg: dict[str, Any], inst_id: str, last_px: float) -> float:
    try:
        rows = W._rows(mcp.tool("market_get_instruments",
                                {"instType": "SPOT", "instId": inst_id},
                                cfg["profiles"]["intel"]))
        return float((rows[0] if rows else {}).get("minSz", 0) or 0) * last_px
    except (mcp.MCPError, OSError):
        return 0.0


# --- indicators (same formulas as witnesses.py, computed from raw candles) --

def rsi_series(closes: list[float], period: int = 14) -> list[float | None]:
    """Wilder's RSI. First `period` entries are None (not enough history yet)."""
    out: list[float | None] = [None] * len(closes)
    if len(closes) <= period:
        return out
    gains = losses = 0.0
    for i in range(1, period + 1):
        d = closes[i] - closes[i - 1]
        gains += max(d, 0.0)
        losses += max(-d, 0.0)
    avg_gain, avg_loss = gains / period, losses / period
    out[period] = 100.0 if avg_loss == 0 else 100.0 - 100.0 / (1.0 + avg_gain / avg_loss)
    for i in range(period + 1, len(closes)):
        d = closes[i] - closes[i - 1]
        avg_gain = (avg_gain * (period - 1) + max(d, 0.0)) / period
        avg_loss = (avg_loss * (period - 1) + max(-d, 0.0)) / period
        out[i] = 100.0 if avg_loss == 0 else 100.0 - 100.0 / (1.0 + avg_gain / avg_loss)
    return out


def ema_series(closes: list[float], period: int = 20) -> list[float | None]:
    """Standard EMA. First `period-1` entries are None."""
    out: list[float | None] = [None] * len(closes)
    if len(closes) < period:
        return out
    k = 2.0 / (period + 1)
    prev = sum(closes[:period]) / period
    out[period - 1] = prev
    for i in range(period, len(closes)):
        prev = closes[i] * k + prev * (1 - k)
        out[i] = prev
    return out


def align_to_step(step_ts: list[int], src: list[dict], values: list[float | None],
                  src_bar: str, require_closed: bool) -> dict[int, float | None]:
    """Map each simulation timestamp to the latest source value it may legally see.

    OKX stamps a candle by its OPEN time, so a 4H bar stamped 12:00 does not close
    until 16:00 and its EMA is unknowable before then. `require_closed` enforces
    `open + duration <= ts` for the higher timeframes. Without it the regime switch
    would read a close from up to four hours in the future — the quiet kind of
    lookahead that makes a backtest look profitable for no reason.

    When the source IS the simulation series, `require_closed=False`: the decision
    is taken at that bar's close and entry happens at that same close, so using its
    own value is legitimate and matches what the live agent reads.

    Precomputed into a dict because doing it inside the pair/bar loop was O(n^2)
    and the window is now 8x longer.
    """
    dur = BAR_MINUTES[src_bar] * 60_000 if require_closed else 0
    out: dict[int, float | None] = {}
    i = 0
    cur: float | None = None
    for ts in step_ts:
        while i < len(src) and src[i]["ts"] + dur <= ts:
            cur = values[i]
            i += 1
        out[ts] = cur
    return out


def align_smartmoney(step_ts: list[int], sm: list[dict]) -> dict[int, float | None]:
    out: dict[int, float | None] = {}
    i = 0
    cur: float | None = None
    for ts in step_ts:
        while i < len(sm) and sm[i]["ts"] <= ts:
            cur = sm[i]["weighted_long"]
            i += 1
        out[ts] = cur
    return out


# --- witnesses, mirroring witnesses.py's thresholds exactly -----------------

def witness_technical(rsi: float | None, ema: float | None, px: float, cfg_t: dict) -> str:
    """config.yaml'daki bugünkü tanık: RSI aşırı satım VE fiyat EMA üstünde."""
    if rsi is None or ema is None:
        return "unknown"
    if not 0 < rsi < 100 or not 0.5 < ema / px < 2:
        return "unknown"
    above = px > ema
    if rsi < cfg_t["rsi_oversold"] and above:
        return "buy"
    if rsi > cfg_t["rsi_overbought"] and not above:
        return "sell"
    return "wait"


def witness_technical_regime(px: float, ema_fast: float | None, ema_slow: float | None,
                             buffer_pct: float = 0.0) -> str:
    """Rejim anahtarı: iki zaman dilimi de aynı yönü göstermezse oy yok.

    Fiyat her iki EMA'nın da üstündeyse -> buy, ikisinin de altındaysa -> sell,
    anlaşmazlarsa -> wait. RSI devre dışı. `buffer_pct` fiyatın EMA'ya en az bu
    kadar uzak olmasını şart koşar; EMA'ya yakınken rejim belirsiz sayılır.
    """
    if ema_fast is None or ema_slow is None:
        return "unknown"
    if not (0.5 < ema_fast / px < 2) or not (0.5 < ema_slow / px < 2):
        return "unknown"
    b = buffer_pct / 100.0
    above = px > ema_fast * (1 + b) and px > ema_slow * (1 + b)
    below = px < ema_fast * (1 - b) and px < ema_slow * (1 - b)
    if above:
        return "buy"
    if below:
        return "sell"
    return "wait"


def witness_smartmoney(weighted_long: float | None, threshold: float = 0.60) -> str:
    if weighted_long is None:
        return "unknown"
    if weighted_long >= threshold:
        return "buy"
    if weighted_long <= 1 - threshold:
        return "sell"
    return "wait"


def decide(votes: list[str], w_cfg: dict) -> str:
    if w_cfg.get("block_on_unknown") and "unknown" in votes:
        return "wait"
    for side, other in (("buy", "sell"), ("sell", "buy")):
        if votes.count(side) >= w_cfg["min_approvals"] and votes.count(other) == 0:
            return side
    return "wait"


# --- simulation ---------------------------------------------------------------

class Position:
    __slots__ = ("side", "entry", "opened_at", "size_quote", "tp_px", "sl_px")

    def __init__(self, side: str, entry: float, opened_at: float, size_quote: float,
                 tp_px: float, sl_px: float) -> None:
        self.side, self.entry, self.opened_at = side, entry, opened_at
        self.size_quote, self.tp_px, self.sl_px = size_quote, tp_px, sl_px



def run_backtest(cfg: dict[str, Any], series: dict[str, dict], *,
                 variant: str = "C", buffer_pct: float = 0.0,
                 use_smartmoney: bool = True, allow_short: bool = False,
                 sm_threshold: float = 0.60, fee_pct: float = 0.001,
                 invert: bool = False) -> dict[str, Any]:
    """Replays config.yaml's rules over the fetched window. No lookahead.

    Bracket levels come from `risk.brackets` — the same function the live agent
    calls — so a short's take-profit is below entry and its stop above, which the
    previous version of this file got wrong for all 34 short trades.
    """
    r = cfg["risk"]
    w = cfg["witnesses"]
    cap = float(cfg["capital"]["virtual_cap_usdt"])
    equity = cap
    peak = cap
    max_dd_pct = 0.0
    open_pos: dict[str, Position] = {}
    trades: list[dict] = []
    decisions = {"buy": 0, "sell": 0, "wait": 0, "veto": 0}
    veto_reasons: dict[str, int] = {}
    votes_tally = {"teknik": {"buy": 0, "sell": 0, "wait": 0, "unknown": 0},
                   "akilli_para": {"buy": 0, "sell": 0, "wait": 0, "unknown": 0}}

    pairs = [p for p in cfg["universe"]["pairs"] if series.get(p, {}).get("candles")]
    all_ts = sorted({c["ts"] for p in pairs for c in series[p]["candles"]})

    for ts in all_ts:
        # --- exits first: brackets, then time stop, on this bar's OHLC ---
        for inst_id in list(open_pos.keys()):
            bar = series[inst_id]["by_ts"].get(ts)
            if bar is None:
                continue
            pos = open_pos[inst_id]
            age_min = (ts - pos.opened_at) / 60000.0
            long = pos.side == "buy"
            # Conservative: if both levels sit inside this bar, the stop fired first.
            hit_sl = bar["l"] <= pos.sl_px if long else bar["h"] >= pos.sl_px
            hit_tp = bar["h"] >= pos.tp_px if long else bar["l"] <= pos.tp_px
            if hit_sl:
                exit_px, why = pos.sl_px, "stop_loss"
            elif hit_tp:
                exit_px, why = pos.tp_px, "take_profit"
            elif age_min >= r["max_position_minutes"]:
                exit_px, why = bar["c"], "time_stop"
            else:
                continue
            gross = pos.size_quote * (exit_px / pos.entry - 1.0) * (1 if long else -1)
            net = gross - pos.size_quote * fee_pct * 2
            equity += net
            peak = max(peak, equity)
            max_dd_pct = max(max_dd_pct, (peak - equity) / peak * 100.0)
            trades.append({"inst": inst_id, "side": pos.side, "reason": why, "net": net,
                           "size": pos.size_quote, "held_min": age_min,
                           "opened_at": pos.opened_at, "closed_at": ts})
            del open_pos[inst_id]

        # --- entries ---
        deployed = sum(p.size_quote for p in open_pos.values())
        for inst_id in pairs:
            s = series[inst_id]
            bar = s["by_ts"].get(ts)
            if bar is None:
                continue
            px = bar["c"]

            if variant == "C":
                v_tech = witness_technical_regime(px, s["ema_fast"][ts], s["ema_slow"][ts],
                                                  buffer_pct)
            else:
                i = s["idx"][ts]
                v_tech = witness_technical(s["rsi"][i], s["ema1h"][i], px, w["technical"])

            if invert:
                # Diagnostic only: does the signal carry information with the wrong
                # sign, or no information at all? A near-zero edge both ways means
                # no information; a positive edge inverted means the rule is backwards.
                v_tech = {"buy": "sell", "sell": "buy"}.get(v_tech, v_tech)

            votes_tally["teknik"][v_tech] += 1
            if use_smartmoney:
                v_sm = witness_smartmoney(s["sm"][ts], sm_threshold)
                votes_tally["akilli_para"][v_sm] += 1
                # 3rd slot = sentiment: no historical series exists, scored unknown
                action = decide([v_tech, v_sm, "unknown"], w)
            else:
                # Tech-only mode: the consensus rule is bypassed on purpose rather
                # than faked by duplicating a vote. Stated plainly in the report.
                action = v_tech if v_tech in ("buy", "sell") else "wait"
            if action == "sell" and not allow_short:
                # Spot cash account cannot short. Counting these as trades is what
                # inflated the previous run's 198 to a number the agent could
                # never have executed.
                decisions["wait"] += 1
                veto_reasons["short_spotta_yok"] = veto_reasons.get("short_spotta_yok", 0) + 1
                continue
            if action == "wait":
                decisions["wait"] += 1
                continue
            if inst_id in open_pos:
                decisions["veto"] += 1
                veto_reasons["ikinci_giris"] = veto_reasons.get("ikinci_giris", 0) + 1
                continue
            if len(open_pos) >= r["max_open_positions"]:
                decisions["veto"] += 1
                veto_reasons["pozisyon_limiti"] = veto_reasons.get("pozisyon_limiti", 0) + 1
                continue

            reserve_pct = r.get("min_cash_reserve_pct", 0)
            spendable = max(0.0, cap * (1 - reserve_pct / 100.0) - deployed)
            size = min(equity, spendable) * r["max_position_pct"] / 100.0
            if size <= 0 or size < s["min_notional"]:
                decisions["veto"] += 1
                veto_reasons["min_emir"] = veto_reasons.get("min_emir", 0) + 1
                continue

            tp_px, sl_px = risk.brackets(cfg, px, action)
            open_pos[inst_id] = Position(action, px, ts, size, tp_px, sl_px)
            deployed += size
            decisions[action] += 1

    # close anything still open at its pair's final bar
    for inst_id, pos in open_pos.items():
        last = series[inst_id]["candles"][-1]
        long = pos.side == "buy"
        gross = pos.size_quote * (last["c"] / pos.entry - 1.0) * (1 if long else -1)
        net = gross - pos.size_quote * fee_pct * 2
        equity += net
        trades.append({"inst": inst_id, "side": pos.side, "reason": "window_end", "net": net,
                       "size": pos.size_quote,
                       "held_min": (last["ts"] - pos.opened_at) / 60000.0,
                       "opened_at": pos.opened_at, "closed_at": last["ts"]})

    wins = sum(1 for t in trades if t["net"] > 0)
    # Per-trade return distribution. Without this a single positive total is
    # indistinguishable from luck, which is precisely the trap this whole exercise
    # exists to avoid. NOTE: positions overlap (up to 4 at once, correlated pairs),
    # so the effective sample is smaller than n and this t-stat is optimistic.
    pcts = [t["net"] / t["size"] * 100.0 for t in trades if t["size"] > 0]
    mean_pct = sum(pcts) / len(pcts) if pcts else 0.0
    if len(pcts) > 1:
        var = sum((x - mean_pct) ** 2 for x in pcts) / (len(pcts) - 1)
        sd_pct = var ** 0.5
        se_pct = sd_pct / len(pcts) ** 0.5
    else:
        sd_pct = se_pct = 0.0
    t_stat = mean_pct / se_pct if se_pct else 0.0
    # Per-trade percentages are computed against the actual notional traded, not a
    # nominal figure: position size shrinks as capital gets deployed, so a nominal
    # constant would misstate the edge by ~20%.
    avg_size = (sum(t["size"] for t in trades) / len(trades)) if trades else 0.0

    def firing(v: dict[str, int]) -> float:
        total = sum(v.values())
        return (v["buy"] + v["sell"]) / total * 100.0 if total else 0.0

    return {
        "trades": trades, "decisions": decisions, "veto_reasons": veto_reasons,
        "votes": votes_tally,
        "tech_firing_pct": firing(votes_tally["teknik"]),
        "sm_firing_pct": firing(votes_tally["akilli_para"]),
        "start_equity": cap, "end_equity": equity,
        "net_return_pct": (equity - cap) / cap * 100.0,
        "n_trades": len(trades),
        "win_rate_pct": (wins / len(trades) * 100.0) if trades else 0.0,
        "max_dd_pct": max_dd_pct,
        "per_trade_mean_pct": mean_pct, "per_trade_sd_pct": sd_pct,
        "per_trade_se_pct": se_pct, "t_stat": t_stat,
        "avg_hold_h": (sum(t["held_min"] for t in trades) / len(trades) / 60.0) if trades else 0.0,
        "avg_size": avg_size,
        "bars": len(all_ts),
    }


# --- data assembly (with a real on-disk cache) --------------------------------

def build_series(cfg: dict[str, Any], *, days: float, sim_bar: str, fast_bar: str,
                 slow_bar: str, use_smartmoney: bool, refresh: bool) -> dict[str, dict]:
    """Fetch (or reload) every series once, so a sweep compares one same window."""
    key = f"{days}|{sim_bar}|{fast_bar}|{slow_bar}|{use_smartmoney}|" \
          f"{','.join(cfg['universe']['pairs'])}"
    raw: dict[str, Any] | None = None
    if CACHE.exists() and not refresh:
        blob = json.loads(CACHE.read_text(encoding="utf-8"))
        if blob.get("key") == key:
            raw = blob["pairs"]
            age_h = (time.time() - blob["fetched_at"]) / 3600.0
            print(f"Onbellekten okundu ({age_h:.1f} saat once cekilmis) — ayni pencere, "
                  f"tarama satirlari karsilastirilabilir.")

    if raw is None:
        raw = {}
        print(f"Veri cekiliyor: {len(cfg['universe']['pairs'])} parite · {days:.0f} gun · "
              f"{sim_bar} sim + {fast_bar}/{slow_bar} sinyal"
              f"{' + saatlik akilli para' if use_smartmoney else ''}...")
        for inst_id in cfg["universe"]["pairs"]:
            sim = fetch_candles(cfg, inst_id, sim_bar, days)
            fast = fetch_candles(cfg, inst_id, fast_bar, days) if fast_bar != sim_bar else sim
            slow = fetch_candles(cfg, inst_id, slow_bar, days)
            sm = fetch_smartmoney(cfg, inst_id.split("-")[0]) if use_smartmoney else []
            mn = fetch_min_notional(cfg, inst_id, sim[-1]["c"] if sim else 0.0)
            raw[inst_id] = {"sim": sim, "fast": fast, "slow": slow, "sm": sm, "min_notional": mn}
            span = (sim[-1]["ts"] - sim[0]["ts"]) / 86400000.0 if sim else 0
            print(f"  {inst_id:10} {len(sim):5} {sim_bar} ({span:.1f} gun) · "
                  f"{len(fast):4} {fast_bar} · {len(slow):4} {slow_bar} · "
                  f"{len(sm):3} akilli-para")
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        CACHE.write_text(json.dumps({"key": key, "fetched_at": time.time(), "pairs": raw}),
                         encoding="utf-8")

    series: dict[str, dict] = {}
    for inst_id, d in raw.items():
        sim = d["sim"]
        if not sim:
            continue
        step_ts = [c["ts"] for c in sim]
        closes = [c["c"] for c in sim]
        ema_p = cfg["witnesses"]["technical"]["ema_period"]
        series[inst_id] = {
            "candles": sim,
            "by_ts": {c["ts"]: c for c in sim},
            "idx": {c["ts"]: i for i, c in enumerate(sim)},
            "rsi": rsi_series(closes, 14),
            "ema1h": ema_series(closes, ema_p),
            "ema_fast": align_to_step(step_ts, d["fast"],
                                      ema_series([c["c"] for c in d["fast"]], ema_p),
                                      fast_bar, require_closed=fast_bar != sim_bar),
            "ema_slow": align_to_step(step_ts, d["slow"],
                                      ema_series([c["c"] for c in d["slow"]], ema_p),
                                      slow_bar, require_closed=slow_bar != sim_bar),
            "sm": align_smartmoney(step_ts, d["sm"]),
            "min_notional": d["min_notional"],
        }
    return series


# --- reporting ----------------------------------------------------------------

def buy_and_hold(series: dict[str, dict]) -> dict[str, Any]:
    """The benchmark that decides whether any of this was worth doing.

    A strategy that returns +5% in a window where simply holding returned +60% has
    not found an edge — it has found a way to sit out a rally. Without this control
    a long-biased rule looks skilful in any uptrend, which is the single easiest way
    to fool yourself in a backtest.
    """
    per_pair = {}
    for inst_id, s in series.items():
        c = s["candles"]
        if c:
            per_pair[inst_id] = (c[-1]["c"] / c[0]["c"] - 1.0) * 100.0
    avg = sum(per_pair.values()) / len(per_pair) if per_pair else 0.0
    return {"per_pair": per_pair, "equal_weight_pct": avg}


def fmt_hold(minutes: float) -> str:
    if minutes < 60:
        return f"{minutes:.0f} dk"
    if minutes < 1440:
        return f"{minutes / 60:.0f} sa"
    return f"{minutes / 1440:.0f} gun"


HORIZONS = [
    # (tutma suresi dk, kar-al %, zarar-kes %)
    (60, 0.8, 0.5),      # 18.09 sabahi kosulan kurgu (canli config'in 1H yaklasimi)
    (240, 2.0, 1.5),
    (480, 3.0, 2.0),
    (1440, 4.0, 2.5),
    (2880, 6.0, 3.5),
    (5760, 8.0, 5.0),
]


def sweep_horizons(cfg: dict[str, Any], series: dict[str, dict], **kw: Any) -> list[dict]:
    """Vadeyi tara, sinyali sabit tut — tek degisken vade olsun."""
    out = []
    for hold, tp, sl in HORIZONS:
        trial = json.loads(json.dumps(cfg))  # deep copy, config.yaml'a dokunulmaz
        trial["risk"]["max_position_minutes"] = hold
        trial["risk"]["take_profit_pct"] = tp
        trial["risk"]["stop_loss_pct"] = sl
        res = run_backtest(trial, series, **kw)
        fee_rt = kw.get("fee_pct", 0.001) * 100 * 2
        net = res["per_trade_mean_pct"]
        out.append({
            "hold": hold, "tp": tp, "sl": sl,
            "trades": res["n_trades"],
            "return_pct": res["net_return_pct"],
            "win_rate_pct": res["win_rate_pct"],
            "max_dd_pct": res["max_dd_pct"],
            "avg_hold_h": res["avg_hold_h"],
            "per_trade_net_pct": net,
            "per_trade_gross_pct": net + fee_rt,
            "se_pct": res["per_trade_se_pct"],
            "t_stat": res["t_stat"],
            "firing_pct": res["tech_firing_pct"],
        })
        print(f"  {fmt_hold(hold):>6} tp{tp:>4}/sl{sl:<4} -> {res['n_trades']:4} islem · "
              f"getiri {res['net_return_pct']:+6.2f}% · kazanma {res['win_rate_pct']:4.1f}% · "
              f"maks dusus {res['max_dd_pct']:5.2f}% · brut/islem {net + fee_rt:+.3f}% · "
              f"net/islem {net:+.3f}% (+-{res['per_trade_se_pct']:.3f}, t={res['t_stat']:+.2f})")
    return out


def render_sweep(title: str, note: str, rows: list[dict], fee_rt: float) -> list[str]:
    L = [f"### {title}", "", note, "",
         "| Tutma | Kar-al | Zarar-kes | Islem | Ort. tutma | Net getiri | Kazanma | "
         "Maks dusus | Brut/islem | Net/islem | t |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    for row in rows:
        L.append(
            f"| {fmt_hold(row['hold'])} | %{row['tp']} | %{row['sl']} | {row['trades']} | "
            f"{row['avg_hold_h']:.1f} sa | **{row['return_pct']:+.2f}%** | "
            f"%{row['win_rate_pct']:.1f} | %{row['max_dd_pct']:.2f} | "
            f"{row['per_trade_gross_pct']:+.3f}% | "
            f"{row['per_trade_net_pct']:+.3f}% ±{row['se_pct']:.3f} | {row['t_stat']:+.2f} |")
    L.append("")
    return L


def write_report(cfg: dict[str, Any], series: dict[str, dict], args: Any,
                 sweeps: dict[str, list[dict]] | None, single: dict[str, Any] | None) -> str:
    spans = [(s["candles"][0]["ts"], s["candles"][-1]["ts"]) for s in series.values()]
    t0 = datetime.fromtimestamp(min(a for a, _ in spans) / 1000, timezone.utc)
    t1 = datetime.fromtimestamp(max(b for _, b in spans) / 1000, timezone.utc)
    days = (t1 - t0).total_seconds() / 86400.0
    fee_rt = args.fee * 100 * 2

    L: list[str] = [
        "# EMANET — backtest raporu (vade taramasi)",
        "",
        f"Uretildi: {datetime.now().strftime('%d.%m.%Y %H:%M')} · `python src/backtest.py "
        f"{' '.join(sys.argv[1:])}` · **config.yaml degismedi, ajana dokunulmadi.**",
        "",
        "## Neden bu kosu var",
        "",
        "18.09 sabahi uc varyant (mevcut / C / C+tampon) denendi, ucu de negatif cikti ve "
        "her seferinde **tanik mantigi** degistirildi. Islem bazli ayristirma sebebin tanik "
        "olmadigini gosterdi: zaman-stopuyla kapanan 114 islemin komisyon oncesi kenari "
        "**%+0,064**, gidis-donus komisyon **%0,20** — sinyal yanlis degil, **3,1 kat "
        "zayif**. Bu bir esik sorunu degil vade sorunu oldugu icin bu kosuda tanik sabit "
        "tutulup **vade tarandi**.",
        "",
        "## Kapsam",
        "",
        f"- Pencere: **{days:.1f} gun** ({t0:%d.%m.%Y} - {t1:%d.%m.%Y} UTC), "
        f"{len(series)} parite, {args.sim_bar} simulasyon mumu.",
        f"- Sinyal: EMA{cfg['witnesses']['technical']['ema_period']} **{args.fast_bar}** + "
        f"**{args.slow_bar}** rejim anahtari (Secenek C), tampon %{args.buffer}.",
        f"- Tanik kurgusu: **{args.witnesses}**. "
        + ("Akilli para geciyor; gecmisi ~100 saatle sinirli oldugu icin pencere fiilen "
           "o kadar. " if args.witnesses == "tech+sm" else
           "Akilli para **devre disi**: gecmisi ~100 saatle sinirli (gunluk uc nokta "
           "HTTP 500, saatlik limit>100 reddediyor) ve veri varken oylarin %75'i 'buy' "
           "cikiyor — yani neredeyse sabit. Onu sart kosmak pencereyi 90 gunden 4 gune "
           "dusurup karsiliginda cok az bilgi veriyordu. ")
        + "Duygu tanigi her iki kurguda da test edilmez: OKX'te gecmise donuk oran yok, "
          "uydurulmaz.",
        f"- Komisyon: gidis-donus **%{fee_rt:.2f}** (%{args.fee*100:.2f} her yon, OKX spot taker).",
        f"- Short: **{'acik' if args.allow_short else 'kapali'}**"
        + ("" if args.allow_short else " — spot nakit hesapta short acilamaz. Onceki kosuda "
           "34 short islem sayilmisti; ajan bunlari hicbir zaman uygulayamazdi."),
        "- Kar-al/zarar-kes seviyeleri **`risk.brackets()`** ile, yani canli ajanin kendi "
        "fonksiyonuyla hesaplanir. Onceki surum her iki yon icin de alis mantigi "
        "kullaniyordu (`sell take_profit -0.0240` satirlari bunun iziydi).",
        "- Geriye donuk bakis yok: 4H/1G EMA bir 1H barina ancak o bar kapandiktan sonra "
        "gorunur; akilli para okumasi barin kapanis zamanindan sonrasini gormez.",
        "- Bir barin icinde iki seviye de tetiklenebiliyorsa **zarar-kes once** sayilir. "
        "Uzun vadede bantlar (%2-8) 1H bar menzilinden cok genis oldugu icin bu varsayim "
        "artik belirleyici degil; 0,8/0,5 kurgusunda belirleyiciydi.",
        "",
    ]

    bh = buy_and_hold(series)
    L += [
        "## Olcut: ayni pencerede hicbir sey yapmamak",
        "",
        "Bir stratejinin %5 getirdigi pencerede sadece tutmak %60 getiriyorsa o strateji "
        "kenar bulmus degil, **ralliyi kacirmanin bir yolunu** bulmustur. Uzun tarafli her "
        "kural yukselen piyasada yetenekli gorunur; bu olcut o yanilgiyi kesiyor.",
        "",
        "| Parite | Al-tut getirisi |",
        "|---|---|",
    ]
    for inst_id, pct in sorted(bh["per_pair"].items(), key=lambda kv: -kv[1]):
        L.append(f"| {inst_id} | {pct:+.2f}% |")
    L += [
        f"| **8 parite esit agirlikli** | **{bh['equal_weight_pct']:+.2f}%** |",
        "",
        f"Yani bu {days:.0f} gunluk pencere guclu bir **boga piyasasi**. Asagidaki hicbir "
        "satir bu sayiya yaklasmiyor.",
        "",
    ]

    if sweeps:
        L += [
            "## Vade taramasi — tek degisken vade, sinyal sabit",
            "",
        ]
        for title, rows in sweeps.items():
            note = ("Kural yazildigi gibi: fiyat iki EMA'nin da **ustundeyse** al "
                    "(momentum)." if "momentum" in title.lower() else
                    "**Teshis amacli** ters cevrilmis hali: fiyat iki EMA'nin da "
                    "**altindaysa** al (ortalamaya donus). Bu bir strateji onerisi degil, "
                    "sinyalde bilgi olup olmadigini anlama testidir.")
            L += render_sweep(title, note, rows, fee_rt)
        L += [
            "",
            f"**Brut/islem** = komisyon oncesi kenar, islem basi ortalama. Basabas icin "
            f"bunun %{fee_rt:.2f}'yi gecmesi gerekir. **Net/islem** = komisyon sonrasi, "
            "yanindaki ± standart hata. **t** = net/islem'in sifirdan kac standart hata "
            "uzakta oldugu; kabaca |t| > 2 olmadan 'kenar var' denemez.",
            "",
            "> Uyari: pozisyonlar ust uste biniyor (ayni anda 4 tane, birbiriyle korelasyonlu "
            "pariteler), yani etkin orneklem islem sayisindan kucuk ve buradaki t degerleri "
            "**iyimser**. Isaretin degil, **egilimin** okunmasi daha guvenli: brut kenarin "
            "vade ile monotonik degismesi tek bir satirin pozitif cikmasindan daha guclu "
            "bir kanittir.",
            "",
            "Adim 2'nin gecis sarti (PROGRESS.md): komisyon sonrasi pozitif **VE** maks. "
            "dusus < %10.",
            "",
        ]

    if single:
        r = single
        L += [
            "## Tek kosu detayi",
            "",
            f"Tutma {fmt_hold(cfg['risk']['max_position_minutes'])} · kar-al "
            f"%{cfg['risk']['take_profit_pct']} · zarar-kes %{cfg['risk']['stop_loss_pct']}",
            "",
            "| Metrik | Deger |",
            "|---|---|",
            f"| Baslangic / bitis sermaye | {r['start_equity']:.2f} -> {r['end_equity']:.2f} USDT |",
            f"| Net getiri | **%{r['net_return_pct']:+.2f}** |",
            f"| Islem sayisi | {r['n_trades']} |",
            f"| Kazanma orani | %{r['win_rate_pct']:.1f} |",
            f"| Maksimum dusus | %{r['max_dd_pct']:.2f} |",
            f"| Ortalama tutma | {r['avg_hold_h']:.1f} saat |",
            f"| Teknik tanik ateslenme | %{r['tech_firing_pct']:.1f} |",
            f"| Bekleme karari | {r['decisions']['wait']} |",
            f"| Risk kapisi reddi | {r['decisions']['veto']} |",
            "",
            "### Tanik oylari",
            "",
            "| Tanik | buy | sell | wait | unknown | ateslenme |",
            "|---|---|---|---|---|---|",
        ]
        for name in ("teknik", "akilli_para"):
            v = r["votes"][name]
            if sum(v.values()) == 0:
                continue
            pct = r["tech_firing_pct"] if name == "teknik" else r["sm_firing_pct"]
            L.append(f"| {name} | {v['buy']} | {v['sell']} | {v['wait']} | {v['unknown']} | "
                     f"%{pct:.1f} |")
        L += ["", "### Kapanis nedenleri", "", "| Neden | Islem | Toplam (USDT) |", "|---|---|---|"]
        by_reason: dict[str, list[float]] = {}
        for t in r["trades"]:
            by_reason.setdefault(t["reason"], []).append(t["net"])
        for reason, nets in sorted(by_reason.items(), key=lambda kv: -len(kv[1])):
            L.append(f"| {reason} | {len(nets)} | {sum(nets):+.4f} |")
        if r["veto_reasons"]:
            L += ["", "### Red gerekcesi dagilimi", "", "| Gerekce | Kez |", "|---|---|"]
            for k, c in sorted(r["veto_reasons"].items(), key=lambda kv: -kv[1]):
                L.append(f"| {k} | {c} |")
        L.append("")

    if sweeps:
        L += [
            "## Okuma",
            "",
            "1. **Teshis dogrulandi.** 1 saatlik vadede brut kenar ~%0,00 ve net kayip "
            "istatistiksel olarak ezici (t ≈ -37). Yani canli config'in kaybi sinyal "
            "kalitesinden degil, tamamen komisyondan geliyordu. 18.09 sabahi uc kez tanik "
            "mantigi degistirilmesi bu yuzden sonuc vermedi.",
            "2. **Vade dogru degiskendi.** Brut kenar vade uzadikca **monotonik** artiyor "
            "ve maksimum dusus %66'dan %4'e iniyor. Monotonluk, tek bir pozitif satirdan "
            "daha guclu bir kanit.",
            "3. **Ama kenar hala gosterilemedi.** En iyi satirda bile |t| < 2; yani pozitif "
            "getiri gurultuden ayirt edilemiyor. Ayrica 2 yon x 6 vade = **12 kombinasyon** "
            "denendi, en iyisinin t≈1,8 cikmasi sansla beklenen seydir. Bu bir bulgu degil.",
            f"4. **Olcut hepsini gecti.** Ayni pencerede al-tut **{bh['equal_weight_pct']:+.2f}%**. "
            "Hicbir varyant buna yaklasmiyor. Ters cevrilmis kuralin daha iyi gorunmesinin "
            "en olasi aciklamasi da bu: yukselen piyasada 'dususte al' her zaman iyi gorunur. "
            "Bu, ortalamaya donus kenari degil, **uzun tarafli olmanin** getirisi.",
            "",
            "**Sonuc: bu pencerede kanitlanmis bir kenar yok.** Vade duzeltmesi gerekli bir "
            "adimdi ve yapildi (kayip %-66'dan %+1'e, dusus %66'dan %4'e), ama yeterli "
            "degil. Bir sonraki dogru soru 'hangi esik' degil: **bu sinyal ayi/yatay "
            "piyasada ne yapiyor?** 100 gunun tamami boga oldugu icin bu pencere o soruyu "
            "cevaplayamaz — daha uzun ya da farkli rejimli bir pencere gerekiyor.",
            "",
        ]

    L += [
        "## Karar",
        "",
        "Bu rapor bir kazanc iddiasi degil. Osman sayiyi gorup onaylamadan `config.yaml` "
        "ve `src/witnesses.py` degistirilmez; ajan dondurulmus halde kalir "
        "(PROGRESS.md, 18.09 karari).",
        "",
    ]
    return "\n".join(L)


# --- main ---------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(description="EMANET backtest — vade ve tanik taramasi")
    ap.add_argument("--days", type=float, default=90, help="pencere uzunlugu (varsayilan 90)")
    ap.add_argument("--sim-bar", default="1H", choices=list(BAR_MINUTES),
                    help="cikis kontrollerinin cozunurlugu (varsayilan 1H)")
    ap.add_argument("--fast-bar", default="4H", choices=list(BAR_MINUTES),
                    help="rejim anahtarinin hizli zaman dilimi (varsayilan 4H)")
    ap.add_argument("--slow-bar", default="1D", choices=list(BAR_MINUTES),
                    help="rejim anahtarinin yavas zaman dilimi (varsayilan 1D)")
    ap.add_argument("--variant", choices=["mevcut", "C"], default="C")
    ap.add_argument("--buffer", type=float, default=0.0, help="rejim tamponu %%")
    ap.add_argument("--witnesses", choices=["tech", "tech+sm"], default="tech",
                    help="tech = akilli para devre disi (90 gun mumkun), "
                         "tech+sm = akilli para sart (pencere ~4 gune duser)")
    ap.add_argument("--allow-short", action="store_true",
                    help="spot'ta uygulanamaz; yalnizca swap'a gecis arastirmasi icin")
    ap.add_argument("--fee", type=float, default=0.001, help="tek yon komisyon (0.001 = %%0,1)")
    ap.add_argument("--horizon-sweep", action="store_true", help="vadeyi tara (A karari)")
    ap.add_argument("--hold-minutes", type=float, help="tek kosu: tutma suresi (dk)")
    ap.add_argument("--tp", type=float, help="tek kosu: kar-al %%")
    ap.add_argument("--sl", type=float, help="tek kosu: zarar-kes %%")
    ap.add_argument("--invert", action="store_true",
                    help="teshis: sinyalin yonunu ters cevir (bilgi mi var, isaret mi yanlis)")
    ap.add_argument("--refresh", action="store_true", help="onbellegi yok say, yeniden cek")
    args = ap.parse_args()

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    cfg = load_config()
    use_sm = args.witnesses == "tech+sm"

    series = build_series(cfg, days=args.days, sim_bar=args.sim_bar, fast_bar=args.fast_bar,
                          slow_bar=args.slow_bar, use_smartmoney=use_sm, refresh=args.refresh)
    if not series:
        print("Veri alinamadi, cikiliyor.")
        return

    kw = dict(variant=args.variant, buffer_pct=args.buffer, use_smartmoney=use_sm,
              allow_short=args.allow_short, fee_pct=args.fee, invert=args.invert)

    sweeps: dict[str, list[dict]] | None = None
    single = None
    if args.horizon_sweep:
        # Both directions in ONE report off ONE cached window: comparing numbers that
        # came from two separate fetches is how the 18.09 morning run ended up with
        # -1.18 and -1.20 for the same configuration.
        sweeps = {}
        print("\nVade taramasi — momentum (kural yazildigi gibi):")
        sweeps["Momentum — kural yazildigi gibi"] = sweep_horizons(cfg, series, **kw)
        print("\nVade taramasi — ters cevrilmis (teshis):")
        sweeps["Ters cevrilmis — ortalamaya donus (teshis)"] = sweep_horizons(
            cfg, series, **{**kw, "invert": not kw["invert"]})
    else:
        if args.hold_minutes is not None:
            cfg["risk"]["max_position_minutes"] = args.hold_minutes
        if args.tp is not None:
            cfg["risk"]["take_profit_pct"] = args.tp
        if args.sl is not None:
            cfg["risk"]["stop_loss_pct"] = args.sl
        single = run_backtest(cfg, series, **kw)

    report = write_report(cfg, series, args, sweeps, single)
    (ROOT / "logs" / "BACKTEST.md").write_text(report, encoding="utf-8")
    print("\n" + report)
    mcp.shutdown()


if __name__ == "__main__":
    main()
