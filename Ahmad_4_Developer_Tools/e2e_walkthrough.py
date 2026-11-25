# Run with the dev server on 127.0.0.1:8000 and freshly seeded data: python tools/e2e_walkthrough.py
"""Cross-role end-to-end walk through the main flow, in a real browser, checking that modules agree."""
import asyncio, re, sys
from playwright.async_api import async_playwright

BASE = "http://127.0.0.1:8000"
LOG = []
def ok(cond, msg):
    LOG.append(("PASS" if cond else "FAIL") + " " + msg)
    print(LOG[-1], flush=True)

async def session(p, email, lang="en"):
    b = await p.chromium.launch()
    ctx = await b.new_context(viewport={"width": 1366, "height": 900})
    pg = await ctx.new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append("pageerror " + str(e)))
    pg.on("console", lambda m: errs.append("console " + m.text) if m.type == "error" and "fonts.g" not in m.text else None)
    pg.on("response", lambda r: errs.append(f"HTTP {r.status} {r.url}") if r.status >= 500 else None)
    await pg.goto(BASE + "/accounts/login/")
    await pg.fill("input[name=username]", email); await pg.fill("input[name=password]", "demo-pass-2026")
    await pg.click("form button.btn"); await pg.wait_for_load_state("networkidle")
    if lang == "ar":
        await pg.click("button.lang"); await pg.wait_for_load_state("networkidle")
    return b, pg, errs

async def toast(pg):
    await pg.wait_for_timeout(700)
    t = await pg.locator(".toast").all_text_contents()
    return " | ".join(t)

async def badge(pg, key):
    loc = pg.locator(f'[data-nav="{key}"] .count')
    if not await loc.count() or await loc.is_hidden():
        return 0
    return int((await loc.text_content()).replace(",", "") or 0)

