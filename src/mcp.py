"""MCP client — the agent's primary path into OKX Agent Trade Kit.

ATK exposes 168 tools over MCP (stdio, JSON-RPC). This module speaks that
protocol directly, so the agent is a first-class MCP client rather than a
process that shells out to a CLI.

One long-lived server process per profile:
  okx-demo -> orders, balances      (demo key, trade permission)
  okx-prod -> smartmoney, news      (live key, READ-ONLY)

If MCP is unavailable the caller falls back to the CLI. Two independent paths
to the same exchange is not duplication — it is why the loop stays alive.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import threading
from typing import Any

_BIN = shutil.which("okx-trade-mcp") or "okx-trade-mcp"
_clients: dict[str, "MCPClient"] = {}
_lock = threading.Lock()


class MCPError(RuntimeError):
    """Raised when a tool call fails or the server cannot be reached."""


class MCPClient:
    """A single stdio MCP session, bound to one credential profile."""

    def __init__(self, profile: str, modules: str = "all") -> None:
        self.profile = profile
        self._id = 0
        self.proc = subprocess.Popen(
            [_BIN, "--profile", profile, "--modules", modules],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            text=True, encoding="utf-8", errors="replace", bufsize=1,
        )
        self._handshake()

    def _next_id(self) -> int:
        self._id += 1
        return self._id

    def _send(self, obj: dict[str, Any]) -> None:
        assert self.proc.stdin
        self.proc.stdin.write(json.dumps(obj) + "\n")
        self.proc.stdin.flush()

    def _read(self, timeout: int = 30) -> dict[str, Any] | None:
        """Read the next JSON-RPC message, skipping any non-JSON server chatter."""
        assert self.proc.stdout
        while True:
            line = self.proc.stdout.readline()
            if not line:
                return None
            line = line.strip()
            if line.startswith("{"):
                try:
                    return json.loads(line)
                except json.JSONDecodeError:
                    continue

    def _handshake(self) -> None:
        self._send({"jsonrpc": "2.0", "id": self._next_id(), "method": "initialize",
                    "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                               "clientInfo": {"name": "emanet", "version": "1.0"}}})
        if self._read() is None:
            raise MCPError(f"MCP handshake failed for profile {self.profile}")
        self._send({"jsonrpc": "2.0", "method": "notifications/initialized"})

    def call(self, tool: str, args: dict[str, Any] | None = None) -> Any:
        """Invoke one ATK tool and return its decoded payload."""
        self._send({"jsonrpc": "2.0", "id": self._next_id(), "method": "tools/call",
                    "params": {"name": tool, "arguments": args or {}}})
        msg = self._read()
        if msg is None:
            raise MCPError(f"{tool}: MCP server closed the connection")
        if "error" in msg:
            raise MCPError(f"{tool}: {msg['error'].get('message', msg['error'])}")

        result = msg.get("result", {})
        if result.get("isError"):
            raise MCPError(f"{tool}: {_text(result)[:300]}")

        payload = _decode(result)
        _raise_on_exchange_error(tool, payload)
        return payload

    def alive(self) -> bool:
        return self.proc.poll() is None

    def close(self) -> None:
        try:
            self.proc.terminate()
        except OSError:
            pass


def client(profile: str) -> MCPClient:
    """Get (or start) the long-lived session for a profile. Restarts a dead one."""
    with _lock:
        existing = _clients.get(profile)
        if existing and existing.alive():
            return existing
        _clients[profile] = MCPClient(profile)
        return _clients[profile]


def tool(name: str, args: dict[str, Any] | None = None, profile: str = "okx-demo") -> Any:
    """Call an ATK tool over MCP."""
    return client(profile).call(name, args)


def shutdown() -> None:
    """Stop every server process."""
    with _lock:
        for c in _clients.values():
            c.close()
        _clients.clear()


def _raise_on_exchange_error(tool: str, payload: Any) -> None:
    """A 200 response is not an accepted order.

    OKX answers rejected orders inside the payload: sCode "51155" ("this pair is
    restricted"), "51000" (bad parameter), and so on. Treating those as success
    is how a journal ends up recording trades that never happened — which, for a
    system whose whole claim is an honest audit trail, is the worst possible bug.
    """
    # Responses arrive either bare or wrapped as {endpoint, requestTime, data}.
    # Checking only the outer level is how a rejection slips through unnoticed.
    if isinstance(payload, dict) and "data" in payload:
        payload = payload["data"]
    rows = payload if isinstance(payload, list) else [payload]
    for row in rows:
        if not isinstance(row, dict):
            continue
        code = str(row.get("sCode", "0") or "0")
        if code not in ("0", ""):
            raise MCPError(f"{tool}: borsa emri reddetti (sCode {code}) — "
                           f"{row.get('sMsg', '').strip()}")


def _text(result: dict[str, Any]) -> str:
    """Join the text blocks of an MCP tool result."""
    return "\n".join(b.get("text", "") for b in result.get("content", [])
                     if b.get("type") == "text")


def _decode(result: dict[str, Any]) -> Any:
    """Tool results arrive as text blocks; most carry JSON inside."""
    raw = _text(result).strip()
    if not raw:
        return result.get("structuredContent", [])
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return raw
    # The CLI-shaped payloads wrap rows under "data".
    if isinstance(payload, dict) and "data" in payload:
        return payload["data"]
    return payload
