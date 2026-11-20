
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Activity, AlertCircle, ArrowDown, ArrowRight, BarChart3,
  Boxes, CheckCircle2, ChevronDown, Clock3, Code2, Database,
  GitBranch, HardDrive, LayoutDashboard, Loader2, Play,
  RefreshCw, Search, Server, ShieldCheck, Table2, Terminal,
  Workflow, Zap, XCircle
} from "lucide-react";

import {
  Background, Controls, MiniMap, ReactFlow, MarkerType
} from "@xyflow/react";

import "@xyflow/react/dist/style.css";

import {
  Area, AreaChart, Bar, BarChart, CartesianGrid,
  Cell, Pie, PieChart, ResponsiveContainer,
  Tooltip, XAxis, YAxis
} from "recharts";

import {
  getHealth, getDatabaseHealth, getDatabaseSummary,
  getCatalog, getCatalogTable, getLineage, getDataQuality,
  getPipelineOverview, getPipelineRuns, getPipelineStages,
  runPipeline, getBusinessInsights, executeSqlQuery
} from "./services/api";

import "./App.css";

const NAVIGATION = [
  { id: "overview", label: "Command Center", icon: LayoutDashboard, section: "PLATFORM" },
  { id: "pipeline", label: "Pipeline Studio", icon: Workflow, section: "PLATFORM" },
  { id: "runs", label: "Run History", icon: Activity, section: "PLATFORM" },
  { id: "lineage", label: "Data Lineage", icon: GitBranch, section: "DATA" },
  { id: "catalog", label: "Data Catalog", icon: Database, section: "DATA" },
  { id: "quality", label: "Data Quality", icon: ShieldCheck, section: "DATA" },
  { id: "sql", label: "SQL Lab", icon: Terminal, section: "TOOLS" },
  { id: "infrastructure", label: "Infrastructure", icon: Server, section: "TOOLS" },
  { id: "insights", label: "Business Insights", icon: BarChart3, section: "ANALYTICS" }
];

const TABLES = ["customers", "products", "orders", "order_items", "payments"];

const PIPELINE_NODES = [
  {
    id: "extract",
    type: "input",
    position: { x: 30, y: 130 },
    data: { label: "EXTRACT", detail: "Read raw CSV datasets", icon: "01" }
  },
  {
    id: "transform",
    position: { x: 270, y: 130 },
    data: { label: "TRANSFORM", detail: "Clean and standardize", icon: "02" }
  },
  {
    id: "validate",
    position: { x: 510, y: 130 },
    data: { label: "VALIDATE", detail: "Run quality checks", icon: "03" }
  },
  {
    id: "load",
    type: "output",
    position: { x: 750, y: 130 },
    data: { label: "LOAD", detail: "Write to MySQL", icon: "04" }
  }
];

const PIPELINE_EDGES = [
  { id: "e1", source: "extract", target: "transform", animated: true },
  { id: "e2", source: "transform", target: "validate", animated: true },
  { id: "e3", source: "validate", target: "load", animated: true }
].map(edge => ({
  ...edge,
  markerEnd: { type: MarkerType.ArrowClosed }
}));

const formatNumber = value =>
  Number(value || 0).toLocaleString("en-IN");

const formatDuration = value =>
  `${Number(value || 0).toFixed(2)}s`;

const formatDate = value => {
  if (!value) return "—";
  return new Date(value).toLocaleString("en-IN");
};

function StatusBadge({ status }) {
  const normalized = String(status || "UNKNOWN").toUpperCase();
  const success = ["SUCCESS", "PASSED", "CONNECTED", "HEALTHY"].includes(normalized);
  const failure = ["FAILED", "ERROR", "DISCONNECTED"].includes(normalized);
  const running = normalized === "RUNNING";

  return (
    <span className={`status-badge ${success ? "success" : failure ? "failed" : running ? "running" : "neutral"}`}>
      <span className="status-dot" />
      {normalized}
    </span>
  );
}

function MetricCard({ label, value, detail, icon: Icon, accent = "blue" }) {
  return (
    <div className={`metric-card accent-${accent}`}>
      <div className="metric-top">
        <span className="metric-label">{label}</span>
        <span className="metric-icon"><Icon size={19} /></span>
      </div>
      <div className="metric-value">{value ?? "—"}</div>
      <div className="metric-detail">{detail}</div>
    </div>
  );
}

function SectionHeading({ eyebrow, title, description, action }) {
  return (
    <div className="page-heading">
      <div>
        <div className="eyebrow">{eyebrow}</div>
        <h1>{title}</h1>
        <p>{description}</p>
      </div>
      {action}
    </div>
  );
}

function EmptyState({ message = "No data available yet." }) {
  return <div className="empty-state">{message}</div>;
}

