"""Render "Scan or Tap" notice images (PNG) for people in people.json.

Usage:
    python make_notice.py            -> all people
    python make_notice.py junong casey

Output: assets/nfc-notice/scan-or-tap-<slug>.png  (2400 x 1400 px, transparent corners)
Needs Google Chrome or Microsoft Edge installed (rendered headless).
"""
import html
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import segno

ROOT = Path(__file__).parent
OUT = ROOT / "assets" / "nfc-notice"
CFG = json.loads((ROOT / "people.json").read_text(encoding="utf-8"))
SITE = CFG["site"]
TEMPLATE = (ROOT / "notice.html").read_text(encoding="utf-8")

BROWSERS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]
BROWSER = next((b for b in BROWSERS if Path(b).exists()), None)
if not BROWSER:
    raise SystemExit("Chrome or Edge not found")

import base64


def data_uri(p: Path) -> str:
    return "data:image/png;base64," + base64.b64encode(p.read_bytes()).decode()


LOGOS = {"safety_logo": data_uri(ROOT / "assets" / "safety.png"), "sbb_logo": data_uri(ROOT / "assets" / "sbb.png")}


def render(p: dict) -> Path:
    url = f"{SITE['base_url']}/{p['slug']}"
    qr = segno.make(url, error="m").svg_inline(scale=1, border=0, dark="#292e57", light=None,
                                                svgclass=None, lineclass=None, omitsize=True)
    ctx = {
        **LOGOS,
        "name": html.escape(p["name"]),
        "name_cn_inline": f'<span class="cn">{html.escape(p["name_cn"])}</span>' if p.get("name_cn") else "",
        "position": html.escape(p.get("position", "")),
        "qr_svg": qr,
        "card_url_label": url.replace("https://", ""),
    }
    page = TEMPLATE
    for k, v in ctx.items():
        page = page.replace("{{" + k + "}}", v)
    if re.search(r"{{\w+}}", page):
        raise SystemExit("unfilled placeholder")

    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / f"scan-or-tap-{p['slug']}.png"
    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / "page.html"
        src.write_text(page, encoding="utf-8")
        subprocess.run([
            BROWSER, "--headless=new", "--disable-gpu", "--hide-scrollbars",
            "--default-background-color=00000000",
            "--window-size=1200,700", "--force-device-scale-factor=2",
            "--virtual-time-budget=10000",
            f"--screenshot={out}", src.as_uri(),
        ], check=True, capture_output=True, timeout=120)
    return out


def main():
    wanted = set(sys.argv[1:])
    for p in CFG["people"]:
        if wanted and p["slug"] not in wanted:
            continue
        print("rendered", render(p))


if __name__ == "__main__":
    main()
