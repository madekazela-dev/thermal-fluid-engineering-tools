# Fluid Flow & Heat Transfer Engineering Suite

A multi-page Streamlit engineering suite built for the PE 262 Capstone Project. It combines a pipe flow analyser (Darcy-Weisbach pressure drop with a Colebrook-White friction factor solver), a heat transfer calculator (steady-state Fourier conduction plus a Newton's Law of Cooling transient cooling curve), and a rock/fluid data dashboard (CSV upload, summary statistics, porosity filtering, and a porosity-permeability crossplot) — all sharing tested `Fluid`, `Pipe`, and `HeatTransferAnalysis` objects defined in `engineering.py`.

**Live app:** PASTE_YOUR_STREAMLIT_CLOUD_URL_HERE

## Project structure

```
Home.py                              # Landing page + suite-wide AI documentation
pages/
  1_Pipe_Flow_Analyser.py            # Module A
  2_Heat_Transfer_Calculator.py      # Module B
  3_Rock_Fluid_Data_Dashboard.py     # Module C
engineering.py                       # OOP core: Fluid, Pipe, HeatTransferAnalysis
sample_rock_data.csv                 # Sample data to test Module C
requirements.txt
```

## Running locally

```bash
pip install -r requirements.txt
streamlit run Home.py
```

## Verification

- **Pipe flow:** the `Pipe`/`Fluid` velocity and Reynolds number calculations match the PE 262 Week 3 worked example exactly (water, D=50 mm, L=200 m, Q=5 L/s → v=2.546 m/s, Re=127,324). The Colebrook-White friction factor solver was cross-checked against an independent `scipy.optimize.brentq` root-finder for a standard Moody-chart test case (Re=1e5, ε/D=0.001), matching to 6 significant figures.
- **Heat transfer:** the conduction formula was hand-verified (k=1 W/m·K, L=0.1 m, ΔT=100°C, A=1 m² → q″=1000 W/m², Q=1000 W). Newton's Law of Cooling was verified with a round-trip test: solving for the time to reach a target temperature and plugging it back into T(t) reproduces the target temperature to within 1e-6 °C.

## Features by module

- **Module A — Pipe Flow Analyser:** fluid selection (water/air/crude oil/user-defined) with auto-populated properties, pipe geometry and flow-rate inputs, velocity/Re/friction-factor/pressure-drop display, an interactive pressure-drop-vs-flow-rate plot, and CSV export.
- **Module B — Heat Transfer Calculator:** single-layer steady-state conduction (Fourier's Law), Newton's Law of Cooling time-to-target calculation, and a live temperature-vs-time cooling curve, with physical descriptions and unit guidance on every input.
- **Module C — Rock & Fluid Data Dashboard:** CSV upload with auto-detection of porosity/permeability columns, summary statistics, a porosity filter, a porosity histogram, a porosity-permeability crossplot, and a filtered-data CSV download.
- **Module D — Code quality:** OOP classes (`Fluid`, `Pipe`, `HeatTransferAnalysis`) in a separate `engineering.py` module, docstrings on every function/method, `try/except` error handling that shows a Streamlit warning instead of crashing on bad input, and an AI-usage documentation block at the top of `Home.py`.
