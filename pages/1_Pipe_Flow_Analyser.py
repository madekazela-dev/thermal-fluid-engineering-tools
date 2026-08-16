"""
Module A — Pipe Flow Analyser.

A complete pipe flow calculator: pick a fluid, enter pipe geometry and flow
rate, and see velocity, Reynolds number, friction factor, and pressure drop,
plus an interactive pressure-drop-vs-flow-rate curve and CSV export.

Physics lives in engineering.py (Fluid, Pipe classes) — this file is purely
the Streamlit UI layer: it collects inputs, calls the engineering objects,
and displays/plots/exports the results.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from engineering import Fluid, Pipe

st.set_page_config(page_title="Pipe Flow Analyser", page_icon="🌀", layout="wide")

st.title("🌀 Pipe Flow Analyser")
st.markdown(
    "Darcy-Weisbach pressure drop for flow of a Newtonian fluid through a "
    "circular pipe, using the Colebrook-White equation for the turbulent "
    "friction factor."
)
st.caption(
    "**Verified against:** the worked example in PE 262 Week 3 (water, "
    "D=50 mm, L=200 m, Q=5 L/s → v=2.546 m/s, Re=127,324) and against an "
    "independent Colebrook-White root-finder (scipy.optimize.brentq) for a "
    "Moody-chart test case at Re=1e5, ε/D=0.001."
)
st.divider()

# ---------------------------------------------------------------------------
# Sidebar inputs
# ---------------------------------------------------------------------------
st.sidebar.header("⚙️ Inputs")

st.sidebar.subheader("Fluid")
fluid_choice = st.sidebar.selectbox(
    "Fluid type",
    options=["Water", "Air", "Crude Oil", "User-defined"],
    help="Water, air, and crude oil use typical reference properties at "
         "~20°C. Choose 'User-defined' to enter your own density/viscosity.",
)

if fluid_choice == "User-defined":
    density = st.sidebar.number_input(
        "Density ρ (kg/m³)", min_value=0.0, value=1000.0, step=10.0,
        help="Mass per unit volume of the fluid.",
    )
    viscosity = st.sidebar.number_input(
        "Dynamic viscosity μ (Pa·s)", min_value=0.0, value=0.001, step=0.0001,
        format="%.5f",
        help="Resistance of the fluid to shear/flow. Water ≈ 0.001 Pa·s.",
    )
else:
    ref = Fluid.LIBRARY[fluid_choice]
    density, viscosity = ref["density"], ref["viscosity"]
    st.sidebar.caption(f"ρ = {density} kg/m³, μ = {viscosity} Pa·s (auto-populated)")

st.sidebar.subheader("Pipe Geometry")
D_mm = st.sidebar.number_input(
    "Internal diameter D (mm)", min_value=0.0, value=50.0, step=1.0,
    help="Internal (bore) diameter of the pipe.",
)
L_m = st.sidebar.number_input(
    "Pipe length L (m)", min_value=0.0, value=200.0, step=1.0,
    help="Total length of straight pipe over which the pressure drop is calculated.",
)
roughness_mm = st.sidebar.number_input(
    "Absolute roughness ε (mm)", min_value=0.0, value=0.046, step=0.001,
    format="%.4f",
    help="Wall roughness height. 0.046 mm is typical for commercial steel pipe.",
)

st.sidebar.subheader("Flow Rate")
Q_Ls = st.sidebar.slider(
    "Flow rate Q (L/s)", min_value=0.1, max_value=50.0, value=5.0, step=0.1,
    help="Volumetric flow rate through the pipe.",
)

# ---------------------------------------------------------------------------
# Calculation with error handling
# ---------------------------------------------------------------------------
try:
    fluid = Fluid(fluid_choice if fluid_choice != "User-defined" else "Custom fluid",
                  density, viscosity)
    pipe = Pipe(D_mm / 1000, L_m, roughness_mm / 1000)
    Q = Q_Ls / 1000  # L/s -> m3/s

    result = pipe.report(fluid, Q)

    st.subheader("📊 Results")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Velocity", f"{result['velocity_m_s']:.3f} m/s")
    c2.metric("Reynolds Number", f"{result['reynolds']:,.0f}")
    c3.metric("Friction Factor", f"{result['friction_factor']:.5f}")
    c4.metric("Pressure Drop", f"{result['pressure_drop_bar']:.4f} bar")

    st.info(f"Flow regime: **{result['flow_regime']}**")

    # -----------------------------------------------------------------
    # Interactive plot: pressure drop vs flow rate over a range
    # -----------------------------------------------------------------
    st.subheader("📈 Pressure Drop vs Flow Rate")

    Q_range_Ls = np.linspace(0.1, max(50.0, Q_Ls * 1.5), 100)
    dP_range_bar = []
    for q_ls in Q_range_Ls:
        dp = pipe.pressure_drop(fluid, q_ls / 1000) / 1e5
        dP_range_bar.append(dp)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=Q_range_Ls, y=dP_range_bar, mode="lines", name="Pressure drop",
        line=dict(color="#2563EB", width=3),
    ))
    fig.add_trace(go.Scatter(
        x=[Q_Ls], y=[result["pressure_drop_bar"]], mode="markers",
        name="Current input", marker=dict(color="#EF4444", size=12, symbol="star"),
    ))
    fig.update_layout(
        xaxis_title="Flow rate Q (L/s)",
        yaxis_title="Pressure drop ΔP (bar)",
        template="plotly_white",
        height=450,
    )
    st.plotly_chart(fig, width='stretch')

    # -----------------------------------------------------------------
    # Results table + CSV export
    # -----------------------------------------------------------------
    st.subheader("📋 Results Table & Export")

    summary_df = pd.DataFrame([{
        "Fluid": fluid_choice,
        "Density (kg/m3)": density,
        "Viscosity (Pa.s)": viscosity,
        "Diameter (mm)": D_mm,
        "Length (m)": L_m,
        "Roughness (mm)": roughness_mm,
        "Flow rate (L/s)": Q_Ls,
        "Velocity (m/s)": result["velocity_m_s"],
        "Reynolds number": result["reynolds"],
        "Flow regime": result["flow_regime"],
        "Friction factor": result["friction_factor"],
        "Pressure drop (Pa)": result["pressure_drop_Pa"],
        "Pressure drop (bar)": result["pressure_drop_bar"],
    }])
    st.dataframe(summary_df, width='stretch', hide_index=True)

    sweep_df = pd.DataFrame({
        "Flow rate (L/s)": Q_range_Ls,
        "Pressure drop (bar)": dP_range_bar,
    })

    dl_col1, dl_col2 = st.columns(2)
    with dl_col1:
        st.download_button(
            "⬇️ Download current result (CSV)",
            data=summary_df.to_csv(index=False),
            file_name="pipe_flow_result.csv",
            mime="text/csv",
        )
    with dl_col2:
        st.download_button(
            "⬇️ Download pressure-drop sweep (CSV)",
            data=sweep_df.to_csv(index=False),
            file_name="pipe_flow_pressure_drop_sweep.csv",
            mime="text/csv",
        )

except ValueError as e:
    st.warning(f"⚠️ Invalid input: {e}")
except ZeroDivisionError:
    st.warning("⚠️ Calculation error: check that diameter and flow rate are greater than 0.")
except Exception as e:
    st.warning(f"⚠️ Something went wrong with the calculation: {e}")
