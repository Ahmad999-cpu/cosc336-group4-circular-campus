# Public guest site (Home, How it works, Contact)

**Module:** `apps/guest` (views, form, delivery service, `ContactMessage` model) · **Templates:** `apps/guest/templates/guest/` ·
**Styles:** `static/css/guest.css` · **Script:** `static/js/guest.js` · **Images:** `static/img/guest/`

| Page | Address | Notes |
|---|---|---|
| Home | `/` (visitors only; signed-in people still get their dashboard) | Headline, intro, calls to action, video area |
| How it works | `/how-it-works/` | Wide browse image with overlay, four alternating steps, administrators section |
| Contact | `/contact/` | Phone and email links, contact form |
| Sign in | `/accounts/login/` | Unchanged; linked from the header |

## Settings (`.env`)

| Setting | Default | What it does |
|---|---|---|
| `BRAND_NAME` | `Circular Campus` | Product name on every guest page. A rename (e.g. Ouro) is this one line for the guest site; the signed-in app still writes the name directly in its templates |
| `GUEST_CTA_URL` | empty = the sign-in page | Where "Create your account", "Get started" and "Explore the platform" go. There is no self-registration in the app today |
| `GUEST_HOME_VIDEO` | empty = placeholder | A file under `static/` (e.g. `video/intro.mp4`) or a full `https://` URL |
| `GUEST_HOME_VIDEO_POSTER` | empty | Optional still image shown before the video plays |
| `CONTACT_PHONE`, `CONTACT_EMAIL` | 0505733540, circularcampus.team@gmail.com | Shown on the Contact page |
| `CONTACT_RECIPIENT` | circularcampus.team@gmail.com | Where form messages are delivered |
| `CONTACT_RATE_LIMIT` | 5 | Messages per hour per visitor address |
| `EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`, `DEFAULT_FROM_EMAIL` | console backend | Real delivery needs SMTP (below). The password stays on the server; it is never sent to the browser |

## Turning on real e-mail delivery (Gmail example)

1. On the Google account, turn on 2-Step Verification, then create an **App password** (Google Account, Security, App passwords).
2. In `.env` on the server:
   ```
   EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_USE_TLS=1
   EMAIL_HOST_USER=<the Gmail address>
   EMAIL_HOST_PASSWORD=<the 16-character app password>
   DEFAULT_FROM_EMAIL=<the same Gmail address>
   ```
3. Restart the site and send a test message from `/contact/`. The page says "Thank you, your message has been sent" only when the mail server accepted it.

Until then the form **saves** every message (Django admin site → Contact messages) and tells the visitor it was not emailed, with the phone and email to use instead. If SMTP is set up but fails, the message is kept with the error and the visitor is told to email or call.

## Spam protection

A hidden "website" field (filled only by bots: discarded quietly), a signed timestamp (sent in under 3 seconds or tampered with: the person is asked to send again, with what they typed kept; older than 6 hours: same), and a per-visitor limit of 5 messages an hour. Inputs are validated on the server; errors are announced to screen readers.

## Images

Every product image is a real screenshot of this app with the demo data, labelled "Demo data", in English (`<name>.png`) and Arabic (`<name>-ar.png`): `browse`, `step-find`, `step-list`, `step-claim`, `step-impact`, `admin`. To update one, replace the file with the same name. The supplied Warp It screenshots were used only as layout references; none of their graphics or branding is used.

## Language

The selector (UAE flag + العربية, UK flag + English) uses Django's language switch, which stores the choice in the `django_language` cookie, so returning visitors get the same language. Arabic switches the whole page to right-to-left, including the product screenshots.

## Home: "Why organisations use" and Pricing (Nov 2026)

- **Why organisations use Circular Campus:** six boxes, each describing something the app already does
  (purchase check, smart matching, approvals within spending limits, sustainability reports with locally selected
  carbon factors, QR tags / CSV import / asset history, Arabic and English with AED pricing).
