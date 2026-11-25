
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="System Capacity & Care Load Analytics",
    page_icon="📊",
    layout="wide"
)

# Colour palette
BLUE = "#6F8798"
TERRACOTTA = "#B8784E"
GREY = "#9A9A8A"
TEXT = "#45413D"
PAPER = "#F3EEE7"

# Dashboard styling
st.markdown("""
<style>
:root {
    color-scheme: light;
}

.stApp,
[data-testid="stAppViewContainer"] {
    background-color: #F3EEE7;
    color: #45413D;
}

[data-testid="stSidebar"] {
    background-color: #E9E2D8;
}

[data-testid="stMetric"] {
    background-color: #FFFFFF;
    padding: 18px;
    border-radius: 9px;
    border: 1px solid #E3D8CB;
}

h1, h2, h3 {
    color: #536B7C;
}

p, label {
    color: #45413D;
}
</style>
""", unsafe_allow_html=True)

# Load dashboard datasets
dashboard_df = pd.read_csv("dashboard_data.csv")
monthly_dashboard = pd.read_csv("monthly_dashboard.csv")

dashboard_df["Date"] = pd.to_datetime(dashboard_df["Date"])
monthly_dashboard["Date"] = pd.to_datetime(monthly_dashboard["Date"])

# Sidebar controls
st.sidebar.title("Dashboard Controls")

min_date = dashboard_df["Date"].min().date()
max_date = dashboard_df["Date"].max().date()

start_date = st.sidebar.date_input(
    "Start Date",
    value=min_date,
    min_value=min_date,
    max_value=max_date
)

end_date = st.sidebar.date_input(
    "End Date",
    value=max_date,
    min_value=min_date,
    max_value=max_date
)

granularity = st.sidebar.selectbox(
    "Time Granularity",
    ["Monthly", "Quarterly", "Yearly"]
)

metric_options = {
    "Total System Load": "Total_System_Load",
    "CBP Custody": "Children in CBP custody",
    "HHS Care": "Children in HHS Care"
}

selected_metric = st.sidebar.selectbox(
    "System Load Metric",
    list(metric_options.keys())
)

selected_column = metric_options[selected_metric]

# Apply date filters
filtered_df = dashboard_df[
    (dashboard_df["Date"].dt.date >= start_date) &
    (dashboard_df["Date"].dt.date <= end_date)
].copy()

# Include every monthly record whose month overlaps the selected date range
monthly_period_start = monthly_dashboard["Date"].dt.to_period("M").dt.start_time
monthly_period_end = monthly_period_start + pd.offsets.MonthEnd(0)

filtered_monthly = monthly_dashboard[
    (monthly_period_start.dt.date <= end_date) &
    (monthly_period_end.dt.date >= start_date)
].copy()

# Dashboard heading
st.title("System Capacity & Care Load Analytics")

st.markdown(
    """
    This dashboard analyzes reported care workload across the
    **U.S. Customs and Border Protection (CBP)** and
    **Department of Health and Human Services (HHS)** systems.

    It examines system-wide care load, agency-level trends,
    intake and discharge patterns, and indicators of sustained
    care-load pressure.
    """
)

st.caption(
    "Reporting Period: January 2023 – December 2025 | "
    "Data Analytics Internship Project – Unified Mentor"
)

st.divider()

# Main dashboard sections
overview_tab, data_tab, insights_tab = st.tabs([
    "Overview",
    "Data Explorer",
    "Insights & Methodology"
])

