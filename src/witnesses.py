"""The Three Witnesses — Uc Tanik Kurali.

No trade happens unless three INDEPENDENT sources agree on a direction:
  1. Technical  — what the price action says      (okx market indicator)
  2. Smart money— what successful traders do      (okx smartmoney)
  3. Sentiment  — what the news and crowd feel    (okx news)

Each witness returns a Verdict. A witness that cannot be reached returns
direction "unknown" rather than raising: a missing witness must block a
trade, never crash the agent.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

import mcp
from okx import OkxError, call

Direction = Literal["buy", "sell", "wait", "unknown"]


@dataclass
class Verdict:
    """One witness's opinion on one instrument, with a human-readable reason."""

    witness: str
    direction: Direction
    reason: str          # plain Turkish, shown to the user — this IS the UX
    detail: dict[str, Any]


def _base_ccy(inst_id: str) -> str:
    """'BTC-USDT' -> 'BTC'."""
    return inst_id.split("-")[0]


def technical(inst_id: str, cfg: dict[str, Any]) -> Verdict:
    """Witness 1: RSI + price vs EMA. Needs no credentials."""
    t = cfg["witnesses"]["technical"]
    bar = t["timeframe"]
    trading = cfg["profiles"]["trading"]
    try:
        rsi_rows = mcp.tool("market_get_indicator",
                            {"instId": inst_id, "indicator": "rsi", "bar": bar,
                             "params": [14]}, trading)
        ema_rows = mcp.tool("market_get_indicator",
                            {"instId": inst_id, "indicator": "ema", "bar": bar,
                             "params": [t["ema_period"]]}, trading)
        ticker = mcp.tool("market_get_ticker", {"instId": inst_id}, trading)
    except (mcp.MCPError, OSError) as exc:
        return Verdict("teknik", "unknown", f"Teknik veri alinamadi: {exc}", {})

    rsi = _indicator_value(rsi_rows, "RSI", bar, "14")
    ema = _indicator_value(ema_rows, "EMA", bar, str(t["ema_period"]))
    tick = _rows(ticker)
    if not tick:
        return Verdict("teknik", "unknown", "Fiyat verisi alinamadi.", {})
    px = float(tick[0]["last"])
    if rsi is None or ema is None:
        return Verdict("teknik", "unknown", "Gosterge verisi bos dondu.", {})

    above_ema = px > ema
    if rsi < t["rsi_oversold"] and above_ema:
        d, why = "buy", f"RSI {rsi:.1f} (asiri satim) ve fiyat EMA{t['ema_period']} uzerinde."
    elif rsi > t["rsi_overbought"] and not above_ema:
        d, why = "sell", f"RSI {rsi:.1f} (asiri alim) ve fiyat EMA{t['ema_period']} altinda."
    else:
        d = "wait"
        why = (f"RSI {rsi:.1f} notr bolgede, fiyat EMA{t['ema_period']}'in "
               f"{'ustunde' if above_ema else 'altinda'}.")
    return Verdict("teknik", d, why, {"rsi": rsi, "ema": ema, "price": px})


def smartmoney(inst_id: str, cfg: dict[str, Any], overview: list[dict] | None = None) -> Verdict:
    """Witness 2: long/short balance of qualified top traders (live read-only key)."""
    ccy = _base_ccy(inst_id)
    rows = overview if overview is not None else fetch_smartmoney_overview(cfg)
    row = next((r for r in rows if r.get("ccy") == ccy), None)
    if row is None:
        return Verdict("akilli_para", "unknown", f"{ccy} icin akilli para verisi yok.", {})

    lsr = row.get("longShortRatio", {})
    long_ratio = float(lsr.get("weightedLongRatio") or lsr.get("longRatio") or 0)
    longs, shorts = row.get("longTraders", 0), row.get("shortTraders", 0)

    if long_ratio >= 0.60:
        d = "buy"
        why = f"Basarili traderlarin %{long_ratio*100:.0f}'i alis yonunde ({longs} alici / {shorts} satici)."
    elif long_ratio <= 0.40:
        d = "sell"
        why = f"Basarili traderlarin %{(1-long_ratio)*100:.0f}'i satis yonunde ({longs} alici / {shorts} satici)."
    else:
        d = "wait"
        why = f"Basarili traderlar bolunmus durumda (%{long_ratio*100:.0f} alis). Net yon yok."
    return Verdict("akilli_para", d, why, {"long_ratio": long_ratio, "longs": longs, "shorts": shorts})