function App() {
  const [activePage, setActivePage] = useState("overview");
  const [health, setHealth] = useState(null);
  const [databaseHealth, setDatabaseHealth] = useState(null);
  const [database, setDatabase] = useState(null);
  const [pipeline, setPipeline] = useState(null);
  const [runs, setRuns] = useState([]);
  const [catalog, setCatalog] = useState([]);
  const [selectedTable, setSelectedTable] = useState("customers");
  const [tableDetail, setTableDetail] = useState(null);
  const [lineage, setLineage] = useState(null);
  const [quality, setQuality] = useState(null);
  const [insights, setInsights] = useState(null);
  const [selectedRun, setSelectedRun] = useState(null);
  const [stages, setStages] = useState([]);
  const [sql, setSql] = useState("SELECT * FROM customers LIMIT 10");
  const [sqlResult, setSqlResult] = useState(null);
  const [sqlError, setSqlError] = useState("");
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  const refreshDashboard = useCallback(async (showLoader = false) => {
    if (showLoader) setRefreshing(true);

    try {
      const results = await Promise.allSettled([
        getHealth(),
        getDatabaseHealth(),
        getDatabaseSummary(),
        getPipelineOverview(),
        getPipelineRuns(20),
        getCatalog(),
        getLineage(),
        getDataQuality(),
        getBusinessInsights()
      ]);

      const read = index =>
        results[index].status === "fulfilled"
          ? results[index].value.data
          : null;

      setHealth(read(0));
      setDatabaseHealth(read(1));
      setDatabase(read(2));
      setPipeline(read(3));
      setRuns(read(4)?.runs || []);
      setCatalog(read(5)?.tables || []);
      setLineage(read(6));
      setQuality(read(7));
      setInsights(read(8));

      const failures = results.filter(result => result.status === "rejected");

      setError(
        failures.length
          ? `${failures.length} API request(s) failed. Check backend connectivity.`
          : ""
      );
    } catch {
      setError("Unable to load dashboard data.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    refreshDashboard();
  }, [refreshDashboard]);

  const loadTable = useCallback(async table => {
    setSelectedTable(table);
    setTableDetail(null);

    try {
      const response = await getCatalogTable(table, 20);
      setTableDetail(response.data);
    } catch {
      setTableDetail({ error: "Unable to load table details." });
    }
  }, []);

  useEffect(() => {
    if (activePage === "catalog") loadTable(selectedTable);
  }, [activePage, selectedTable, loadTable]);

  const loadStages = useCallback(async runId => {
    setSelectedRun(runId);
    setStages([]);

    try {
      const response = await getPipelineStages(runId);
      setStages(response.data.stages || []);
    } catch {
      setStages([]);
    }
  }, []);

  const handleRunPipeline = async () => {
    if (running) return;

    setRunning(true);

    try {
      await runPipeline();
      await refreshDashboard();
      setActivePage("runs");
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        "Pipeline execution failed. Check the backend terminal."
      );
    } finally {
      setRunning(false);
    }
  };

  const handleSql = async () => {
    setSqlError("");
    setSqlResult(null);

    try {
      const response = await executeSqlQuery(sql);
      setSqlResult(response.data);
    } catch (err) {
      setSqlError(err.response?.data?.detail || "Unable to execute query.");
    }
  };

  const groupedNavigation = useMemo(() => {
    return ["PLATFORM", "DATA", "TOOLS", "ANALYTICS"].map(section => ({
      section,
      items: NAVIGATION.filter(item => item.section === section)
    }));
  }, []);

  const activeLabel =
    NAVIGATION.find(item => item.id === activePage)?.label || "Command Center";

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark"><Boxes size={23} /></div>
          <div>
            <div className="brand-name">shopflow<span>.</span></div>
            <div className="brand-subtitle">DATA ENGINEERING PLATFORM</div>
          </div>
        </div>

        <div className="workspace-label">WORKSPACE</div>
        <div className="workspace-select">
          <div className="workspace-avatar">SF</div>
          <div className="workspace-copy">
            <strong>ShopFlow Platform</strong>
            <span>Development environment</span>
          </div>
          <ChevronDown size={15} />
        </div>

        <nav className="navigation">
          {groupedNavigation.map(group => (
            <div className="nav-group" key={group.section}>
              <div className="nav-section-label">{group.section}</div>
              {group.items.map(item => {
                const Icon = item.icon;
                return (
                  <button
                    key={item.id}
                    className={`nav-item ${activePage === item.id ? "active" : ""}`}
                    onClick={() => setActivePage(item.id)}
                  >
                    <Icon size={17} />
                    <span>{item.label}</span>
                    {item.id === "quality" && quality?.failed_checks > 0 && (
                      <span className="nav-alert">{quality.failed_checks}</span>
                    )}
                  </button>
                );
              })}
            </div>
          ))}
        </nav>

        <div className="sidebar-bottom">
          <div className="connection-card">
            <div className="connection-title">
              <span className="live-indicator" />
              SYSTEM STATUS
            </div>
            <div className="connection-row">
              <span>API</span>
              <StatusBadge status={health?.status || "UNKNOWN"} />
            </div>
            <div className="connection-row">
              <span>MySQL</span>
              <StatusBadge status={databaseHealth?.status || "UNKNOWN"} />
            </div>
          </div>
          <div className="sidebar-version">
            <span>SHOPFLOW</span>
            <span>v2.0.0</span>
          </div>
        </div>
      </aside>

      <main className="main-area">
        <header className="topbar">
          <div className="breadcrumb">
            <span>ShopFlow</span>
            <ArrowRight size={14} />
            <strong>{activeLabel}</strong>
          </div>
          <div className="topbar-actions">
            <span className="environment-pill">
              <span className="live-indicator" /> LOCAL ENVIRONMENT
            </span>
            <button
              className="icon-button"
              title="Refresh dashboard"
              onClick={() => refreshDashboard(true)}
              disabled={refreshing}
            >
              {refreshing
                ? <Loader2 size={17} className="spin" />
                : <RefreshCw size={17} />}
            </button>
            <div className="profile-avatar">SF</div>
          </div>
        </header>

        <div className="page-content">
          {error && (
            <div className="alert-banner">
              <AlertCircle size={17} />
              <span>{error}</span>
              <button onClick={() => setError("")}><XCircle size={16} /></button>
            </div>
          )}

          {loading ? (
            <div className="loading-screen">
              <Loader2 className="spin" size={30} />
              <span>Loading ShopFlow platform...</span>
            </div>
          ) : (
            <>
              {activePage === "overview" && (
                <OverviewPage
                  database={database}
                  pipeline={pipeline}
                  quality={quality}
                  runs={runs}
                  insights={insights}
                  onNavigate={setActivePage}
                  onRun={handleRunPipeline}
                  running={running}
                />
              )}

              {activePage === "pipeline" && (
                <PipelinePage
                  onRun={handleRunPipeline}
                  running={running}
                  onNavigate={setActivePage}
                />
              )}

              {activePage === "runs" && (
                <RunsPage
                  runs={runs}
                  selectedRun={selectedRun}
                  stages={stages}
                  onSelect={loadStages}
                  onRefresh={() => refreshDashboard(true)}
                />
              )}

              {activePage === "lineage" && <LineagePage lineage={lineage} />}

              {activePage === "catalog" && (
                <CatalogPage
                  catalog={catalog}
                  selectedTable={selectedTable}
                  tableDetail={tableDetail}
                  onSelect={loadTable}
                />
              )}

              {activePage === "quality" && <QualityPage quality={quality} />}

              {activePage === "sql" && (
                <SqlPage
                  sql={sql}
                  setSql={setSql}
                  result={sqlResult}
                  error={sqlError}
                  onExecute={handleSql}
                />
              )}

              {activePage === "infrastructure" && (
                <InfrastructurePage
                  health={health}
                  databaseHealth={databaseHealth}
                  database={database}
                />
              )}

              {activePage === "insights" && <InsightsPage insights={insights} />}
            </>
          )}

          <footer className="app-footer">
            <span>SHOPFLOW DATA ENGINEERING PLATFORM</span>
            <span>Built with Python · FastAPI · React · MySQL</span>
          </footer>
        </div>
      </main>
    </div>
  );
}


