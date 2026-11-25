
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="System Capacity & Care Load Analytics",
    page_icon="📊",
    layout="wide"
)

# --------------------------------------------------
# CUSTOM DESIGN
# --------------------------------------------------

st.markdown("""
<style>

.stApp {
    background-color: #F3EEE7;
}

[data-testid="stMetric"] {
    background-color: #FFFFFF;
    padding: 18px;
    border-radius: 8px;
    border: 1px solid #E3D8CB;
}

h1, h2, h3 {
    color: #536B7C;
}

</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# LOAD DATASETS
# --------------------------------------------------

dashboard_df = pd.read_csv("dashboard_data.csv")
monthly_dashboard = pd.read_csv("monthly_dashboard.csv")

dashboard_df["Date"] = pd.to_datetime(dashboard_df["Date"])
monthly_dashboard["Date"] = pd.to_datetime(monthly_dashboard["Date"])

# --------------------------------------------------
# DASHBOARD HEADER
# --------------------------------------------------

st.title("System Capacity & Care Load Analytics")

st.markdown(
    "### Analytical Overview of Unaccompanied Children Care System"
)

st.caption("Data Analysis Period: January 2023 – December 2025")

st.divider()

# --------------------------------------------------
# DATA LOADING CONFIRMATION
# --------------------------------------------------

st.success("Dashboard datasets loaded successfully!")

st.write("Observation-level records:", len(dashboard_df))
st.write("Monthly analytical records:", len(monthly_dashboard))

# --------------------------------------------------
# DASHBOARD FILTERS
# --------------------------------------------------

st.subheader("Dashboard Filters")

col1, col2 = st.columns(2)

with col1:
    start_date = st.date_input(
        "Start Date",
        value=dashboard_df["Date"].min().date(),
        min_value=dashboard_df["Date"].min().date(),
        max_value=dashboard_df["Date"].max().date()
    )

with col2:
    end_date = st.date_input(
        "End Date",
        value=dashboard_df["Date"].max().date(),
        min_value=dashboard_df["Date"].min().date(),
        max_value=dashboard_df["Date"].max().date()
    )

granularity = st.selectbox(
    "Select Time Granularity",
    ["Monthly", "Quarterly", "Yearly"]
)

# Filter observation-level data
filtered_df = dashboard_df[
    (dashboard_df["Date"] >= pd.Timestamp(start_date)) &
    (dashboard_df["Date"] <= pd.Timestamp(end_date))
].copy()

# Filter monthly data
filtered_monthly = monthly_dashboard[
    (monthly_dashboard["Date"] >= pd.Timestamp(start_date)) &
    (monthly_dashboard["Date"] <= pd.Timestamp(end_date))
].copy()

st.write("Selected reporting period:", start_date, "to", end_date)
st.write("Selected granularity:", granularity)
st.write("Available observations:", len(filtered_df))

# --------------------------------------------------
# METRIC SELECTION
# --------------------------------------------------

metric_options = {
    "Total System Load": "Total_System_Load",
    "CBP Custody": "Children in CBP custody",
    "HHS Care": "Children in HHS Care"
}

selected_metric = st.selectbox(
    "Select System Load Metric",
    list(metric_options.keys())
)

selected_column = metric_options[selected_metric]

st.write("Selected metric:", selected_metric)
st.write("Metric column:", selected_column)

# --------------------------------------------------
# KPI SUMMARY CARDS
# --------------------------------------------------

st.divider()
st.subheader("Key Performance Indicators")

if not filtered_df.empty and not filtered_monthly.empty:

    # Calculate system load KPIs
    average_load = filtered_df[selected_column].mean()
    maximum_load = filtered_df[selected_column].max()
    minimum_load = filtered_df[selected_column].min()

    # Calculate monthly analytical KPIs
    net_intake = filtered_monthly["Net_Intake_Pressure"].mean()

    backlog_proxy = filtered_monthly[
        "Three_Month_Rolling_Net_Intake_Pressure_Proxy"
    ].mean()

    volatility = filtered_monthly[
        "Care_Load_Volatility_Index"
    ].mean()

    # First row of KPI cards
    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Average System Load",
        f"{average_load:,.0f}"
    )

    col2.metric(
        "Maximum System Load",
        f"{maximum_load:,.0f}"
    )

    col3.metric(
        "Minimum System Load",
        f"{minimum_load:,.0f}"
    )

    # Second row of KPI cards
    col4, col5, col6 = st.columns(3)

    col4.metric(
        "Net Intake Pressure",
        f"{net_intake:,.2f}"
    )

    col5.metric(
        "3-Month Rolling Net Intake Pressure (Proxy)",
        f"{backlog_proxy:,.2f}"
    )

    col6.metric(
        "Care Load Volatility Index",
        f"{volatility:,.2f}%"
    )

else:
    st.warning(
        "No sufficient data available for the selected reporting period."
    )

# --------------------------------------------------
# SYSTEM LOAD TREND ANALYSIS
# --------------------------------------------------

st.divider()
st.subheader("System Load Overview")

if not filtered_df.empty:

    trend_df = filtered_df.copy()
    trend_df = trend_df.set_index("Date")

    # Aggregate according to selected granularity
    if granularity == "Monthly":
        trend_data = trend_df[selected_column].resample("MS").mean()

    elif granularity == "Quarterly":
        trend_data = trend_df[selected_column].resample("QS").mean()

    else:
        trend_data = trend_df[selected_column].resample("YS").mean()

    trend_data = trend_data.dropna().reset_index()
    trend_data.columns = ["Date", "System Load"]

    # Create line chart
    fig = px.line(
        trend_data,
        x="Date",
        y="System Load",
        markers=True,
        title=f"{selected_metric} Trend Over Time"
    )

    fig.update_traces(
        line=dict(color="#6F8798", width=3),
        marker=dict(size=6, color="#B8784E")
    )

    fig.update_layout(
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#F3EEE7",
        font=dict(color="#45413D"),
        xaxis_title="Reporting Period",
        yaxis_title="Number of Children",
        hovermode="x unified"
    )

    st.plotly_chart(fig, use_container_width=True)

else:
    st.warning("No observations available for the selected date range.")

# --------------------------------------------------
# CBP VS HHS LOAD COMPARISON
# --------------------------------------------------

st.divider()
st.subheader("CBP vs HHS Care Load Comparison")

if not filtered_df.empty:

    agency_df = filtered_df.set_index("Date")

    # Aggregate both agency measures by selected granularity
    if granularity == "Monthly":
        agency_data = agency_df[
            ["Children in CBP custody", "Children in HHS Care"]
        ].resample("MS").mean()

    elif granularity == "Quarterly":
        agency_data = agency_df[
            ["Children in CBP custody", "Children in HHS Care"]
        ].resample("QS").mean()

    else:
        agency_data = agency_df[
            ["Children in CBP custody", "Children in HHS Care"]
        ].resample("YS").mean()

    agency_data = agency_data.dropna().reset_index()

    agency_data = agency_data.melt(
        id_vars="Date",
        value_vars=[
            "Children in CBP custody",
            "Children in HHS Care"
        ],
        var_name="Agency",
        value_name="Children"
    )

    fig = px.line(
        agency_data,
        x="Date",
        y="Children",
        color="Agency",
        markers=True,
        title="Children in CBP Custody vs HHS Care"
    )

    fig.update_traces(line=dict(width=3))

    fig.update_layout(
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#F3EEE7",
        font=dict(color="#45413D"),
        xaxis_title="Reporting Period",
        yaxis_title="Number of Children",
        hovermode="x unified",
        legend_title="Agency",
        colorway=["#B8784E", "#6F8798"]
    )

    st.plotly_chart(fig, use_container_width=True)

else:
    st.warning("No observations available for the selected date range.")
