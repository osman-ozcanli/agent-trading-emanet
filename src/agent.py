"""Autonomous agent loop: Sense -> Reason -> Act -> Evaluate.

Run it and walk away:  python src/agent.py
Single pass for testing: python src/agent.py --once

The loop is deterministic and costs zero LLM tokens. It only gathers evidence,
applies the Three Witness rule, and asks the risk gate. Nothing here can bypass
the gate — not a bug, not a bad signal, not a language model.
"""
from __future__ import annotations

import argparse
import time
from datetime import datetime, timezone
from typing import Any

import journal
import mcp
import risk
import state
import witnesses as W
from okx import load_config


# --- SENSE -------------------------------------------------------------------

def sense(cfg: dict[str, Any]) -> dict[str, Any]:
    """Read the world once per tick: portfolio, persisted state, one batch call per witness."""
    # First pass with no deduction, only to open the state file.
    first, _ = _portfolio(cfg)
    st = state.load(cfg, first if first is not None else 0.0)
    _reconcile(cfg, st)
    _time_stop(cfg, st)
    deployed = sum(float(p.get("sz", 0)) for p in st["open"].values())
    measured, _ = _portfolio(cfg, deployed)
    known = measured is not None
    equity = measured if known else 0.0
    pnl = state.daily_pnl_pct(st, equity + deployed) if known else 0.0

    # Safe Mode latches only on a MEASURED loss. An unreadable balance is an
    # unknown, not a loss — treating it as one shut the agent down during a
    # six-minute OKX outage on 12.09 and would have done the same in live.
    if known and pnl <= -abs(cfg["risk"]["daily_loss_limit_pct"]):
        st["safe_mode"] = True
        state.save(cfg, st)

    return {
        "equity_quote": equity,
        "deployed_quote": deployed,
        "exchange_open": _exchange_open(cfg),
        "open_positions": len(st["open"]),
        "smartmoney": W.fetch_smartmoney_overview(cfg),
        "sentiment": W.fetch_sentiment(cfg),
        "daily_pnl_pct": pnl,
        "equity_known": known,
        "safe_mode": st["safe_mode"],
        "_state": st,
    }


def _portfolio(cfg: dict[str, Any], deployed: float = 0.0) -> tuple[float | None, int]:
    """Quote balance still free to deploy, capped to the virtual capital.

    `deployed` is what open positions are already holding. Subtracting it is what
    keeps demo honest: the demo account has thousands of USDT, so capping alone
    would report a full 30 no matter how much is already at work, while live —
    where the balance really does fall as positions open — would size down.
    Without this, demo and live behave differently and the cap is a lie.
    """
    quote = cfg["universe"]["quote"]
    cap = float(cfg["capital"]["virtual_cap_usdt"])
    try:
        rows = W._rows(mcp.tool("account_get_balance", {"ccy": quote},
                                cfg["profiles"]["trading"]))
    except (mcp.MCPError, OSError):
        # Unknown, NOT zero. Returning 0.0 here once made the agent read a network
        # outage as a 100% loss and latch Safe Mode. Never guess a balance.
        return None, 0

    balance = 0.0
    for r in _flatten_balance(rows):
        if r.get("ccy") == quote:
            balance = float(r.get("availBal") or r.get("availEq") or r.get("eq") or 0)
            break
    return max(0.0, min(balance, cap - deployed)), 0


def _bracket_live(cfg: dict[str, Any], inst_id: str) -> bool:
    """Did the protective bracket actually appear on the exchange?

    OKX accepts a bracketed order for some pairs and silently drops the attached
    take-profit / stop-loss. A 200 response is not protection; only a live algo
    order is. Checked with one short retry, because the algo lands a beat later.
    """
    for _ in range(2):
        time.sleep(1.0)
        if inst_id in _exchange_open(cfg):
            return True
    return False


def _unwind(cfg: dict[str, Any], inst_id: str, px: float, size_quote: float) -> None:
    """Sell back a position that could not be protected."""
    try:
        mcp.tool("spot_place_order", {
            "instId": inst_id, "tdMode": "cash", "side": "sell", "ordType": "market",
            "sz": str(round(size_quote / px, 8)), "tgtCcy": "base_ccy",
            "clOrdId": f"{cfg['execution']['client_order_id_prefix']}u{int(time.time())}",
        }, cfg["profiles"]["trading"])
    except (mcp.MCPError, OSError) as exc:
        print(f"  !! {inst_id} geri alinamadi: {exc}")