// ============================================================
// COMMAND CENTER
// ============================================================

function OverviewPage({
  database, pipeline, quality, runs, insights,
  onNavigate, onRun, running
}) {
  const recentRuns = runs.slice(0, 5);
  const successful = Number(pipeline?.successful_runs || 0);
  const total = Number(pipeline?.total_runs || 0);
  const successRate = total ? (successful / total * 100).toFixed(1) : "0.0";

  const chartData = [...runs].reverse().map((run, index) => ({
    run: `Run ${index + 1}`,
    duration: Number(run.duration_seconds || 0),
    inserted: Number(run.records_inserted || 0),
    skipped: Number(run.records_skipped || 0)
  }));

  return (
    <>
      <SectionHeading
        eyebrow="PLATFORM OVERVIEW"
        title="Command Center"
        description="Monitor your data engineering platform, pipeline performance and data quality."
        action={
          <button className="primary-button" onClick={onRun} disabled={running}>
            {running ? <Loader2 size={16} className="spin" /> : <Play size={16} />}
            {running ? "Running..." : "Run Pipeline"}
          </button>
        }
      />

      <div className="metrics-grid">
        <MetricCard label="Total Pipeline Runs" value={formatNumber(pipeline?.total_runs)} detail="Recorded executions" icon={Workflow} />
        <MetricCard label="Successful Runs" value={formatNumber(pipeline?.successful_runs)} detail={`${successRate}% success rate`} icon={CheckCircle2} accent="green" />
        <MetricCard label="Records in Database" value={formatNumber(database?.total_records)} detail={`${database?.total_tables || 0} business tables`} icon={Database} accent="purple" />
        <MetricCard label="Average Duration" value={formatDuration(pipeline?.average_duration)} detail="Across recorded pipeline runs" icon={Clock3} accent="orange" />
      </div>

      <div className="overview-grid">
        <section className="panel performance-panel">
          <div className="panel-heading">
            <div><h3>Pipeline Performance</h3><p>Recent execution duration</p></div>
            <span className="panel-icon"><Activity size={18} /></span>
          </div>
          {chartData.length ? (
            <div className="chart-area">
              <ResponsiveContainer width="100%" height={245}>
                <AreaChart data={chartData}>
                  <defs>
                    <linearGradient id="durationGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#4c91ff" stopOpacity={0.35} />
                      <stop offset="100%" stopColor="#4c91ff" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid stroke="#202b3a" strokeDasharray="3 3" />
                  <XAxis dataKey="run" stroke="#718096" tick={{ fontSize: 11 }} />
                  <YAxis stroke="#718096" tick={{ fontSize: 11 }} />
                  <Tooltip contentStyle={{ background: "#111b29", border: "1px solid #29374a", borderRadius: 9 }} />
                  <Area type="monotone" dataKey="duration" stroke="#5b9cff" fill="url(#durationGradient)" strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          ) : <EmptyState message="Run the pipeline to see performance history." />}
        </section>

        <section className="panel quality-summary-panel">
          <div className="panel-heading">
            <div><h3>Data Quality Overview</h3><p>Latest validation results</p></div>
            <ShieldCheck size={19} />
          </div>
          <div className="quality-score">
            <div className="quality-score-number">
              {quality?.total_checks
                ? Math.round(quality.passed_checks / quality.total_checks * 100)
                : 0}%
            </div>
            <span>Validation success</span>
          </div>
          <div className="quality-progress">
            <div style={{ width: `${quality?.total_checks ? quality.passed_checks / quality.total_checks * 100 : 0}%` }} />
          </div>
          <div className="quality-counts">
            <div><strong className="green-text">{quality?.passed_checks ?? "—"}</strong><span>Passed</span></div>
            <div><strong className="red-text">{quality?.failed_checks ?? "—"}</strong><span>Failed</span></div>
            <div><strong>{quality?.total_checks ?? "—"}</strong><span>Total</span></div>
          </div>
          <button className="text-link" onClick={() => onNavigate("quality")}>View quality checks <ArrowRight size={14} /></button>
        </section>
      </div>

      <section className="panel">
        <div className="panel-heading">
          <div><h3>Recent Pipeline Runs</h3><p>Latest execution activity</p></div>
          <button className="text-link" onClick={() => onNavigate("runs")}>View all <ArrowRight size={14} /></button>
        </div>
        <RunsTable runs={recentRuns} />
      </section>

      <div className="overview-grid lower-grid">
        <section className="panel">
          <div className="panel-heading">
            <div><h3>Database Tables</h3><p>Current business data inventory</p></div>
            <Database size={18} />
          </div>
          <div className="table-count-list">
            {Object.entries(database?.tables || {}).map(([name, count]) => (
              <div className="table-count-row" key={name}>
                <div><Table2 size={15} /><span>{name}</span></div>
                <strong>{formatNumber(count)}</strong>
              </div>
            ))}
          </div>
          <button className="text-link" onClick={() => onNavigate("catalog")}>Explore catalog <ArrowRight size={14} /></button>
        </section>

        <section className="panel">
          <div className="panel-heading">
            <div><h3>Business Snapshot</h3><p>Current e-commerce metrics</p></div>
            <BarChart3 size={18} />
          </div>
          <div className="business-snapshot">
            <div><span>Total Orders</span><strong>{formatNumber(insights?.orders?.total_orders)}</strong></div>
            <div><span>Customers</span><strong>{formatNumber(insights?.customers?.total_customers)}</strong></div>
            <div><span>Products</span><strong>{formatNumber(insights?.products?.total_products)}</strong></div>
            <div><span>Order Value</span><strong>₹{formatNumber(insights?.orders?.total_order_value)}</strong></div>
          </div>
          <button className="text-link" onClick={() => onNavigate("insights")}>Explore insights <ArrowRight size={14} /></button>
        </section>
      </div>
    </>
  );
}


