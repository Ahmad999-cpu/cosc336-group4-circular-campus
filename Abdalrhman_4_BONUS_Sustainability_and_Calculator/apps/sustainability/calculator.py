"""Potential cost-avoidance calculator (bonus feature) and shared formulas.

Formula and constants agreed by the team (Nov 2026). They are starting assumptions until KU pilot data
replaces them:
  active users   = staff x participation
  annual savings = active users x savings per active user per year (by institution type)
  return         = annual savings / annual subscription
  payback months = annual subscription / (annual savings / 12)
AED 490 = median savings per registered user per year across 7 public Warp It university profiles
(GBP 99 at GBP 1 = AED 4.93). Medium and low keep the ratios of the team's original per-item values.
"""
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

PARTICIPATION = {"conservative": Decimal("0.06"), "typical": Decimal("0.12"), "high": Decimal("0.18")}

SAVINGS_PER_ACTIVE_USER = {"asset_intensive": Decimal("490"), "medium": Decimal("290"), "low": Decimal("165")}

# Monthly price in AED (excluding VAT) by institution type and staff band. 10,000+ staff -> quote (None).
# Nov 2026: raised 1.75x (rounded to AED 50) so the worked example pays back in about 6 months, not 3.4.
VAT_RATE = Decimal("0.05")  # UAE VAT
MONTHLY_PRICE = {
    "asset_intensive": [(500, 1050), (5000, 2450), (10000, 3700)],
    "medium": [(500, 550), (5000, 1400), (10000, 2100)],
    "low": [(500, 350), (5000, 800), (10000, 1250)],
}


# ---------------------------------------------------------------- reuse cost assumptions (net-cost comparison)
# Locally chosen starting values, shared by the matching score (f6) and the net-cost comparison so the two agree.
TRANSFER_COST_SAME_CAMPUS = Decimal("40")    # AED per move inside one campus
TRANSFER_COST_OTHER_CAMPUS = Decimal("120")  # AED per move between campuses
REPAIR_SHARE_POOR = Decimal("0.20")          # a Poor item is assumed to need repairs worth 20 % of its value
LEAD_DAYS_SAME_CAMPUS, LEAD_DAYS_OTHER_CAMPUS, REPAIR_DAYS = 2, 5, 7


def monthly_price(institution_type: str, staff: int) -> Decimal | None:
    for upper, price in MONTHLY_PRICE[institution_type]:
        if staff < upper:
            return Decimal(price)
    return None  # quote


@dataclass(frozen=True)
class SavingsEstimate:
    active_users: Decimal
    annual_savings: Decimal
    annual_subscription: Decimal | None
    return_multiple: Decimal | None
    payback_months: Decimal | None


def estimate_savings(institution_type: str, staff: int, participation: str = "typical") -> SavingsEstimate:
    rate = PARTICIPATION[participation]
    active = Decimal(staff) * rate
    savings = (active * SAVINGS_PER_ACTIVE_USER[institution_type]).quantize(Decimal("1"), ROUND_HALF_UP)
    price = monthly_price(institution_type, staff)
    if price is None:
        return SavingsEstimate(active, savings, None, None, None)
    annual = price * 12
    ret = (savings / annual).quantize(Decimal("0.01"), ROUND_HALF_UP) if annual else None
    payback = (annual / (savings / 12)).quantize(Decimal("0.1"), ROUND_HALF_UP) if savings else None
    return SavingsEstimate(active, savings, annual, ret, payback)
