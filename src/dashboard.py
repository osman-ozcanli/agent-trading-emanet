"""EMANET dashboard — a local page that shows what the agent did and what it refused.

Run:  python src/dashboard.py      then open http://localhost:8787

Standard library only: no Flask, no build step, nothing to install. The page
reads the same journal the agent writes, so it is always the truth, never a
second copy of it.

The centre of this page is the REFUSAL log. Most bots only speak when they
trade. This one is judged by what it declined to do.
"""
from __future__ import annotations

import json
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

from okx import load_config

ROOT = Path(__file__).resolve().parent.parent
PORT = 8787


def read_journal(cfg: dict[str, Any], limit: int = 200) -> list[dict]:
    """Latest decisions, newest first."""
    path = ROOT / cfg["logging"]["journal"]
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows[::-1][:limit]


def read_state(cfg: dict[str, Any]) -> dict[str, Any]:
    """Agent state: open positions, safe mode, day's starting equity."""
    path = ROOT / cfg["logging"].get("state", f'{cfg["logging"]["dir"]}/state.json')
    if not path.exists():
        return {"open": {}, "safe_mode": False, "start_equity": 0}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"open": {}, "safe_mode": False, "start_equity": 0}


def summary(rows: list[dict]) -> dict[str, Any]:
    """Headline metrics — the numbers that go in the submission."""
    decisions = [r for r in rows if r.get("instId") != "-"]
    traded = [r for r in decisions if r.get("order")]
    vetoed = [r for r in decisions if r.get("action") == "veto"]
    waited = [r for r in decisions if r.get("action") == "wait"]
    opportunities = len(traded) + len(vetoed)

    # Group refusals by reason. One rule firing 200 times is not 200 judgments,
    # and listing it 200 times buries the rules that fired once.
    reasons: dict[str, int] = {}
    for r in vetoed:
        key = _reason_key(r.get("veto_reason", ""))
        reasons[key] = reasons.get(key, 0) + 1

    return {
        "decisions": len(decisions),
        "opportunities": opportunities,
        "traded": len(traded),
        "vetoed": len(vetoed),
        "waited": len(waited),
        "refusal_rate": round(len(vetoed) / opportunities * 100) if opportunities else 0,
        "refusal_reasons": sorted(reasons.items(), key=lambda kv: -kv[1]),
        "rules_fired": len(reasons),
    }


def _reason_key(text: str) -> str:
    """Collapse a refusal to its rule, dropping the changing numbers."""
    if "ikinci kez" in text:
        return "Ayni paritede zaten acik pozisyon var"
    if "Zaman stopu" in text:
        return "Zaman stopu — ajan pozisyonu kendisi kapatti"
    if "acik pozisyon" in text:
        return "Acik pozisyon limiti dolu"
    if "minimum emir" in text:
        return "Borsanin minimum emir tutarinin altinda"
    if "Safe Mode" in text:
        return "Safe Mode aktif"
    if "Gunluk kayip" in text:
        return "Gunluk kayip limiti asildi"
    if "bakiye" in text:
        return "Yetersiz bakiye"
    return text[:60] or "Bilinmeyen"


def payload() -> dict[str, Any]:
    """Everything the page needs, in one response."""
    cfg = load_config()
    rows = read_journal(cfg)
    st = read_state(cfg)
    last_ts = rows[0]["ts"] if rows else None
    age = None
    if last_ts:
        try:
            age = (datetime.now() - datetime.fromisoformat(last_ts)).total_seconds()
        except ValueError:
            age = None

    return {
        # Heartbeat: "is it still alive?" must be answerable at a glance. A quiet
        # agent holding four positions looks identical to a dead one otherwise.
        "heartbeat": {"last_ts": last_ts, "age_seconds": age,
                      "interval": cfg["loop"]["interval_seconds"]},
        "config": {
            "mode": cfg["capital"]["mode"],
            "cap": cfg["capital"]["virtual_cap_usdt"],
            "pairs": cfg["universe"]["pairs"],
            "risk": cfg["risk"],
            "dry_run": cfg["execution"]["dry_run"],
        },
        "state": {"open": st.get("open", {}), "safe_mode": st.get("safe_mode", False)},
        "summary": summary(rows),
        "rows": rows[:60],
    }