// ============================================================
// PIPELINE STUDIO
// ============================================================

function PipelinePage({ onRun, running, onNavigate }) {
  const [selectedNode, setSelectedNode] = useState("extract");
  const selected = PIPELINE_NODES.find(node => node.id === selectedNode);

  return (
    <>
      <SectionHeading
        eyebrow="ORCHESTRATION"
        title="Pipeline Studio"
        description="Explore the ShopFlow ETL workflow from raw data extraction to MySQL loading."
        action={
          <button className="primary-button" onClick={onRun} disabled={running}>
            {running ? <Loader2 size={16} className="spin" /> : <Play size={16} />}
            {running ? "Executing..." : "Execute Pipeline"}
          </button>
        }
      />

      <div className="pipeline-toolbar">
        <div className="toolbar-left">
          <span className="live-indicator" /> WORKFLOW DEFINITION
          <span className="toolbar-divider" />
          <span>4 stages</span><span>·</span><span>Sequential execution</span>
        </div>
        <button className="secondary-button" onClick={() => onNavigate("runs")}><Activity size={15} /> Run history</button>
      </div>

      <div className="pipeline-workspace">
        <div className="pipeline-canvas">
          <ReactFlow
            nodes={PIPELINE_NODES}
            edges={PIPELINE_EDGES}
            fitView
            fitViewOptions={{ padding: 0.25 }}
            nodesDraggable={false}
            nodesConnectable={false}
            elementsSelectable
            onNodeClick={(_, node) => setSelectedNode(node.id)}
          >
            <Background color="#29384b" gap={22} />
            <Controls />
            <MiniMap nodeColor="#427fca" maskColor="rgba(5, 12, 22, 0.65)" />
          </ReactFlow>
        </div>

        <aside className="node-inspector">
          <div className="inspector-heading"><span>NODE INSPECTOR</span><Workflow size={17} /></div>
          {selected && (
            <>
              <div className="inspector-node-icon">{selected.data.icon}</div>
              <h3>{selected.data.label}</h3>
              <p>{selected.data.detail}</p>
              <div className="inspector-details">
                <div><span>Stage ID</span><strong>{selected.id}</strong></div>
                <div><span>Execution mode</span><strong>Sequential</strong></div>
                <div><span>Pipeline</span><strong>ShopFlow ETL</strong></div>
              </div>
            </>
          )}
          <div className="inspector-note">Select a pipeline node to inspect its stage details.</div>
        </aside>
      </div>

      <div className="pipeline-stage-grid">
        {PIPELINE_NODES.map((node, index) => (
          <div
            key={node.id}
            className={`pipeline-stage-card ${selectedNode === node.id ? "selected" : ""}`}
            onClick={() => setSelectedNode(node.id)}
          >
            <span className="stage-number">{node.data.icon}</span>
            <div><strong>{node.data.label}</strong><span>{node.data.detail}</span></div>
            {index < 3 && <ArrowRight size={15} />}
          </div>
        ))}
      </div>
    </>
  );
}


// ============================================================
// RUN HISTORY TABLE
// ============================================================

