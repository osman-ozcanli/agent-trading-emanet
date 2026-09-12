"""Thin wrapper around the OKX Agent Trade Kit CLI (`okx`).

Every ATK call in this project goes through here, so profile routing
(demo vs live read-only) lives in exactly one place.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent

# On Windows `okx` is a .cmd shim; resolve it once so shell=False can find it.
_BIN = shutil.which("okx") or "okx"


def load_config(path: Path | None = None) -> dict[str, Any]:
    """Read config.yaml. No value in this project is hardcoded in code."""
    cfg_path = path or ROOT / "config.yaml"
    with open(cfg_path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


class OkxError(RuntimeError):
    """Raised when the okx CLI returns a non-zero exit code or unparsable output."""


def call(*args: str, profile: str | None = None, timeout: int = 30) -> Any:
    """Run `okx [--profile P] <args> --json` and return the parsed payload.

    `profile` selects which credential set is used:
      - trading profile (demo key)  -> orders, portfolio
      - intel profile (live, read-only) -> smartmoney, news

    Raises OkxError on failure; the caller decides whether that is fatal.
    """
    cmd: list[str] = [_BIN]
    if profile:
        cmd += ["--profile", profile]
    cmd += list(args) + ["--json"]

    # shell=False on purpose: cmd.exe treats "=" as a delimiter and mangles
    # arguments like --tpOrdPx=-1, which silently breaks bracket orders.
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip()[:400]
        raise OkxError(f"{' '.join(cmd)} -> exit {proc.returncode}: {detail}")

    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise OkxError(f"{' '.join(cmd)} -> unparsable output: {proc.stdout[:200]}") from exc

    # The CLI returns either a bare list or {endpoint, requestTime, data}.
    if isinstance(payload, dict) and "data" in payload:
        return payload["data"]
    return payload
