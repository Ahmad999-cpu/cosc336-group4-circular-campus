# Feature 1: QR codes for assets

**Module:** Catalogue (`apps/catalogue/qr.py`, views `qr_label`, `qr_download`) · **New dependency:** `segno`

## What it does

Every asset that is still in the register has a QR label. The custodian, and people who register, hold
custody of or maintain that unit's items, open **QR label** in the asset panel. From there they can print the label
or download it as an SVG file. Scanning the label opens the asset page.

| Screen | URL | Who |
|---|---|---|
| Asset page (what the code opens) | `/assets/<id>/` | Signed in; the existing `can_view` rule |
| Label page: preview, Print, Download | `/assets/<id>/qr/` | `can_label`: custodian, `asset.register`, `asset.custody` or `maintenance.record` for the unit |
| Label file | `/assets/<id>/qr/label.svg` | Same as the label page |

## Design decisions

**Q1. The code holds only the address.** The payload is `SITE_BASE_URL + /assets/<uuid>/`. The name, value,
owner and custodian are never in it. The asset id is a random UUID, so the address can't be guessed.
*Why:* the brief says "do not put sensitive asset information directly inside the QR code". The address is
also stable: renaming or moving the item doesn't break a printed label.

**Q2. No way around access control.** The code opens the normal asset page. It still needs a sign-in, with a
redirect back after sign-in, and `can_view` still applies. A person who may not see the item gets the same
"isn't available to you" page as someone who scans a label for a missing item. The page never confirms that
the asset exists. *Found while building:* the demo sign-in followed any `next` address, including outside sites.
It now only follows addresses on this site (`url_has_allowed_host_and_scheme`).

**Q3. Configured base address, never a fixed host.** `SITE_BASE_URL` in `.env` is the address printed in labels.
When it is empty, the address of the incoming request is used. That only works for hosts in
`DJANGO_ALLOWED_HOSTS`, so a forged Host header can't put another address in a label. In that case the label
page shows a warning, because a label printed from `localhost` won't open on a phone.

**Q4. The label identifies the asset.** The printed label and the downloaded SVG both show the name,
category, owning unit and an 8-character **Asset ID**: the first part of the UUID, which a person can read
out or type. This is descriptive text that is already visible on the item, not anything sensitive. We offer
SVG rather than PNG because SVG can carry the text without Pillow, prints sharply at any size and opens in
browsers and Word.

**Q5. Removed items.** Donated, recycled and disposed items get no new label: the page explains why and the
download returns 404. If an old label is scanned, the asset page shows "No longer in service" above the kept
record and history. Retired items show "Waiting for its final end-of-life step".

**Q6. Error correction level M** (about 15 % of the label can be damaged and it still scans).

## Setup

`pip install -r requirements.txt` (adds `segno`). Set `SITE_BASE_URL` in `.env`. For a phone demo on the same
Wi-Fi, use `http://<laptop-IP>:8000`, add that IP to `DJANGO_ALLOWED_HOSTS`, and start the server with
`python manage.py runserver 0.0.0.0:8000`.

## Tests

`tests/test_qr.py` (14 tests) covers:
- the payload uses the configured base address and only the id;
- the request-host fallback, and the refusal when there is no base address and no request;
- the label text and escaping;
- who may label;
- sign-in redirect on scan, the role-limited page, the hidden unpublished item, the unknown id;
- download headers;
- removed items;
- the open-redirect fix.
