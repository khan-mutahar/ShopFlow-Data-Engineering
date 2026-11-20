
/*
 * SHOPFLOW — PUBLIC DEMO API
 * -----------------------------------------
 * Uses local sample data instead of FastAPI/MySQL.
 * Original backend and ETL files remain untouched.
 */

const wait = (ms = 250) =>
  new Promise(resolve => setTimeout(resolve, ms));

const response = data => ({ data });

const tables = {
  customers: [
    { customer_id: 1, name: "Aarav Sharma", email: "aarav@example.com", city: "Bangalore", state: "Karnataka", signup_date: "2026-01-12" },
    { customer_id: 2, name: "Priya Nair", email: "priya@example.com", city: "Kochi", state: "Kerala", signup_date: "2026-02-03" },
    { customer_id: 3, name: "Rahul Verma", email: "rahul@example.com", city: "Delhi", state: "Delhi", signup_date: "2026-02-18" },
    { customer_id: 4, name: "Sara Khan", email: "sara@example.com", city: "Mumbai", state: "Maharashtra", signup_date: "2026-03-09" },
    { customer_id: 5, name: "Aditya Rao", email: "aditya@example.com", city: "Hyderabad", state: "Telangana", signup_date: "2026-03-21" }
  ],
  products: [
    { product_id: 101, product_name: "Wireless Headphones", category: "Electronics", price: 2499, stock: 45, supplier: "SoundTech" },
    { product_id: 102, product_name: "Mechanical Keyboard", category: "Electronics", price: 3499, stock: 28, supplier: "KeyWorks" },
    { product_id: 103, product_name: "Running Shoes", category: "Fashion", price: 1999, stock: 62, supplier: "ActiveWear" },
    { product_id: 104, product_name: "Smart Watch", category: "Electronics", price: 4999, stock: 19, supplier: "TechLife" },
    { product_id: 105, product_name: "Backpack", category: "Accessories", price: 1299, stock: 80, supplier: "CarryCo" }
  ],
  orders: [
    { order_id: 1001, customer_id: 1, order_date: "2026-10-02", total_amount: 2499, order_status: "DELIVERED" },
    { order_id: 1002, customer_id: 2, order_date: "2026-10-04", total_amount: 3499, order_status: "DELIVERED" },
    { order_id: 1003, customer_id: 3, order_date: "2026-10-08", total_amount: 1999, order_status: "SHIPPED" },
    { order_id: 1004, customer_id: 4, order_date: "2026-10-11", total_amount: 4999, order_status: "PROCESSING" },
    { order_id: 1005, customer_id: 5, order_date: "2026-10-15", total_amount: 1299, order_status: "DELIVERED" }
  ],
  order_items: [
    { item_id: 1, order_id: 1001, product_id: 101, quantity: 1, unit_price: 2499 },
    { item_id: 2, order_id: 1002, product_id: 102, quantity: 1, unit_price: 3499 },
    { item_id: 3, order_id: 1003, product_id: 103, quantity: 1, unit_price: 1999 },
    { item_id: 4, order_id: 1004, product_id: 104, quantity: 1, unit_price: 4999 },
    { item_id: 5, order_id: 1005, product_id: 105, quantity: 1, unit_price: 1299 }
  ],
  payments: [
    { payment_id: 501, order_id: 1001, payment_method: "UPI", payment_amount: 2499, payment_status: "SUCCESS" },
    { payment_id: 502, order_id: 1002, payment_method: "CARD", payment_amount: 3499, payment_status: "SUCCESS" },
    { payment_id: 503, order_id: 1003, payment_method: "UPI", payment_amount: 1999, payment_status: "SUCCESS" },
    { payment_id: 504, order_id: 1004, payment_method: "CARD", payment_amount: 4999, payment_status: "PENDING" },
    { payment_id: 505, order_id: 1005, payment_method: "COD", payment_amount: 1299, payment_status: "SUCCESS" }
  ]
};

const schemas = {
  customers: [
    ["customer_id", "int", "NO", "PRI"],
    ["name", "varchar", "NO", ""],
    ["email", "varchar", "NO", "UNI"],
    ["city", "varchar", "YES", ""],
    ["state", "varchar", "YES", ""],
    ["signup_date", "date", "YES", ""]
  ],
  products: [
    ["product_id", "int", "NO", "PRI"],
    ["product_name", "varchar", "NO", ""],
    ["category", "varchar", "YES", ""],
    ["price", "decimal", "NO", ""],
    ["stock", "int", "NO", ""],
    ["supplier", "varchar", "YES", ""]
  ],
  orders: [
    ["order_id", "int", "NO", "PRI"],
    ["customer_id", "int", "NO", "MUL"],
    ["order_date", "date", "NO", ""],
    ["total_amount", "decimal", "NO", ""],
    ["order_status", "varchar", "NO", ""]
  ],
  order_items: [
    ["item_id", "int", "NO", "PRI"],
    ["order_id", "int", "NO", "MUL"],
    ["product_id", "int", "NO", "MUL"],
    ["quantity", "int", "NO", ""],
    ["unit_price", "decimal", "NO", ""]
  ],
  payments: [
    ["payment_id", "int", "NO", "PRI"],
    ["order_id", "int", "NO", "MUL"],
    ["payment_method", "varchar", "NO", ""],
    ["payment_amount", "decimal", "NO", ""],
    ["payment_status", "varchar", "NO", ""]
  ]
};