function RunsTable({ runs }) {
  if (!runs?.length) return <EmptyState message="No pipeline runs recorded yet." />;

  return (
    <div className="table-scroll">
      <table className="data-table">
        <thead>
          <tr>
            <th>RUN ID</th><th>STATUS</th><th>STARTED AT</th>
            <th>DURATION</th><th>INSERTED</th><th>SKIPPED</th>
          </tr>
        </thead>
        <tbody>
          {runs.map(run => (
            <tr key={run.run_id}>
              <td className="mono">{String(run.run_id).slice(0, 13)}...</td>
              <td><StatusBadge status={run.status} /></td>
              <td>{formatDate(run.started_at)}</td>
              <td>{formatDuration(run.duration_seconds)}</td>
              <td>{formatNumber(run.records_inserted)}</td>
              <td>{formatNumber(run.records_skipped)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}


// ============================================================
// RUN HISTORY — IMPROVED
// ============================================================

function RunsPage({ runs, selectedRun, stages, onSelect, onRefresh }) {
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");

  const filteredRuns = runs.filter(run => {
    const searchValue = search.toLowerCase();

    const matchesSearch =
      String(run.run_id || "").toLowerCase().includes(searchValue) ||
      String(run.status || "").toLowerCase().includes(searchValue);

    const matchesStatus =
      statusFilter === "ALL" ||
      String(run.status || "").toUpperCase() === statusFilter;

    return matchesSearch && matchesStatus;
  });

  const selectedStatus = stages.length
    ? stages.some(stage => String(stage.status).toUpperCase() === "FAILED")
      ? "FAILED"
      : stages.some(stage => String(stage.status).toUpperCase() === "RUNNING")
        ? "RUNNING"
        : stages.every(stage => String(stage.status).toUpperCase() === "SUCCESS")
          ? "SUCCESS"
          : "UNKNOWN"
    : "UNKNOWN";

  const successfulCount = runs.filter(
    run => String(run.status).toUpperCase() === "SUCCESS"
  ).length;

  const failedCount = runs.filter(
    run => String(run.status).toUpperCase() === "FAILED"
  ).length;

  const averageDuration = runs.length
    ? runs.reduce((sum, run) => sum + Number(run.duration_seconds || 0), 0) / runs.length
    : 0;

  return (
    <>
      <SectionHeading
        eyebrow="EXECUTION MONITORING"
        title="Run History"
        description="Inspect pipeline executions, execution outcomes and individual stage timings."
        action={
          <button className="secondary-button" onClick={onRefresh}>
            <RefreshCw size={15} /> Refresh
          </button>
        }
      />

      <div className="metrics-grid">
        <MetricCard label="Total Executions" value={formatNumber(runs.length)} detail="Recorded pipeline runs" icon={Activity} />
        <MetricCard label="Successful" value={formatNumber(successfulCount)} detail="Completed successfully" icon={CheckCircle2} accent="green" />
        <MetricCard label="Failed" value={formatNumber(failedCount)} detail="Executions requiring attention" icon={XCircle} accent="orange" />
        <MetricCard label="Average Duration" value={formatDuration(averageDuration)} detail="Across recorded executions" icon={Clock3} accent="purple" />
      </div>

      <section className="panel">
        <div className="panel-heading">
          <div>
            <h3>Execution Records</h3>
            <p>Search and inspect individual pipeline runs</p>
          </div>
          <span>{filteredRuns.length} of {runs.length} runs</span>
        </div>

        <div style={{
          display: "flex",
          gap: 12,
          flexWrap: "wrap",
          marginBottom: 18
        }}>
          <div style={{
            flex: "1 1 230px",
            display: "flex",
            alignItems: "center",
            gap: 9,
            padding: "0 12px",
            minHeight: 38,
            background: "#0d1727",
            border: "1px solid #26364d",
            borderRadius: 8
          }}>
            <Search size={15} color="#91a2b8" />
            <input
              value={search}
              onChange={event => setSearch(event.target.value)}
              placeholder="Search run ID or status..."
              style={{
                flex: 1,
                minWidth: 0,
                background: "transparent",
                border: 0,
                outline: 0,
                color: "#e6edf6",
                fontSize: 11
              }}
            />
          </div>

          <select
            value={statusFilter}
            onChange={event => setStatusFilter(event.target.value)}
            style={{
              minWidth: 135,
              padding: "0 12px",
              background: "#0d1727",
              color: "#c2cfdf",
              border: "1px solid #26364d",
              borderRadius: 8,
              fontSize: 11
            }}
          >
            <option value="ALL">All statuses</option>
            <option value="SUCCESS">Successful</option>
            <option value="FAILED">Failed</option>
            <option value="RUNNING">Running</option>
          </select>
        </div>

        {filteredRuns.length ? (
          <div className="table-scroll">
            <table className="data-table">
              <thead>
                <tr>
                  <th>RUN ID</th><th>STATUS</th><th>STARTED</th>
                  <th>DURATION</th><th>INSERTED</th><th>SKIPPED</th><th>DETAILS</th>
                </tr>
              </thead>
              <tbody>
                {filteredRuns.map(run => (
                  <tr key={run.run_id}>
                    <td className="mono" title={run.run_id}>
                      {String(run.run_id).slice(0, 13)}...
                    </td>
                    <td><StatusBadge status={run.status} /></td>
                    <td>{formatDate(run.started_at)}</td>
                    <td>{formatDuration(run.duration_seconds)}</td>
                    <td>{formatNumber(run.records_inserted)}</td>
                    <td>{formatNumber(run.records_skipped)}</td>
                    <td>
                      <button className="small-button" onClick={() => onSelect(run.run_id)}>
                        Inspect
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyState message="No pipeline runs match your search or filter." />
        )}
      </section>

      {selectedRun && (
        <section className="panel stage-history-panel">
          <div className="panel-heading">
            <div>
              <h3>Execution Details</h3>
              <p className="mono">{selectedRun}</p>
            </div>
            <StatusBadge status={selectedStatus} />
          </div>

          {stages.length ? (
            <div className="stage-history-list">
              {stages.map((stage, index) => (
                <div className="stage-history-item" key={stage.stage_id}>
                  <div className="stage-history-number">
                    {String(index + 1).padStart(2, "0")}
                  </div>
                  <div className="stage-history-copy">
                    <strong>{stage.stage_name}</strong>
                    <span>{formatDate(stage.started_at)}</span>
                    {stage.error_message && (
                      <span className="red-text">{stage.error_message}</span>
                    )}
                  </div>
                  <StatusBadge status={stage.status} />
                  <strong>{formatDuration(stage.duration_seconds)}</strong>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState message="No stage records were returned for this run." />
          )}
        </section>
      )}
    </>
  );
}


// ============================================================
// DATA LINEAGE
// ============================================================

function LineagePage({ lineage }) {
  const nodes = useMemo(() => {
    const positions = {
      customers: { x: 30, y: 40 },
      products: { x: 30, y: 280 },
      orders: { x: 350, y: 40 },
      order_items: { x: 680, y: 160 },
      payments: { x: 1000, y: 40 }
    };

    return (lineage?.nodes || []).map(node => ({
      id: node.id,
      position: positions[node.id] || { x: 100, y: 100 },
      data: { label: node.label },
      style: {
        background: "#142235",
        color: "#e6edf5",
        border: "1px solid #3a5878",
        borderRadius: 10,
        padding: 14,
        minWidth: 145,
        fontWeight: 600
      }
    }));
  }, [lineage]);

  const edges = useMemo(() => (lineage?.edges || []).map(edge => ({
    ...edge,
    label: edge.label,
    animated: true,
    markerEnd: { type: MarkerType.ArrowClosed },
    style: { stroke: "#5798df", strokeWidth: 2 },
    labelStyle: { fill: "#9cb5d0", fontSize: 11 }
  })), [lineage]);

  return (
    <>
      <SectionHeading
        eyebrow="DATA ARCHITECTURE"
        title="Data Lineage"
        description="Explore how records flow between ShopFlow business entities through their key relationships."
      />
      <div className="lineage-summary">
        <div><strong>{nodes.length}</strong><span>Data entities</span></div>
        <div><strong>{edges.length}</strong><span>Relationships</span></div>
        <div><strong>MySQL</strong><span>Destination database</span></div>
      </div>
      <section className="panel lineage-panel">
        {nodes.length ? (
          <div className="lineage-canvas">
            <ReactFlow
              nodes={nodes}
              edges={edges}
              fitView
              fitViewOptions={{ padding: 0.2 }}
              nodesDraggable={false}
              nodesConnectable={false}
            >
              <Background color="#29384b" gap={22} />
              <Controls />
              <MiniMap nodeColor="#427fca" />
            </ReactFlow>
          </div>
        ) : <EmptyState message="Lineage information is unavailable." />}
      </section>
      <section className="panel">
        <div className="panel-heading">
          <div><h3>Relationship Definitions</h3><p>Foreign-key connections</p></div>
        </div>
        <div className="relationship-list">
          {(lineage?.edges || []).map(edge => (
            <div className="relationship-row" key={edge.id}>
              <strong>{edge.source}</strong>
              <ArrowRight size={17} />
              <strong>{edge.target}</strong>
              <span>{edge.label}</span>
            </div>
          ))}
        </div>
      </section>
    </>
  );
}


// ============================================================
// DATA CATALOG
// ============================================================

function CatalogPage({ catalog, selectedTable, tableDetail, onSelect }) {
  return (
    <>
      <SectionHeading
        eyebrow="DATA DISCOVERY"
        title="Data Catalog"
        description="Discover the MySQL tables, inspect their schemas and preview stored records."
      />

      <div className="catalog-layout">
        <section className="panel catalog-sidebar">
          <div className="panel-heading">
            <div><h3>Database Tables</h3><p>{catalog.length} tables discovered</p></div>
          </div>
          {catalog.map(table => (
            <button
              className={`catalog-table-item ${selectedTable === table.table_name ? "selected" : ""}`}
              key={table.table_name}
              onClick={() => onSelect(table.table_name)}
            >
              <Database size={16} />
              <span>{table.table_name}</span>
              <strong>{formatNumber(table.actual_rows)}</strong>
            </button>
          ))}
        </section>

        <div className="catalog-main">
          <section className="panel">
            <div className="panel-heading">
              <div><h3>{selectedTable}</h3><p>MySQL table schema and metadata</p></div>
              <StatusBadge status={tableDetail?.error ? "FAILED" : "CONNECTED"} />
            </div>

            {tableDetail?.error ? (
              <EmptyState message={tableDetail.error} />
            ) : tableDetail?.columns ? (
              <div className="table-scroll">
                <table className="data-table">
                  <thead><tr><th>COLUMN</th><th>DATA TYPE</th><th>NULLABLE</th><th>KEY</th></tr></thead>
                  <tbody>
                    {tableDetail.columns.map(column => (
                      <tr key={column.column_name}>
                        <td className="mono">{column.column_name}</td>
                        <td>{column.data_type}</td>
                        <td>{column.is_nullable}</td>
                        <td>{column.column_key || "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : <EmptyState message="Select a table to inspect its schema." />}
          </section>

          <section className="panel">
            <div className="panel-heading">
              <div><h3>Data Preview</h3><p>First 20 records from the selected table</p></div>
              <span>{tableDetail?.returned_rows ?? 0} rows</span>
            </div>
            {tableDetail?.preview?.length ? (
              <div className="table-scroll">
                <table className="data-table">
                  <thead><tr>{Object.keys(tableDetail.preview[0]).map(key => <th key={key}>{key}</th>)}</tr></thead>
                  <tbody>
                    {tableDetail.preview.map((row, index) => (
                      <tr key={index}>
                        {Object.values(row).map((value, cellIndex) => (
                          <td key={cellIndex}>{String(value ?? "NULL")}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : <EmptyState message="No preview records available." />}
          </section>
        </div>
      </div>
    </>
  );
}


// ============================================================
// DATA QUALITY
// ============================================================

function QualityPage({ quality }) {
  return (
    <>
      <SectionHeading
        eyebrow="TRUST & RELIABILITY"
        title="Data Quality"
        description="Review the validation checks applied to your ShopFlow datasets."
      />

      <div className="metrics-grid">
        <MetricCard label="Total Checks" value={quality?.total_checks ?? 0} detail="Configured validations" icon={ShieldCheck} />
        <MetricCard label="Passed" value={quality?.passed_checks ?? 0} detail="Successful checks" icon={CheckCircle2} accent="green" />
        <MetricCard label="Failed" value={quality?.failed_checks ?? 0} detail="Checks requiring attention" icon={XCircle} accent="orange" />
        <MetricCard label="Overall Status" value={quality?.overall_status || "UNKNOWN"} detail="Latest validation response" icon={Activity} accent="purple" />
      </div>

      <section className="panel">
        <div className="panel-heading">
          <div><h3>Validation Results</h3><p>Individual data-quality checks</p></div>
          <StatusBadge status={quality?.overall_status} />
        </div>
        <div className="quality-check-list">
          {(quality?.results || []).map((result, index) => (
            <div className="quality-check-row" key={result.check}>
              <div className="quality-check-icon">
                {result.passed ? <CheckCircle2 size={19} /> : <XCircle size={19} />}
              </div>
              <div className="quality-check-copy">
                <strong>{result.check}</strong>
                <span>Validation rule {String(index + 1).padStart(2, "0")}</span>
              </div>
              <StatusBadge status={result.status} />
            </div>
          ))}
        </div>
      </section>
      <div className="info-note">
        <ShieldCheck size={18} />
        <span>These results are produced by the existing ShopFlow validation functions using the current extracted and transformed CSV datasets.</span>
      </div>
    </>
  );
}


// ============================================================
// SQL LAB
// ============================================================

function SqlPage({ sql, setSql, result, error, onExecute }) {
  return (
    <>
      <SectionHeading
        eyebrow="QUERY WORKSPACE"
        title="SQL Lab"
        description="Explore ShopFlow data using read-only SQL queries."
      />

      <section className="panel sql-editor-panel">
        <div className="sql-editor-heading">
          <div><Code2 size={18} /><strong>Query Editor</strong></div>
          <StatusBadge status="READ ONLY" />
        </div>
        <textarea
          className="sql-editor"
          value={sql}
          onChange={event => setSql(event.target.value)}
          spellCheck={false}
          placeholder="SELECT * FROM customers LIMIT 10"
        />
        <div className="sql-editor-footer">
          <span>MySQL · Maximum 200 returned rows</span>
          <button className="primary-button" onClick={onExecute}>
            <Play size={15} /> Run Query
          </button>
        </div>
      </section>

      {error && <div className="alert-banner"><AlertCircle size={17} />{error}</div>}

      {result && (
        <section className="panel sql-results-panel">
          <div className="panel-heading">
            <div><h3>Query Results</h3><p>Returned records</p></div>
            <span>{result.returned_rows} rows</span>
          </div>
          {result.rows?.length ? (
            <div className="table-scroll">
              <table className="data-table">
                <thead><tr>{result.columns.map(column => <th key={column}>{column}</th>)}</tr></thead>
                <tbody>
                  {result.rows.map((row, index) => (
                    <tr key={index}>
                      {result.columns.map(column => (
                        <td key={column}>{String(row[column] ?? "NULL")}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : <EmptyState message="The query returned no rows." />}
          {result.truncated && <div className="info-note">Results were limited to 200 rows.</div>}
        </section>
      )}

      <section className="panel">
        <div className="panel-heading">
          <div><h3>Available Tables</h3><p>Use these tables in your queries</p></div>
        </div>
        <div className="sql-table-chips">
          {TABLES.map(table => (
            <button key={table} onClick={() => setSql(`SELECT * FROM ${table} LIMIT 10`)}>
              <Database size={14} /> {table}
            </button>
          ))}
        </div>
      </section>
    </>
  );
}


// ============================================================
// INFRASTRUCTURE
// ============================================================

function InfrastructurePage({ health, databaseHealth, database }) {
  const services = [
    {
      name: "FastAPI Application",
      description: "Backend API service",
      status: health?.status,
      detail: health?.version || "Version unavailable",
      icon: Server
    },
    {
      name: "MySQL Database",
      description: "Business data storage",
      status: databaseHealth?.status,
      detail: databaseHealth?.mysql_version || "Version unavailable",
      icon: Database
    },
    {
      name: "Database Schema",
      description: "ShopFlow business tables",
      status: database?.total_tables ? "HEALTHY" : "UNKNOWN",
      detail: `${database?.total_tables || 0} tables detected`,
      icon: HardDrive
    }
  ];

  return (
    <>
      <SectionHeading
        eyebrow="SYSTEM OPERATIONS"
        title="Infrastructure"
        description="Monitor the availability of the application and database services."
      />
      <div className="service-grid">
        {services.map(service => {
          const Icon = service.icon;
          return (
            <div className="panel service-card" key={service.name}>
              <div className="service-icon"><Icon size={22} /></div>
              <div className="service-title">
                <h3>{service.name}</h3>
                <StatusBadge status={service.status} />
              </div>
              <p>{service.description}</p>
              <div className="service-detail">{service.detail}</div>
            </div>
          );
        })}
      </div>
      <section className="panel">
        <div className="panel-heading">
          <div><h3>Database Inventory</h3><p>Current table record counts</p></div>
        </div>
        <div className="table-count-list">
          {Object.entries(database?.tables || {}).map(([name, count]) => (
            <div className="table-count-row" key={name}>
              <div><Database size={15} /><span>{name}</span></div>
              <strong>{formatNumber(count)} records</strong>
            </div>
          ))}
        </div>
      </section>
      <div className="info-note">
        <Activity size={18} />
        <span>This workspace reports application and database connectivity. It does not yet report host CPU, RAM or disk utilization.</span>
      </div>
    </>
  );
}


// ============================================================
// BUSINESS INSIGHTS
// ============================================================

function InsightsPage({ insights }) {
  const orderStatuses = insights?.orders_by_status || [];
  const paymentStatuses = insights?.payments_by_status || [];

  const orderData = orderStatuses.map(item => ({
    name: item.order_status,
    orders: Number(item.order_count || 0),
    value: Number(item.order_value || 0)
  }));

  const paymentData = paymentStatuses.map(item => ({
    name: item.payment_status,
    count: Number(item.payment_count || 0),
    amount: Number(item.payment_amount || 0)
  }));

  const pieColors = ["#5798df", "#38b88b", "#e4a64f", "#a68bdf", "#e47777"];

  return (
    <>
      <SectionHeading
        eyebrow="BUSINESS ANALYTICS"
        title="Business Insights"
        description="Explore business metrics calculated directly from your ShopFlow MySQL tables."
      />

      <div className="metrics-grid">
        <MetricCard label="Total Orders" value={formatNumber(insights?.orders?.total_orders)} detail="Orders in database" icon={Boxes} />
        <MetricCard label="Total Customers" value={formatNumber(insights?.customers?.total_customers)} detail="Registered customers" icon={Activity} accent="green" />
        <MetricCard label="Total Products" value={formatNumber(insights?.products?.total_products)} detail="Products in catalog" icon={Database} accent="purple" />
        <MetricCard label="Average Order Value" value={`₹${formatNumber(insights?.orders?.average_order_value)}`} detail="Average order amount" icon={BarChart3} accent="orange" />
      </div>

      <div className="overview-grid">
        <section className="panel">
          <div className="panel-heading">
            <div><h3>Orders by Status</h3><p>Order count distribution</p></div>
            <BarChart3 size={18} />
          </div>
          {orderData.length ? (
            <div className="chart-area">
              <ResponsiveContainer width="100%" height={270}>
                <BarChart data={orderData}>
                  <CartesianGrid stroke="#202b3a" strokeDasharray="3 3" />
                  <XAxis dataKey="name" stroke="#718096" tick={{ fontSize: 11 }} />
                  <YAxis stroke="#718096" tick={{ fontSize: 11 }} />
                  <Tooltip contentStyle={{ background: "#111b29", border: "1px solid #29374a", borderRadius: 9 }} />
                  <Bar dataKey="orders" fill="#5798df" radius={[5, 5, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : <EmptyState />}
        </section>

        <section className="panel">
          <div className="panel-heading">
            <div><h3>Payments by Status</h3><p>Payment distribution</p></div>
            <Activity size={18} />
          </div>
          {paymentData.length ? (
            <div className="chart-area">
              <ResponsiveContainer width="100%" height={270}>
                <PieChart>
                  <Pie
                    data={paymentData}
                    dataKey="count"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    outerRadius={90}
                    innerRadius={52}
                    paddingAngle={3}
                  >
                    {paymentData.map((entry, index) => (
                      <Cell key={entry.name} fill={pieColors[index % pieColors.length]} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ background: "#111b29", border: "1px solid #29374a", borderRadius: 9 }} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          ) : <EmptyState />}
          <div className="chart-legend">
            {paymentData.map((item, index) => (
              <div key={item.name}>
                <span style={{ background: pieColors[index % pieColors.length] }} />
                {item.name}: {item.count}
              </div>
            ))}
          </div>
        </section>
      </div>

      <section className="panel">
        <div className="panel-heading">
          <div><h3>Order Status Breakdown</h3><p>Order volume and value by status</p></div>
        </div>
        {orderData.length ? (
          <div className="table-scroll">
            <table className="data-table">
              <thead>
                <tr><th>ORDER STATUS</th><th>ORDER COUNT</th><th>ORDER VALUE</th></tr>
              </thead>
              <tbody>
                {orderData.map(item => (
                  <tr key={item.name}>
                    <td>{item.name}</td>
                    <td>{formatNumber(item.orders)}</td>
                    <td>₹{formatNumber(item.value)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : <EmptyState />}
      </section>
    </>
  );
}

export default App;
