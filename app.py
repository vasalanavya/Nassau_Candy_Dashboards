import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Nassau Candy Profitability Dashboard",
    page_icon="🍬",
    layout="wide"
)

st.title("🍬 Nassau Candy Distributor")
st.subheader("Product Line Profitability and Margin Performance Analysis")

st.markdown("""
This dashboard analyzes product profitability, sales,
cost, gross profit, margins and division performance.
""")

# --------------------------------------------------
# 1. LOAD DATASET
# --------------------------------------------------

uploaded_file = st.sidebar.file_uploader(
    "Upload Nassau Candy CSV",
    type=["csv"]
)

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
else:
    try:
        df = pd.read_csv("Nassau_Candy.csv")
    except FileNotFoundError:
        st.error(
            "Nassau_Candy.csv not found. "
            "Keep the CSV in the same folder as app.py."
        )
        st.stop()

# --------------------------------------------------
# 2. CLEAN COLUMN NAMES
# --------------------------------------------------

df.columns = df.columns.str.strip()

required_columns = [
    "Sales",
    "Cost",
    "Gross Profit",
    "Units",
    "Product Name",
    "Division",
    "Region"
]

missing_columns = [
    col for col in required_columns
    if col not in df.columns
]

if missing_columns:
    st.error(
        f"Missing required columns: {missing_columns}"
    )
    st.write("Available columns:", df.columns.tolist())
    st.stop()

# --------------------------------------------------
# 3. DATA CLEANING
# --------------------------------------------------

numeric_columns = [
    "Sales",
    "Cost",
    "Gross Profit",
    "Units"
]

for col in numeric_columns:
    df[col] = pd.to_numeric(
        df[col],
        errors="coerce"
    )

df = df.dropna(
    subset=[
        "Sales",
        "Cost",
        "Gross Profit",
        "Units",
        "Product Name",
        "Division",
        "Region"
    ]
).copy()

df = df.replace([np.inf, -np.inf], np.nan)

df = df.dropna(
    subset=numeric_columns
).copy()

# Remove invalid negative sales, costs and units
df = df[
    (df["Sales"] >= 0) &
    (df["Cost"] >= 0) &
    (df["Units"] >= 0)
].copy()

# --------------------------------------------------
# 4. CALCULATE PROFITABILITY METRICS
# --------------------------------------------------

# Gross Profit is already present in the dataset.
# Do not overwrite it or create it again.

df["Gross Margin"] = np.where(
    df["Sales"] > 0,
    (df["Gross Profit"] / df["Sales"]) * 100,
    np.nan
)

df["Profit Per Unit"] = np.where(
    df["Units"] > 0,
    df["Gross Profit"] / df["Units"],
    np.nan
)

df["Total Profit Contribution"] = df["Gross Profit"]

df["Cost Percentage"] = np.where(
    df["Sales"] > 0,
    (df["Cost"] / df["Sales"]) * 100,
    np.nan
)

# --------------------------------------------------
# 5. SIDEBAR FILTERS
# --------------------------------------------------

st.sidebar.header("Dashboard Filters")

divisions = sorted(
    df["Division"].dropna().unique().tolist()
)

selected_divisions = st.sidebar.multiselect(
    "Select Division",
    divisions,
    default=divisions
)

regions = sorted(
    df["Region"].dropna().unique().tolist()
)

selected_regions = st.sidebar.multiselect(
    "Select Region",
    regions,
    default=regions
)

filtered_df = df[
    df["Division"].isin(selected_divisions) &
    df["Region"].isin(selected_regions)
].copy()

if filtered_df.empty:
    st.warning("No records available for selected filters.")
    st.stop()

# --------------------------------------------------
# 6. PRODUCT PROFITABILITY OVERVIEW
# --------------------------------------------------

st.header("1. Product Profitability Overview")

total_sales = filtered_df["Sales"].sum()
total_cost = filtered_df["Cost"].sum()
total_profit = filtered_df["Gross Profit"].sum()
total_units = filtered_df["Units"].sum()

overall_margin = (
    total_profit / total_sales * 100
    if total_sales != 0 else 0
)

c1, c2, c3, c4 = st.columns(4)

c1.metric("Total Sales", f"${total_sales:,.2f}")
c2.metric("Total Cost", f"${total_cost:,.2f}")
c3.metric("Gross Profit", f"${total_profit:,.2f}")
c4.metric("Gross Margin", f"{overall_margin:.2f}%")

c5, c6 = st.columns(2)

c5.metric("Total Units Sold", f"{total_units:,.0f}")

c6.metric(
    "Number of Products",
    filtered_df["Product Name"].nunique()
)

st.subheader("Dataset Preview")

st.dataframe(
    filtered_df[
        [
            "Product Name",
            "Sales",
            "Cost",
            "Gross Profit",
            "Units",
            "Gross Margin",
            "Profit Per Unit"
        ]
    ],
    use_container_width=True
)

