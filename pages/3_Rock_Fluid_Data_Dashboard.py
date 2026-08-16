"""
Module C — Rock & Fluid Data Dashboard.

Upload a CSV of rock/fluid sample data, view summary statistics, filter by
porosity, and see a porosity histogram and a porosity-permeability
crossplot, then download the filtered data.
"""

import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Rock & Fluid Data Dashboard", page_icon="🪨", layout="wide")

st.title("🪨 Rock & Fluid Data Dashboard")
st.markdown(
    "Upload a CSV of core/rock sample data (needs at least **porosity** and "
    "**permeability** columns) to explore summary statistics, filter "
    "samples, and visualise porosity-permeability relationships."
)

st.info(
    "Don't have a file handy? A sample CSV (`sample_rock_data.csv`) is "
    "included in the project repository — use it to test this module."
)

uploaded_file = st.file_uploader("Upload rock/fluid data (CSV)", type=["csv"])

def find_column(df: pd.DataFrame, keywords: list) -> str | None:
    """Return the first column name in df whose lowercase name contains any
    of the given keywords, or None if no match is found.

    Used so the dashboard works with slightly different column-naming
    conventions (e.g. 'porosity', 'Porosity_frac', 'PHI') without forcing
    the user to rename their CSV columns.
    """
    for col in df.columns:
        col_lower = col.lower()
        if any(kw in col_lower for kw in keywords):
            return col
    return None


if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)

        if df.empty:
            st.warning("⚠️ The uploaded CSV has no rows. Please upload a file with data.")
        else:
            st.subheader("📋 Data Preview")
            st.dataframe(df.head(20), width='stretch')

            st.subheader("📊 Summary Statistics")
            st.dataframe(df.describe(), width='stretch')

            # ---------------------------------------------------------
            # Try to auto-detect porosity / permeability columns
            # ---------------------------------------------------------
            poro_col = find_column(df, ["poro", "phi"])
            perm_col = find_column(df, ["perm", "k_md", "permeability"])

            if poro_col is None or perm_col is None:
                st.warning(
                    "⚠️ Could not automatically detect porosity and/or "
                    "permeability columns. Please ensure your CSV has "
                    "columns with names containing 'poro' and 'perm' "
                    "(e.g. 'porosity', 'permeability_mD')."
                )
            else:
                st.success(f"Detected porosity column: **{poro_col}**, permeability column: **{perm_col}**")

                # Porosity may be stored as a fraction (0-1) or a percentage (0-100)
                poro_series = pd.to_numeric(df[poro_col], errors="coerce")
                poro_is_fraction = poro_series.max() <= 1.5

                st.subheader("🔍 Filter")
                if poro_is_fraction:
                    threshold = st.slider(
                        "Show only samples where porosity >", 0.0, float(poro_series.max()), 0.10, step=0.01,
                        help="Porosity appears to be stored as a fraction (0-1).",
                    )
                else:
                    threshold = st.slider(
                        "Show only samples where porosity (%) >", 0.0, float(poro_series.max()), 10.0, step=0.5,
                        help="Porosity appears to be stored as a percentage.",
                    )

                filtered_df = df[poro_series > threshold].copy()
                st.write(f"**{len(filtered_df)}** of **{len(df)}** samples pass the filter.")
                st.dataframe(filtered_df, width='stretch')

                if filtered_df.empty:
                    st.warning("⚠️ No samples pass this filter — try lowering the threshold.")
                else:
                    # -------------------------------------------------
                    # Charts
                    # -------------------------------------------------
                    st.subheader("📈 Charts")
                    chart_col1, chart_col2 = st.columns(2)

                    with chart_col1:
                        fig_hist = px.histogram(
                            filtered_df, x=poro_col, nbins=20,
                            title="Porosity Distribution",
                            color_discrete_sequence=["#2563EB"],
                        )
                        fig_hist.update_layout(template="plotly_white", height=400)
                        st.plotly_chart(fig_hist, width='stretch')

                    with chart_col2:
                        fig_cross = px.scatter(
                            filtered_df, x=poro_col, y=perm_col,
                            title="Porosity–Permeability Crossplot",
                            color_discrete_sequence=["#EF4444"],
                            log_y=True,
                        )
                        fig_cross.update_layout(template="plotly_white", height=400)
                        fig_cross.update_yaxes(title=f"{perm_col} (log scale)")
                        st.plotly_chart(fig_cross, width='stretch')

                    # -------------------------------------------------
                    # Download filtered data
                    # -------------------------------------------------
                    st.download_button(
                        "⬇️ Download filtered data (CSV)",
                        data=filtered_df.to_csv(index=False),
                        file_name="filtered_rock_data.csv",
                        mime="text/csv",
                    )

    except pd.errors.EmptyDataError:
        st.warning("⚠️ The uploaded file is empty or not a valid CSV.")
    except pd.errors.ParserError:
        st.warning("⚠️ Could not parse this file as a CSV. Please check the file format.")
    except Exception as e:
        st.warning(f"⚠️ Something went wrong reading the file: {e}")
else:
    st.caption("Waiting for a CSV upload...")