def sentiment(inst_id: str, cfg: dict[str, Any], snapshot: list[dict] | None = None) -> Verdict:
    """Witness 3: news and social mood (live read-only key)."""
    s = cfg["witnesses"]["sentiment"]
    ccy = _base_ccy(inst_id)
    rows = snapshot if snapshot is not None else fetch_sentiment(cfg, [ccy])
    row = next((r for r in rows if r.get("ccy") == ccy), None)
    if row is None:
        return Verdict("duygu", "unknown", f"{ccy} icin haber verisi yok.", {})

    sent = row.get("sentiment", {})
    bull = float(sent.get("bullishRatio", 0))
    bear = float(sent.get("bearishRatio", 0))
    mentions = row.get("mentionCnt", 0)

    if bull >= s["bullish_threshold"] and bull > bear:
        d, why = "buy", f"Haber akisi olumlu (pozitif {bull:.2f} / negatif {bear:.2f}, {mentions} haber)."
    elif bear >= s["bearish_threshold"] and bear > bull:
        d, why = "sell", f"Haber akisi olumsuz (negatif {bear:.2f} / pozitif {bull:.2f}, {mentions} haber)."
    else:
        d, why = "wait", f"Haber havasi notr (pozitif {bull:.2f} / negatif {bear:.2f}, {mentions} haber)."
    return Verdict("duygu", d, why, {"bullish": bull, "bearish": bear, "mentions": mentions})


# --- batch fetchers: one call serves every instrument, keeps the loop cheap ---

def fetch_smartmoney_overview(cfg: dict[str, Any]) -> list[dict]:
    """One smartmoney call covering the whole universe."""
    try:
        rows = mcp.tool("smartmoney_get_signal_overview_by_filter",
                        {"topInstruments": 20,
                         "period": str(cfg["witnesses"]["smartmoney"]["period"])},
                        cfg["profiles"]["intel"])
        return _rows(rows)
    except (mcp.MCPError, OSError):
        return []


def fetch_sentiment(cfg: dict[str, Any], ccys: list[str] | None = None) -> list[dict]:
    """One news call covering the whole universe."""
    coins = ",".join(ccys or [_base_ccy(p) for p in cfg["universe"]["pairs"]])
    try:
        rows = _rows(mcp.tool("news_get_coin_sentiment", {"coins": coins},
                              cfg["profiles"]["intel"]))
        # Shape: [{details: [{ccy, mentionCnt, sentiment: {...}}, ...]}]
        if rows and isinstance(rows[0], dict) and "details" in rows[0]:
            return rows[0]["details"]
        return rows
    except (mcp.MCPError, OSError):
        return []


def _rows(payload: Any) -> list[dict]:
    """Unwrap the {endpoint, requestTime, data} envelope ATK tools return."""
    if isinstance(payload, dict):
        payload = payload.get("data", payload)
    return payload if isinstance(payload, list) else []


def _indicator_value(rows: Any, name: str, bar: str, period: str) -> float | None:
    """Dig the latest indicator reading out of the CLI's nested shape.

    Shape: [{data: [{instId, timeframes: {<bar>: {indicators: {<NAME>: [{ts, values: {<period>: "42.4"}}]}}}}]}]
    """
    try:
        if isinstance(rows, dict):
            rows = rows.get("data", rows)
        if isinstance(rows, dict):
            rows = [rows]
        entry = rows[0]
        if "data" in entry:
            entry = entry["data"][0]
        series = entry["timeframes"][bar]["indicators"][name]
        values = series[0]["values"]
        raw = values.get(period) or next(iter(values.values()))
        return float(raw)
    except (KeyError, IndexError, TypeError, ValueError, StopIteration):
        return None