def _exchange_open(cfg: dict[str, Any]) -> set[str]:
    """Instruments that already carry a live bracket ON THE EXCHANGE.

    The local state file can drift — a crash, a race, a manual run. The exchange
    cannot. Asking it directly is what stops the agent from stacking a second
    position on a pair it is already holding.
    """
    try:
        rows = W._rows(mcp.tool("spot_get_algo_orders", {}, cfg["profiles"]["trading"]))
    except (mcp.MCPError, OSError):
        return set()
    return {r["instId"] for r in rows if r.get("state") == "live" and r.get("instId")}


def _time_stop(cfg: dict[str, Any], st: dict[str, Any]) -> None:
    """Close positions that have outstayed their welcome.

    A bracket that never triggers is a position that never frees its slot, and
    an agent whose slots are all taken stops deciding anything. The time stop
    guarantees turnover: no position may sit longer than max_position_minutes.
    """
    limit = cfg["risk"].get("max_position_minutes")
    if not limit or not st["open"]:
        return
    now = time.time()
    for inst_id, pos in list(st["open"].items()):
        # A position with no timestamp predates this rule — treat it as overdue.
        legacy = not pos.get("opened_at")
        age_min = 1e6 if legacy else (now - pos["opened_at"]) / 60.0
        if age_min < limit:
            continue
        try:
            _close(cfg, inst_id, pos)
        except (mcp.MCPError, OSError) as exc:
            print(f"  !! {inst_id} zaman stopu basarisiz: {exc}")
            continue
        st["open"].pop(inst_id, None)
        journal.record(cfg, {
            "instId": inst_id, "action": "sell", "witnesses": [],
            "veto_reason": (
                f"Zaman stopu: pozisyon {'zaman damgasiz (eski kayit)' if legacy else f'{age_min:.0f} dakikadir acik'} "
                f"— limit {limit} dk. Ajan pozisyonu kendisi kapatti."),
        })
        print(f"  zaman stopu: {inst_id} ({'eski kayit' if legacy else f'{age_min:.0f} dk'})")
    state.save(cfg, st)


def _close(cfg: dict[str, Any], inst_id: str, pos: dict[str, Any]) -> None:
    """Cancel the bracket, then sell the position back at market."""
    trading = cfg["profiles"]["trading"]
    for row in W._rows(mcp.tool("spot_get_algo_orders", {}, trading)):
        if row.get("instId") == inst_id and row.get("state") == "live":
            mcp.tool("spot_cancel_algo_order",
                     {"instId": inst_id, "algoId": row.get("algoId")}, trading)
    base_sz = pos.get("base_sz")
    if base_sz:
        mcp.tool("spot_place_order", {
            "instId": inst_id, "tdMode": "cash", "side": "sell",
            "ordType": "market", "sz": str(base_sz), "tgtCcy": "base_ccy",
            "clOrdId": f"{cfg['execution']['client_order_id_prefix']}x{int(time.time())}",
        }, trading)


def _reconcile(cfg: dict[str, Any], st: dict[str, Any]) -> None:
    """Drop positions the exchange has already closed.

    A position lives until its OCO bracket fires. Without this the agent would
    hit the position limit once and veto everything for the rest of the day.
    """
    if not st["open"]:
        return
    try:
        rows = W._rows(mcp.tool("spot_get_algo_orders", {}, cfg["profiles"]["trading"]))
    except (mcp.MCPError, OSError):
        return  # Cannot verify -> change nothing. Never guess a position closed.

    still_open = {r.get("instId") for r in rows if r.get("state") == "live"}
    closed = [inst for inst in st["open"] if inst not in still_open]
    for inst in closed:
        st["open"].pop(inst, None)
    if closed:
        state.save(cfg, st)
        print(f"  kapandi: {', '.join(closed)}")


def _flatten_balance(rows: Any) -> list[dict]:
    """Balance payload nests per-currency details under 'details'."""
    if isinstance(rows, dict):
        rows = [rows]
    out: list[dict] = []
    for r in rows or []:
        out.extend(r.get("details", [r]) if isinstance(r, dict) else [])
    return out


# --- REASON ------------------------------------------------------------------

