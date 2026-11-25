# Run: python manage.py shell < tools/crawl.py   (needs seed_demo data)
"""Validation crawl: every demo user, both languages, every link and hx-get reachable within 3 hops."""
import re, html, collections, sys
from django.test import Client
from apps.access.models import User

USERS = ["club@demo.local", "requester@demo.local", "custodian@demo.local", "lina@demo.local", "approver@demo.local",
         "dean@demo.local", "facilities@demo.local", "tech@demo.local", "sustain@demo.local", "admin@demo.local"]
LINK = re.compile(r'(?:href|hx-get)="(/[^"#]*)"')
SKIP = ("/static/", "/media/", "/i18n/", "/accounts/logout", "/admin/")
problems = collections.defaultdict(list)
seen_total = 0
for email in USERS:
    u = User.objects.filter(email=email).first()
    if not u:
        print("missing user", email); continue
    for lang in ("en", "ar"):
        c = Client(HTTP_HOST="127.0.0.1", raise_request_exception=False)
        c.force_login(u)
        c.post("/i18n/setlang/", {"language": lang, "next": "/"})
        queue, seen = [("/", 0)], set()
        while queue:
            url, depth = queue.pop(0)
            if url in seen or any(url.startswith(s) for s in SKIP):
                continue
            seen.add(url)
            hx = {"HTTP_HX_REQUEST": "true"} if depth and ("drawer" in url or url.count("/") > 3) else {}
            try:
                r = c.get(html.unescape(url), **hx)
            except Exception as e:
                problems[(email, lang)].append((url, "EXC " + type(e).__name__ + ": " + str(e)[:120])); continue
            if r.status_code >= 500:
                problems[(email, lang)].append((url, r.status_code))
            elif r.status_code == 404 and "/find/for/" not in url:
                problems[(email, lang)].append((url, 404))
            if r.status_code == 200 and "html" in r.get("Content-Type", "") and depth < 3:
                body = r.content.decode("utf-8", "ignore")
                if lang == "ar" and '<html' in body and 'dir="rtl"' not in body:
                    problems[(email, lang)].append((url, "not RTL"))
                for m in LINK.findall(body):
                    m = html.unescape(m)
                    if m not in seen:
                        queue.append((m, depth + 1))
        seen_total += len(seen)
        print(f"{email:24} {lang} pages={len(seen)} problems={len(problems[(email, lang)])}")
print("TOTAL urls", seen_total)
for k, v in problems.items():
    for url, what in v[:15]:
        print("PROBLEM", k, url, what)
