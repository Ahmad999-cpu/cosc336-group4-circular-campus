# Module: Sustainability (`apps/sustainability`): C7 and three bonus features

**Delivers:**
- **C7:** a sustainability dashboard. The lab slide asks for at least 3 measures, each shown with its formula
  and source; we show 5.
- **Bonus features:**
  - a potential cost-avoidance calculator;
  - feasibility and net-cost comparison.
- **Also covers:** Feature 4.11, BR-15, Section 9.6, FR-13.8 and FR-15.10.

**Owns:** `EmissionFactor`, `SustainabilityImpact`, `SustainabilityRecommendation`.

## Screens

| Screen | URL | Who |
|---|---|---|
| **Impact** dashboard | `/impact/` | everyone signed in |
| **Savings calculator** | `/impact/calculator/` | public, no sign-in |
| **Reuse or buy new?** side panel | `/impact/compare/<asset>/` | `request.submit` |

**Impact dashboard** contents:
- Period: last 30 days, this term, this year or all time.
- Five measure tiles. Each tile has a "How it's calculated" panel with the formula, the source and the coverage.
- Items reused per month for the last six months.
- A breakdown by category.
- The full table of locally selected carbon factors, showing which ones the figures used.

**Savings calculator** inputs and outputs:
- Inputs:
  - institution type;
  - number of staff (a slider);
  - share of staff who use it.
- Live results:
  - active users;
  - saved per year;
  - subscription per month and per year;
  - return and payback;
  - a savings-against-cost bar.
- Below the results:
  - the three formulas;
  - the price table;
  - the source note.

**Reuse or buy new?** side panel:
- Opened from an item's panel in Browse.
- Editable inputs: quantity, campus, new price, needed-by date, transport, storage and repair.
- A feasibility verdict (Feasible / Feasible after a repair / Not feasible) with reasons.
- Buy-new against reuse cost bars, and the saving in AED and %.
- The carbon not emitted, every input listed, and a "Request it" button.

## Public interface

**`services.py`:**
- `factor_for(category)`;
- `record_transfer_impact(transfer, quantity)`;
- `dashboard_measures(user, start, end, unit_ids)` → `Dashboard`;
- `net_cost_comparison(asset, quantity, new_unit_price, transport, storage, repair, destination_campus, required_date)` → `NetCost`.

**`calculator.py`:**
- `estimate_savings`, `monthly_price`;
- the shared reuse-cost assumptions (`TRANSFER_COST_*`, `REPAIR_SHARE_POOR`, `LEAD_DAYS_*`, `REPAIR_DAYS`).

## The five measures (Section 9.6)