const rowCounts = {
  customers: 10,
  products: 20,
  orders: 50,
  order_items: 154,
  payments: 50
};

const catalog = Object.keys(tables).map(table_name => ({
  table_name,
  actual_rows: rowCounts[table_name]
}));

const lineage = {
  nodes: [
    { id: "customers", label: "CUSTOMERS" },
    { id: "products", label: "PRODUCTS" },
    { id: "orders", label: "ORDERS" },
    { id: "order_items", label: "ORDER ITEMS" },
    { id: "payments", label: "PAYMENTS" }
  ],
  edges: [
    { id: "e1", source: "customers", target: "orders", label: "customer_id" },
    { id: "e2", source: "orders", target: "order_items", label: "order_id" },
    { id: "e3", source: "products", target: "order_items", label: "product_id" },
    { id: "e4", source: "orders", target: "payments", label: "order_id" }
  ]
};

const quality = {
  total_checks: 6,
  passed_checks: 6,
  failed_checks: 0,
  overall_status: "PASSED",
  results: [
    { check: "Primary Keys", status: "PASSED", passed: true },
    { check: "Foreign Keys", status: "PASSED", passed: true },
    { check: "Business Rules", status: "PASSED", passed: true },
    { check: "Product Prices", status: "PASSED", passed: true },
    { check: "Order Totals", status: "PASSED", passed: true },
    { check: "Payment Amounts", status: "PASSED", passed: true }
  ]
};

const insights = {
  orders: {
    total_orders: 50,
    average_order_value: 2859.5
  },
  customers: {
    total_customers: 10
  },
  products: {
    total_products: 20
  },
  orders_by_status: [
    { order_status: "DELIVERED", order_count: 28, order_value: 68000 },
    { order_status: "SHIPPED", order_count: 12, order_value: 32000 },
    { order_status: "PROCESSING", order_count: 7, order_value: 19000 },
    { order_status: "CANCELLED", order_count: 3, order_value: 7000 }
  ],
  payments_by_status: [
    { payment_status: "SUCCESS", payment_count: 42, payment_amount: 112000 },
    { payment_status: "PENDING", payment_count: 5, payment_amount: 14000 },
    { payment_status: "FAILED", payment_count: 3, payment_amount: 8000 }
  ]
};

let runs = [
  {
    run_id: "demo-run-2026-001",
    status: "SUCCESS",
    started_at: "2026-11-20T09:30:00",
    duration_seconds: 0.42,
    records_inserted: 0,
    records_skipped: 284
  },
  {
    run_id: "demo-run-2026-002",
    status: "SUCCESS",
    started_at: "2026-11-19T15:42:00",
    duration_seconds: 0.51,
    records_inserted: 12,
    records_skipped: 272
  },
  {
    run_id: "demo-run-2026-003",
    status: "SUCCESS",
    started_at: "2026-11-19T11:15:00",
    duration_seconds: 0.39,
    records_inserted: 0,
    records_skipped: 284
  },
  {
    run_id: "demo-run-2026-004",
    status: "SUCCESS",
    started_at: "2026-11-18T17:20:00",
    duration_seconds: 0.46,
    records_inserted: 5,
    records_skipped: 279
  },
  {
    run_id: "demo-run-2026-005",
    status: "SUCCESS",
    started_at: "2026-11-18T10:05:00",
    duration_seconds: 0.44,
    records_inserted: 0,
    records_skipped: 284
  }
];

const stagesFor = runId => [
  { stage_id: `${runId}-1`, stage_name: "EXTRACT", status: "SUCCESS", duration_seconds: 0.08, started_at: "2026-11-20T09:30:00" },
  { stage_id: `${runId}-2`, stage_name: "TRANSFORM", status: "SUCCESS", duration_seconds: 0.12, started_at: "2026-11-20T09:30:01" },
  { stage_id: `${runId}-3`, stage_name: "VALIDATE", status: "SUCCESS", duration_seconds: 0.09, started_at: "2026-11-20T09:30:01" },
  { stage_id: `${runId}-4`, stage_name: "LOAD", status: "SUCCESS", duration_seconds: 0.13, started_at: "2026-11-20T09:30:02" }
];

const totalRuns = () => runs.length;

const pipelineOverview = () => ({
  total_runs: runs.length,
  successful_runs: runs.filter(run => run.status === "SUCCESS").length,
  failed_runs: runs.filter(run => run.status === "FAILED").length,
  average_duration: runs.length
    ? runs.reduce((sum, run) => sum + Number(run.duration_seconds), 0) / runs.length
    : 0
});

const databaseSummary = {
  total_tables: 5,
  total_records: 284,
  tables: rowCounts
};

