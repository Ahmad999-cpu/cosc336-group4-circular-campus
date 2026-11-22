# Feature 4: Demand forecast

**Module:** Reporting (`apps/reporting/forecast.py`, view `demand`) · **URL:** `/reports/demand/` · **Menu:** Demand ·
**Who:** `reports.view` (approvers, the dean, the sustainability officer, the system administrator).

## The data we have

Demand comes from `ResourceRequest`, using these fields: `submitted_at` (date sent), `category`, `quantity` and
the requesting `department`. Cancelled requests are left out, so demand means units asked for and not withdrawn.
The demo database has only the requests made during a demo, so with real data the page honestly says
**Insufficient data**. Forecasts are made for categories and units, never for individual people.

## Method (shown on the page)

| Item | Rule |
|---|---|
| History | The 12 full months before the current month. The current month is shown as "so far" and not used. |
| Forecast period | The month after the current one |
| Baseline forecast | Average units per month over the last 3 full months, with the min–max of those months as "recent range" |
| Trend | The last 3 months against the 3 before: more than 20 % up is rising, more than 20 % down is falling, otherwise steady |
| Insufficient data | Fewer than 10 requests in the selection, or fewer than 3 months since the first one. A category row with fewer than 3 requests shows no number. |
| Optional comparison | A straight-line trend (least squares). It is offered only with 9 or more months of history and is scored against the baseline on past months: one-step-ahead, mean absolute error in units. Both errors are shown, and the page says this is not proof of which method will be right next month. |
| Filters | Category (the category and everything inside it), and requesting unit (only units within the person's `reports.view` scope, using the same `scope()` as Reports) |

## Design decisions

**D1. Simple and explainable first.** For a pilot with a few hundred requests a year, a 3-month average is about as
good as anything more complex, and every number can be checked by hand. The straight-line model is optional
and is compared against the average rather than presented as better. No accuracy is claimed beyond the
errors shown.

**D2. Rows by the requested category.** A request for "Monitors" is shown as Monitors, not as IT Equipment. That
matches the brief's example ("monitors or laboratory equipment"). The category filter still takes a whole subtree.

**D3. Sample data is separate and labelled.** **Show sample data (demo)** builds a made-up 12-month series in
memory, with a fixed seed so it looks the same every time. It is for four categories, with peaks at the start of
semesters and a summer dip. It is never written to the database, and the banner, the facts row and the chart
caption all say "sample". Real records and sample records are never mixed.

**D4. Honest when empty.** With too little data the page explains why ("Only N requests… needs at least 10")
and offers the sample, instead of showing a confident number.

## Tests

`tests/test_demand.py` covers:
- too few records and too short a history;
- baseline, trend, range, history end, forecast month, and the current month left out;
- cancelled requests;
- category rows (including a row with too little data) and the filter;
- unit scope;
- the straight-line comparison, offered only with 9+ months;
- the sample is never stored and is repeatable;
- page permissions and wording;
- Arabic.