def reason(cfg: dict[str, Any], inst_id: str, snapshot: dict[str, Any]) -> tuple[str, list[W.Verdict]]:
    """Apply the Three Witness consensus rule. Returns (action, verdicts).

    A trade needs at least `min_approvals` witnesses pointing the same way and
    NO witness pointing the other way. One dissenting voice is enough to veto —
    that is the whole idea. "wait" is neutral; "unknown" is recorded, and only
    blocks if `block_on_unknown` is set.
    """
    w = cfg["witnesses"]
    verdicts = [
        W.technical(inst_id, cfg),
        W.smartmoney(inst_id, cfg, snapshot["smartmoney"]),
        W.sentiment(inst_id, cfg, snapshot["sentiment"]),
    ]

    if w.get("block_on_unknown") and any(v.direction == "unknown" for v in verdicts):
        return "wait", verdicts

    votes = [v.direction for v in verdicts]
    for side, other in (("buy", "sell"), ("sell", "buy")):
        approvals = votes.count(side)
        dissent = votes.count(other)
        if approvals >= w["min_approvals"] and (dissent == 0 or w.get("allow_dissent")):
            return side, verdicts
    return "wait", verdicts


# --- ACT ---------------------------------------------------------------------

def act(cfg: dict[str, Any], inst_id: str, action: str,
        verdicts: list[W.Verdict], snapshot: dict[str, Any]) -> None:
    """Run the proposal past the risk gate, then place it (or explain why not).

    A position opened here is registered immediately, so the very next pair in
    the same tick sees the updated count. Without this the position limit would
    only be enforced between ticks, and one tick could open five positions.
    """
    payload: dict[str, Any] = {
        "instId": inst_id,
        "action": action,
        "witnesses": [v.__dict__ for v in verdicts],
    }

    if action == "wait":
        journal.record(cfg, payload)
        return

    if inst_id in snapshot["_state"].get("no_bracket", []):
        payload.update(action="veto",
                       veto_reason=f"{inst_id}: bu paritede borsa koruma emri olusturmuyor, "
                                   "stop-loss'suz islem yapilmaz. Oturum boyunca kapali.")
        journal.record(cfg, payload)
        return

    if inst_id in snapshot.get("exchange_open", set()):
        payload.update(action="veto",
                       veto_reason=f"{inst_id} icin borsada zaten acik bir pozisyon var; "
                                   "ayni pariteye ikinci kez girilmez.")
        journal.record(cfg, payload)
        return

    px = _last_price(cfg, inst_id)
    min_notional = _min_notional(cfg, inst_id, px)
    decision = risk.check(cfg, snapshot, {"instId": inst_id, "side": action,
                                          "min_notional": min_notional})
    if not decision.allowed:
        payload.update(action="veto", veto_reason=decision.reason)
        journal.record(cfg, payload)
        return

    tp, sl = risk.brackets(cfg, px, action)
    # Alphanumeric only: OKX TR rejects "-" with sCode 51000, despite the docs
    # listing it as allowed. Verified 15:14.
    cl_ord_id = f"{cfg['execution']['client_order_id_prefix']}{int(time.time())}"
    order = {"sz": round(decision.size_quote, 2), "tp": round(tp, 6),
             "sl": round(sl, 6), "clOrdId": cl_ord_id}
    payload["order"] = order

    if cfg["execution"]["dry_run"]:
        payload["dry_run"] = True
    else:
        try:
            _place(cfg, inst_id, action, order)
        except (mcp.MCPError, OSError) as exc:
            # The exchange refused. Record that as the truth and register nothing:
            # a position we do not hold must never appear in the journal.
            payload.update(action="veto", veto_reason=str(exc), order=None)
            journal.record(cfg, payload)
            print(f"  {inst_id} REDDEDILDI: {str(exc)[:90]}")
            return

        if cfg["risk"]["require_stop_loss"] and not _bracket_live(cfg, inst_id):
            # The order went through but the protective bracket did not appear.
            # An unprotected position breaks the one rule that may never bend,
            # so it is unwound at once and the pair is barred for this session.
            _unwind(cfg, inst_id, px, decision.size_quote)
            snapshot["_state"].setdefault("no_bracket", []).append(inst_id)
            state.save(cfg, snapshot["_state"])
            payload.update(action="veto", order=None,
                           veto_reason=f"{inst_id}: borsa koruma emrini (kar-al/zarar-kes) "
                                       "olusturmadi. Stop-loss'suz pozisyon yasak — "
                                       "pozisyon geri alindi, parite bu oturumda kapatildi.")
            journal.record(cfg, payload)
            print(f"  {inst_id} KORUMASIZ — geri alindi, parite kapatildi")
            return

    st = snapshot["_state"]
    st["open"][inst_id] = {"side": action, "entry": px, "opened_at": time.time(),
                           "base_sz": round(decision.size_quote / px, 8), **order}
    state.save(cfg, st)
    snapshot["open_positions"] = len(st["open"])
    snapshot.setdefault("exchange_open", set()).add(inst_id)
    journal.record(cfg, payload)