# --------------------------------------------------
# 7. PRODUCT LEVEL MARGIN LEADERBOARD
# --------------------------------------------------

st.header("2. Product-Level Margin Leaderboard")

product_summary = (
    filtered_df.groupby("Product Name", as_index=False)
    .agg({
        "Sales": "sum",
        "Cost": "sum",
        "Gross Profit": "sum",
        "Units": "sum"
    })
)

product_summary["Gross Margin"] = np.where(
    product_summary["Sales"] > 0,
    product_summary["Gross Profit"] /
    product_summary["Sales"] * 100,
    np.nan
)

product_summary["Profit Per Unit"] = np.where(
    product_summary["Units"] > 0,
    product_summary["Gross Profit"] /
    product_summary["Units"],
    np.nan
)

product_summary = product_summary.sort_values(
    "Gross Margin",
    ascending=False
)

st.dataframe(
    product_summary,
    use_container_width=True
)

top_products = product_summary.nlargest(
    10, "Gross Margin"
)

fig1 = px.bar(
    top_products,
    x="Gross Margin",
    y="Product Name",
    orientation="h",
    title="Top 10 Products by Gross Margin",
    text_auto=".2f"
)

st.plotly_chart(fig1, use_container_width=True)

# --------------------------------------------------
# 8. PROFIT CONTRIBUTION CHARTS
# --------------------------------------------------

st.header("3. Profit Contribution Charts")

profit_products = product_summary.sort_values(
    "Gross Profit",
    ascending=False
).head(10)

fig2 = px.bar(
    profit_products,
    x="Product Name",
    y="Gross Profit",
    color="Gross Profit",
    title="Top 10 Products by Gross Profit"
)

fig2.update_layout(xaxis_tickangle=-45)

st.plotly_chart(fig2, use_container_width=True)

fig3 = px.pie(
    profit_products,
    names="Product Name",
    values="Gross Profit",
    title="Profit Contribution by Product"
)

st.plotly_chart(fig3, use_container_width=True)

# --------------------------------------------------
# 9. DIVISION PERFORMANCE DASHBOARD
# --------------------------------------------------

st.header("4. Division Performance Dashboard")

division_summary = (
    filtered_df.groupby("Division", as_index=False)
    .agg({
        "Sales": "sum",
        "Cost": "sum",
        "Gross Profit": "sum",
        "Units": "sum"
    })
)

division_summary["Gross Margin"] = np.where(
    division_summary["Sales"] > 0,
    division_summary["Gross Profit"] /
    division_summary["Sales"] * 100,
    np.nan
)

st.dataframe(
    division_summary,
    use_container_width=True
)

# --------------------------------------------------
# 10. REVENUE VS PROFIT COMPARISON
# --------------------------------------------------

st.header("5. Revenue vs Profit Comparison")

fig4 = px.bar(
    division_summary,
    x="Division",
    y=["Sales", "Gross Profit"],
    barmode="group",
    title="Division-wise Revenue vs Gross Profit"
)

st.plotly_chart(fig4, use_container_width=True)

# --------------------------------------------------
# 11. MARGIN DISTRIBUTION BY DIVISION
# --------------------------------------------------

st.header("6. Margin Distribution by Division")

fig5 = px.box(
    filtered_df,
    x="Division",
    y="Gross Margin",
    color="Division",
    title="Gross Margin Distribution by Division"
)

st.plotly_chart(fig5, use_container_width=True)

# --------------------------------------------------
# 12. COST VS MARGIN DIAGNOSTIC
# --------------------------------------------------

st.header("7. Cost vs Margin Diagnostic")

fig6 = px.scatter(
    product_summary,
    x="Cost",
    y="Gross Margin",
    size="Sales",
    color="Gross Profit",
    hover_name="Product Name",
    title="Product Cost vs Gross Margin"
)

st.plotly_chart(fig6, use_container_width=True)

# --------------------------------------------------
# 13. COST-SALES SCATTER PLOT
# --------------------------------------------------

st.header("8. Cost-Sales Scatter Plot")

fig7 = px.scatter(
    filtered_df,
    x="Cost",
    y="Sales",
    color="Division",
    size="Units",
    hover_name="Product Name",
    title="Relationship Between Cost and Sales"
)

st.plotly_chart(fig7, use_container_width=True)

# --------------------------------------------------
# 14. MARGIN RISK FLAGS
# --------------------------------------------------

st.header("9. Margin Risk Flags")

def assign_flag(row):

    if row["Gross Profit"] < 0:
        return "Loss Making"

    elif row["Gross Margin"] < 10:
        return "Margin Poor"

    elif row["Cost Percentage"] > 90:
        return "Cost Heavy"

    elif row["Gross Margin"] < 20:
        return "Pricing Review"

    else:
        return "Healthy"


