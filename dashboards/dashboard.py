
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ==========================================
# PROJECT CONFIGURATION
# ==========================================

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR / "src"))

from database import get_connection

st.set_page_config(
    page_title="AI Cloud Monitoring",
    page_icon="☁️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==========================================
# SIDEBAR
# ==========================================

st.sidebar.title("☁️ Cloud Monitoring")
st.sidebar.caption("AI Infrastructure Observability")

hours = st.sidebar.selectbox(
    "Time range",
    options=[1, 6, 24, 72],
    index=2,
    format_func=lambda h: f"Last {h} hours",
)

refresh_seconds = st.sidebar.selectbox(
    "Refresh interval",
    options=[5, 10, 30, 60],
    index=1,
    format_func=lambda s: f"{s} seconds",
)

auto_refresh = st.sidebar.toggle(
    "Auto Refresh",
    value=True,
)

st.sidebar.divider()
st.sidebar.write("Data Source: PostgreSQL")
st.sidebar.write("AI Model: Isolation Forest")

# ==========================================
# DATABASE
# ==========================================

def load_data(selected_hours):
    query = """
        SELECT
            m.id,
            m.timestamp,
            m.cpu_percent,
            m.memory_percent,
            m.disk_percent,
            a.prediction,
            a.anomaly_score
        FROM system_metrics m
        LEFT JOIN anomaly_predictions a
            ON a.metric_id = m.id
        WHERE m.timestamp >=
            CURRENT_TIMESTAMP - (%s * INTERVAL '1 hour')
        ORDER BY m.timestamp DESC, m.id DESC
        LIMIT 5000
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (selected_hours,))
            rows = cur.fetchall()
            columns = [
                desc.name for desc in cur.description
            ]

    df = pd.DataFrame(rows, columns=columns)

    if not df.empty:
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values(
            ["timestamp", "id"]
        ).reset_index(drop=True)

        df["status"] = df["prediction"].map({
            1: "NORMAL",
            -1: "ANOMALY",
        }).fillna("WAITING")

    return df


# ==========================================
# AUTO REFRESH FRAGMENT
# ==========================================

interval = f"{refresh_seconds}s" if auto_refresh else None


@st.fragment(run_every=interval)
def dashboard():
    st.title("☁️ AI Cloud Infrastructure Monitoring")
    st.caption(
        "Real-time resource metrics and "
        "machine learning anomaly detection"
    )

    try:
        df = load_data(hours)

    except Exception as error:
        st.error(f"Database error: {error}")
        return

    if df.empty:
        st.warning(
            "Tidak ada data pada rentang waktu ini. "
            "Jalankan monitor.py atau ubah time range."
        )
        return

    latest = df.iloc[-1]

    # ======================================
    # KPI CARDS
    # ======================================

    predicted = df[df["prediction"].notna()]
    anomalies = df[df["prediction"] == -1]

    # Ambil prediksi paling baru yang tersedia
    latest_predicted = (
        predicted.iloc[-1]
        if not predicted.empty
        else None
    )

    current_status = (
        latest_predicted["status"]
        if latest_predicted is not None
        else "WAITING"
    )

    # Hindari menampilkan status lama sebagai status terbaru
    if (
        latest_predicted is None
        or latest_predicted["id"] != latest["id"]
    ):
        current_status = "WAITING"

    k1, k2, k3, k4 = st.columns(4)

    k1.metric(
        "CPU Usage",
        f"{latest['cpu_percent']:.1f}%"
    )
    k2.metric(
        "RAM Usage",
        f"{latest['memory_percent']:.1f}%"
    )
    k3.metric(
        "Disk Usage",
        f"{latest['disk_percent']:.1f}%"
    )
    k4.metric(
        "Latest AI Status",
        current_status
    )

    st.caption(
        f"Latest sample: {latest['timestamp']} | "
        f"AI predictions available: {len(predicted)}/{len(df)}"
    )

    st.divider()

    # ======================================
    # RESOURCE USAGE CHART
    # ======================================

    st.subheader("📈 Resource Utilization")

    chart_df = df.melt(
        id_vars=["timestamp"],
        value_vars=[
            "cpu_percent",
            "memory_percent",
            "disk_percent",
        ],
        var_name="Resource",
        value_name="Usage (%)",
    )

    fig = px.line(
        chart_df,
        x="timestamp",
        y="Usage (%)",
        color="Resource",
        title="CPU, Memory & Disk Usage",
    )

    fig.update_layout(
        template="plotly_dark",
        hovermode="x unified",
        height=390,
        legend_title_text="",
    )
    fig.update_yaxes(range=[0, 100])

    st.plotly_chart(fig, width="stretch")

    # ======================================
    # ANOMALY CHART
    # ======================================

    left, right = st.columns([3, 1])

    with left:
        st.subheader("🧠 AI Anomaly Detection")

        fig_ai = go.Figure()

        fig_ai.add_trace(go.Scatter(
            x=df["timestamp"],
            y=df["cpu_percent"],
            mode="lines",
            name="CPU Usage",
            line=dict(color="#4da3ff"),
        ))

        if not anomalies.empty:
            fig_ai.add_trace(go.Scatter(
                x=anomalies["timestamp"],
                y=anomalies["cpu_percent"],
                mode="markers",
                name="AI Anomaly",
                marker=dict(
                    color="#ff4b4b",
                    size=11,
                    symbol="x",
                ),
                customdata=anomalies[
                    ["anomaly_score"]
                ].to_numpy(),
                hovertemplate=(
                    "Time: %{x}<br>"
                    "CPU: %{y:.1f}%<br>"
                    "AI Score: %{customdata[0]:.4f}"
                    "<extra></extra>"
                ),
            ))

        fig_ai.update_layout(
            template="plotly_dark",
            height=370,
            yaxis_title="CPU Usage (%)",
            xaxis_title="Time",
            hovermode="closest",
            yaxis=dict(range=[0, 100]),
        )

        st.plotly_chart(fig_ai, width="stretch")

    with right:
        st.subheader("AI Summary")

        st.metric("Total Records", len(df))
        st.metric("Predicted", len(predicted))
        st.metric("Anomalies", len(anomalies))

        anomaly_rate = (
            len(anomalies) / len(predicted) * 100
            if len(predicted) > 0
            else 0
        )

        st.metric(
            "Anomaly Rate",
            f"{anomaly_rate:.2f}%"
        )

        st.caption(
            "Anomaly rate = share of predicted "
            "records labeled anomalous."
        )

    # ======================================
    # ANOMALY SCORE CHART
    # ======================================

    st.subheader("📉 Anomaly Score History")

    if not predicted.empty:
        fig_score = px.line(
            predicted,
            x="timestamp",
            y="anomaly_score",
            title="Isolation Forest Decision Score",
        )

        fig_score.add_hline(
            y=0,
            line_dash="dash",
            line_color="red",
        )

        fig_score.update_layout(
            template="plotly_dark",
            height=310,
        )

        st.plotly_chart(fig_score, width="stretch")
        st.caption(
            "Skor negatif menunjukkan anomali "
            "menurut ambang keputusan model."
        )
    else:
        st.info("Belum tersedia prediksi AI.")

    # ======================================
    # ANOMALY EVENTS TABLE
    # ======================================

    st.subheader("🚨 Anomaly Event History")

    if anomalies.empty:
        st.info(
            "Belum ada anomali terdeteksi "
            "pada rentang waktu ini."
        )
    else:
        columns = [
            "timestamp",
            "cpu_percent",
            "memory_percent",
            "disk_percent",
            "anomaly_score",
            "status",
        ]

        st.dataframe(
            anomalies[columns].sort_values(
                "timestamp", ascending=False
            ),
            width="stretch",
            hide_index=True,
        )

    # ======================================
    # CRITICAL ALERT HISTORY
    # ======================================

    st.subheader("🚨 Critical Alert History")

    alert_query = """
        SELECT
            created_at,
            severity,
            message
        FROM system_alerts
        ORDER BY created_at DESC
        LIMIT 50
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(alert_query)
            alert_rows = cur.fetchall()

    alert_df = pd.DataFrame(
        alert_rows,
        columns=["created_at", "severity", "message"]
    )

    if alert_df.empty:
        st.success("No critical alerts recorded.")
    else:
        st.error(
            f"{len(alert_df)} recent critical alert records."
        )

        st.dataframe(
            alert_df,
            width="stretch",
            hide_index=True,
        )

    # ======================================
    # RAW DATA AND EXPORT
    # ======================================

    with st.expander("📋 View Raw Monitoring Data"):
        st.dataframe(
            df.sort_values(
                "timestamp", ascending=False
            ),
            width="stretch",
            hide_index=True,
        )

    csv_data = df.to_csv(index=False).encode("utf-8")

    st.download_button(
        "📥 Export Monitoring CSV",
        data=csv_data,
        file_name="monitoring_report.csv",
        mime="text/csv",
    )


dashboard()