# Overview section
with overview_tab:

    st.subheader("Care Load Snapshot")

    if not filtered_df.empty:

        latest_row = filtered_df.sort_values("Date").iloc[-1]

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Total Children Under Care",
            f"{latest_row['Total_System_Load']:,.0f}"
        )

        col2.metric(
            "Children in HHS Care",
            f"{latest_row['Children in HHS Care']:,.0f}"
        )

        col3.metric(
            "Children in CBP Custody",
            f"{latest_row['Children in CBP custody']:,.0f}"
        )

        st.caption(
            f"Latest available observation: {latest_row['Date'].strftime('%d %B %Y')}"
        )

        st.markdown("### System Performance Indicators")
        st.caption("These indicators summarize the selected reporting period.")

        avg_load = filtered_df["Total_System_Load"].mean()
        max_load = filtered_df["Total_System_Load"].max()
        min_load = filtered_df["Total_System_Load"].min()

        net_intake_avg = (
            filtered_monthly["Net_Intake_Pressure"].mean()
            if not filtered_monthly.empty else None
        )

        backlog_avg = (
            filtered_monthly[
                "Three_Month_Rolling_Net_Intake_Pressure_Proxy"
            ].mean()
            if not filtered_monthly.empty else None
        )

        volatility_avg = (
            filtered_monthly["Care_Load_Volatility_Index"].mean()
            if not filtered_monthly.empty else None
        )

        def format_kpi(value):
            return f"{value:,.2f}" if pd.notna(value) else "—"

        kpi1, kpi2, kpi3 = st.columns(3)

        kpi1.metric("Average System Load", format_kpi(avg_load))
        kpi2.metric("Maximum System Load", format_kpi(max_load))
        kpi3.metric("Minimum System Load", format_kpi(min_load))

        kpi4, kpi5, kpi6 = st.columns(3)

        kpi4.metric("Net Intake Pressure", format_kpi(net_intake_avg))
        kpi5.metric("3-Month Rolling Net Intake Pressure", format_kpi(backlog_avg))
        kpi6.metric("Care Load Volatility Index", format_kpi(volatility_avg))

        st.caption(
            "System-load KPIs use observation-level records. "
            "The other three indicators use monthly analytical values. "
            "Values are averages over the selected period."
        )

    else:
        st.warning("No records are available for the selected date range.")

    st.divider()

    st.subheader("Analytical Chart")

    chart_options = [
        "System Load Overview",
        "CBP vs HHS Load Comparison",
        "Net Intake & Backlog Trends",
        "HHS Transfers vs Discharges",
        "Care Load Volatility",
        "Discharge Offset Ratio",
        "Rolling Average System Load",
        "System Load Distribution by Agency",
        "Care Load Growth Rate"
    ]

    selected_chart = st.selectbox(
        "Choose an analysis",
        chart_options
    )


    # Common chart styling
    chart_df = filtered_df.copy()
    chart_df = chart_df.sort_values("Date")

    period_map = {
        "Monthly": "MS",
        "Quarterly": "QS",
        "Yearly": "YS"
    }

    period = period_map[granularity]

    def style_chart(fig):
        fig.update_layout(
            paper_bgcolor=PAPER,
            plot_bgcolor="#FFFFFF",

            font=dict(
                family="Arial, sans-serif",
                size=13,
                color=TEXT
            ),

            title=dict(
                font=dict(size=19, color="#536B7C"),
                x=0.02,
                xanchor="left"
            ),

            margin=dict(
                l=65,
                r=35,
                t=75,
                b=65
            ),

            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                font=dict(size=11)
            ),

            xaxis=dict(
                showgrid=False,
                linecolor="#D8CEC2",
                tickfont=dict(size=11, color=TEXT),
                title_font=dict(size=13, color=TEXT)
            ),

            yaxis=dict(
                showgrid=True,
                gridcolor="#EAE4DC",
                zeroline=False,
                tickfont=dict(size=11, color=TEXT),
                title_font=dict(size=13, color=TEXT)
            ),

            hoverlabel=dict(
                bgcolor="#FFFFFF",
                font=dict(color=TEXT, size=12),
                bordercolor=BLUE
            )
        )

        return fig

    if chart_df.empty:
        st.warning("No data available for this chart and date range.")

    elif selected_chart == "System Load Overview":

        trend = (
            chart_df.set_index("Date")[selected_column]
            .resample(period).mean().reset_index()
        )

        fig = px.line(
            trend,
            x="Date",
            y=selected_column,
            markers=True,
            title=f"{selected_metric} — {granularity} Trend",
            labels={
                "Date": "Reporting Period",
                selected_column: "Number of Children"
            }
        )
        fig.update_traces(line_color=BLUE, marker_color=TERRACOTTA)
        st.plotly_chart(style_chart(fig), use_container_width=True)

    elif selected_chart == "CBP vs HHS Load Comparison":

        trend = (
            chart_df.set_index("Date")[
                ["Children in CBP custody", "Children in HHS Care"]
            ]
            .resample(period).mean().reset_index()
        )

        fig = px.line(
            trend,
            x="Date",
            y=["Children in CBP custody", "Children in HHS Care"],
            markers=True,
            title="Average Children in CBP Custody vs HHS Care",
            labels={
                "Date": "Reporting Period",
                "value": "Number of Children",
                "variable": "Agency"
            },
            color_discrete_map={
                "Children in CBP custody": TERRACOTTA,
                "Children in HHS Care": BLUE
            }
        )
        st.plotly_chart(style_chart(fig), use_container_width=True)

    elif selected_chart == "Net Intake & Backlog Trends":

        required = [
            "Net_Intake_Pressure",
            "Three_Month_Rolling_Net_Intake_Pressure_Proxy"
        ]

        if all(col in filtered_monthly.columns for col in required):
            fig = go.Figure()

            fig.add_trace(go.Bar(
                x=filtered_monthly["Date"],
                y=filtered_monthly["Net_Intake_Pressure"],
                name="Monthly Net Intake Pressure",
                marker_color=TERRACOTTA
            ))

            fig.add_trace(go.Scatter(
                x=filtered_monthly["Date"],
                y=filtered_monthly["Three_Month_Rolling_Net_Intake_Pressure_Proxy"],
                name="3-Month Backlog Pressure Proxy",
                mode="lines+markers",
                line=dict(color=BLUE, width=3)
            ))

            fig.update_layout(
                title="HHS Net Intake Pressure and Backlog Proxy",
                xaxis_title="Month",
                yaxis_title="Average Children per Recorded Observation"
            )
            st.plotly_chart(style_chart(fig), use_container_width=True)
        else:
            st.warning("The required monthly KPI columns were not found.")

    elif selected_chart == "HHS Transfers vs Discharges":

        required = ["Transfers_Avg", "Discharges_Avg"]

        if all(col in filtered_monthly.columns for col in required):
            fig = go.Figure()

            fig.add_trace(go.Bar(
                x=filtered_monthly["Date"],
                y=filtered_monthly["Transfers_Avg"],
                name="Average HHS Transfers",
                marker_color=BLUE
            ))

            fig.add_trace(go.Bar(
                x=filtered_monthly["Date"],
                y=filtered_monthly["Discharges_Avg"],
                name="Average HHS Discharges",
                marker_color=TERRACOTTA
            ))

            fig.update_layout(
                title="Average Monthly HHS Transfers vs Discharges",
                xaxis_title="Month",
                yaxis_title="Average Children",
                barmode="group"
            )
            st.plotly_chart(style_chart(fig), use_container_width=True)
        else:
            st.warning("The required monthly flow columns were not found.")

    elif selected_chart == "Care Load Volatility":

        if "Care_Load_Volatility_Index" in filtered_monthly.columns:
            fig = px.line(
                filtered_monthly,
                x="Date",
                y="Care_Load_Volatility_Index",
                markers=True,
                title="Care Load Volatility Index Over Time",
                labels={
                    "Date": "Month",
                    "Care_Load_Volatility_Index": "Volatility Index (%)"
                }
            )
            fig.update_traces(line_color=BLUE, marker_color=TERRACOTTA)
            st.plotly_chart(style_chart(fig), use_container_width=True)
        else:
            st.warning("The volatility KPI column was not found.")

    elif selected_chart == "Discharge Offset Ratio":

        if "Discharge_Offset_Ratio" in filtered_monthly.columns:
            fig = px.line(
                filtered_monthly,
                x="Date",
                y="Discharge_Offset_Ratio",
                markers=True,
                title="Discharge Offset Ratio Over Time",
                labels={
                    "Date": "Month",
                    "Discharge_Offset_Ratio": "Discharges as % of Transfers"
                }
            )
            fig.update_traces(line_color=TERRACOTTA, marker_color=BLUE)
            st.plotly_chart(style_chart(fig), use_container_width=True)
        else:
            st.warning("The discharge offset ratio column was not found.")

    elif selected_chart == "Rolling Average System Load":

        required = [
            "Total_System_Load",
            "Load_7Day_Rolling_Avg",
            "Load_14Day_Rolling_Avg"
        ]

        if all(col in chart_df.columns for col in required):
            fig = go.Figure()

            fig.add_trace(go.Scatter(
                x=chart_df["Date"],
                y=chart_df["Total_System_Load"],
                name="Recorded System Load",
                mode="lines",
                line=dict(color=GREY, width=1)
            ))

            fig.add_trace(go.Scatter(
                x=chart_df["Date"],
                y=chart_df["Load_7Day_Rolling_Avg"],
                name="7-Day Rolling Average",
                mode="lines",
                line=dict(color=BLUE, width=2)
            ))

            fig.add_trace(go.Scatter(
                x=chart_df["Date"],
                y=chart_df["Load_14Day_Rolling_Avg"],
                name="14-Day Rolling Average",
                mode="lines",
                line=dict(color=TERRACOTTA, width=2)
            ))

            fig.update_layout(
                title="System Load and Rolling Averages",
                xaxis_title="Reporting Date",
                yaxis_title="Number of Children"
            )
            st.plotly_chart(style_chart(fig), use_container_width=True)
        else:
            st.warning("The rolling average columns were not found.")

    elif selected_chart == "System Load Distribution by Agency":

        cbp_avg = chart_df["Children in CBP custody"].mean()
        hhs_avg = chart_df["Children in HHS Care"].mean()

        fig = go.Figure(data=[go.Pie(
            labels=["CBP Custody", "HHS Care"],
            values=[cbp_avg, hhs_avg],
            hole=0.55,
            marker=dict(colors=[TERRACOTTA, BLUE]),
            textinfo="label+percent"
        )])

        fig.update_layout(
            title="Average Recorded System Load Distribution by Agency"
        )
        st.plotly_chart(style_chart(fig), use_container_width=True)

    elif selected_chart == "Care Load Growth Rate":

        growth_df = chart_df.dropna(subset=["Care_Load_Growth_Rate"])

        if not growth_df.empty:
            fig = px.bar(
                growth_df,
                x="Date",
                y="Care_Load_Growth_Rate",
                title="Observation-to-Observation Care Load Growth",
                labels={
                    "Date": "Reporting Date",
                    "Care_Load_Growth_Rate": "Growth Rate (%)"
                }
            )
            fig.update_traces(marker_color=BLUE)
            st.plotly_chart(style_chart(fig), use_container_width=True)
        else:
            st.warning("No growth-rate observations are available.")