| Measure | Formula | Source | Estimate? |
|---|---|---|---|
| Items reused | Σ units confirmed received in completed transfers | Transfer records | No |
| Purchases avoided (AED) | Σ (units × the item's estimated value − transfer cost) | Custodian's estimated value | Yes, except the verified share |
| Carbon avoided (kg CO2e) | Σ units × kg CO2e of making one new unit | Locally selected carbon factors | Yes |
| Waste diverted (kg) | Σ units × typical mass per unit | Mass recorded with each factor | Yes |
| Reuse rate (%) | requests fulfilled by reuse ÷ requests made (cancelled excluded) | Request records | No |

## Design decisions

**D1. Impacts are recorded once, when the receiver confirms.**
- Transfers sends a `transfer_received` signal inside the receipt transaction, and this module writes the
  `SustainabilityImpact` rows.
- Recording is idempotent per transfer.
- Transfers does not import Sustainability. The dependency already runs the other way.

**D2. "Unavailable", never 0.**
- If no factor covers the items moved, carbon and waste show "Unavailable" with the reason.
- Each tile states its coverage, for example "Covers 8 of 10 units moved" (FR-13.8, FR-15.10).

**D3. Verified savings are kept apart from estimates.**
- When the receiving unit ticks "this replaced a planned purchase", the impact is stored as
  `VERIFIED_AVOIDED_PURCHASE`.
- The Purchases avoided tile shows how much of its total is verified.

**D4. Carbon wording.**
- The page says "locally selected carbon factors", never "official".
- Every factor needs a source, a date and a boundary.
- The factor table is on the page, so anyone can check the numbers.
- The seeded demo factors say plainly that they are sample values to be replaced.

**D5. One set of reuse-cost assumptions.**
- Transport cost: AED 40 within a campus, AED 120 between campuses.
- Repair of a Poor item: 20 % of its value.
- Lead times: 2 days within a campus, 5 days between campuses, plus 7 days for a repair.
- All of these live in `calculator.py`. The matching score (f6) and the net-cost comparison both use them, so
  they always agree.

**D6. The calculator uses the competition brief exactly.**
- Active users = staff × 6 / 12 / 18 %.
- Savings = active users × AED 490 / 290 / 165.
- Prices come from the brief's table; 10,000+ staff is a custom quote.
- Return = savings ÷ annual subscription. Payback = subscription ÷ monthly savings.
- The page reproduces the worked example: 1,000 staff → 120 active users, AED 58,800, AED 2,450 a month,
  2×, 6 months.
- Prices were raised 1.75× in Nov 2026 (rounded to AED 50) so the worked example pays back in about 6 months.
  Prices exclude VAT; the guest Pricing section can show them with 5 % UAE VAT added.
- The institution-type labels and the source note are the wording already approved in the prototype.
- Results are worked out on the server from `calculator.py`, so the website and the tests can't disagree.

**D7. Net cost is an estimate you can change.**
- Every default is shown in grey and can be overridden.
- The result lists every input used.
- If buying new is cheaper with the inputs given, the panel says so.

## Model changes (design change 16)

- `EmissionFactor.mass_kg_per_unit` (optional): waste diverted needs a typical mass.
- `SustainabilityImpact.units`: how many units a figure covers, used for the coverage line.
- Migration: `0002_factor_mass_impact_units`.

## Added to other modules

- **Transfers:**
  - `apps/transfers/signals.py` (new): `transfer_received`.
  - `services.confirm_receipt` sends it.
- **Matching:**
  - `engine.py` imports the shared cost assumptions.
  - `services._emission_kg` uses `factor_for`.
- **Catalogue:** the item panel gains a "Reuse or buy new?" button.
- **Seed data:** `seed_demo` adds eight sample factors, labelled as samples.
- **Web:**
  - `config/urls.py`: the prefix is now `/impact/`.
  - `static/js/app.js`: `data-mirror` keeps the slider label in step.
  - `theme.css`: styles for the dashboard, calculator and comparison.

## Conflicts with earlier phases

- **Avoided purchase formula.** Phase 5 defines avoided purchase as value × quantity. The approved prototype
  subtracts the transfer cost. I followed the prototype, because it is the more conservative figure, and the
  formula is shown on the tile.
- **Transport emissions.** The prototype's carbon formula subtracts transport emissions. We have no locally
  selected factor for transport yet, so nothing is subtracted, and the tile says "transport emissions not yet
  subtracted".

## Tests

**`tests/test_sustainability.py` (10 tests):**
- Receipt records the avoided purchase net of transfer cost.
- Verified, carbon and waste figures work with a factor set on a parent category; recording is idempotent.
- The dashboard has 5 measures, each with formula and source.
- Carbon and waste show "unavailable", not 0, when no factor applies.
- The reuse rate, the category and month breakdowns, and the period filter.
- The dashboard page never says "official".
- Net cost: defaults and overrides; "buying new is cheaper"; feasibility (not enough units, repair first,
  tight date); the side panel and its live update.
- The calculator page needs no sign-in, shows the worked example, handles a quote, and survives bad input.

**`tests/test_calculator.py` (4 tests):** the worked example, participation rates and price bands.
