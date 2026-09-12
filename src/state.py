"""Agent state that must survive a restart.

Why a file and not the account balance: the demo account is pre-seeded with
BTC/ETH/OKB the agent never bought. Counting raw balances would report three
open positions before the agent does anything. So we track only what the agent
itself opened.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent


def _path(cfg: dict[str, Any]) -> Path:
    p = ROOT / cfg["logging"]["dir"] / "state.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def load(cfg: dict[str, Any], equity_now: float) -> dict[str, Any]:
    """Read state, rolling it over at the start of a new day."""
    path = _path(cfg)
    today = date.today().isoformat()
    if path.exists():
        st = json.loads(path.read_text(encoding="utf-8"))
        if st.get("day") == today:
            return st
    # New day (or first run): today's loss limit is measured from here.
    return {"day": today, "start_equity": equity_now, "open": {}, "safe_mode": False}


def save(cfg: dict[str, Any], st: dict[str, Any]) -> None:
    """Persist state so a restart does not forget open positions or Safe Mode."""
    _path(cfg).write_text(json.dumps(st, ensure_ascii=False, indent=2), encoding="utf-8")


def daily_pnl_pct(st: dict[str, Any], equity_now: float) -> float:
    """Today's change against the equity the agent started the day with."""
    start = float(st.get("start_equity") or 0)
    if start <= 0:
        return 0.0
    return (equity_now - start) / start * 100.0
