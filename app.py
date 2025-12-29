import streamlit as st
from calculator import calculate_bill
from PIL import Image
import os

if "results" not in st.session_state:
    st.session_state.results = None

# -----------------------------
# Reverse calculation helper
# -----------------------------
def invert_bill_to_kwh(year, category, target_total, tol=0.01, max_iter=60):
    if target_total <= 0:
        return 0.0

    lo, hi = 0.0, 1.0
    while calculate_bill(year, category, hi).total < target_total:
        hi *= 2
        if hi > 1_000_000:
            raise RuntimeError("Unable to estimate kWh for this bill amount.")

    for _ in range(max_iter):
        mid = (lo + hi) / 2
        diff = calculate_bill(year, category, mid).total - target_total
        if abs(diff) <= tol:
            return mid
        if diff < 0:
            lo = mid
        else:
            hi = mid

    return (lo + hi) / 2


# -----------------------------
# Extract billing components
# -----------------------------
def extract_summary(result, category: str):
    energy = 0.0
    service = 0.0
    levies = 0.0
    taxes = 0.0

    for line in getattr(result, "breakdown", []):
        label = str(getattr(line, "label", "")).lower()
        amount = float(getattr(line, "amount", 0.0))

        if "energy" in label:
            energy += amount
        elif "service" in label:
            service += amount
        elif "tax" in label or "vat" in label:
            taxes += amount
        elif "levy" in label:
            levies += amount
            

    # Residential rule: show levies as 5% of energy, and taxes should be zero
    if category == "Residential":
        levies = 0.05 * energy
        taxes = 0.0

    total = float(getattr(result, "total", energy + service + levies + taxes))
    return energy, service, levies, taxes, total



# -----------------------------
# Page setup
# -----------------------------
st.set_page_config(
    page_title="PURC Electricity Tariff Calculator",
    layout="centered"
)

st.markdown("""
<style>

/* Keep your dark gradient */
.stApp {
    background: radial-gradient(circle at top, #121826 0%, #0b0f18 55%, #070a11 100%);
}
h1,h2 {
    color: #ffffff !important;
}


p, span {
    color: rgba(0, 225,255,0.50) !important;
}

/* Make Streamlit's main container transparent */
section[data-testid="stAppViewContainer"] {
    background: transparent;
}

/* Also neutralise inner blocks */
div[data-testid="stVerticalBlock"] {
    background: transparent;
}
.total-box {
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 14px;
    padding: 20px;
    margin-top: 10px;
}

.total-label {
    font-size: 18px;
    color: rgba(255, 255, 255, 0.85);
}

.total-value {
    font-size: 42px;
    font-weight: 900;
    color: #ffffff;
    margin-top: 4px;
}

.breakdown-label {
    font-size: 16px;
    color: rgba(255, 255, 255, 0.85);
}

.breakdown-value {
    font-size: 18px;
    font-weight: 600;
    color: #ffffff;
}

</style>
""", unsafe_allow_html=True)

# -----------------------------
# Header
# -----------------------------
logo_path = os.path.join(os.path.dirname(__file__), "purc_logo.png")
if os.path.exists(logo_path):
    st.image(Image.open(logo_path), width=130)

st.title("Electricity Tariff Calculator")

# -----------------------------
# Inputs
# -----------------------------
year = st.selectbox("Tariff Year", ["2025", "2026"])

category = st.selectbox(
    "Customer Category",
    [
        "Residential",
        "Non-Residential",
        "SLT-LV",
        "SLT-MV1/HV",
        "SLT-MV2",
        "SLT-HV",
        "SLT-HV MINES",
    ]
)

mode = st.radio(
    "Calculation Type",
    ["Bill from kWh", "kWh from Bill"],
    horizontal=True
)

if mode == "Bill from kWh":
    value = st.number_input("Consumption (kWh)", min_value=0.0, step=1.0, format="%.2f")
else:
    value = st.number_input("Total Amount (GHS)", min_value=0.0, step=1.0, format="%.2f")

calculate_clicked = st.button("CALCULATE")

auto_calculate = (
    mode == "Bill from kWh"
    and value > 0
)


# -----------------------------
# Result Summary
# -----------------------------
st.markdown("## Result Summary")

show_breakdown = st.toggle("Show detailed breakdown", value=False)

headline_label = "Total Amount (GHS)" if mode == "Bill from kWh" else "Estimated Consumption (kWh)"
headline_value = "0.00"

energy = service = levies = taxes = total = 0.0

if calculate_clicked or auto_calculate:
    if mode == "Bill from kWh":
        result = calculate_bill(year, category, value)
        energy, service, levies, taxes, total = extract_summary(result, category)

        st.session_state.results = {
            "headline_label": "Total Amount (GHS)",
            "headline_value": f"{total:,.2f}",
            "energy": energy,
            "service": service,
            "levies": levies,
             "taxes": taxes,
        }

    else:
        est_kwh = invert_bill_to_kwh(year, category, value)
        result = calculate_bill(year, category, est_kwh)
        energy, service, levies, taxes, total = extract_summary(result, category)

        st.session_state.results = {
            "headline_label": "Estimated Consumption (kWh)",
            "headline_value": f"{est_kwh:,.2f}",
            "energy": energy,
            "service": service,
            "levies": levies,
             "taxes": taxes,
        }

# -----------------------------
# Render Results
# -----------------------------
if st.session_state.results is not None:

    r = st.session_state.results

    # 🔹 Decide what to show for levies based on category
    if category == "Residential":
        levies_display = r["levies"]
        levies_label = "Levies (GHS)"
    else:
        levies_display = r["levies"] + r["taxes"]
        levies_label = "Levies and Taxes (GHS)"

    # 🔹 Big total at the top
    st.markdown(
        f"""
        <div class="total-box">
            <div class="total-label">{r["headline_label"]}</div>
            <div class="total-value">{r["headline_value"]}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 🔹 Breakdown section
    if show_breakdown:
        st.markdown("<br>", unsafe_allow_html=True)

        col1, col2 = st.columns([3, 1])

        with col1:
            st.markdown('<div class="breakdown-label">Energy Charge (GHS)</div>', unsafe_allow_html=True)
            st.markdown('<div class="breakdown-label">Service Charge (GHS)</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="breakdown-label">{levies_label}</div>', unsafe_allow_html=True)

        with col2:
            st.markdown(f'<div class="breakdown-value">{r["energy"]:,.2f}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="breakdown-value">{r["service"]:,.2f}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="breakdown-value">{levies_display:,.2f}</div>', unsafe_allow_html=True)

# -----------------------------
# Footer
# -----------------------------
st.caption("© Public Utilities Regulatory Commission (PURC) | For informational purposes only")

