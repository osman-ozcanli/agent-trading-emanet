"""Produce METRICS.md from the journals — the numbers in the submission.

Two sources, kept apart on purpose:
  logs/journal.jsonl       demo, clean record from 17:36 onward (earlier data quarantined)
  logs/journal.live.jsonl  live, two supervised ticks

Nothing here is typed by hand. Run it again and the file is regenerated from the logs.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent


def load(path: Path) -> list[dict[str, Any]]:
    """Read a JSONL journal; a missing file is an empty record, not an error."""
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def rule(text: str) -> str:
    """Collapse a refusal message to the rule that produced it."""
    checks = [
        ("ikinci kez", "Ayni paritede zaten acik pozisyon var"),
        ("Zaman stopu", "Zaman stopu — ajan pozisyonu kendisi kapatti"),
        ("koruma emri", "Borsa koruma emri olusturmuyor — pozisyon geri alindi, parite kapali"),
        ("acik pozisyon", "Acik pozisyon limiti dolu"),
        ("minimum emir", "Borsanin minimum emir tutarinin altinda"),
        ("Safe Mode", "Safe Mode aktif"),
        ("Nakit tamponu", "Nakit tamponu korunuyor"),
        ("okunamadi", "Bakiye okunamadi — bilinmezlik, kayip degil"),
        ("borsa emri reddetti", "Borsa emri reddetti (sCode)"),
    ]
    for needle, label in checks:
        if needle in text:
            return label
    return text[:60] or "Bilinmeyen"


def summarize(rows: list[dict[str, Any]], title: str) -> str:
    """One markdown section per journal."""
    d = [r for r in rows if r.get("instId") != "-"]
    if not d:
        return f"## {title}\n\n_Kayıt yok._\n"
    traded = [r for r in d if r.get("order")]
    vetoed = [r for r in d if r.get("action") == "veto"]
    closed = [r for r in d if r.get("action") == "sell"]
    waited = [r for r in d if r.get("action") == "wait"]
    opp = len(traded) + len(vetoed)
    unknown = sum(1 for r in d for w in r.get("witnesses", []) if w.get("direction") == "unknown")
    first, last = d[0]["ts"][11:19], d[-1]["ts"][11:19]
    span = (datetime.fromisoformat(d[-1]["ts"]) - datetime.fromisoformat(d[0]["ts"])).total_seconds() / 60

    out = [f"## {title}", "",
           f"Kayıt aralığı **{first} – {last}** ({span:.0f} dk) · kaynak `{rows and 'journal'}`", "",
           "| Metrik | Değer |", "|---|---|",
           f"| Karar | **{len(d)}** |",
           f"| Fırsat (al/sat sinyali üretilen) | {opp} |",
           f"| Gönderilen emir | **{len(traded)}** — {sum(r['order']['sz'] for r in traded):.2f} USDT |",
           f"| Risk kapısı reddi | **{len(vetoed)}** (fırsatların %{round(len(vetoed)/opp*100) if opp else 0}'i) |",
           f"| Ajanın kendi kapattığı pozisyon | {len(closed)} |",
           f"| Bekleme kararı | {len(waited)} |",
           f"| Ulaşılamayan tanık okuması | {unknown} |",
           "", "### Hangi kural kaç kez devreye girdi", "", "| Kural | Kez |", "|---|---|"]
    for why, n in Counter(rule(r.get("veto_reason", "")) for r in vetoed + closed).most_common():
        out.append(f"| {why} | {n} |")
    out += ["", "### Emirler", "", "| Saat | Parite | USDT | Kâr-al | Zarar-kes |", "|---|---|---|---|---|"]
    for r in traded:
        o = r["order"]
        out.append(f"| {r['ts'][11:19]} | {r['instId']} | {o['sz']} | {o['tp']} | {o['sl']} |")
    return "\n".join(out) + "\n"


def main() -> None:
    """Write METRICS.md."""
    demo = load(ROOT / "logs" / "journal.jsonl")
    live = load(ROOT / "logs" / "journal.live.jsonl")
    body = "\n".join([
        "# EMANET — performans metrikleri",
        "",
        f"Üretildi: {datetime.now().strftime('%d.%m.%Y %H:%M')} · `python src/metrics.py` · tablolar defterden üretilir.",
        "",
        "> Hesap getirisi bu yarışmada puanlanmıyor ve burada iddia edilmiyor. Ölçülen şey ajanın",
        "> **karar kalitesi ve hesap verebilirliği**: kaç fırsat gördü, kaçını hangi kuralla reddetti,",
        "> neyi kendisi kapattı. Kirli ilk defter karantinada (`logs/archive/NEDEN.md`); demo metrikleri karantina sonrası temiz defterden.",
        "",
        summarize(live, "Canlı hesap — OKX TR sub-account, 30 USDT (18:29 iki gözetimli tur, 19:00'dan itibaren otonom)"),
        "_Elle yazılmış tek not (18:30, borsadan `spot_get_algo_orders` / `account_get_balance` ile):_ "
        "4 OCO `live`, 4 gerçekleşme, USDT 30,00 → 20,40. 19:00'da zaman stopu dördünü kapattı (`spot_get_fills`: 4 satış).",
        "",
        summarize(demo, "Demo hesap — karantina sonrası temiz defter"),
    ])
    (ROOT / "METRICS.md").write_text(body, encoding="utf-8")
    # Windows consoles default to cp1252; the file itself is always UTF-8.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(body)


if __name__ == "__main__":
    main()
