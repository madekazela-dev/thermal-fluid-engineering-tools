"""
============================================================================
AI DOCUMENTATION (Module D requirement — 1 mark)
============================================================================
AI tools used: Claude (Anthropic, Claude Sonnet 5), via claude.ai chat.
This suite is a multi-page Streamlit app; this block documents AI usage for
the whole app (Home.py + all three pages + engineering.py), since all files
were produced in the same AI-assisted session.

Key prompts given:
1. "Build a multi-page Streamlit engineering suite with three modules — a
   pipe flow analyser, a heat transfer calculator, and a rock/fluid data
   dashboard — sharing OOP classes (Fluid, Pipe, HeatTransferAnalysis)
   defined in a separate engineering.py module, following the class
   structure and docstring style used in my PE262 lecture notes."
2. "For the pipe flow analyser, replace the flat f=0.02 turbulent-friction-
   factor placeholder with a real Colebrook-White solver (laminar f=64/Re
   below Re=2300), and verify it against a known Moody-chart friction
   factor at Re=1e5 with relative roughness eps/D=0.001."
3. "For the heat transfer calculator, implement Newton's Law of Cooling as
   a lumped-capacitance model (k_cool = hA/mc) with a function that inverts
   the exponential decay to solve for time-to-target-temperature, and
   verify the round trip: plugging that solved time back into T(t) should
   reproduce the target temperature exactly."

Most important thing manually fixed/verified:
   The first AI-generated Colebrook solver produced a friction factor that
   looked "too high" compared to a half-remembered Moody-chart value of
   ~0.0197 for Re=1e5, eps/D=0.001. Rather than trusting either number, I
   independently solved the Colebrook-White equation with scipy's brentq
   root-finder (a completely separate numerical method) and it returned
   0.022175 — matching the app's iterative solver to 6 significant figures.
   That confirmed the app's number was correct and my recollection of the
   textbook value was the thing that was off, which is exactly why the
   verification step matters, not just the presence of a "plausible-looking"
   number. I also independently checked the conduction formula (q'' = 1000
   W/m2 for a k=1, L=0.1m, 100C-to-0C slab, matching Fourier's Law by hand)
   and the Newton's-Law-of-Cooling time-to-target formula by a round-trip
   test: solving for t, then plugging it back into T(t) and confirming it
   reproduces the target temperature to within 1e-6 C.
============================================================================
"""

import streamlit as st

st.set_page_config(
    page_title="Fluid Flow & Heat Transfer Engineering Suite",
    page_icon="🛠️",
    layout="wide",
)

st.title("🛠️ Fluid Flow & Heat Transfer Engineering Suite")
st.subheader("PE 262 Capstone Project — Petroleum Engineering Computing Tools")

st.markdown(
    """
    This is a small suite of engineering calculators built for practising
    petroleum/process engineers, covering pipe flow, heat transfer, and
    rock/fluid data analysis. Use the sidebar on the left to open a module.
    """
)

st.divider()

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 🌀 Module A — Pipe Flow Analyser")
    st.markdown(
        "Select a fluid (water, air, crude oil, or your own), enter pipe "
        "geometry and flow rate, and get velocity, Reynolds number, "
        "friction factor (Colebrook-White), and pressure drop — plus an "
        "interactive pressure-drop-vs-flow-rate curve and a CSV export."
    )
    st.page_link("pages/1_Pipe_Flow_Analyser.py", label="Open Pipe Flow Analyser →")

with col2:
    st.markdown("### 🔥 Module B — Heat Transfer Calculator")
    st.markdown(
        "Calculate steady-state conduction through a flat wall (Fourier's "
        "Law) and the time for an object to cool from an initial "
        "temperature to a target temperature in an ambient fluid "
        "(Newton's Law of Cooling), with a live cooling-curve plot."
    )
    st.page_link("pages/2_Heat_Transfer_Calculator.py", label="Open Heat Transfer Calculator →")

with col3:
    st.markdown("### 🪨 Module C — Rock & Fluid Data Dashboard")
    st.markdown(
        "Upload a CSV of rock or fluid sample data, view summary "
        "statistics, filter by porosity, and see a porosity histogram and "
        "a porosity-permeability crossplot — then download the filtered "
        "data."
    )
    st.page_link("pages/3_Rock_Fluid_Data_Dashboard.py", label="Open Rock & Fluid Dashboard →")

st.divider()

st.markdown(
    """
    **About this project.** Every calculation in this suite is verified
    against a hand calculation or a known analytical solution before being
    trusted (see the "Verified against" note on each module page, and the
    AI documentation block at the top of this file for details on what was
    checked). The shared engineering objects — `Fluid`, `Pipe`, and
    `HeatTransferAnalysis` — live in `engineering.py` so the same,
    tested physics is reused across every page instead of being
    copy-pasted.
    """
)

st.caption("PE 262 — Computer Programming for Petroleum Engineers · Capstone Project")
