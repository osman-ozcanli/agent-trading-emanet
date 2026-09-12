"""Refresh the numbers on slides 5 and 7 of EMANET-sunum.pptx from METRICS.md.

Run right before presenting:  python src/sunum_guncelle.py
Always rebuilds from the pristine export (EMANET-sunum.orig.pptx, 19:10 numbers),
so it is idempotent. Only text nodes change; layout and images stay as exported.
"""
from __future__ import annotations

import re
import shutil
import zipfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PPTX = ROOT / "EMANET-sunum.pptx"
ORIG = ROOT / "EMANET-sunum.orig.pptx"


def _section(md: str, title: str) -> dict[str, str]:
    """Metric table of one section (demo or live) as {label: value}, '**' stripped."""
    body = md.split(title, 1)[1].split("\n## ", 1)[0]
    rows = re.findall(r"^\| ([^|]+?) \| ([^|]+?) \|$", body, re.M)
    return {k.strip(): v.replace("*", "").strip() for k, v in rows}


def _num(text: str) -> str:
    """First integer in a metric cell, e.g. '166 (fırsatların %89'i)' -> '166'."""
    return re.search(r"\d+", text).group(0)


def main() -> None:
    """Rewrite the stat text on the two number-heavy slides."""
    if not ORIG.exists():
        shutil.copy(PPTX, ORIG)
    md = (ROOT / "METRICS.md").read_text(encoding="utf-8")
    demo = _section(md, "## Demo hesap")
    live = _section(md, "## Canlı hesap")
    now = datetime.now().strftime("%H:%M")
    red_pct = re.search(r"%(\d+)", demo["Risk kapısı reddi"]).group(1)

    swaps = {
        "ppt/slides/slide5.xml": [
            ("19:10 itibarıyla demo hesap:", f"{now} itibarıyla demo hesap:"),
            ("<a:t>279</a:t>", f"<a:t>{demo['Karar']}</a:t>"),
            ("156 fırsat değerlendirildi", f"{demo['Fırsat (al/sat sinyali üretilen)']} fırsat değerlendirildi"),
            ("<a:t>136</a:t>", f"<a:t>{_num(demo['Risk kapısı reddi'])}</a:t>"),
            (re.compile(r"%87(&apos;|'|’)si"), lambda m: f"%{red_pct}{m.group(1)}si"),
            ("<a:t>20</a:t>", f"<a:t>{_num(demo['Gönderilen emir'])}</a:t>"),
            (re.compile(r"20(&apos;|'|’)si de ajan tarafından kapatıldı"), "hepsi ajan tarafından kapatıldı"),
        ],
        "ppt/slides/slide7.xml": [
            ("<a:t>19:10</a:t>", f"<a:t>{now}</a:t>"),
            ("48 karar, 12 emir, 8 kapanış, 13 red",
             f"{live['Karar']} karar, {_num(live['Gönderilen emir'])} emir, "
             f"{live['Ajanın kendi kapattığı pozisyon']} kapanış, {_num(live['Risk kapısı reddi'])} red"),
        ],
    }
    tmp = PPTX.with_suffix(".tmp")
    with zipfile.ZipFile(ORIG) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename in swaps:
                x = data.decode("utf-8")
                for old, new in swaps[item.filename]:
                    if isinstance(old, re.Pattern):
                        x, n = old.subn(new, x, count=1)
                    else:
                        n = x.count(old)
                        x = x.replace(old, new, 1)
                    if not n:
                        print(f"  uyari: bulunamadi {old!r}")
                data = x.encode("utf-8")
            zout.writestr(item, data)
    shutil.move(tmp, PPTX)
    print(f"EMANET-sunum.pptx guncellendi ({now}): demo {demo['Karar']} karar / %{red_pct} red · "
          f"canli {live['Karar']} karar / {_num(live['Gönderilen emir'])} emir")


if __name__ == "__main__":
    main()
