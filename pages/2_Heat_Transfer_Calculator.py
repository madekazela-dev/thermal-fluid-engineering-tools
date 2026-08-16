"""
Module B — Heat Transfer Calculator.

(1) Steady-state conduction through a single-layer flat wall (Fourier's Law).
(2) Newton's Law of Cooling: time to cool from T0 to a target temperature in
    an ambient fluid at T_inf.
(3) A live temperature-vs-time cooling curve.

Physics lives in engineering.py (HeatTransferAnalysis class) — this file is
purely the Streamlit UI layer.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from engineering import HeatTransferAnalysis

st.set_page_config(page_title="Heat Transfer Calculator", page_icon="🔥", layout="wide")

st.title("🔥 Heat Transfer Calculator")
st.markdown("Steady-state conduction (Fourier's Law) and transient cooling (Newton's Law of Cooling).")
st.caption(
    "**Verified against analytical solutions:** the conduction formula was "
    "hand-checked (k=1 W/m·K, L=0.1 m, ΔT=100°C, A=1 m² → q″=1000 W/m², "
    "Q=1000 W, matching Fourier's Law exactly). Newton's Law of Cooling was "
    "verified with a round-trip test: the time solved for reaching a target "
    "temperature is plugged back into T(t), and it reproduces the target "
    "temperature to within 1e-6 °C."
)
st.divider()

hta = HeatTransferAnalysis()

# ===========================================================================
# PART 1 — Steady-state conduction (Fourier's Law)
# ===========================================================================
st.header("1️⃣ Steady-State Conduction Through a Flat Wall")
st.markdown("Fourier's Law: **q″ = k·(T_hot − T_cold) / L**, and Q = q″·A")

st.sidebar.header("⚙️ Part 1 — Conduction Inputs")
k_cond = st.sidebar.number_input(
    "Thermal conductivity, k (W/m·K)", min_value=0.0, value=1.7, step=0.1,
    help="How well the wall material conducts heat. Concrete ≈ 1.7, steel ≈ 45, "
         "fiberglass insulation ≈ 0.04 W/(m·K).",
)
L_wall = st.sidebar.number_input(
    "Wall thickness, L (m)", min_value=0.0, value=0.2, step=0.01, format="%.3f",
    help="Distance the heat travels through the wall, in metres.",
)
area_wall = st.sidebar.number_input(
    "Wall area, A (m²)", min_value=0.0, value=10.0, step=1.0,
    help="Cross-sectional area of the wall perpendicular to heat flow.",
)
T_hot_wall = st.sidebar.number_input(
    "Hot-face temperature, T_hot (°C)", value=80.0, step=1.0,
    help="Temperature on the hotter side of the wall.",
)
T_cold_wall = st.sidebar.number_input(
    "Cold-face temperature, T_cold (°C)", value=20.0, step=1.0,
    help="Temperature on the cooler side of the wall.",
)

try:
    q_flux = hta.conduction_heat_flux(k_cond, L_wall, T_hot_wall, T_cold_wall)
    Q_cond = hta.conduction_heat_rate(k_cond, L_wall, area_wall, T_hot_wall, T_cold_wall)

    c1, c2 = st.columns(2)
    c1.metric("Heat flux, q″", f"{q_flux:,.2f} W/m²")
    c2.metric("Total heat rate, Q", f"{Q_cond:,.2f} W")

except ValueError as e:
    st.warning(f"⚠️ Invalid conduction input: {e}")

st.divider()

# ===========================================================================
# PART 2 & 3 — Newton's Law of Cooling + cooling curve
# ===========================================================================
st.header("2️⃣ Newton's Law of Cooling")
st.markdown(
    "Lumped-capacitance model: **T(t) = T∞ + (T₀ − T∞)·e^(−k_cool·t)**, "
    "where k_cool = h·A / (m·c) is the cooling-rate constant."
)

st.sidebar.header("⚙️ Part 2 — Cooling Inputs")
T0 = st.sidebar.number_input(
    "Initial temperature, T₀ (°C)", value=90.0, step=1.0,
    help="Starting temperature of the object being cooled (or heated).",
)
T_inf = st.sidebar.number_input(
    "Ambient temperature, T∞ (°C)", value=20.0, step=1.0,
    help="Temperature of the surrounding fluid the object is cooling into.",
)
T_target = st.sidebar.number_input(
    "Target temperature, T_target (°C)", value=40.0, step=1.0,
    help="The temperature you want to know the time-to-reach. Must lie "
         "strictly between T₀ and T∞.",
)
h_conv = st.sidebar.slider(
    "Convection coefficient, h (W/m²·K)", min_value=1.0, max_value=500.0, value=15.0,
    help="How effectively the surrounding fluid carries heat away from the "
         "surface. Still air ≈ 5–25, moving air ≈ 25–250, water ≈ 500+ W/(m²·K).",
)
area_obj = st.sidebar.number_input(
    "Surface area, A (m²)", min_value=0.0, value=0.1, step=0.01, format="%.3f",
    help="Surface area of the object exposed to the ambient fluid.",
)
mass_obj = st.sidebar.number_input(
    "Mass, m (kg)", min_value=0.0, value=1.0, step=0.1,
    help="Mass of the object being cooled.",
)
c_obj = st.sidebar.number_input(
    "Specific heat capacity, c (J/kg·K)", min_value=0.0, value=450.0, step=10.0,
    help="Energy needed to raise 1 kg of the object by 1°C/K. Steel ≈ 450, "
         "water ≈ 4186, aluminium ≈ 900 J/(kg·K).",
)

try:
    k_cool = hta.cooling_rate_constant(h_conv, area_obj, mass_obj, c_obj)
    t_target = hta.time_to_reach_target(T0, T_inf, T_target, k_cool)

    c1, c2 = st.columns(2)
    c1.metric("Cooling rate constant, k_cool", f"{k_cool:.6f} 1/s")
    c2.metric("Time to reach target", f"{t_target:,.1f} s  ({t_target/60:,.2f} min)")

    # -----------------------------------------------------------------
    # Live cooling curve
    # -----------------------------------------------------------------
    st.subheader("📈 Temperature vs Time — Cooling Curve")

    t_max = t_target * 1.5
    t_range = np.linspace(0, t_max, 200)
    T_range = [hta.temperature_at_time(t, T0, T_inf, k_cool) for t in t_range]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=t_range, y=T_range, mode="lines", name="T(t)",
        line=dict(color="#EF4444", width=3),
    ))
    fig.add_trace(go.Scatter(
        x=[t_target], y=[T_target], mode="markers", name="Target reached",
        marker=dict(color="#2563EB", size=12, symbol="star"),
    ))
    fig.add_hline(y=T_inf, line_dash="dash", line_color="gray",
                  annotation_text="Ambient T∞", annotation_position="bottom right")
    fig.update_layout(
        xaxis_title="Time (s)",
        yaxis_title="Temperature (°C)",
        template="plotly_white",
        height=450,
    )
    st.plotly_chart(fig, width='stretch')

    cooling_df = pd.DataFrame({"Time (s)": t_range, "Temperature (°C)": T_range})
    st.download_button(
        "⬇️ Download cooling curve (CSV)",
        data=cooling_df.to_csv(index=False),
        file_name="cooling_curve.csv",
        mime="text/csv",
    )

except ValueError as e:
    st.warning(f"⚠️ Invalid cooling input: {e}")
except ZeroDivisionError:
    st.warning("⚠️ Calculation error: check that h, area, mass, and specific heat are all greater than 0.")
except Exception as e:
    st.warning(f"⚠️ Something went wrong with the cooling calculation: {e}")
