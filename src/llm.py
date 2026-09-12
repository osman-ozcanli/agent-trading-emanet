"""LLM layer — two jobs, neither of which can place an order.

  1. intake()  : turn a plain-Turkish goal into config values
  2. explain() : turn a decision into a paragraph a non-trader can read

Deliberate design: the LLM never decides whether to trade. The Three Witness
rule decides, the risk gate vetoes, the exchange executes. The LLM only
translates — human language in, machine rules out; machine decision in,
human language out.

Every call degrades gracefully. If the LLM is slow, offline or returns
nonsense, the agent keeps running on its deterministic path.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

_BIN = shutil.which("claude") or "claude"

# Hard bounds the LLM cannot argue its way past, whatever the user asks for.
_BOUNDS = {
    "max_position_pct": (1.0, 25.0),
    "max_open_positions": (1, 4),
    "daily_loss_limit_pct": (1.0, 10.0),
    "take_profit_pct": (0.5, 10.0),
    "stop_loss_pct": (0.5, 5.0),
}


ROOT = Path(__file__).resolve().parent.parent


def _workdir() -> Path:
    """A neutral directory with no project context, created once."""
    work = Path(tempfile.gettempdir()) / "emanet-llm"
    work.mkdir(parents=True, exist_ok=True)
    cfg_file = work / "no-mcp.json"
    if not cfg_file.exists():
        cfg_file.write_text('{"mcpServers":{}}', encoding="utf-8")
    return work


def available(cfg: dict[str, Any] | None = None) -> bool:
    """Whether the LLM layer is switched on and reachable."""
    if cfg is not None and not cfg.get("llm", {}).get("enabled", False):
        return False
    return shutil.which("claude") is not None


def _ask(prompt: str, cfg: dict[str, Any] | None = None, timeout: int | None = None) -> str:
    """One headless Claude call. Returns "" on any failure — never raises.

    MCP servers are deliberately not loaded: starting all 16 took 91s, versus
    5s with none. A slow LLM must never stall the trading loop.
    """
    c = (cfg or {}).get("llm", {})
    work = _workdir()
    cmd = [_BIN, "-p", prompt,
           "--model", c.get("model", "haiku"),
           "--strict-mcp-config",
           "--mcp-config", str(work / "no-mcp.json"),
           "--disallowed-tools", "Bash", "Read", "Write", "Edit", "WebFetch", "WebSearch"]
    try:
        # Run OUTSIDE the project. Inside it, claude picks up CLAUDE.md and the
        # source files and behaves like a code reviewer instead of answering the
        # prompt: 105s and an off-topic reply, versus 5s and a clean one here.
        proc = subprocess.run(
            cmd, capture_output=True, text=True, cwd=str(work),
            timeout=timeout or c.get("timeout_seconds", 45), encoding="utf-8", errors="replace",
        )
        return proc.stdout.strip() if proc.returncode == 0 else ""
    except (subprocess.TimeoutExpired, OSError):
        return ""


# --- Job 1: plain Turkish goal -> config values ------------------------------

def intake(goal: str, cfg: dict[str, Any] | None = None) -> dict[str, Any]:
    """Translate a user's stated goal into risk settings, clamped to safe bounds.

    Example goal:
      "30 dolarim var, %5'ten fazla kaybetmek istemiyorum, yavas buyusun"
    """
    prompt = (
        f"Yatirimci hedefi: {goal}\n"
        "Bu hedefe uygun risk ayarlarini SADECE JSON olarak yaz, baska hicbir sey yazma. "
        "Sayilari hedefe gore degistir:\n"
        '{"max_position_pct": 10, "max_open_positions": 2, "daily_loss_limit_pct": 5, '
        '"take_profit_pct": 2, "stop_loss_pct": 1, "aciklama": "tek cumle Turkce ozet"}'
    )
    # Runs once at startup, not per tick, so a slower careful answer is affordable.
    raw = _ask(prompt, cfg, timeout=150)
    parsed = _extract_json(raw)
    if not parsed:
        return {}

    out: dict[str, Any] = {}
    for key, (lo, hi) in _BOUNDS.items():
        if key in parsed:
            try:
                val = float(parsed[key])
            except (TypeError, ValueError):
                continue
            # Clamp: the LLM proposes, the bounds dispose.
            out[key] = int(min(max(val, lo), hi)) if key == "max_open_positions" \
                else round(min(max(val, lo), hi), 2)
    if parsed.get("aciklama"):
        out["aciklama"] = str(parsed["aciklama"])[:300]
    return out


# --- Job 2: decision -> human paragraph --------------------------------------

def explain(entry: dict[str, Any], cfg: dict[str, Any] | None = None) -> str:
    """Write the decision as one short paragraph in plain Turkish, no jargon."""
    witnesses = "\n".join(
        f"- {w['witness']}: {w['direction']} — {w['reason']}"
        for w in entry.get("witnesses", [])
    )
    action = {"buy": "ALIM yapti", "sell": "SATIM yapti",
              "wait": "BEKLEDI", "veto": "risk kapisi tarafindan DURDURULDU"}.get(
        entry.get("action", "wait"), entry.get("action", ""))

    prompt = (
        "Kripto bilmeyen birine, bir trading ajaninin kararini anlatiyorsun.\n"
        f"Varlik: {entry.get('instId')}\n"
        f"Karar: {action}\n"
        f"Tanik gorusleri:\n{witnesses}\n"
        + (f"Durdurma sebebi: {entry['veto_reason']}\n" if entry.get("veto_reason") else "")
        + (f"Emir: {entry['order']}\n" if entry.get("order") else "")
        + "\nEN FAZLA 2 CUMLE yaz. Jargon kullanma (RSI, EMA gibi terimleri gunluk dille acikla). "
          "Yatirim tavsiyesi verme, sadece ne olduguna dair olguyu anlat. Sadece cumleleri yaz."
    )
    return _ask(prompt, cfg)


def _extract_json(text: str) -> dict[str, Any]:
    """Pull the first JSON object out of a model reply."""
    match = re.search(r"\{.*\}", text, re.S)
    if not match:
        return {}
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return {}