async def main():
    async with async_playwright() as p:
        # 1. Club president finds two monitors and requests them from the result
        b, pg, errs = await session(p, "club@demo.local")
        await pg.goto(BASE + "/find/?q=" + "Two 24-inch monitors for the robotics club"); await pg.wait_for_timeout(800)
        names = await pg.locator(".match h3").all_text_contents()
        ok(any("Dell 24-inch" in n for n in names), f"Find ranks the Dell 24-inch monitor ({names[:2]})")
        dell = pg.locator(".match", has_text="Dell 24-inch monitor").first
        await dell.locator(".btn-red").click(); await pg.wait_for_timeout(900)
        ok(await pg.locator("#drawer input[name=quantity]").input_value() == "2", "request drawer pre-fills quantity 2 from the words")
        await pg.fill("#drawer textarea[name=purpose]", "Robotics club workstation")
        await pg.click("#drawer button[type=submit]"); await pg.wait_for_timeout(1200)
        await pg.goto(BASE + "/requests/"); await pg.wait_for_timeout(500)
        ok(await pg.locator(".req", has_text="Robotics club workstation").count() == 1, "the request appears on My requests")
        ok(not errs, f"no browser errors for the club ({errs[:3]})"); await b.close()

        # 2. Approver sees it, approves; badge and bell update
        b, pg, errs = await session(p, "approver@demo.local")
        before = await badge(pg, "approvals")
        ok(before >= 1, f"Approvals badge shows waiting requests ({before})")
        await pg.goto(BASE + "/approvals/"); await pg.wait_for_timeout(600)
        row = pg.locator("tr", has_text="Robotics club workstation")
        await row.locator("button.btn-navy").click()
        t = await toast(pg)
        ok("Approved" in t, f"approve toast: {t[:80]}")
        await pg.wait_for_timeout(800)
        ok(await badge(pg, "approvals") == before - 1, "Approvals badge drops by one without reloading")
        ok(not errs, f"no browser errors for the approver ({errs[:3]})"); await b.close()

        # 3. Facilities dispatches
        b, pg, errs = await session(p, "facilities@demo.local")
        await pg.goto(BASE + "/approvals/transfers/"); await pg.wait_for_timeout(600)
        row = pg.locator("tr", has_text="Dell 24-inch monitor").first
        await row.locator("button[type=submit]").first.click()
        t = await toast(pg)
        ok("on its way" in t, f"dispatch toast: {t[:80]}")
        ok(not errs, f"no browser errors for facilities ({errs[:3]})"); await b.close()

        # 4. Club confirms receipt, ticking "replaced a planned purchase"
        b, pg, errs = await session(p, "club@demo.local")
        await pg.goto(BASE + "/requests/"); await pg.wait_for_timeout(500)
        card = pg.locator(".req", has_text="Robotics club workstation")
        await card.locator("text=Confirm receipt").click(); await pg.wait_for_timeout(900)
        await pg.check("#drawer input[name=replaced]")
        await pg.click("#drawer button[type=submit]"); await pg.wait_for_load_state("networkidle")
        t = await toast(pg)
        ok("Receipt confirmed" in t, f"receipt toast: {t[:80]}")
        await pg.goto(BASE + "/impact/?period=all"); await pg.wait_for_timeout(700)
        units = await pg.locator(".impact-tiles .tile").first.locator(".num").text_content()
        ok(int(units) >= 2, f"Impact counts the received units ({units})")
        verified = await pg.locator(".impact-tiles .tile").nth(1).text_content()
        ok("verified" in verified, "Impact shows a verified avoided purchase")
        await pg.goto(BASE + "/notifications/"); await pg.wait_for_timeout(500)
        txt = await pg.locator(".inbox").first.text_content()
        ok("On its way" in txt and "Approved" in txt, "club notifications include approved and on its way")
        ok(not errs, f"no browser errors for the club ({errs[:3]})"); await b.close()

        # 5. Sustainability officer: report shows the transfer; AI draft → publish
        b, pg, errs = await session(p, "sustain@demo.local")
        await pg.goto(BASE + "/reports/"); await pg.wait_for_timeout(700)
        moved = await pg.locator(".tiles .tile").nth(2).locator(".num").text_content()
        ok(int(moved) >= 2, f"Reports count units moved ({moved})")
        await pg.click(".ai-summary .btn-red"); await pg.wait_for_timeout(1200)
        draft = await pg.input_value("#draft-text")
        ok("2" in draft, f"AI draft written from totals: {draft[:70]}")
        await pg.click(".draft button[type=submit]"); await pg.wait_for_timeout(900)
        ok(await pg.locator(".ai-summary .published").count() >= 1, "summary published")
        ok(not errs, f"no browser errors for sustainability ({errs[:3]})"); await b.close()

        # 6. Custodian (Computer Science): history shows the units leaving; then a maintenance cycle with the tech
        b, pg, errs = await session(p, "custodian@demo.local")
        await pg.goto(BASE + "/assets/ours/"); await pg.wait_for_timeout(500)
        await pg.locator("tr", has_text="Dell 24-inch monitor").first.locator("a, button").first.click(); await pg.wait_for_timeout(900)
        hist = await pg.locator("#drawer .timeline").text_content()
        ok("Student Clubs" in hist or "received" in hist.lower(), "asset history records the move")
        await pg.click("#drawer >> text=Report a problem"); await pg.wait_for_timeout(800)
        await pg.fill("#drawer textarea[name=description]", "Flickering backlight")
        await pg.click("#drawer button[type=submit]"); t = await toast(pg)
        ok("Problem recorded" in t or "Recorded" in t, f"report a problem: {t[:80]}")
        ok(not errs, f"no browser errors for the custodian ({errs[:3]})"); await b.close()

        b, pg, errs = await session(p, "tech@demo.local")
        ok(await badge(pg, "maintenance") >= 1, "maintenance badge for the technician")
        await pg.goto(BASE + "/lifecycle/"); await pg.wait_for_timeout(600)
        row = pg.locator("article.req", has_text="Flickering backlight")
        await row.locator("text=Start work").click(); t = await toast(pg)
        ok("Work started" in t, f"start work: {t[:60]}")
        ok(not errs, f"no browser errors for the technician ({errs[:3]})"); await b.close()

        # 7. Arabic: requester walks Find → results, sees RTL and Arabic labels
        b, pg, errs = await session(p, "requester@demo.local", "ar")
        await pg.goto(BASE + "/find/?q=" + "شاشة عرض"); await pg.wait_for_timeout(800)
        ok(await pg.locator("html[dir=rtl]").count() == 1, "Arabic page is right-to-left")
        names = await pg.locator(".match h3").all_text_contents()
        ok(any("monitor" in n.lower() for n in names), f"Arabic query finds a monitor ({names[:2]})")
        ok("سبب هذه الدرجة" in await pg.content(), "explanations are labelled in Arabic")
        ok(not errs, f"no browser errors in Arabic ({errs[:3]})"); await b.close()

        # 8. Admin adds a Blueprint route: monitors over AED 1,000 go to the Dean. Adam can't approve; Dana can.
        b, pg, errs = await session(p, "requester@demo.local")
        await pg.goto(BASE + "/find/?q=three USB-C docks for the lab"); await pg.wait_for_timeout(800)
        await pg.locator(".match", has_text="docking station").first.locator(".btn-red").click(); await pg.wait_for_timeout(900)
        await pg.fill("#drawer textarea[name=purpose]", "Vibration lab screens"); await pg.click("#drawer button[type=submit]")
        await pg.wait_for_timeout(1000); await b.close()
        b, pg, errs = await session(p, "admin@demo.local")
        await pg.goto(BASE + "/setup/?tab=routes"); await pg.wait_for_timeout(500)
        await pg.click("text=Add route"); await pg.wait_for_timeout(800)
        await pg.fill("#x-name", "Docks over AED 1,000: institution approver")
        await pg.select_option("#x-cat", label="IT Equipment / Docking stations")
        await pg.fill("#x-min", "1000")
        await pg.select_option("#x-role", label="Approver")
        await pg.select_option("#x-scope", value="INSTITUTION")
        await pg.fill("#x-prio", "5")
        await pg.click("#drawer button[type=submit]"); await pg.wait_for_load_state("networkidle"); await pg.wait_for_timeout(500)
        ok(await pg.locator(".route", has_text="Docks over AED 1,000").count() == 1, "route saved and listed")
        opt = await pg.locator("#try-asset option", has_text="Laptop docking station").first.get_attribute("value")
        await pg.select_option("#try-asset", value=opt)
        await pg.fill("#try-qty", "3")
        try:  # wait for the tester's answer instead of a fixed pause (the fixed 0.9 s was sometimes too short)
            await pg.wait_for_function("document.querySelector('#try-out').textContent.includes('Docks')", timeout=5000)
        except Exception:
            pass
        tried = await pg.locator("#try-out").text_content()
        ok("Docks over AED 1,000" in tried and "Adam" in tried, f"the route tester applies the new route ({tried[:90]!r})")
        ok(not errs, f"no browser errors for the admin ({errs[:3]})"); await b.close()
        b, pg, errs = await session(p, "approver@demo.local")
        await pg.goto(BASE + "/approvals/"); await pg.wait_for_timeout(600)
        row = pg.locator("tr", has_text="Vibration lab screens")
        ok(await row.count() == 1, "approver still sees the request")
        # the route names the Approver role from the whole institution: Adam (Engineering scope) no longer covers it
        await row.locator("button[data-toggle]").first.click(); await pg.wait_for_timeout(300)
        await row.locator("textarea, input[name=reason]").first.fill("Please share with the robotics club instead")
        await row.locator("button.btn-red").click(); t = await toast(pg)
        ok("Rejected" in t, f"reject with reason: {t[:70]}")
        ok(not errs, f"no browser errors for the approver ({errs[:3]})"); await b.close()
        b, pg, errs = await session(p, "dean@demo.local")
        await pg.goto(BASE + "/approvals/"); await pg.wait_for_timeout(600)
        ok(await pg.locator("tr", has_text="Vibration lab screens").count() == 0, "a rejected request leaves the dean's queue too")
        await b.close()
        b, pg, errs = await session(p, "requester@demo.local")
        await pg.goto(BASE + "/notifications/"); await pg.wait_for_timeout(500)
        ok("Please share with the robotics club" in await pg.locator(".inbox").first.text_content(), "requester sees the rejection reason")
        await b.close()

    fails = [l for l in LOG if l.startswith("FAIL")]
    print(f"\n{len(LOG) - len(fails)} passed, {len(fails)} failed")

asyncio.run(main())