def _place(cfg: dict[str, Any], inst_id: str, side: str, order: dict[str, Any]) -> None:
    """Send the order with take-profit and stop-loss attached at the exchange."""
    mcp.tool("spot_place_order", {
        "instId": inst_id, "tdMode": "cash", "side": side,
        "ordType": cfg["execution"]["order_type"],
        "sz": str(order["sz"]), "tgtCcy": "quote_ccy",
        "tpTriggerPx": str(order["tp"]), "tpOrdPx": "-1",
        "slTriggerPx": str(order["sl"]), "slOrdPx": "-1",
        "clOrdId": order["clOrdId"],
    }, cfg["profiles"]["trading"])


def _last_price(cfg: dict[str, Any], inst_id: str) -> float:
    """Latest traded price."""
    rows = W._rows(mcp.tool("market_get_ticker", {"instId": inst_id},
                            cfg["profiles"]["trading"]))
    return float(rows[0]["last"])


def _min_notional(cfg: dict[str, Any], inst_id: str, px: float) -> float:
    """Exchange minimum order size, expressed in quote currency."""
    rows = W._rows(mcp.tool("market_get_instruments",
                            {"instType": "SPOT", "instId": inst_id},
                            cfg["profiles"]["trading"]))
    row = rows[0] if rows else {}
    return float(row.get("minSz", 0)) * px


# --- EVALUATE ----------------------------------------------------------------

def evaluate(cfg: dict[str, Any], snapshot: dict[str, Any]) -> None:
    """Close the loop: report where the account stands after this tick."""
    journal.record(cfg, {
        "instId": "-", "action": "wait", "witnesses": [],
        "evaluation": {"equity_quote": snapshot["equity_quote"],
                       "open_positions": snapshot["open_positions"]},
    })


# --- LOOP --------------------------------------------------------------------

def tick(cfg: dict[str, Any]) -> None:
    """One full Sense -> Reason -> Act pass over the whole universe."""
    snapshot = sense(cfg)
    stamp = datetime.now(timezone.utc).astimezone().strftime("%H:%M:%S")
    print(f"[{stamp}] bakiye={snapshot['equity_quote']:.2f} {cfg['universe']['quote']} "
          f"· dagitilmis={snapshot['deployed_quote']:.2f} "
          f"· acik={snapshot['open_positions']} · gunluk={snapshot['daily_pnl_pct']:+.2f}%"
          + (" · SAFE MODE" if snapshot["safe_mode"] else ""))

    for inst_id in cfg["universe"]["pairs"]:
        action, verdicts = reason(cfg, inst_id, snapshot)
        agree = sum(1 for v in verdicts if v.direction == action)
        print(f"  {inst_id:10} -> {action:5} ({agree}/3 tanik)")
        act(cfg, inst_id, action, verdicts, snapshot)


def main() -> None:
    """Entry point. Errors are logged and the loop continues — it must not die."""
    ap = argparse.ArgumentParser(description="Uc Tanik otonom trading agent")
    ap.add_argument("--once", action="store_true", help="tek tur calis ve cik")
    args = ap.parse_args()

    cfg = load_config()
    mode = "KURU CALISMA" if cfg["execution"]["dry_run"] else "CANLI EMIR"
    print(f"Agent basladi — profil={cfg['profiles']['trading']} · {mode}")

    while True:
        try:
            # Re-read config each tick: editing config.yaml must take effect
            # without restarting a running agent.
            cfg = load_config()
            tick(cfg)
        except Exception as exc:                     # noqa: BLE001 — loop must survive anything
            print(f"  !! tur hatasi: {exc}")
        if args.once:
            break
        time.sleep(cfg["loop"]["interval_seconds"])


if __name__ == "__main__":
    main()
