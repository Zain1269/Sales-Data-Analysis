import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# -----------------------------
# Page setup
# -----------------------------
st.set_page_config(
    page_title="Sales Data Analysis",
    layout="wide"
)

# -----------------------------
# Load data
# -----------------------------
st.sidebar.header("Data and Filters")
uploaded_file = st.sidebar.file_uploader(
    "Upload sales CSV",
    type="csv"
)

default_data_path = Path(__file__).with_name("online_retail_task2_students.csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
elif default_data_path.exists():
    df = pd.read_csv(default_data_path)
else:
    st.error(
        "Upload online_retail_task2_students.csv in the sidebar to load the dashboard."
    )
    st.stop()

df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])

# -----------------------------
# Clean data
# -----------------------------
df = df.drop_duplicates()

df = df.dropna(subset=["Description"])

df = df[
    (df["Quantity"] > 0) &
    (df["UnitPrice"] > 0)
].copy()

df["Sales"] = df["Quantity"] * df["UnitPrice"]

# -----------------------------
# Title
# -----------------------------
st.title("Sales Data Analysis Dashboard")
st.caption("Online Retail Sales Analysis")

def update_chart_filter(chart_key, filter_key):
    selection = st.session_state[chart_key].selection
    points = selection.get("points", [])
    st.session_state[filter_key] = {
        point["customdata"][0]
        for point in points
        if point.get("customdata")
    }


for filter_key in ("chart_countries", "chart_products", "chart_months"):
    st.session_state.setdefault(filter_key, set())

# -----------------------------
# Filters
# -----------------------------
if st.sidebar.button("Reset chart selections"):
    st.session_state.chart_countries = set()
    st.session_state.chart_products = set()
    st.session_state.chart_months = set()
    st.rerun()

countries = sorted(df["Country"].dropna().unique())

selected_countries = st.sidebar.multiselect(
    "Select Country",
    countries
)

if selected_countries:
    filtered_df = df[
        df["Country"].isin(selected_countries)
    ].copy()
else:
    filtered_df = df.copy()

date_range = st.sidebar.date_input(
    "Select date range",
    value=(df["InvoiceDate"].min().date(), df["InvoiceDate"].max().date())
)

if len(date_range) == 2:
    filtered_df = filtered_df[
        filtered_df["InvoiceDate"].dt.date.between(date_range[0], date_range[1])
    ].copy()

if st.session_state.chart_countries:
    filtered_df = filtered_df[
        filtered_df["Country"].isin(st.session_state.chart_countries)
    ].copy()

if st.session_state.chart_products:
    filtered_df = filtered_df[
        filtered_df["Description"].isin(st.session_state.chart_products)
    ].copy()

if st.session_state.chart_months:
    filtered_df = filtered_df[
        filtered_df["InvoiceDate"].dt.to_period("M").astype(str).isin(
            st.session_state.chart_months
        )
    ].copy()

# -----------------------------
# KPIs
# -----------------------------
total_sales = filtered_df["Sales"].sum()
total_invoices = filtered_df["InvoiceNo"].nunique()
total_customers = filtered_df["CustomerID"].nunique()
total_products = filtered_df["StockCode"].nunique()

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Total Sales",
    f"${total_sales:,.2f}"
)

col2.metric(
    "Invoices",
    f"{total_invoices:,}"
)

col3.metric(
    "Customers",
    f"{total_customers:,}"
)

col4.metric(
    "Products",
    f"{total_products:,}"
)

st.divider()

# -----------------------------
# Monthly Sales
# -----------------------------
st.subheader("Monthly Sales Trend")

monthly_sales = (
    filtered_df
    .groupby(filtered_df["InvoiceDate"].dt.to_period("M"))["Sales"]
    .sum()
    .reset_index()
)

monthly_sales["InvoiceDate"] = monthly_sales["InvoiceDate"].astype(str)

fig = px.line(
    monthly_sales,
    x="InvoiceDate",
    y="Sales",
    markers=True,
    title="Sales by Month",
    custom_data=["InvoiceDate"]
)

st.plotly_chart(
    fig,
    use_container_width=True,
    key="monthly_chart",
    on_select=lambda: update_chart_filter("monthly_chart", "chart_months"),
    selection_mode=("points",)
)

# -----------------------------
# Product analysis
# -----------------------------
col1, col2 = st.columns(2)

with col1:

    st.subheader("Top 5 Products by Revenue")

    top_products = (
        filtered_df
        .groupby("Description")["Sales"]
        .sum()
        .nlargest(5)
        .sort_values()
        .reset_index()
    )

    fig = px.bar(
        top_products,
        x="Sales",
        y="Description",
        orientation="h",
        title="Top 5 Products by Revenue",
        custom_data=["Description"]
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        key="revenue_chart",
        on_select=lambda: update_chart_filter("revenue_chart", "chart_products"),
        selection_mode=("points",)
    )


with col2:

    st.subheader("Top 5 Products by Quantity")

    top_quantity = (
        filtered_df
        .groupby("Description")["Quantity"]
        .sum()
        .nlargest(5)
        .sort_values()
        .reset_index()
    )

    fig = px.bar(
        top_quantity,
        x="Quantity",
        y="Description",
        orientation="h",
        title="Top 5 Products by Quantity",
        custom_data=["Description"]
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        key="quantity_chart",
        on_select=lambda: update_chart_filter("quantity_chart", "chart_products"),
        selection_mode=("points",)
    )

# -----------------------------
# Country analysis
# -----------------------------
st.subheader("Sales by Country")

country_sales = (
    filtered_df
    .groupby("Country")["Sales"]
    .sum()
    .nlargest(10)
    .sort_values()
    .reset_index()
)

fig = px.bar(
    country_sales,
    x="Sales",
    y="Country",
    orientation="h",
    title="Sales by Country",
    custom_data=["Country"]
)

st.plotly_chart(
    fig,
    use_container_width=True,
    key="country_chart",
    on_select=lambda: update_chart_filter("country_chart", "chart_countries"),
    selection_mode=("points",)
)

# =====================================================
# KEY INSIGHTS
# =====================================================

st.divider()

st.header("Key Insights")

insights = [
    f"The dataset covers ${total_sales:,.2f} in total sales across "
    f"{total_invoices:,} invoices, {total_customers:,} customers, "
    f"and {total_products:,} unique products.",

    "Revenue leaders differed from the most frequently purchased "
    "products — product 22423 led sales by a wide margin.",

    "The UK generated more than 15× the sales of the Netherlands.",

    "November 2011 was the highest-sales month, with sales peaking "
    "well above the rest of the year.",

    "Sales fluctuated significantly across the analyzed period."
]

for insight in insights:
    st.write("•", insight)

# =====================================================
# RECOMMENDATIONS
# =====================================================

st.header("Recommendations")

recommendations = [
    "Focus marketing efforts on the UK market.",

    "Maintain sufficient stock of high-revenue products.",

    "Investigate low-performing months.",

    "Review the profitability of lower-performing markets."
]

for recommendation in recommendations:
    st.write("•", recommendation)