const tableDetail = tableName => {
  const rows = tables[tableName] || [];
  return {
    table_name: tableName,
    columns: (schemas[tableName] || []).map(([column_name, data_type, is_nullable, column_key]) => ({
      column_name,
      data_type,
      is_nullable,
      column_key
    })),
    preview: rows,
    returned_rows: rows.length
  };
};

// -----------------------------------------
// HEALTH & DATABASE
// -----------------------------------------

export const getHealth = async () => {
  await wait();
  return response({
    status: "HEALTHY",
    application: "ShopFlow",
    version: "2.0.0-demo"
  });
};

export const getDatabaseHealth = async () => {
  await wait();
  return response({
    status: "CONNECTED",
    mysql_version: "8.0 — Demo dataset"
  });
};

export const getDatabaseSummary = async () => {
  await wait();
  return response(databaseSummary);
};

// -----------------------------------------
// CATALOG
// -----------------------------------------

export const getCatalog = async () => {
  await wait();
  return response({ tables: catalog });
};

export const getCatalogTable = async tableName => {
  await wait();
  if (!tables[tableName]) {
    throw { response: { data: { detail: "Table not found." } } };
  }
  return response(tableDetail(tableName));
};

// -----------------------------------------
// LINEAGE & QUALITY
// -----------------------------------------

export const getLineage = async () => {
  await wait();
  return response(lineage);
};

export const getDataQuality = async () => {
  await wait();
  return response(quality);
};

// -----------------------------------------
// PIPELINE MONITORING
// -----------------------------------------

export const getPipelineOverview = async () => {
  await wait();
  return response(pipelineOverview());
};

export const getPipelineRuns = async (limit = 20) => {
  await wait();
  return response({ runs: runs.slice(0, limit) });
};

export const getPipelineStages = async runId => {
  await wait();
  return response({ stages: stagesFor(runId) });
};

export const runPipeline = async () => {
  await wait(900);

  const runId = `demo-${Date.now()}`;

  const newRun = {
    run_id: runId,
    status: "SUCCESS",
    started_at: new Date().toISOString(),
    duration_seconds: 0.43,
    records_inserted: 0,
    records_skipped: 284
  };

  runs = [newRun, ...runs].slice(0, 20);

  return response({
    run_id: runId,
    status: "SUCCESS",
    records_inserted: 0,
    records_skipped: 284,
    duration_seconds: 0.43,
    demo: true
  });
};

// -----------------------------------------
// BUSINESS INSIGHTS
// -----------------------------------------

export const getBusinessInsights = async () => {
  await wait();
  return response(insights);
};

// -----------------------------------------
// READ-ONLY DEMO SQL
// -----------------------------------------

export const executeSqlQuery = async query => {
  await wait(350);

  const normalized = String(query || "").trim();

  if (!/^(SELECT|WITH)\b/i.test(normalized)) {
    throw {
      response: {
        data: { detail: "Demo SQL Lab only supports SELECT queries." }
      }
    };
  }

  if (/[;]/.test(normalized) || /(--|\/\*|\*\/)/.test(normalized)) {
    throw {
      response: {
        data: { detail: "Multiple statements and SQL comments are not allowed." }
      }
    };
  }

  const match = normalized.match(/\bFROM\s+`?([a-z_]+)`?/i);
  if (!match) {
    throw {
      response: {
        data: { detail: "Use SELECT with one of the available ShopFlow tables." }
      }
    };
  }

  const tableName = match[1].toLowerCase();

  if (!tables[tableName]) {
    throw {
      response: {
        data: { detail: `Unknown demo table: ${tableName}` }
      }
    };
  }

  const limitMatch = normalized.match(/\bLIMIT\s+(\d+)/i);
  const limit = Math.min(Number(limitMatch?.[1] || 20), 200);
  const sourceRows = tables[tableName];
  const selectedRows = sourceRows.slice(0, limit);

  let columns = Object.keys(sourceRows[0] || {});
  const selectMatch = normalized.match(/^\s*SELECT\s+(.+?)\s+FROM\b/i);

  if (selectMatch && selectMatch[1].trim() !== "*") {
    columns = selectMatch[1]
      .split(",")
      .map(column => column.trim().replace(/`/g, ""))
      .filter(column => columns.includes(column));

    if (!columns.length) {
      throw {
        response: {
          data: { detail: "No matching columns found in the selected table." }
        }
      };
    }
  }

  const rows = selectedRows.map(row =>
    Object.fromEntries(columns.map(column => [column, row[column]]))
  );

  return response({
    columns,
    rows,
    returned_rows: rows.length,
    truncated: sourceRows.length > rows.length,
    demo: true
  });
};

// -----------------------------------------
// AXIOS COMPATIBILITY
// -----------------------------------------

const api = {
  getHealth,
  getDatabaseHealth,
  getDatabaseSummary,
  getCatalog,
  getCatalogTable,
  getLineage,
  getDataQuality,
  getPipelineOverview,
  getPipelineRuns,
  getPipelineStages,
  runPipeline,
  getBusinessInsights,
  executeSqlQuery
};

export default api;
