# Run with the dev server on 127.0.0.1:8000: python tools/a11y_scan.py
import asyncio, json
from playwright.async_api import async_playwright
BASE = "http://127.0.0.1:8000"
PAGES = {
 "club@demo.local": ["/", "/find/?q=monitor", "/assets/", "/requests/", "/impact/", "/notifications/",
                     "/find/before-buying/?description=24-inch+monitors&quantity=4", "/find/saved/", "/assets/questions/"],
 "custodian@demo.local": ["/assets/ours/", "/lifecycle/", "/assets/import/", "/assets/questions/"],
 "approver@demo.local": ["/approvals/"],
 "facilities@demo.local": ["/approvals/transfers/"],
 "sustain@demo.local": ["/reports/", "/reports/demand/", "/reports/demand/?sample=1&compare=1"],
 "admin@demo.local": ["/people/", "/setup/?tab=units", "/setup/?tab=roles", "/setup/?tab=routes", "/setup/?tab=start"],
 None: ["/accounts/login/", "/impact/calculator/", "/", "/how-it-works/", "/contact/"],
}
JS = """() => {
  const out = [];
  const ids = {};
  document.querySelectorAll('[id]').forEach(e => { ids[e.id] = (ids[e.id]||0)+1; });
  Object.entries(ids).filter(([k,v]) => v>1).forEach(([k]) => out.push('duplicate id #' + k));
  document.querySelectorAll('input:not([type=hidden]), select, textarea').forEach(e => {
    const lab = e.labels && e.labels.length || e.getAttribute('aria-label') || e.getAttribute('aria-labelledby') || e.closest('label');
    if (!lab) out.push('unlabelled ' + e.tagName.toLowerCase() + ' name=' + e.name);
  });
  document.querySelectorAll('button, a[href]').forEach(e => {
    const t = (e.textContent||'').trim() || e.getAttribute('aria-label') || e.getAttribute('title');
    if (!t && e.offsetParent) out.push('nameless ' + e.tagName.toLowerCase() + ' ' + (e.className||''));
  });
  document.querySelectorAll('img').forEach(e => { if (!e.hasAttribute('alt')) out.push('img without alt'); });
  if (document.documentElement.scrollWidth > window.innerWidth + 1) out.push('horizontal overflow ' + document.documentElement.scrollWidth + '>' + window.innerWidth);
  return out;
}"""
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        total = 0
        for vw in (1366, 390):
            for user, pages in PAGES.items():
                ctx = await b.new_context(viewport={"width": vw, "height": 860}); pg = await ctx.new_page()
                if user:
                    await pg.goto(BASE + "/accounts/login/")
                    await pg.fill("input[name=username]", user); await pg.fill("input[name=password]", "demo-pass-2026")
                    await pg.click("form button.btn"); await pg.wait_for_load_state("networkidle")
                for path in pages:
                    await pg.goto(BASE + path); await pg.wait_for_timeout(500)
                    issues = await pg.evaluate(JS)
                    if issues:
                        total += len(issues)
                        print(vw, user, path, sorted(set(issues))[:8])
                await ctx.close()
        print("issues:", total)
        await b.close()
asyncio.run(main())
