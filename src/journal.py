"""Decision journal — two outputs, two audiences.

  journal.jsonl  : machine-readable, one line per decision (metrics, replay)
  decisions.md   : human-readable decision cards in plain Turkish (the UX layer)

Every decision is written, including the decision to WAIT. A bot that only
speaks when it trades is a black box; this one explains its silence too.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent

_ICON = {"buy": "🟢", "sell": "🔴", "wait": "⏸️", "unknown": "❓", "veto": "⛔"}


def _paths(cfg: dict[str, Any]) -> tuple[Path, Path]:
    """Resolve journal paths from config and make sure the directory exists."""
    jsonl = ROOT / cfg["logging"]["journal"]
    md = ROOT / cfg["logging"]["decisions"]
    jsonl.parent.mkdir(parents=True, exist_ok=True)
    return jsonl, md


def record(cfg: dict[str, Any], entry: dict[str, Any]) -> None:
    """Append one decision to both the machine log and the human log."""
    jsonl, md = _paths(cfg)
    entry = {"ts": datetime.now().isoformat(timespec="seconds"), **entry}

    with open(jsonl, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    with open(md, "a", encoding="utf-8") as fh:
        fh.write(_card(entry) + "\n")


def _card(e: dict[str, Any]) -> str:
    """Render one decision as a card a non-technical person can read."""
    icon = _ICON.get(e.get("action", "wait"), "•")
    head = f"### {icon} {e['ts']} — {e.get('instId','-')} — {_verb(e)}"
    lines = [head, ""]

    for w in e.get("witnesses", []):
        lines.append(f"- **{w['witness']}** ({_ICON.get(w['direction'],'•')}): {w['reason']}")

    if e.get("veto_reason"):
        lines += ["", f"> ⛔ **Risk kapisi durdurdu:** {e['veto_reason']}"]
    if e.get("order"):
        o = e["order"]
        lines += ["", f"> Emir: {o.get('sz')} {e.get('instId')} · "
                      f"kar-al {o.get('tp')} · zarar-kes {o.get('sl')} · id `{o.get('clOrdId')}`"]
    if e.get("dry_run"):
        lines += ["", "> *(kuru calisma — gercek emir gonderilmedi)*"]

    lines.append("")
    return "\n".join(lines)


def _verb(e: dict[str, Any]) -> str:
    """Plain-Turkish label for what the agent did."""
    return {
        "buy": "ALIM",
        "sell": "SATIM",
        "wait": "BEKLEDI",
        "veto": "RISK KAPISI ENGELLEDI",
    }.get(e.get("action", "wait"), e.get("action", "-"))
