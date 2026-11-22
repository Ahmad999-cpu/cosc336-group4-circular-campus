# The eight features added in November 2026: index and demo script

| # | Feature | Doc |
|---|---|---|
| 1 | QR labels for assets | [01-qr-codes.md](01-qr-codes.md) |
| 2 | Sustainable-action recommendations (green button) | [02-sustainable-actions.md](02-sustainable-actions.md) |
| 3 | Check before buying | [03-check-before-buying.md](03-check-before-buying.md) |
| 4 | Demand forecast | [04-demand-forecast.md](04-demand-forecast.md) |
| 5 | Saved needs and availability alerts | [05-saved-needs.md](05-saved-needs.md) |
| 6 | Coming-soon items | [06-coming-soon.md](06-coming-soon.md) |
| 7 | Questions on an asset | [07-asset-questions.md](07-asset-questions.md) |
| 8 | Bulk CSV upload | [08-bulk-import.md](08-bulk-import.md) |

## Setup

```bash
pip install -r requirements.txt          # adds segno
python manage.py migrate                 # catalogue 0003-0005, matching 0003, notifications 0003
python manage.py seed_demo               # also adds the coming-soon office chairs
python manage.py runserver               # and python manage.py runworker in a second terminal
```

To start the demo from clean data: `python manage.py flush --no-input && python manage.py seed_demo`.
Every demo password is `demo-pass-2026`. Use the one-click buttons on the sign-in page while `DJANGO_DEBUG=1`.

## Demo script (about 15 minutes)

1. **QR label.** Sign in as **Cara**. Go to **Our assets**, open **Dell 24-inch monitor** and click **QR label**.
   Show the label, then **Print label** and **Download label (SVG)**. Copy the address under the label and open it
   in a private window: it asks you to sign in, then opens the item. Signed in as **Rana**, the same page
   has no QR button.
2. **Sustainable actions.** As **Cara**, open the Dell monitor and click the green **Sustainable actions** button.
   Show the recommendation, its reasons, the other options, the labelled estimates and "How this was decided".
   Click **Ask AI to explain this**. With the offline setup it says the AI is unavailable and the rule-based result
   stands. Open **Wooden lectern** the same way: the advice is "Confirm condition".
3. **Check before buying.** Sign in as **Omar**. Go to **Find** and click **Planning a purchase? Check before buying**.
   Enter "24-inch monitors for the robotics lab", quantity **6** and price **900**. Show:
   - the summary "Reuse could cover 6 of the 6 units", with each unit counted once;
   - the partial cards ("Only 2 of the 6 units…");
   - **How this was worked out**.

   **Request 2 units** opens the normal form. Close it without sending.
4. **Demand forecast.** Sign in as **Sara** and open **Demand**. The real data shows **Insufficient data**. Tick
   **Show sample data (demo)**: point to the banner, the facts row and the chart with its dashed forecast bar.
   Then tick **Compare with a straight-line trend** and show the past-error columns.
5. **Saved needs and alert.** As **Omar**, open **Saved needs**, click **Save a need** and enter "Lectern for club
   events", quantity 1. Sign in as **Cara**, go to **Our assets** and on **Wooden lectern** click **Confirm
   condition**, then **Publish**. Back as **Omar**, the bell shows "Wooden lectern may fit your saved need…". The
   alert links to the item; nothing was requested or reserved.
6. **Coming soon.** As **Omar**, go to **Browse** and scroll to **Coming soon**. Open **Office chair, mesh back**: it
   has no Request button. Click **Tell me when it's ready**. As **Cara**, open the chair and click **Change expected
   date** to move it a week later: Omar is told the new date. Then **Confirm condition** and **Publish** in Our
   assets: Omar is told "now available".
7. **Questions.** As **Rana**, open the **Dell 24-inch monitor** from Browse and ask "Does this monitor have an HDMI
   port?". As **Cara**: the bell and **Our assets** both show the waiting question. Click **Answer them**, answer
   "Yes, two HDMI ports", and Rana is told. As **Omar**, open the same monitor: he sees the question with "Asked by
   someone in Mechanical Engineering", not Rana's name.
8. **Bulk CSV.** As **Cara**, go to **Our assets** and click **Import from CSV**, then **Download template**. Upload
   `docs/features/sample-import.csv`. The preview shows:
   - 1 row OK;
   - 1 possible duplicate (the existing Dell monitor), ticked;
   - 2 errors: "you can't register assets for 'Chemistry'", and the quantity "two".

   Click **Import 2 valid rows**. The result lists the rows that weren't imported and why. The new items are
   Registered and not published. Uploading the same file again is refused.

## Checks run

- `python manage.py test`: 297 tests pass. 105 of them are new: QR 14, advice 23, procurement 15, demand 10,
  saved needs 13, coming soon 9, questions 10, import 11.
- `tools/e2e_walkthrough.py`: 37 of 37 pass on fresh demo data.
- `tools/a11y_scan.py`: 0 issues. The new pages were added to the scan.
- `tools/crawl.py`: 1,200 URLs, 10 users, both languages, 0 problems.
