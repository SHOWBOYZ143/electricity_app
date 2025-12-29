# calculator.py
# Electricity tariff calculation engine
# Ghana tariffs for 2025 and 2026
# No UI, no input, no printing

from dataclasses import dataclass
from typing import List

# ----------------------------
# Constants
# ----------------------------
RES_LIFELINE_MAX = 30.0
BLOCK_300 = 300.0
LEVY_RATE = 0.05
TAX_RATE = 0.20

# ----------------------------
# Tariff data
# ----------------------------
TARIFFS = {
    "2025": {
        "rates": {
            "RES_LIFELINE": 80.4389 / 100,
            "RES_B1": 182.2442 / 100,
            "RES_B2": 240.8059 / 100,
            "NONRES_B1": 164.5377 / 100,
            "NONRES_B2": 204.4809 / 100,
            "SLT_LV": 245.5597 / 100,
            "SLT_MV1": 196.0119 / 100,
            "SLT_MV2": 127.8861 / 100,
            "SLT_HV": 196.0119 / 100,
        },
        "service": {
            "Residential (Lifeline)": 2.13,
            "Residential (Other)": 10.7301,
            "Non-Residential": 12.428,
            "SLT": 500.00,
        }
    },
    "2026": {
        "rates": {
            "RES_LIFELINE": 88.3739 / 100,
            "RES_B1": 200.2218 / 100,
            "RES_B2": 264.5604 / 100,
            "NONRES_B1": 180.7687 / 100,
            "NONRES_B2": 224.6521 / 100,
            "SLT_LV": 269.7832 / 100,
            "SLT_MV1": 215.3477 / 100,
            "SLT_MV2": 134.2804 / 100,
            "SLT_HV": 215.3477 / 100,
        },
        "service": {
            "Residential (Lifeline)": 2.13,
            "Residential (Other)": 10.730886,
            "Non-Residential": 12.428245,
            "SLT": 500.00,
        }
    }
}

# ----------------------------
# Data models
# ----------------------------
@dataclass
class BillLine:
    label: str
    amount: float

@dataclass
class BillResult:
    year: str
    category: str
    kwh: float
    energy_charge: float
    service_charge: float
    levy: float
    tax: float
    total: float
    breakdown: List[BillLine]

# ----------------------------
# Helpers
# ----------------------------
def is_taxable(category: str) -> bool:
    return not category.startswith("Residential")

# ----------------------------
# Core calculation
# ----------------------------
def calculate_bill(year: str, category: str, kwh: float) -> BillResult:
    if year not in TARIFFS:
        raise ValueError("Unsupported tariff year.")

    if kwh < 0:
        raise ValueError("kWh cannot be negative.")

    tariff = TARIFFS[year]
    rates = tariff["rates"]
    services = tariff["service"]
    breakdown: List[BillLine] = []

    # Energy charge
    if category == "Residential":
        if kwh <= RES_LIFELINE_MAX:
            energy = kwh * rates["RES_LIFELINE"]
            service = services["Residential (Lifeline)"]
            breakdown.append(BillLine("Energy charge (Lifeline)", energy))
        else:
            kwh_b1 = min(kwh, BLOCK_300)
            kwh_b2 = max(0.0, kwh - BLOCK_300)
            e1 = kwh_b1 * rates["RES_B1"]
            e2 = kwh_b2 * rates["RES_B2"]
            energy = e1 + e2
            service = services["Residential (Other)"]
            breakdown.append(BillLine("Energy charge block 1", e1))
            if kwh_b2 > 0:
                breakdown.append(BillLine("Energy charge block 2", e2))

    elif category == "Non-Residential":
        kwh_b1 = min(kwh, BLOCK_300)
        kwh_b2 = max(0.0, kwh - BLOCK_300)
        e1 = kwh_b1 * rates["NONRES_B1"]
        e2 = kwh_b2 * rates["NONRES_B2"]
        energy = e1 + e2
        service = services["Non-Residential"]
        breakdown.append(BillLine("Energy charge block 1", e1))
        if kwh_b2 > 0:
            breakdown.append(BillLine("Energy charge block 2", e2))

    else:
        rate_map = {
            "SLT-LV": rates["SLT_LV"],
            "SLT-MV1/HV": rates["SLT_MV1"],
            "SLT-MV2": rates["SLT_MV2"],
            "SLT-HV": rates["SLT_HV"],
            "SLT-HV MINES": rates["SLT_HV"],
        }
        if category not in rate_map:
            raise ValueError("Unsupported customer category.")
        energy = kwh * rate_map[category]
        service = services["SLT"]
        breakdown.append(BillLine("Energy charge", energy))

    # Levies and taxes
    levy = LEVY_RATE * energy
    tax = TAX_RATE * (energy + service) if is_taxable(category) else 0.0

    breakdown.append(BillLine("Service charge", service))
    breakdown.append(BillLine("Levies", levy))
    breakdown.append(BillLine("Taxes", tax))

    total = energy + service + levy + tax
    breakdown.append(BillLine("Total payable", total))

    return BillResult(
        year=year,
        category=category,
        kwh=kwh,
        energy_charge=energy,
        service_charge=service,
        levy=levy,
        tax=tax,
        total=total,
        breakdown=breakdown
    )