product_summary["Cost Percentage"] = np.where(
    product_summary["Sales"] > 0,
    product_summary["Cost"] /
    product_summary["Sales"] * 100,
    np.nan
)

product_summary["Product_Flag"] = product_summary.apply(
    assign_flag,
    axis=1
)

st.dataframe(
    product_summary[
        [
            "Product Name",
            "Sales",
            "Cost",
            "Gross Profit",
            "Gross Margin",
            "Cost Percentage",
            "Product_Flag"
        ]
    ],
    use_container_width=True
)

flag_counts = (
    product_summary["Product_Flag"]
    .value_counts()
    .reset_index()
)

flag_counts.columns = [
    "Product Flag",
    "Number of Products"
]

fig8 = px.bar(
    flag_counts,
    x="Product Flag",
    y="Number of Products",
    color="Product Flag",
    title="Product Margin Risk Classification"
)

st.plotly_chart(fig8, use_container_width=True)

# --------------------------------------------------
# 15. PROFIT CONCENTRATION ANALYSIS
# --------------------------------------------------

st.header("10. Profit Concentration Analysis")

concentration = product_summary.sort_values(
    "Gross Profit",
    ascending=False
).copy()

positive_profit_total = concentration[
    "Gross Profit"
].clip(lower=0).sum()

if positive_profit_total > 0:

    concentration["Profit Contribution %"] = (
        concentration["Gross Profit"].clip(lower=0) /
        positive_profit_total * 100
    )

    concentration["Cumulative Profit %"] = (
        concentration["Profit Contribution %"].cumsum()
    )

    concentration["Cumulative Products %"] = (
        np.arange(1, len(concentration) + 1) /
        len(concentration) * 100
    )

    st.dataframe(
        concentration[
            [
                "Product Name",
                "Gross Profit",
                "Profit Contribution %",
                "Cumulative Profit %"
            ]
        ],
        use_container_width=True
    )

else:
    st.warning(
        "Positive gross profit is not available for concentration analysis."
    )

# --------------------------------------------------
# 16. PARETO ANALYSIS
# --------------------------------------------------

st.header("11. Pareto Analysis")

pareto_df = product_summary.sort_values(
    "Gross Profit",
    ascending=False
).copy()

pareto_total = pareto_df["Gross Profit"].clip(lower=0).sum()

if pareto_total > 0:

    pareto_df["Contribution"] = (
        pareto_df["Gross Profit"].clip(lower=0) /
        pareto_total * 100
    )

    pareto_df["Cumulative Contribution"] = (
        pareto_df["Contribution"].cumsum()
    )

    fig9 = go.Figure()

    fig9.add_trace(
        go.Bar(
            x=pareto_df["Product Name"],
            y=pareto_df["Contribution"],
            name="Profit Contribution"
        )
    )

    fig9.add_trace(
        go.Scatter(
            x=pareto_df["Product Name"],
            y=pareto_df["Cumulative Contribution"],
            name="Cumulative Profit %",
            yaxis="y2",
            mode="lines+markers"
        )
    )

    fig9.update_layout(
        title="Pareto Chart - Product Profit Contribution",
        xaxis_title="Product Name",
        yaxis_title="Profit Contribution %",
        yaxis2=dict(
            title="Cumulative Profit %",
            overlaying="y",
            side="right",
            range=[0, 105]
        )
    )

    st.plotly_chart(fig9, use_container_width=True)

else:
    st.warning("Cannot create Pareto chart without positive profit.")

# --------------------------------------------------
# 17. DEPENDENCY INDICATOR
# --------------------------------------------------

st.header("12. Profit Dependency Indicator")

if positive_profit_total > 0:

    top_5_profit = (
        concentration["Gross Profit"]
        .clip(lower=0)
        .head(5)
        .sum()
    )

    dependency = (
        top_5_profit / positive_profit_total * 100
    )

    st.metric(
        "Top 5 Products Profit Dependency",
        f"{dependency:.2f}%"
    )

    if dependency >= 80:
        st.warning(
            "High dependency: A large share of profit comes from "
            "the top 5 products."
        )

    elif dependency >= 50:
        st.info(
            "Moderate dependency: Monitor the contribution "
            "of leading products."
        )

    else:
        st.success(
            "Low dependency: Profit is relatively distributed "
            "across products."
        )

else:
    st.warning(
        "Dependency cannot be calculated because positive profit is zero."
    )

# --------------------------------------------------
# 18. DOWNLOAD ANALYSIS
# --------------------------------------------------

st.header("Download Analysis")

csv_data = product_summary.to_csv(index=False).encode("utf-8")

st.download_button(
    label="Download Product Profitability Report",
    data=csv_data,
    file_name="Nassau_Candy_Profitability_Analysis.csv",
    mime="text/csv"
)

st.success("Nassau Candy Dashboard Loaded Successfully!")