PAGE = """<!doctype html>
<html lang="tr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>EMANET — hesap veren otonom trading ajani</title>
<style>
:root{--bg:#0d1117;--panel:#161b22;--line:#272e38;--ink:#e6edf3;--dim:#8b949e;
--buy:#3fb950;--sell:#f85149;--veto:#d29922;--wait:#58a6ff;}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
font:14px/1.55 ui-sans-serif,system-ui,"Segoe UI",Roboto,sans-serif}
.wrap{max-width:1180px;margin:0 auto;padding:24px 16px 64px}
header{display:flex;flex-wrap:wrap;gap:12px;align-items:baseline;justify-content:space-between;
border-bottom:1px solid var(--line);padding-bottom:16px;margin-bottom:24px}
h1{margin:0;font-size:26px;letter-spacing:.4px}
h1 span{color:var(--dim);font-weight:400;font-size:14px;margin-left:10px;letter-spacing:0}
.badges{display:flex;gap:8px;flex-wrap:wrap}
.badge{border:1px solid var(--line);border-radius:999px;padding:4px 12px;font-size:12px;color:var(--dim)}
.badge.on{border-color:var(--buy);color:var(--buy)}
.badge.warn{border-color:var(--veto);color:var(--veto)}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-bottom:12px}
.stat{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:14px 16px}
.stat b{display:block;font-size:28px;font-weight:600;letter-spacing:-.5px}
.stat small{color:var(--dim);font-size:12px;text-transform:uppercase;letter-spacing:.6px}
.stat.hero b{color:var(--veto)}
.lead{background:var(--panel);border:1px solid var(--line);border-left:3px solid var(--veto);
border-radius:10px;padding:14px 18px;margin:12px 0 28px;color:var(--dim)}
.lead b{color:var(--ink)}
h2{font-size:13px;text-transform:uppercase;letter-spacing:1px;color:var(--dim);
margin:28px 0 12px;font-weight:600}
.card{background:var(--panel);border:1px solid var(--line);border-radius:10px;
padding:14px 16px;margin-bottom:10px;border-left:3px solid var(--line)}
.card.buy{border-left-color:var(--buy)} .card.sell{border-left-color:var(--sell)}
.card.veto{border-left-color:var(--veto)} .card.wait{border-left-color:var(--line)}
.card h3{margin:0 0 8px;font-size:15px;display:flex;gap:10px;align-items:center;flex-wrap:wrap}
.tag{font-size:11px;padding:2px 8px;border-radius:5px;letter-spacing:.5px;font-weight:600}
.tag.buy{background:rgba(63,185,80,.15);color:var(--buy)}
.tag.sell{background:rgba(248,81,73,.15);color:var(--sell)}
.tag.veto{background:rgba(210,153,34,.15);color:var(--veto)}
.tag.wait{background:rgba(88,166,255,.12);color:var(--wait)}
.ts{color:var(--dim);font-size:12px;margin-left:auto;font-variant-numeric:tabular-nums}
.w{display:flex;gap:8px;margin:3px 0;font-size:13px;color:var(--dim)}
.w i{font-style:normal;min-width:96px;color:var(--ink);font-size:12px;
text-transform:uppercase;letter-spacing:.5px}
.reason{margin-top:10px;padding:9px 12px;background:rgba(210,153,34,.08);
border-radius:6px;color:var(--veto);font-size:13px}
.order{margin-top:10px;padding:9px 12px;background:rgba(63,185,80,.07);
border-radius:6px;color:var(--buy);font-size:13px;font-variant-numeric:tabular-nums}
.muted{color:var(--dim)}
footer{margin-top:40px;padding-top:16px;border-top:1px solid var(--line);
color:var(--dim);font-size:12px}
@media(max-width:520px){.stat b{font-size:22px}h1{font-size:20px}}
</style></head><body>
<div class="wrap">
<header>
  <h1>EMANET <span>hesap veren otonom trading ajani</span></h1>
  <div class="badges" id="badges"></div>
</header>
<div class="stats" id="stats"></div>
<div class="lead" id="lead"></div>
<h2>Hangi kural kac kez devreye girdi</h2>
<div id="rules"></div>
<h2>Karar akisi</h2>
<div id="feed"></div>
<footer>Sayfa 5 saniyede bir kendini yeniler &middot; veri kaynagi: logs/journal.jsonl</footer>
</div>
<script>
const ICON={buy:"\\u2191",sell:"\\u2193",wait:"\\u2014",unknown:"?",veto:"\\u26d4"};
const VERB={buy:"ALIM",sell:"SATIM",wait:"BEKLEDI",veto:"REDDEDILDI"};
function esc(s){return String(s??"").replace(/[&<>]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;"}[c]));}
function hhmm(ts){return (ts||"").slice(11,19);}
async function tick(){
  const d = await (await fetch("/api/state")).json();
  const s = d.summary, c = d.config, st = d.state;

  document.getElementById("badges").innerHTML =
    `<span class="badge ${c.mode==='demo'?'on':'warn'}">${c.mode.toUpperCase()} hesap</span>`+
    `<span class="badge">${c.cap} USDT sermaye</span>`+
    `<span class="badge">${c.pairs.length} parite</span>`+
    `<span class="badge">acik pozisyon ${Object.keys(st.open).length}/${c.risk.max_open_positions}</span>`+
    (st.safe_mode?`<span class="badge warn">SAFE MODE</span>`:``) + hb(d.heartbeat);

  document.getElementById("stats").innerHTML = [
    ["karar",s.decisions],["firsat",s.opportunities],["islem",s.traded],
    ["reddedilen",s.vetoed,"hero"],["red orani","%"+s.refusal_rate,"hero"],["devreye giren kural",s.rules_fired]
  ].map(([k,v,cls])=>`<div class="stat ${cls||''}"><b>${v}</b><small>${k}</small></div>`).join("");

  document.getElementById("lead").innerHTML =
    `Ajan <b>${s.opportunities}</b> firsat gordu, <b>${s.vetoed}</b> tanesini kendi kurallari `+
    `yuzunden <b>reddetti</b>, <b>${s.traded}</b> islem acti. `+
    `Her karar — reddedilenler dahil — gerekcesiyle kayitli.`;

  document.getElementById("rules").innerHTML = (s.refusal_reasons||[]).map(([why,n])=>
    `<div class="card veto"><h3>${esc(why)}<span class="tag veto">${n} kez</span></h3></div>`
  ).join("") || `<div class="card wait muted">Henuz hicbir kural devreye girmedi.</div>`;

  document.getElementById("feed").innerHTML = d.rows.filter(r=>r.instId!=="-").map(r=>{
    const a = r.action||"wait";
    const w = (r.witnesses||[]).map(x=>
      `<div class="w"><i>${esc(x.witness)}</i><span>${ICON[x.direction]||""} ${esc(x.reason)}</span></div>`).join("");
    const veto = r.veto_reason?`<div class="reason">\\u26d4 ${esc(r.veto_reason)}</div>`:"";
    const o = r.order?`<div class="order">Emir ${o_(r)} &middot; kar-al ${r.order.tp} &middot; `+
      `zarar-kes ${r.order.sl} &middot; <span class="muted">${esc(r.order.clOrdId)}</span>`+
      (r.dry_run?' <span class="muted">(kuru calisma)</span>':'')+`</div>`:"";
    return `<div class="card ${a}"><h3>${esc(r.instId)}`+
      `<span class="tag ${a}">${VERB[a]||a}</span><span class="ts">${hhmm(r.ts)}</span></h3>`+
      `${w}${veto}${o}</div>`;
  }).join("") || `<div class="card wait muted">Henuz karar yok.</div>`;
}
function o_(r){return r.order.sz+" USDT";}
function hb(h){
  if(!h||h.age_seconds==null) return `<span class="badge warn">veri yok</span>`;
  const a=Math.round(h.age_seconds), n=h.interval||180;
  const t=(h.last_ts||"").slice(11,19);
  // Alive while the last decision is younger than two tick intervals.
  const ok = a < n*2;
  return `<span class="badge ${ok?'on':'warn'}">`+
    (ok?"● canli":"● yanit yok")+` &middot; son karar ${t} (${a} sn once)</span>`;
}
tick(); setInterval(tick,5000);
</script></body></html>"""


class Handler(BaseHTTPRequestHandler):
    """Two routes: the page, and the JSON it polls."""

    def do_GET(self) -> None:  # noqa: N802 — stdlib naming
        if self.path.startswith("/api/state"):
            body = json.dumps(payload(), ensure_ascii=False).encode("utf-8")
            ctype = "application/json; charset=utf-8"
        else:
            body = PAGE.encode("utf-8")
            ctype = "text/html; charset=utf-8"
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args: Any) -> None:
        """Silence per-request logging; the agent's output is what matters."""


def main() -> None:
    """Serve the dashboard until interrupted."""
    print(f"EMANET paneli: http://localhost:{PORT}")
    HTTPServer(("127.0.0.1", PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()
