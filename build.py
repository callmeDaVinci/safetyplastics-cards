"""Generate one digital name card per person from people.json.

Usage:
    python build.py            -> writes docs/<slug>/index.html + docs/<slug>/<slug>.vcf
    python build.py --fragment -> also writes docs/_fragments/<slug>.html (page body only,
                                  for pasting into a host that supplies its own <html> wrapper)

Requires: pip install segno
"""
import base64
import html
import json
import re
import shutil
import sys
import urllib.parse
from pathlib import Path

import segno

ROOT = Path(__file__).parent
DIST = ROOT / "docs"
TEMPLATE = (ROOT / "template.html").read_text(encoding="utf-8")
CFG = json.loads((ROOT / "people.json").read_text(encoding="utf-8"))
SITE = CFG["site"]
FRAGMENT = "--fragment" in sys.argv


def data_uri(path: Path) -> str:
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode()


LOGOS = {
    "safety_logo": data_uri(ROOT / "assets" / "safety.png"),
    "sbb_logo": data_uri(ROOT / "assets" / "sbb.png"),
    "iso_logo": data_uri(ROOT / "assets" / "iso.png"),
}


def digits(s: str) -> str:
    return re.sub(r"\D", "", s)


def my_e164(local: str) -> str:
    """Malaysian local number (01x...) -> +601x..."""
    d = digits(local)
    if d.startswith("60"):
        return "+" + d
    return "+60" + d.lstrip("0")


def pretty(local: str) -> str:
    """0182342288 -> 018-234 2288 ; 01121234567 -> 011-2123 4567"""
    d = digits(local)
    if d.startswith("60"):
        d = "0" + d[2:]
    if len(d) == 10:
        return f"{d[:3]}-{d[3:6]} {d[6:]}"
    if len(d) == 11:
        return f"{d[:3]}-{d[3:7]} {d[7:]}"
    return local


def vcard(p: dict) -> str:
    parts = p["name"].split()
    last = parts[-1] if len(parts) > 1 else ""
    first = " ".join(parts[:-1]) if len(parts) > 1 else parts[0]
    adr = ";".join(["", "", ", ".join(SITE["address_lines"][:3]), "Semenyih", "Selangor", "43500", "Malaysia"])
    lines = [
        "BEGIN:VCARD",
        "VERSION:3.0",
        f"N:{last};{first};;;",
        f"FN:{p['name']}",
        f"ORG:{SITE['company']}",
        f"TITLE:{p['position']}",
        f"TEL;TYPE=CELL,VOICE:{my_e164(p['phone'])}",
        f"TEL;TYPE=WORK,VOICE:{my_e164(SITE['office_phone'])}",
        f"EMAIL;TYPE=INTERNET,WORK:{p['email']}",
        f"URL:{SITE['website']}",
        f"URL;TYPE=card:{SITE['base_url']}/{p['slug']}",
        f"ADR;TYPE=WORK:{adr}",
        "END:VCARD",
    ]
    return "\r\n".join(lines) + "\r\n"


def render(p: dict) -> str:
    card_url = f"{SITE['base_url']}/{p['slug']}"
    qr = segno.make(card_url, error="m")
    qr_svg = qr.svg_inline(scale=1, border=0, dark="#292e57", light=None,
                           svgclass=None, lineclass=None, omitsize=True)

    name_cn_block = f'<div class="name-cn">{html.escape(p["name_cn"])}</div>' if p.get("name_cn") else ""
    wa_text = urllib.parse.quote(f"Hi {p['name']}, ")

    ctx = {
        **LOGOS,
        "name": html.escape(p["name"]),
        "name_cn_block": name_cn_block,
        "position": html.escape(p["position"]),
        "email": p["email"],
        "phone_display": pretty(p["phone"]),
        "phone_pretty": my_e164(p["phone"])[:3] + " " + pretty(p["phone"])[1:],
        "phone_e164": my_e164(p["phone"]),
        "wa_number": my_e164(p["phone"]).lstrip("+"),
        "wa_text": wa_text,
        "vcf_file": f"{p['slug']}.vcf",
        "company": html.escape(SITE["company"]),
        "company_cn": SITE["company_cn"],
        "reg_no": SITE["reg_no"],
        "tagline": SITE["tagline"],
        "office_phone": SITE["office_phone"],
        "office_phone_e164": my_e164(SITE["office_phone"]),
        "website": SITE["website"],
        "website_label": SITE["website_label"],
        "address_html": "<br>".join(html.escape(l) for l in SITE["address_lines"]),
        "maps_query": urllib.parse.quote(SITE["maps_query"]),
        "card_url": card_url,
        "card_url_label": card_url.replace("https://", ""),
        "qr_svg": qr_svg,
    }
    out = TEMPLATE
    for k, v in ctx.items():
        out = out.replace("{{" + k + "}}", v)
    leftover = re.findall(r"{{\w+}}", out)
    if leftover:
        raise SystemExit(f"unfilled placeholders for {p['slug']}: {leftover}")
    return out


def wrap(fragment: str) -> str:
    return (
        "<!doctype html>\n<html lang=\"en\">\n<head>\n"
        "<meta charset=\"utf-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1, viewport-fit=cover\">\n"
        + fragment.split("<main", 1)[0]
        + "</head>\n<body>\n<main"
        + fragment.split("<main", 1)[1]
        + "\n</body>\n</html>\n"
    )


def main():
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()
    (DIST / ".nojekyll").write_text("")
    index_links = []
    for p in CFG["people"]:
        frag = render(p)
        d = DIST / p["slug"]
        d.mkdir()
        (d / "index.html").write_text(wrap(frag), encoding="utf-8")
        (d / f"{p['slug']}.vcf").write_text(vcard(p), encoding="utf-8", newline="")
        if FRAGMENT:
            fd = DIST / "_fragments"
            fd.mkdir(exist_ok=True)
            (fd / f"{p['slug']}.html").write_text(frag, encoding="utf-8")
        index_links.append(f'<li><a href="/{p["slug"]}/">{html.escape(p["name"])}</a> — {html.escape(p["position"])}</li>')
        print(f"built {p['slug']:10s} -> {SITE['base_url']}/{p['slug']}")

    # Root page: plain redirect to the company website so the bare domain isn't blank.
    (DIST / "index.html").write_text(
        "<!doctype html><meta charset='utf-8'>"
        f"<meta http-equiv='refresh' content='0;url={SITE['website']}'>"
        f"<title>Safety Plastics</title><a href='{SITE['website']}'>Safety Plastics Sdn Bhd</a>",
        encoding="utf-8",
    )
    # 404 for GitHub Pages / Cloudflare Pages
    (DIST / "404.html").write_text(
        "<!doctype html><meta charset='utf-8'><title>Card not found</title>"
        "<style>body{font-family:sans-serif;text-align:center;padding:60px 16px;color:#292e57}</style>"
        "<h1>Card not found</h1><p>Check the link, or visit "
        f"<a href='{SITE['website']}'>safetyplastics.com.my</a>.</p>",
        encoding="utf-8",
    )
    host = urllib.parse.urlparse(SITE["base_url"]).hostname
    (DIST / "CNAME").write_text(host + "\n")


if __name__ == "__main__":
    main()