# Data Explorer section
with data_tab:
    st.subheader("Data Explorer")
    st.caption("Explore and download the underlying analytical datasets.")

    data_col1, data_col2 = st.columns(2)

    with data_col1:
        st.metric("Observation-Level Records", f"{len(filtered_df):,}")

    with data_col2:
        st.metric("Monthly Analytical Records", f"{len(filtered_monthly):,}")

    observation_tab, monthly_tab = st.tabs([
        "Observation-Level Data",
        "Monthly Summary"
    ])

    with observation_tab:
        st.markdown("#### Observation-Level Records")
        st.dataframe(filtered_df, use_container_width=True, height=400)

        st.download_button(
            "Download Observation-Level Data",
            data=filtered_df.to_csv(index=False).encode("utf-8"),
            file_name="observation_level_data.csv",
            mime="text/csv"
        )

    with monthly_tab:
        st.markdown("#### Monthly Analytical Summary")
        st.dataframe(filtered_monthly, use_container_width=True, height=400)

        st.download_button(
            "Download Monthly Summary",
            data=filtered_monthly.to_csv(index=False).encode("utf-8"),
            file_name="monthly_analytical_summary.csv",
            mime="text/csv"
        )

# Insights section
with insights_tab:

    st.subheader("Insights, Recommendations & Methodology")
    st.caption(
        "Analytical findings and operational recommendations "
        "based on the 2023–2025 reporting period."
    )

    findings_tab, recommendations_tab, limitations_tab, methodology_tab, kpi_tab = st.tabs([
        "Key Findings",
        "Recommendations",
        "Limitations",
        "Methodology",
        "KPI Definitions"
    ])

    with findings_tab:

        st.markdown("#### Executive Summary")

        st.write(
            "This project examines the reported care workload across CBP "
            "custody and HHS care from January 2023 to December 2025. "
            "It evaluates combined system load, agency-level workload, "
            "intake and discharge patterns, reporting consistency and "
            "indicators of sustained care-load pressure."
        )

        if not filtered_df.empty:

            analysis_data = filtered_df.sort_values("Date")

            highest_row = analysis_data.loc[
                analysis_data["Total_System_Load"].idxmax()
            ]

            lowest_row = analysis_data.loc[
                analysis_data["Total_System_Load"].idxmin()
            ]

            average_hhs_share = (
                analysis_data["Children in HHS Care"] /
                analysis_data["Total_System_Load"].replace(0, pd.NA)
            ).mean() * 100

            positive_months = (
                (filtered_monthly["Net_Intake_Pressure"] > 0).sum()
                if not filtered_monthly.empty else 0
            )

            st.markdown("#### Key Observations")

            st.markdown(
                f"- **Highest recorded system load:** "
                f"{highest_row['Total_System_Load']:,.0f} children "
                f"on {highest_row['Date'].strftime('%d %B %Y')}."
            )

            st.markdown(
                f"- **Lowest recorded system load:** "
                f"{lowest_row['Total_System_Load']:,.0f} children "
                f"on {lowest_row['Date'].strftime('%d %B %Y')}."
            )

            st.markdown(
                f"- **Average HHS share of system load:** "
                f"{average_hhs_share:.2f}% across recorded observations."
            )

            st.markdown(
                f"- **Months with positive net intake pressure:** "
                f"{positive_months} out of {len(filtered_monthly)} "
                f"available monthly records."
            )

            st.markdown(
                f"- **Average recorded system load:** "
                f"{analysis_data['Total_System_Load'].mean():,.2f} children."
            )

        st.markdown("#### Analytical Values")

        st.write(
            "The combined system-load measure represents the sum of "
            "children recorded in CBP custody and HHS care. Net intake "
            "pressure compares HHS transfers with HHS discharges. The "
            "three-month rolling measure is a pressure proxy, not a direct "
            "count of children in a backlog. The volatility index helps "
            "identify variation in recorded system load."
        )

        st.markdown("#### Strategic Implementation Implications")

        st.markdown(
            "- **HHS workload monitoring:** Give particular attention to "
            "HHS care levels because HHS accounts for the largest share "
            "of the combined recorded system load."
        )

        st.markdown(
            "- **Workforce and shelter planning:** Use sustained load "
            "patterns and rolling indicators to inform planning reviews. "
            "Actual staffing and bed-allocation decisions require facility "
            "and workforce data."
        )

        st.markdown(
            "- **Intake and discharge coordination:** Review transfers "
            "and discharges together to identify periods when HHS intake "
            "pressure remains positive."
        )

        st.markdown(
            "- **Early-warning monitoring:** Use rolling net intake "
            "pressure and care-load volatility as signals for further "
            "operational investigation, not as proof of overcrowding."
        )

        st.markdown(
            "- **Reporting improvements:** Investigate missing reporting "
            "dates and unusual transfer-to-custody relationships to improve "
            "the reliability of future analysis."
        )

        st.markdown(
            "- **Capacity assessment:** Integrate facility capacity, "
            "available beds, staffing and resource data before calculating "
            "actual capacity utilization or making capacity-stress claims."
        )

        st.markdown("#### Key Analytical Findings")

        findings = pd.DataFrame([
            {
                "Finding": "System Load",
                "Observation": "Highest monthly average system load was approximately 11,255 in December 2023."
            },
            {
                "Finding": "Long-Term Trend",
                "Observation": "Monthly average system load reached approximately 2,027 in August 2025."
            },
            {
                "Finding": "HHS Share",
                "Observation": "HHS represented more than 96% of average combined recorded system load in each year."
            },
            {
                "Finding": "Net Intake",
                "Observation": "Monthly net intake pressure varied across the reporting period, with positive and negative periods."
            },
            {
                "Finding": "Reporting Quality",
                "Observation": "The dataset contains 720 observations across a calendar span with 355 dates without records."
            },
            {
                "Finding": "Validation",
                "Observation": "86 records show transfers exceeding the recorded CBP custody count and require investigation."
            }
        ])

        st.dataframe(findings, use_container_width=True, hide_index=True)

        st.markdown("#### Key Analytical Insights")

        if not filtered_df.empty:

            insight_data = filtered_df.sort_values("Date")

            high = insight_data.loc[
                insight_data["Total_System_Load"].idxmax()
            ]

            low = insight_data.loc[
                insight_data["Total_System_Load"].idxmin()
            ]

            hhs_share = (
                insight_data["Children in HHS Care"] /
                insight_data["Total_System_Load"].replace(0, pd.NA)
            ).mean() * 100

            positive_count = (
                (filtered_monthly["Net_Intake_Pressure"] > 0).sum()
                if not filtered_monthly.empty else 0
            )

            insight1, insight2 = st.columns(2)

            with insight1:
                st.metric(
                    "Highest Recorded System Load",
                    f"{high['Total_System_Load']:,.0f}"
                )
                st.caption(
                    high["Date"].strftime("Recorded on %d %B %Y")
                )

            with insight2:
                st.metric(
                    "Lowest Recorded System Load",
                    f"{low['Total_System_Load']:,.0f}"
                )
                st.caption(
                    low["Date"].strftime("Recorded on %d %B %Y")
                )

            insight3, insight4 = st.columns(2)

            with insight3:
                st.metric(
                    "Average HHS Share of System Load",
                    f"{hhs_share:.2f}%"
                )

            with insight4:
                st.metric(
                    "Months with Positive Net Intake Pressure",
                    f"{positive_count}"
                )

            st.caption(
                "These insights are calculated from the selected date range. "
                "System-load highs and lows refer to recorded observations, "
                "not monthly averages."
            )

        st.markdown("#### Data Quality Snapshot")

        q1, q2, q3 = st.columns(3)

        q1.metric("Available Observations", f"{len(dashboard_df):,}")
        q2.metric(
            "Dates Without Records",
            f"{(dashboard_df['Date'].max() - dashboard_df['Date'].min()).days + 1 - len(dashboard_df):,}"
        )
        q3.metric(
            "Transfer Validation Flags",
            f"{(dashboard_df['Children transferred out of CBP custody'] > dashboard_df['Children in CBP custody']).sum():,}"
        )

        st.info(
            "Missing reporting dates are not treated as zero activity. "
            "Transfer validation flags are retained for investigation "
            "rather than automatically corrected."
        )

    with recommendations_tab:

        st.markdown("#### Project Recommendations")

        recommendations = pd.DataFrame([
            {
                "Area": "HHS Resource Planning",
                "Recommendation": "Prioritize monitoring HHS care workload because it represents the largest share of recorded system load."
            },
            {
                "Area": "System Load Monitoring",
                "Recommendation": "Use rolling averages to monitor sustained changes in reported care load."
            },
            {
                "Area": "Intake and Discharge",
                "Recommendation": "Monitor transfers and discharges together to understand changes in HHS intake pressure."
            },
            {
                "Area": "Backlog Monitoring",
                "Recommendation": "Use the three-month rolling net intake proxy to identify sustained positive intake pressure."
            },
            {
                "Area": "Operational Stability",
                "Recommendation": "Investigate periods of elevated care-load volatility and changes in reporting patterns."
            },
            {
                "Area": "Data Quality",
                "Recommendation": "Improve reporting consistency and investigate missing dates and stock-flow validation flags."
            },
            {
                "Area": "Capacity Planning",
                "Recommendation": "Integrate facility capacity, bed availability and staffing data for actual capacity assessment."
            }
        ])

        st.dataframe(recommendations, use_container_width=True, hide_index=True)

    with limitations_tab:

        st.markdown("#### Project Limitations")

        limitations = pd.DataFrame([
            {
                "Limitation": "Missing Calendar Dates",
                "Explanation": "The dataset has 355 calendar dates without records. Missing dates cannot be assumed to represent zero activity."
            },
            {
                "Limitation": "No Facility Capacity Data",
                "Explanation": "Bed counts and facility capacity are unavailable, so actual occupancy and capacity utilization cannot be calculated."
            },
            {
                "Limitation": "No Staffing Information",
                "Explanation": "Staffing levels and resource availability are not provided."
            },
            {
                "Limitation": "Stock and Flow Differences",
                "Explanation": "Custody and care figures are stocks, while apprehensions, transfers and discharges are flows."
            },
            {
                "Limitation": "Irregular Reporting Intervals",
                "Explanation": "Observations are not consistently daily, so consecutive-record changes may cover different time intervals."
            },
            {
                "Limitation": "Backlog Is a Proxy",
                "Explanation": "The three-month rolling net intake measure indicates sustained pressure, not a directly measured backlog of children."
            },
            {
                "Limitation": "Limited Operational Context",
                "Explanation": "The dataset does not provide enough information to determine causes of workload changes or service outcomes."
            }
        ])

        st.dataframe(limitations, use_container_width=True, hide_index=True)

        st.warning(
            "This project identifies care-load patterns and pressure indicators. "
            "It does not establish actual overcrowding, capacity utilization "
            "or staffing shortages."
        )

    with methodology_tab:

        st.markdown("#### Project Methodology")

        methodology = pd.DataFrame([
            {
                "Stage": "1. Data Ingestion",
                "Work Performed": "Loaded the source Excel dataset and inspected its structure and reporting period."
            },
            {
                "Stage": "2. Data Cleaning & Validation",
                "Work Performed": "Checked missing values, duplicate dates, chronological order, negative values and logical constraints."
            },
            {
                "Stage": "3. Feature Engineering",
                "Work Performed": "Created total system load, net intake, growth rate, rolling averages and volatility indicators."
            },
            {
                "Stage": "4. Trend & Temporal Analysis",
                "Work Performed": "Examined observation-level and monthly patterns and compared reporting periods."
            },
            {
                "Stage": "5. KPI Development",
                "Work Performed": "Developed five indicators to assess care load, intake pressure, volatility, backlog pressure and discharge offset."
            },
            {
                "Stage": "6. Comparative Analysis",
                "Work Performed": "Compared CBP and HHS workloads, intake and discharge patterns, and yearly trends."
            },
            {
                "Stage": "7. Findings & Recommendations",
                "Work Performed": "Summarized findings, operational recommendations and analytical limitations."
            }
        ])

        st.dataframe(methodology, use_container_width=True, hide_index=True)

    with kpi_tab:

        st.markdown("#### KPI Definitions")

        kpi_definitions = pd.DataFrame([
            {
                "KPI": "Total Children Under Care",
                "Meaning": "Combined recorded CBP custody and HHS care stock."
            },
            {
                "KPI": "Net Intake Pressure",
                "Meaning": "HHS transfers minus HHS discharges; a positive value indicates higher transfers than discharges."
            },
            {
                "KPI": "Care Load Volatility Index",
                "Meaning": "Percentage-based coefficient of variation of system load over a 14-day rolling window."
            },
            {
                "KPI": "Backlog Accumulation Rate",
                "Meaning": "Three-month rolling average of monthly net intake pressure, used as a backlog pressure proxy."
            },
            {
                "KPI": "Discharge Offset Ratio",
                "Meaning": "Average monthly discharges divided by average monthly transfers, multiplied by 100."
            }
        ])

        st.dataframe(kpi_definitions, use_container_width=True, hide_index=True)

        st.caption(
            "These indicators are analytical measures, not direct measures "
            "of facility capacity, service efficiency or the number of children awaiting placement."
        )


# FINAL PROJECT FOOTER

st.divider()

st.markdown(
    "<div style='text-align:center;'>"
    "<h3 style='color:#536B7C;'>"
    "System Capacity & Care Load Analytics"
    "</h3>"
    "<p>Data Analytics Internship Project | Unified Mentor</p>"
    "<p>Data Source: HHS_Unaccompanied_Alien_Children_Program.xlsx</p>"
    "<p>Analysis Period: January 2023 – December 2025</p>"
    "</div>",
    unsafe_allow_html=True
)

st.caption(
    "Analytical Note: This dashboard evaluates reported care-load "
    "patterns and pressure indicators. Facility capacity, bed availability "
    "and staffing data were not provided; therefore, actual capacity "
    "utilization and overcrowding cannot be determined."
)
