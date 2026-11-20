
import sys
import time
from pathlib import Path

import streamlit as st
import pandas as pd
import plotly.express as px
import mysql.connector

# ==========================================================
# 1. PROJECT SETUP
# ==========================================================

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from shopflow.config import DB_CONFIG
from shopflow.pipeline import run_pipeline

st.set_page_config(
    page_title="ShopFlow | Data Operations",
    page_icon="S",
    layout="wide",
    initial_sidebar_state="collapsed"
)

TABLES = [
    "customers", "products", "orders",
    "order_items", "payments",
    "pipeline_runs", "pipeline_stage_runs"
]

BUSINESS_TABLES = TABLES[:5]

# ==========================================================
# 2. VISUAL DESIGN SYSTEM
# ==========================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Inter:wght@400;500;600;700;800&display=swap');

:root {
    --bg: #101820;
    --rail: #131E28;
    --surface: #192630;
    --surface2: #202F3A;
    --border: #344653;
    --text: #E0E8EC;
    --muted: #91A2AC;
    --teal: #36B6A5;
    --blue: #7196D5;
    --green: #69B987;
    --amber: #D5A64A;
    --red: #D47777;
}

html, body, [class*="css"] {
    font-family: Inter, sans-serif;
}

.stApp {
    background: var(--bg);
    color: var(--text);
}

[data-testid="stHeader"] {
    background: var(--bg);
}

[data-testid="stSidebar"] {
    display: none;
}

.block-container {
    max-width: 1800px;
    padding: 1.1rem 1.7rem 2rem 1.2rem;
}

h1, h2, h3, h4 {
    color: var(--text) !important;
    letter-spacing: -0.5px;
}

p, label {
    color: var(--muted);
}

[data-testid="stMetric"] {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 9px;
    padding: 14px 16px;
}

[data-testid="stMetricLabel"] {
    color: var(--muted) !important;
    font-size: 11px !important;
}

[data-testid="stMetricValue"] {
    color: var(--text) !important;
    font-weight: 700 !important;
}

[data-testid="stDataFrame"] {
    border: 1px solid var(--border);
    border-radius: 8px;
}

.stButton button {
    border-radius: 7px;
    min-height: 39px;
    font-weight: 600;
    border: 1px solid var(--border);
    background: var(--surface);
    color: var(--text);
}

.stButton button:hover {
    border-color: var(--teal);
    color: var(--teal);
}

.stButton button[kind="primary"] {
    background: var(--teal);
    color: #0C1919;
    border-color: var(--teal);
}

.stButton button[kind="primary"]:hover {
    background: #55C8B8;
    color: #0C1919;
}

[data-baseweb="select"] > div,
[data-baseweb="input"] > div,
[data-baseweb="textarea"] > div {
    background: var(--surface);
    border-color: var(--border);
}

hr {
    border-color: var(--border);
}

code, pre, .mono {
    font-family: "DM Mono", monospace !important;
}

.sf-brand {
    font-size: 23px;
    font-weight: 800;
    letter-spacing: 2px;
    color: #E7EFF1;
}

.sf-kicker {
    color: var(--teal);
    font-family: "DM Mono", monospace;
    font-size: 10px;
    letter-spacing: 1.5px;
}

.sf-muted {
    color: var(--muted);
    font-size: 12px;
}

.sf-panel {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 16px;
    margin-bottom: 10px;
}

.sf-panel-title {
    color: var(--text);
    font-weight: 700;
    font-size: 13px;
}

