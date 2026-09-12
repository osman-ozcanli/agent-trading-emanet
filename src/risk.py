"""Risk gate — the only component that can say NO.

Pure functions, no network: testable in milliseconds, and it can never fail
because an API was slow. Whatever proposes a trade (rule engine or LLM), the
order still has to pass through here. A veto is final.

NOTE: Adim 5 will extend this (daily loss tracking, safe mode persistence).
This is the minimum needed for the Adim 4 loop to be honest about its limits.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Decision:
    """Result of the gate. `allowed=False` means the order must not be sent."""

    allowed: bool
    reason: str
    size_quote: float = 0.0   # order size in quote currency (USDT)


def check(cfg: dict[str, Any], state: dict[str, Any], proposal: dict[str, Any]) -> Decision:
    """Vet one proposed order against every hard rule.

    state    : {equity_quote, open_positions, daily_pnl_pct, safe_mode}
    proposal : {instId, side, min_notional}
    """
    r = cfg["risk"]

    if not state.get("equity_known", True):
        return Decision(False, "Bakiye okunamadi (ag/API sorunu). Olculemeyen bakiyeyle "
                               "islem yapilmaz — bu bir kayip degil, bilinmezliktir.")

    if state.get("safe_mode"):
        return Decision(False, "Safe Mode aktif — gunluk kayip limiti asilmisti, yeni islem yok.")

    if state.get("daily_pnl_pct", 0.0) <= -abs(r["daily_loss_limit_pct"]):
        return Decision(False,
                        f"Gunluk kayip limiti asildi (%{state['daily_pnl_pct']:.2f} / "
                        f"limit %{r['daily_loss_limit_pct']}). Safe Mode'a geciliyor.")

    if state.get("open_positions", 0) >= r["max_open_positions"]:
        return Decision(False,
                        f"Ayni anda en fazla {r['max_open_positions']} acik pozisyon olabilir "
                        f"(su an {state['open_positions']}).")

    if r["require_stop_loss"] and not cfg["risk"].get("exchange_side_brackets"):
        return Decision(False, "Stop-loss zorunlu ama borsa tarafi bracket kapali.")

    equity = float(state.get("equity_quote", 0.0))

    # Never spend the reserve. Sizing already tends to leave cash idle, but this
    # states it as a rule so it holds whatever the percentages are set to.
    reserve_pct = r.get("min_cash_reserve_pct", 0)
    cap = float(cfg["capital"]["virtual_cap_usdt"])
    deployed = float(state.get("deployed_quote", 0.0))
    spendable = max(0.0, cap * (1 - reserve_pct / 100.0) - deployed)
    if spendable <= 0:
        return Decision(False,
                        f"Nakit tamponu korunuyor: sermayenin %{reserve_pct}'i "
                        "hic kullanilmaz, dagitilabilir bakiye kalmadi.")

    size = min(equity, spendable) * r["max_position_pct"] / 100.0
    if size <= 0:
        return Decision(False, "Kullanilabilir bakiye yok.")

    min_notional = float(proposal.get("min_notional", 0.0))
    if size < min_notional:
        return Decision(False,
                        f"Pozisyon buyuklugu ({size:.2f}) borsanin minimum emir tutarinin "
                        f"({min_notional:.2f}) altinda.")

    return Decision(True, f"Tum risk kurallari saglandi. Buyukluk {size:.2f} USDT.", size)


def brackets(cfg: dict[str, Any], entry_px: float, side: str) -> tuple[float, float]:
    """Take-profit and stop-loss prices, attached to the order at the exchange.

    Exchange-side means they survive an agent crash, a network drop or a dead laptop.
    """
    r = cfg["risk"]
    tp_pct, sl_pct = r["take_profit_pct"] / 100.0, r["stop_loss_pct"] / 100.0
    if side == "buy":
        return entry_px * (1 + tp_pct), entry_px * (1 - sl_pct)
    return entry_px * (1 - tp_pct), entry_px * (1 + sl_pct)
