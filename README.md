# Safety Plastics digital name cards

One web page per staff member, e.g. `https://card.safetyplastics.com.my/junong`.
Each card has one-tap WhatsApp / Call / Email, a Save-to-Contacts (.vcf) button,
a QR code, and the company details from the printed card.

## Files

| File | What it is |
|---|---|
| `people.json` | The list of people + company details. **This is the only file you edit day to day.** |
| `template.html` | The card design (HTML/CSS). Same for everyone. |
| `assets/` | Safety logo, SBB logo, ISO badge. |
| `build.py` | Generates the `docs/` folder from the two files above. |
| `docs/` | The finished website. Upload this folder (or push it) to the host. |

## Add or change a person

1. Open `people.json` and add a block:

   ```json
   {
     "slug": "casey",
     "name": "Casey Hor Kar Chun",
     "name_cn": "",
     "position": "R&D Engineer",
     "phone": "0196080430",
     "email": "casey@safetyplastics.com.my"
   }
   ```

   `slug` becomes the URL (`/casey`). Lowercase letters only, no spaces.
   `name_cn` is optional (Chinese name shown under the English name).
   `phone` is the Malaysian mobile as normally written; the script converts it
   for WhatsApp (`wa.me/60196080430`) and the vCard (`+60196080430`).

2. Run the build:

   ```bash
   pip install segno
   python build.py
   ```

3. Upload / push the `docs/` folder. Done. The new card is live at
   `https://card.safetyplastics.com.my/<slug>`.

## Hosting (one-time setup)

The main website is on Wix, so the cards live on a **subdomain** that points to a
free static host. Recommended: **Cloudflare Pages** or **GitHub Pages**. Both are
free, give HTTPS automatically, and take a folder of HTML files.

### Option A: GitHub Pages

1. Create a **public** GitHub repository named `safetyplastics-cards`
   (a custom domain on a private repo needs a paid GitHub plan).
2. Push this whole project to its `main` branch:

   ```bash
   git remote add origin https://github.com/callmeDaVinci/safetyplastics-cards.git
   git push -u origin main
   ```

3. Repo → Settings → Pages → Build and deployment → Source: **Deploy from a
   branch** → Branch: `main`, folder: `/docs` → Save.
4. Same page → Custom domain: `card.safetyplastics.com.my` → Save.
   Tick "Enforce HTTPS" once the DNS check passes (`docs/CNAME` already
   contains the hostname).

After every `python build.py`, publish the change with:

```bash
git add -A
git commit -m "Update cards"
git push
```

### Option B: Cloudflare Pages

1. Cloudflare dashboard → Workers & Pages → Create → Pages → Upload assets.
2. Drag the `docs/` folder in. Name the project `safetyplastics-cards`.
3. Project → Custom domains → add `card.safetyplastics.com.my`.

### DNS (in Wix, where the domain is managed)

Wix → Domains → safetyplastics.com.my → Manage DNS records → Add CNAME:

| Host | Points to |
|---|---|
| `card` | `callmedavinci.github.io` (GitHub Pages) **or** `safetyplastics-cards.pages.dev` (Cloudflare Pages) |

Wait 10–30 minutes for DNS, then `https://card.safetyplastics.com.my/junong` works.

To change the subdomain (e.g. `me.safetyplastics.com.my`), edit `base_url` in
`people.json`, rebuild, and update the CNAME record. The QR codes and the vCard
link embed the URL, so always rebuild after changing it.

## Design notes

* Colours are taken from the printed card: navy `#292e57`, red `#ed1c24`.
* Fonts: Barlow Condensed (headings) + Barlow (text) from Google Fonts, with
  system fallbacks. Chinese text uses Noto Sans TC.
* Logos are embedded inside each page, so every card is a single self-contained
  HTML file plus its `.vcf`.

## Staff directory (password protected)

`https://card.safetyplastics.com.my/` asks for a password and then lists every
card with Open / Copy link / WhatsApp buttons. The list is encrypted inside the
page and decrypted in the browser, so the host never sees the password.

The password lives in `directory.auth` on this PC only (git-ignored). To change it:

```bash
python build.py --password "NEW_PASSWORD"
git add -A
git commit -m "Change directory password"
git push
```

If `directory.auth` is missing (e.g. on a new PC), the build falls back to
`123456` and the page shows a warning banner until it is changed.