.sf-node {
    background: linear-gradient(145deg, #202F3A, #192630);
    border: 1px solid #405462;
    border-radius: 10px;
    min-height: 135px;
    padding: 15px 11px;
    box-shadow: 0 5px 18px rgba(0,0,0,.14);
}

.sf-node-label {
    font-size: 12px;
    font-weight: 800;
    letter-spacing: 1px;
    color: #E5EDF0;
}

.sf-node-meta {
    font-family: "DM Mono", monospace;
    font-size: 10px;
    color: var(--muted);
    margin-top: 8px;
}

.sf-node-status {
    font-family: "DM Mono", monospace;
    font-size: 10px;
    font-weight: 600;
    margin-top: 12px;
}

.sf-section {
    font-size: 11px;
    font-weight: 700;
    color: var(--muted);
    letter-spacing: 1.2px;
    margin: 12px 0 7px 0;
}

.sf-divider {
    height: 1px;
    background: var(--border);
    margin: 15px 0;
}

.sf-topbar {
    background: #131E28;
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 12px 15px;
    margin-bottom: 17px;
}

.sf-console {
    background: #0C131A;
    border: 1px solid #2D414D;
    border-radius: 9px;
    padding: 13px;
}

.sf-console-line {
    font-family: "DM Mono", monospace;
    font-size: 11px;
    color: #A9BBC3;
    padding: 4px 0;
}

.sf-green { color: var(--green); }
.sf-teal { color: var(--teal); }
.sf-amber { color: var(--amber); }
.sf-red { color: var(--red); }

[data-testid="stVerticalBlock"] {
    gap: 0.65rem;
}

</style>
""", unsafe_allow_html=True)


# ==========================================================
# 3. DATABASE ACCESS
# ==========================================================

def get_connection():
    return mysql.connector.connect(**DB_CONFIG)


def read_sql(query, params=None):
    connection = get_connection()
    try:
        return pd.read_sql(query, connection, params=params)
    finally:
        connection.close()


def table_exists(table):
    result = read_sql(
        """
        SELECT COUNT(*) AS total
        FROM information_schema.tables
        WHERE table_schema = %s AND table_name = %s
        """,
        (DB_CONFIG["database"], table)
    )
    return int(result.iloc[0]["total"]) > 0


def load_table(table):
    if not table_exists(table):
        return pd.DataFrame()
    return read_sql(f"SELECT * FROM `{table}`")


@st.cache_data(ttl=15)
def load_all_data():
    result = {}
    for table in TABLES:
        try:
            result[table] = load_table(table)
        except Exception:
            result[table] = pd.DataFrame()
    return result


def refresh_data():
    load_all_data.clear()
    st.rerun()


try:
    data = load_all_data()
    database_online = True
except Exception as exc:
    data = {}
    database_online = False
    database_error = str(exc)

customers = data.get("customers", pd.DataFrame())
products = data.get("products", pd.DataFrame())
orders = data.get("orders", pd.DataFrame())
order_items = data.get("order_items", pd.DataFrame())
payments = data.get("payments", pd.DataFrame())
runs = data.get("pipeline_runs", pd.DataFrame())
stage_runs = data.get("pipeline_stage_runs", pd.DataFrame())


# ==========================================================
# 4. NAVIGATION MODEL
# ==========================================================

NAVIGATION = [
    ("OPERATIONS", [
        ("⌂", "Command Center"),
        ("◈", "Pipeline Studio"),
        ("◷", "Run History"),
    ]),
    ("DATA MANAGEMENT", [
        ("⌘", "Data Lineage"),
        ("▦", "Data Catalog"),
        ("✓", "Data Quality"),
    ]),
    ("DEVELOPMENT", [
        ("</>", "SQL Lab"),
        ("⬡", "Infrastructure"),
        ("▤", "Business Insights"),
    ]),
]

if "workspace" not in st.session_state:
    st.session_state.workspace = "Pipeline Studio"


def navigate_to(name):
    st.session_state.workspace = name


def page_header(group, title, description):
    st.markdown(f'<div class="sf-kicker">{group}</div>', unsafe_allow_html=True)
    st.markdown(f"<h1 style='font-size:29px;margin:3px 0 2px 0'>{title}</h1>",
                unsafe_allow_html=True)
    st.markdown(f'<div class="sf-muted">{description}</div>',
                unsafe_allow_html=True)
    st.markdown('<div class="sf-divider"></div>', unsafe_allow_html=True)


def status_colour(status):
    status = str(status).upper()
    if status == "SUCCESS":
        return "#69B987"
    if status == "FAILED":
        return "#D47777"
    if status in ("RUNNING", "IN PROGRESS"):
        return "#36B6A5"
    return "#91A2AC"


def latest_run():
    if runs.empty:
        return None
    frame = runs.copy()
    if "started_at" in frame.columns:
        frame["started_at"] = pd.to_datetime(
            frame["started_at"], errors="coerce"
        )
        frame = frame.sort_values("started_at", ascending=False)
    return frame.iloc[0]


def stages_for(run_id):
    if stage_runs.empty or "run_id" not in stage_runs.columns:
        return pd.DataFrame()
    return stage_runs[
        stage_runs["run_id"].astype(str) == str(run_id)
    ].copy()


def seconds(value):
    try:
        return f"{float(value):.3f}s"
    except (ValueError, TypeError):
        return "—"


def panel(title, subtitle=None):
    st.markdown(
        f"""
        <div class="sf-panel">
            <div class="sf-panel-title">{title}</div>
            {f'<div class="sf-muted">{subtitle}</div>' if subtitle else ''}
        </div>
        """,
        unsafe_allow_html=True
    )


# ==========================================================
# 5. APPLICATION FRAME + CUSTOM NAVIGATION RAIL
# ==========================================================

rail, workspace_area = st.columns([0.72, 8.8], gap="medium")

with rail:
    st.markdown(
        """
        <div style="text-align:center;padding:10px 0 15px 0">
            <div style="font-size:25px;font-weight:900;color:#36B6A5">S</div>
            <div style="font-size:8px;letter-spacing:1px;color:#91A2AC">FLOW</div>
        </div>
        <div class="sf-divider"></div>
        """,
        unsafe_allow_html=True
    )

    for group, items in NAVIGATION:
        st.markdown(
            f'<div style="font-size:8px;letter-spacing:1px;'
            f'color:#718591;text-align:center;margin:13px 0 6px 0">'
            f'{group.split()[0]}</div>',
            unsafe_allow_html=True
        )

        for icon, name in items:
            active = st.session_state.workspace == name
            if st.button(
                icon,
                key=f"nav_{name}",
                type="primary" if active else "secondary",
                help=name,
                use_container_width=True
            ):
                navigate_to(name)
                st.rerun()

    st.markdown('<div class="sf-divider"></div>', unsafe_allow_html=True)

    if st.button("↻", key="nav_refresh", help="Refresh data",
                 use_container_width=True):
        refresh_data()

    st.markdown(
        f"""
        <div style="text-align:center;margin-top:12px;font-size:9px;
        color:{'#69B987' if database_online else '#D47777'}">
        ●
        </div>
        """,
        unsafe_allow_html=True
    )


# ==========================================================
# 6. MAIN APPLICATION HEADER
# ==========================================================

with workspace_area:

    top_left, top_right = st.columns([4, 2])

    with top_left:
        st.markdown(
            """
            <div class="sf-brand">SHOPFLOW</div>
            <div class="sf-kicker">DATA OPERATIONS PLATFORM</div>
            """,
            unsafe_allow_html=True
        )

    with top_right:
        status_label = "MYSQL CONNECTED" if database_online else "MYSQL OFFLINE"
        status_color = "#69B987" if database_online else "#D47777"
        st.markdown(
            f"""
            <div style="text-align:right;padding-top:7px">
                <span style="font-size:10px;color:{status_color};
                font-family:'DM Mono',monospace">● {status_label}</span>
                <div class="sf-muted" style="margin-top:5px">
                    LOCAL DEVELOPMENT · SHOPFLOW
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown('<div class="sf-divider"></div>', unsafe_allow_html=True)

    current_workspace = st.session_state.workspace


# ==========================================================
# 7. PIPELINE STUDIO
# ==========================================================

if current_workspace == "Pipeline Studio":

    with workspace_area:

        page_header(
            "ORCHESTRATION / WORKFLOW",
            "Pipeline Studio",
            "Monitor and execute the ShopFlow end-to-end data pipeline."
        )

        latest = latest_run()
        latest_stages = (
            stages_for(latest["run_id"])
            if latest is not None else pd.DataFrame()
        )

        # Top operational metrics
        m1, m2, m3, m4 = st.columns(4)

        m1.metric(
            "LAST EXECUTION",
            str(latest.get("status", "NOT RUN")) if latest is not None else "NOT RUN"
        )
        m2.metric(
            "EXECUTION TIME",
            seconds(latest.get("duration_seconds")) if latest is not None else "—"
        )
        m3.metric("SOURCE DATASETS", "05")
        m4.metric("WORKFLOW TASKS", "04")

        st.markdown('<div class="sf-divider"></div>', unsafe_allow_html=True)

        # Main workflow and inspector
        workflow_col, inspector_col = st.columns([3.3, 1.15], gap="large")

        stage_definitions = [
            ("EXTRACT", "01", "CSV INGESTION", "PANDAS"),
            ("TRANSFORM", "02", "DATA PROCESSING", "PANDAS"),
            ("VALIDATE", "03", "QUALITY ENGINE", "RULES"),
            ("LOAD", "04", "DATABASE WRITE", "MYSQL"),
        ]

        stage_statuses = {}

        for name, _, _, _ in stage_definitions:
            matching = pd.DataFrame()
            if not latest_stages.empty and "stage_name" in latest_stages.columns:
                matching = latest_stages[
                    latest_stages["stage_name"].astype(str).str.upper() == name
                ]
            stage_statuses[name] = (
                str(matching.iloc[-1].get("status", "UNKNOWN")).upper()
                if not matching.empty else "NOT RUN"
            )

        with workflow_col:

            st.markdown("### Workflow Canvas")
            st.markdown(
                '<div class="sf-muted">SHOPFLOW_ETL_MAIN '
                ' / SEQUENTIAL EXECUTION GRAPH</div>',
                unsafe_allow_html=True
            )

            node_cols = st.columns([1, 0.25, 1, 0.25, 1, 0.25, 1])

            for i, (name, number, description, engine) in enumerate(stage_definitions):

                status = stage_statuses[name]
                colour = status_colour(status)

                with node_cols[i * 2]:
                    st.markdown(
                        f"""
                        <div class="sf-node"
                        style="border-top:3px solid {colour}">
                            <div class="sf-kicker">TASK {number}</div>
                            <div class="sf-node-label">{name}</div>
                            <div class="sf-node-meta">{description}</div>
                            <div class="sf-node-status" style="color:{colour}">
                                ● {status}
                            </div>
                            <div class="sf-node-meta">{engine}</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                if i < 3:
                    with node_cols[i * 2 + 1]:
                        st.markdown(
                            """
                            <div style="text-align:center;padding-top:48px;
                            color:#36B6A5;font-size:20px">→</div>
                            """,
                            unsafe_allow_html=True
                        )

            st.markdown('<div class="sf-divider"></div>', unsafe_allow_html=True)

            st.markdown("### Execution Control")

            run_button = st.button(
                "▶  EXECUTE PIPELINE",
                type="primary",
                use_container_width=True
            )

            if run_button:
                load_all_data.clear()
                with st.spinner("Executing ETL workflow..."):
                    try:
                        result = run_pipeline()
                        st.success("Pipeline execution completed.")
                        if isinstance(result, dict):
                            st.json(result)
                        else:
                            st.write(result)
                        load_all_data.clear()
                        time.sleep(0.7)
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Pipeline execution failed: {exc}")

        with inspector_col:

            st.markdown("### Task Inspector")

            task_names = [item[0] for item in stage_definitions]

            selected_task = st.selectbox(
                "Select workflow task",
                task_names,
                label_visibility="collapsed"
            )

            task_info = next(
                item for item in stage_definitions
                if item[0] == selected_task
            )

            matching = pd.DataFrame()

            if not latest_stages.empty and "stage_name" in latest_stages.columns:
                matching = latest_stages[
                    latest_stages["stage_name"].astype(str).str.upper()
                    == selected_task
                ]

            task_status = stage_statuses[selected_task]
            task_duration = (
                matching.iloc[-1].get("duration_seconds")
                if not matching.empty else None
            )

            st.markdown(
                f"""
                <div class="sf-panel">
                    <div class="sf-kicker">SELECTED TASK</div>
                    <h3 style="margin:8px 0">{selected_task}</h3>
                    <div class="sf-divider"></div>
                    <div class="sf-muted">EXECUTION STATUS</div>
                    <div style="font-size:14px;font-weight:700;
                    color:{status_colour(task_status)};margin:6px 0">
                    ● {task_status}</div>
                    <div class="sf-divider"></div>
                    <div class="sf-muted">TASK DURATION</div>
                    <div style="font-size:22px;font-weight:700;margin-top:5px">
                    {seconds(task_duration)}</div>
                    <div class="sf-divider"></div>
                    <div class="sf-muted">EXECUTION ENGINE</div>
                    <div class="sf-node-meta">{task_info[3]}</div>
                    <div class="sf-divider"></div>
                    <div class="sf-muted">TASK DESCRIPTION</div>
                    <div style="font-size:12px;margin-top:5px">
                    {task_info[2]}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        # Execution console
        st.markdown('<div class="sf-divider"></div>', unsafe_allow_html=True)

        console_left, console_right = st.columns([3, 1])

        with console_left:
            st.markdown("### Execution Console")
            st.markdown(
                '<div class="sf-muted">LATEST PERSISTED TASK EVENTS</div>',
                unsafe_allow_html=True
            )

            if latest_stages.empty:
                st.markdown(
                    """
                    <div class="sf-console">
                        <div class="sf-console-line">
                        Waiting for pipeline execution...
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                console_lines = []

                for _, row in latest_stages.iterrows():
                    name = row.get("stage_name", "TASK")
                    status = str(row.get("status", "UNKNOWN")).upper()
                    duration = seconds(row.get("duration_seconds"))
                    colour = status_colour(status)

                    console_lines.append(
                        f'<div class="sf-console-line">'
                        f'<span style="color:#718591">[SHOPFLOW]</span> '
                        f'{name} &nbsp; '
                        f'<span style="color:{colour}">{status}</span> '
                        f'&nbsp; {duration}</div>'
                    )

                st.markdown(
                    '<div class="sf-console">' +
                    "".join(console_lines) +
                    '</div>',
                    unsafe_allow_html=True
                )

        with console_right:
            st.markdown("### Latest Run")
            if latest is not None:
                st.markdown(
                    f"""
                    <div class="sf-panel">
                        <div class="sf-muted">RUN IDENTIFIER</div>
                        <div class="sf-node-meta" style="word-break:break-all">
                        {latest.get('run_id', 'N/A')}</div>
                        <div class="sf-divider"></div>
                        <div class="sf-muted">STARTED AT</div>
                        <div class="sf-node-meta">
                        {latest.get('started_at', 'N/A')}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                st.caption("No recorded run yet.")


# ==========================================================
# 8. COMMAND CENTER
# ==========================================================

elif current_workspace == "Command Center":

    with workspace_area:

        page_header(
            "OPERATIONS",
            "Command Center",
            "Platform-wide operational status and data infrastructure overview."
        )

        total_records = sum(
            len(data.get(table, pd.DataFrame()))
            for table in BUSINESS_TABLES
        )

        successful = 0
        failed = 0

        if not runs.empty and "status" in runs.columns:
            statuses = runs["status"].astype(str).str.upper()
            successful = int((statuses == "SUCCESS").sum())
            failed = int((statuses == "FAILED").sum())

        a, b, c, d = st.columns(4)
        a.metric("BUSINESS RECORDS", f"{total_records:,}")
        b.metric("PIPELINE RUNS", len(runs))
        c.metric("SUCCESSFUL RUNS", successful)
        d.metric("FAILED RUNS", failed)

        st.markdown("### Data Infrastructure")

        cols = st.columns(5)
        for col, table in zip(cols, BUSINESS_TABLES):
            with col:
                st.metric(table.upper(), len(data.get(table, [])))

        st.markdown("### Recent Pipeline Runs")
        if runs.empty:
            st.info("No pipeline executions recorded.")
        else:
            st.dataframe(runs.head(12), use_container_width=True, hide_index=True)


# ==========================================================
# 9. RUN HISTORY
# ==========================================================

elif current_workspace == "Run History":

    with workspace_area:

        page_header(
            "OPERATIONS / OBSERVABILITY",
            "Run History",
            "Inspect historical pipeline executions and task-level performance."
        )

        if runs.empty:
            st.info("No pipeline runs recorded.")
        else:
            st.dataframe(runs, use_container_width=True, hide_index=True)

            if "run_id" in runs.columns:
                selected = st.selectbox(
                    "Inspect execution",
                    runs["run_id"].astype(str).tolist()
                )

                detail = stages_for(selected)

                if not detail.empty:
                    st.markdown("### Stage Execution Details")
                    st.dataframe(detail, use_container_width=True, hide_index=True)

                    if "duration_seconds" in detail.columns:
                        fig = px.bar(
                            detail,
                            x="stage_name",
                            y="duration_seconds",
                            title="Execution time by stage"
                        )
                        fig.update_traces(marker_color="#36B6A5")
                        fig.update_layout(
                            template="plotly_dark",
                            paper_bgcolor="#192630",
                            plot_bgcolor="#192630",
                            font_color="#DCE5E9"
                        )
                        st.plotly_chart(fig, use_container_width=True)


# ==========================================================
# 10. DATA LINEAGE
# ==========================================================

elif current_workspace == "Data Lineage":

    with workspace_area:

        page_header(
            "DATA MANAGEMENT / GOVERNANCE",
            "Data Lineage",
            "Explore relationships between the ShopFlow business datasets."
        )

        relations = [
            ("CUSTOMERS", "ORDERS", "customer_id"),
            ("ORDERS", "ORDER ITEMS", "order_id"),
            ("PRODUCTS", "ORDER ITEMS", "product_id"),
            ("ORDERS", "PAYMENTS", "order_id")
        ]

        for source, target, key in relations:
            left, arrow, right = st.columns([2, 0.8, 2])

            with left:
                st.markdown(
                    f"""
                    <div class="sf-panel">
                        <div class="sf-kicker">SOURCE TABLE</div>
                        <h3>{source}</h3>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            with arrow:
                st.markdown(
                    f"""
                    <div style="text-align:center;padding-top:27px;
                    color:#36B6A5;font-size:19px">⟶
                    <div class="sf-node-meta">{key}</div></div>
                    """,
                    unsafe_allow_html=True
                )

            with right:
                st.markdown(
                    f"""
                    <div class="sf-panel">
                        <div class="sf-kicker">RELATED TABLE</div>
                        <h3>{target}</h3>
                    </div>
                    """,
                    unsafe_allow_html=True
                )


# ==========================================================
# 11. DATA CATALOG
# ==========================================================

elif current_workspace == "Data Catalog":

    with workspace_area:

        page_header(
            "DATA MANAGEMENT / METADATA",
            "Data Catalog",
            "Browse MySQL tables, column definitions and stored records."
        )

        selected = st.selectbox("Select table", TABLES)

        if table_exists(selected):

            schema = read_sql(
                """
                SELECT COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE,
                       COLUMN_KEY, COLUMN_DEFAULT
                FROM information_schema.columns
                WHERE table_schema = %s AND table_name = %s
                ORDER BY ORDINAL_POSITION
                """,
                (DB_CONFIG["database"], selected)
            )

            st.markdown("### Schema")
            st.dataframe(schema, use_container_width=True, hide_index=True)

            st.markdown("### Data Preview")
            st.dataframe(
                load_table(selected).head(50),
                use_container_width=True,
                hide_index=True
            )


# ==========================================================
# 12. DATA QUALITY
# ==========================================================

elif current_workspace == "Data Quality":

    with workspace_area:

        page_header(
            "DATA MANAGEMENT / OBSERVABILITY",
            "Data Quality",
            "Review persisted validation-stage results and implemented rules."
        )

        latest = latest_run()

        if latest is None:
            st.info("Run the ETL pipeline to produce validation results.")
        else:
            details = stages_for(latest["run_id"])

            validation = pd.DataFrame()
            if not details.empty:
                validation = details[
                    details["stage_name"].astype(str).str.upper() == "VALIDATE"
                ]

            if not validation.empty:
                result = str(validation.iloc[-1]["status"]).upper()
                if result == "SUCCESS":
                    st.success("Validation stage completed successfully.")
                elif result == "FAILED":
                    st.error("Validation stage failed.")
                else:
                    st.warning(f"Validation status: {result}")
            else:
                st.info("No validation record for the latest run.")

        rules = [
            "Primary Key Validation",
            "Foreign Key Validation",
            "Business Rule Validation",
            "Product Price Validation",
            "Order Total Validation",
            "Payment Amount Validation"
        ]

        st.markdown("### Implemented Validation Rules")
        for rule in rules:
            st.markdown(
                f'<div class="sf-panel">✓ &nbsp; {rule}</div>',
                unsafe_allow_html=True
            )

        st.caption(
            "Individual rule outcomes are not currently persisted separately; "
            "the backend records the overall validation-stage status."
        )


# ==========================================================
# 13. SQL LAB
# ==========================================================

elif current_workspace == "SQL Lab":

    with workspace_area:

        page_header(
            "DEVELOPMENT / QUERY ENGINE",
            "SQL Lab",
            "Explore ShopFlow data using read-only SQL queries."
        )

        st.markdown("### Query Editor")

        query = st.text_area(
            "SQL statement",
            "SELECT * FROM orders LIMIT 10;",
            height=190,
            label_visibility="collapsed"
        )

        if st.button("▶ EXECUTE QUERY", type="primary"):

            cleaned = query.strip()
            upper = cleaned.upper()
            allowed = ("SELECT", "WITH", "SHOW", "DESCRIBE", "DESC", "EXPLAIN")

            if not cleaned:
                st.warning("Enter a query.")
            elif ";" in cleaned.rstrip(";"):
                st.error("Multiple SQL statements are not allowed.")
            elif not upper.startswith(allowed):
                st.error("Only read-only SQL statements are allowed.")
            else:
                try:
                    result = read_sql(cleaned)
                    st.success(f"{len(result)} rows returned.")
                    st.dataframe(result, use_container_width=True, hide_index=True)
                    st.download_button(
                        "Download CSV",
                        result.to_csv(index=False),
                        "shopflow_query_results.csv",
                        "text/csv"
                    )
                except Exception as exc:
                    st.error(f"SQL error: {exc}")


# ==========================================================
# 14. INFRASTRUCTURE
# ==========================================================

elif current_workspace == "Infrastructure":

    with workspace_area:

        page_header(
            "DEVELOPMENT / INFRASTRUCTURE",
            "Infrastructure",
            "Inspect MySQL connectivity, database version and table availability."
        )

        try:
            connection = get_connection()
            cursor = connection.cursor()
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()[0]
            cursor.close()
            connection.close()

            st.success("MySQL connection established.")

            a, b = st.columns(2)
            a.metric("DATABASE", DB_CONFIG["database"])
            b.metric("MYSQL VERSION", version)

        except Exception as exc:
            st.error(str(exc))

        health = []

        for table in TABLES:
            try:
                exists = table_exists(table)
                health.append([table, "AVAILABLE" if exists else "MISSING"])
            except Exception:
                health.append([table, "ERROR"])

        st.markdown("### Database Table Health")
        st.dataframe(
            pd.DataFrame(health, columns=["TABLE", "STATUS"]),
            use_container_width=True,
            hide_index=True
        )


# ==========================================================
# 15. BUSINESS INSIGHTS
# ==========================================================

elif current_workspace == "Business Insights":

    with workspace_area:

        page_header(
            "ANALYTICS / BUSINESS INTELLIGENCE",
            "Business Insights",
            "Supporting analytics from the ShopFlow e-commerce datasets."
        )

        if orders.empty:
            st.info("No order records available.")
        else:
            frame = orders.copy()
            frame["total_amount"] = pd.to_numeric(
                frame["total_amount"], errors="coerce"
            )

            a, b, c = st.columns(3)
            a.metric("ORDERS", len(frame))
            b.metric("REVENUE", f"₹{frame['total_amount'].sum():,.2f}")
            c.metric("CUSTOMERS", len(customers))

            if "order_date" in frame.columns:
                frame["order_date"] = pd.to_datetime(
                    frame["order_date"], errors="coerce"
                )
                daily = frame.dropna(subset=["order_date"]).copy()
                daily["date"] = daily["order_date"].dt.date
                daily = daily.groupby("date", as_index=False)["total_amount"].sum()

                if not daily.empty:
                    fig = px.line(
                        daily, x="date", y="total_amount",
                        markers=True, title="Daily Revenue"
                    )
                    fig.update_traces(line_color="#36B6A5")
                    fig.update_layout(
                        template="plotly_dark",
                        paper_bgcolor="#192630",
                        plot_bgcolor="#192630",
                        font_color="#DCE5E9"
                    )
                    st.plotly_chart(fig, use_container_width=True)

            if "order_status" in frame.columns:
                counts = frame["order_status"].value_counts().reset_index()
                counts.columns = ["status", "orders"]
                fig = px.pie(
                    counts, names="status", values="orders",
                    hole=0.55, title="Order Status"
                )
                fig.update_layout(
                    template="plotly_dark",
                    paper_bgcolor="#192630",
                    font_color="#DCE5E9"
                )
                st.plotly_chart(fig, use_container_width=True)


# ==========================================================
# 16. FOOTER
# ==========================================================

with workspace_area:
    st.markdown('<div class="sf-divider"></div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div style="display:flex;justify-content:space-between;
        color:#71838D;font-family:'DM Mono',monospace;font-size:9px">
            <span>SHOPFLOW DATA OPERATIONS PLATFORM</span>
            <span>PYTHON · PANDAS · MYSQL · STREAMLIT</span>
        </div>
        """,
        unsafe_allow_html=True
    )