- **Pricing** (`#pricing`, linked from the top nav and the footer):
  - Prices come from `apps/sustainability/calculator.py` (`MONTHLY_PRICE`, `VAT_RATE`), the same table the savings
    calculator uses. `apps/guest/pricing.py` maps the visitor-facing types onto the calculator's three groups:
    universities and hospitals; schools and hotels; offices and consultancies.
    Charities and non-profits show "Contact for a reduced price" and link to Contact.
  - Monthly prices only, no yearly discount. Three staff bands; 10,000+ staff is the red "Over 10,000 employees?"
    band below, with Contact us and Estimate savings (the public calculator).
  - "Pick institution type" and the VAT button swap prices in place (`static/js/guest.js`). Without JavaScript the
    same links reload with `?type=…&vat=1#pricing` and the server renders the prices. VAT is 5 %; prices with VAT
    show fils (e.g. AED 577.50).
- The top nav now has Pricing and Savings calculator. It collapses into the menu button below 1120px.

## Home: Institution Blueprint (Nov 2026)

The guest site now shows the Blueprint (this replaces the earlier rule of not mentioning it). It sits between
"Why organisations use" and Pricing, on a dark navy background.
- Intro, three numbered steps (units, member types, approval routes), the AI line, and two buttons:
  "Create your account" (neon navy) and "Talk to us".
- **Interactive preview** (`apps/guest/blueprint_demo.py`): University / School / Hospital, built from the real
  `apps.blueprint.services.TEMPLATES`, so it shows exactly what each template creates: the unit tree, member
  types (with approval limits) and approval routes. JS switches in place; without JS `?bp=school#blueprint`.
- **Background tree** (`static/js/guest.js`): a line-art tree drawn from the selected template's unit tree
  (one branch per unit, so each template's tree has its own height, branches and depth, and its own fruit
  shape). Switching templates morphs it directly: shared branches move, extra ones grow from or shrink into
  their parent. Hidden on phone widths; no animation for "reduce motion".

## Home: the introduction film (Nov 2026)

- The hero now plays the Circular Campus film (`static/video/circular-campus-film.mp4`, 1:42, 1920×1080, with an original
  music bed and no voiceover yet) with a navy poster (`static/video/circular-campus-poster.jpg`).
- It is the default for `GUEST_HOME_VIDEO`; set the variable to a URL to host the film elsewhere (e.g. once the
  voiceover version is ready), or to an empty value to show the "Coming soon" placeholder again.

## Menu and pages (Nov 2026, update)

- Menu order: Home · How it works · Blueprint · Calculator · Pricing · Contact (footer keeps the full names "Institution Blueprint" and "Savings calculator", and adds Sign in). The header collapses into the menu button below 1180px, so it stays full on 1280px laptops.
- **Institution Blueprint** has its own page (`/institution-blueprint/`, `guest/blueprint.html`); it is no longer a
  section of the home page.
- **Savings calculator** (`/impact/calculator/`): visitors now see it inside the guest site (guest header and menu,
  "Savings calculator" marked as the current page); signed-in people still see it inside the app. The
  "Back to sign in" link is gone, since Sign in is in the header. The login page's "Estimate savings" link opens the
  same page.
- The header runs up to 1320px wide so all six links fit on one line; below 1340px it becomes the menu button.

- **Pricing** now has its own page too (`/pricing/`, `guest/pricing.html`): the institution-type picker, the VAT
  button, the price cards and the red "Over 10,000 employees?" band. None of it is on the home page any more; the
  menu's Pricing link opens the page at the top. The home page is now: hero, "Use what you have before you buy",
  "Why organisations use Circular Campus", then the closing band.

## Icons, link previews and search (Nov 2026)
- Browser-tab icon (links carry `?v=2` so browsers drop any old cached icon; `/favicon.ico` redirects to the real file): `static/img/brand/` holds `favicon.ico`, `favicon.svg`, `apple-touch-icon.png` (iPhone home screen) and `icon-512.png`. Both the public layout and the signed-in layout load them through `guest/_icons.html`.
- Link previews: the public layout adds Open Graph and Twitter tags, so a shared link shows `og-image.jpg` (1200×630), the name and the description on WhatsApp, LinkedIn and X. The absolute image address comes from the `og_image` context value.
- `/robots.txt` keeps search engines out of everything behind sign-in and points them to `/sitemap.xml`, which lists the six public pages. Both are built from the request, so they show the right domain wherever the site is hosted.
