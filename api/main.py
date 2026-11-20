
import os
import re
import threading
from decimal import Decimal
from datetime import date, datetime
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from shopflow.db import get_connection, close_connection
from shopflow.pipeline import run_pipeline
from shopflow.extract import extract_data
from shopflow.transform import transform_data
from shopflow.validate import (
    validate_primary_keys,
    validate_foreign_keys,
    validate_business_rules,
    validate_product_prices,
    validate_order_totals,
    validate_payment_amounts,
)


# ============================================================
# CONFIGURATION
# ============================================================

APP_ENV = os.getenv("SHOPFLOW_ENV", "development").lower()

# Pipeline execution is allowed locally, but disabled by default
# in production so a public demo cannot trigger repeated ETL runs.
ALLOW_PIPELINE_RUN = os.getenv(
    "SHOPFLOW_ALLOW_PIPELINE_RUN",
    "false" if APP_ENV == "production" else "true"
).lower() == "true"

TABLES = [
    "customers",
    "products",
    "orders",
    "order_items",
    "payments",
]

PIPELINE_LOCK = threading.Lock()

app = FastAPI(
    title="ShopFlow API",
    description="API for the ShopFlow Data Engineering Platform",
    version="2.0.0",
)

allowed_origins = [
    origin.strip()
    for origin in os.getenv(
        "SHOPFLOW_CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173"
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


# ============================================================
# HELPERS
# ============================================================

def serialize(value: Any):
    """Convert MySQL and Python values into JSON-safe values."""

    if isinstance(value, dict):
        return {key: serialize(item) for key, item in value.items()}

    if isinstance(value, list):
        return [serialize(item) for item in value]

    if isinstance(value, (datetime, date)):
        return value.isoformat()

    if isinstance(value, Decimal):
        return float(value)

    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")

    return value


def get_db_cursor(dictionary=True):
    """Create a database connection and cursor."""

    connection = get_connection()
    cursor = connection.cursor(dictionary=dictionary)

    return connection, cursor


def close_db(connection, cursor):
    """Close database resources safely."""

    if cursor:
        cursor.close()

    if connection:
        close_connection(connection)


def database_error():
    """Return a generic error without exposing database credentials."""

    raise HTTPException(
        status_code=503,
        detail="Database operation failed. Check the backend configuration."
    )


def get_table_count(cursor, table_name):
    """Count rows in an allowlisted business table."""

    if table_name not in TABLES:
        raise ValueError("Invalid table name")

    cursor.execute(f"SELECT COUNT(*) AS total FROM `{table_name}`")
    return cursor.fetchone()["total"]


# ============================================================
# 1. APPLICATION HEALTH
# ============================================================

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "application": "ShopFlow",
        "version": "2.0.0",
        "environment": APP_ENV,
    }


# ============================================================
# 2. DATABASE HEALTH
# ============================================================

@app.get("/api/database/health")
def database_health():
    connection = None
    cursor = None

    try:
        connection, cursor = get_db_cursor()

        cursor.execute("SELECT VERSION() AS version")
        result = cursor.fetchone()

        return {
            "status": "connected",
            "database": "shopflow",
            "mysql_version": result["version"],
        }

    except Exception:
        database_error()

    finally:
        close_db(connection, cursor)


# ============================================================
# 3. DATABASE SUMMARY
# ============================================================

@app.get("/api/database/summary")
def database_summary():
    connection = None
    cursor = None

    try:
        connection, cursor = get_db_cursor()

        table_counts = {
            table: get_table_count(cursor, table)
            for table in TABLES
        }

        return {
            "status": "success",
            "total_tables": len(TABLES),
            "total_records": sum(table_counts.values()),
            "tables": table_counts,
        }

    except Exception:
        database_error()

    finally:
        close_db(connection, cursor)


# ============================================================
# 4. DATA CATALOG
# ============================================================

@app.get("/api/catalog")
def data_catalog():
    connection = None
    cursor = None

    try:
        connection, cursor = get_db_cursor()

        cursor.execute("""
            SELECT
                TABLE_NAME AS table_name,
                TABLE_ROWS AS estimated_rows,
                ENGINE AS engine
            FROM information_schema.TABLES
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME IN (
                  'customers',
                  'products',
                  'orders',
                  'order_items',
                  'payments'
              )
            ORDER BY TABLE_NAME
        """)

        tables = cursor.fetchall()

        for table in tables:
            table["actual_rows"] = get_table_count(
                cursor,
                table["table_name"]
            )

        return {
            "total_tables": len(tables),
            "tables": serialize(tables),
        }

    except Exception:
        database_error()

    finally:
        close_db(connection, cursor)


@app.get("/api/catalog/{table_name}")
def catalog_table(
    table_name: str,
    limit: int = Query(default=10, ge=1, le=100),
):
    if table_name not in TABLES:
        raise HTTPException(status_code=404, detail="Table not found")

    connection = None
    cursor = None

    try:
        connection, cursor = get_db_cursor()

        cursor.execute("""
            SELECT
                COLUMN_NAME AS column_name,
                DATA_TYPE AS data_type,
                IS_NULLABLE AS is_nullable,
                COLUMN_KEY AS column_key
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = %s
            ORDER BY ORDINAL_POSITION
        """, (table_name,))

        columns = cursor.fetchall()

        cursor.execute(
            f"SELECT * FROM `{table_name}` LIMIT %s",
            (limit,)
        )

        rows = cursor.fetchall()

        return {
            "table_name": table_name,
            "columns": serialize(columns),
            "preview": serialize(rows),
            "returned_rows": len(rows),
        }

    except Exception:
        database_error()

    finally:
        close_db(connection, cursor)


# ============================================================
# 5. DATA LINEAGE
# ============================================================

@app.get("/api/lineage")
def data_lineage():
    """Return the relationships defined in the ShopFlow schema."""

    return {
        "nodes": [
            {"id": "customers", "label": "Customers"},
            {"id": "products", "label": "Products"},
            {"id": "orders", "label": "Orders"},
            {"id": "order_items", "label": "Order Items"},
            {"id": "payments", "label": "Payments"},
        ],
        "edges": [
            {
                "id": "customers-orders",
                "source": "customers",
                "target": "orders",
                "label": "customer_id",
            },
            {
                "id": "orders-order-items",
                "source": "orders",
                "target": "order_items",
                "label": "order_id",
            },
            {
                "id": "products-order-items",
                "source": "products",
                "target": "order_items",
                "label": "product_id",
            },
            {
                "id": "orders-payments",
                "source": "orders",
                "target": "payments",
                "label": "order_id",
            },
        ],
    }


# ============================================================
# 6. DATA QUALITY
# ============================================================

@app.get("/api/quality")
def data_quality():
    """Run the six existing validation functions on current raw data."""

    try:
        datasets = extract_data()
        datasets = transform_data(datasets)

        checks = [
            ("Primary Keys", validate_primary_keys),
            ("Foreign Keys", validate_foreign_keys),
            ("Business Rules", validate_business_rules),
            ("Product Prices", validate_product_prices),
            ("Order Totals", validate_order_totals),
            ("Payment Amounts", validate_payment_amounts),
        ]

        results = []

        for name, validation_function in checks:
            passed = validation_function(datasets)

            results.append({
                "check": name,
                "status": "PASSED" if passed else "FAILED",
                "passed": bool(passed),
            })

        passed_count = sum(
            1 for result in results if result["passed"]
        )

        return {
            "total_checks": len(results),
            "passed_checks": passed_count,
            "failed_checks": len(results) - passed_count,
            "overall_status": (
                "PASSED" if passed_count == len(results) else "FAILED"
            ),
            "results": results,
        }

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to run data quality checks. Check the ETL data files."
        )


# ============================================================
# 7. PIPELINE OVERVIEW
# ============================================================

@app.get("/api/pipeline/overview")
def pipeline_overview():
    connection = None
    cursor = None

    try:
        connection, cursor = get_db_cursor()

        cursor.execute("""
            SELECT
                COUNT(*) AS total_runs,
                COALESCE(SUM(status = 'SUCCESS'), 0) AS successful_runs,
                COALESCE(SUM(status = 'FAILED'), 0) AS failed_runs,
                COALESCE(SUM(status = 'RUNNING'), 0) AS running_runs,
                COALESCE(AVG(duration_seconds), 0) AS average_duration,
                COALESCE(SUM(records_inserted), 0) AS total_inserted,
                COALESCE(SUM(records_skipped), 0) AS total_skipped
            FROM pipeline_runs
        """)

        return serialize(cursor.fetchone())

    except Exception:
        database_error()

    finally:
        close_db(connection, cursor)


# ============================================================
# 8. PIPELINE RUN HISTORY
# ============================================================

@app.get("/api/pipeline/runs")
def pipeline_runs(
    limit: int = Query(default=20, ge=1, le=100)
):
    connection = None
    cursor = None

    try:
        connection, cursor = get_db_cursor()

        cursor.execute("""
            SELECT
                run_id,
                status,
                started_at,
                finished_at,
                duration_seconds,
                records_inserted,
                records_skipped,
                error_message
            FROM pipeline_runs
            ORDER BY started_at DESC
            LIMIT %s
        """, (limit,))

        runs = cursor.fetchall()

        return {
            "total_returned": len(runs),
            "runs": serialize(runs),
        }

    except Exception:
        database_error()

    finally:
        close_db(connection, cursor)


# ============================================================
# 9. PIPELINE STAGE HISTORY
# ============================================================

@app.get("/api/pipeline/runs/{run_id}/stages")
def pipeline_stages(run_id: str):
    connection = None
    cursor = None

    try:
        connection, cursor = get_db_cursor()

        cursor.execute("""
            SELECT run_id
            FROM pipeline_runs
            WHERE run_id = %s
        """, (run_id,))

        if not cursor.fetchone():
            raise HTTPException(
                status_code=404,
                detail="Pipeline run not found"
            )

        cursor.execute("""
            SELECT
                stage_id,
                run_id,
                stage_name,
                status,
                started_at,
                finished_at,
                duration_seconds,
                details,
                error_message
            FROM pipeline_stage_runs
            WHERE run_id = %s
            ORDER BY stage_id ASC
        """, (run_id,))

        stages = cursor.fetchall()

        return {
            "run_id": run_id,
            "total_stages": len(stages),
            "stages": serialize(stages),
        }

    except HTTPException:
        raise

    except Exception:
        database_error()

    finally:
        close_db(connection, cursor)


# ============================================================
# 10. EXECUTE PIPELINE
# ============================================================

@app.post("/api/pipeline/run")
def execute_pipeline():
    if not ALLOW_PIPELINE_RUN:
        raise HTTPException(
            status_code=403,
            detail="Pipeline execution is disabled in the public demo."
        )

    if not PIPELINE_LOCK.acquire(blocking=False):
        raise HTTPException(
            status_code=409,
            detail="A pipeline execution is already in progress."
        )

    try:
        result = run_pipeline()

        return {
            "message": "Pipeline execution completed",
            "result": serialize(result),
        }

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Pipeline execution failed. Check backend logs."
        )

    finally:
        PIPELINE_LOCK.release()


# ============================================================
# 11. BUSINESS INSIGHTS
# ============================================================

@app.get("/api/insights/overview")
def business_insights():
    connection = None
    cursor = None

    try:
        connection, cursor = get_db_cursor()

        cursor.execute("""
            SELECT
                COUNT(*) AS total_orders,
                COALESCE(SUM(total_amount), 0) AS total_order_value,
                COALESCE(AVG(total_amount), 0) AS average_order_value
            FROM orders
        """)
        order_metrics = cursor.fetchone()

        cursor.execute("""
            SELECT
                COUNT(*) AS total_customers
            FROM customers
        """)
        customer_metrics = cursor.fetchone()

        cursor.execute("""
            SELECT
                COUNT(*) AS total_products,
                COALESCE(SUM(stock_quantity), 0) AS total_stock
            FROM products
        """)
        product_metrics = cursor.fetchone()

        cursor.execute("""
            SELECT
                payment_status,
                COUNT(*) AS payment_count,
                COALESCE(SUM(amount), 0) AS payment_amount
            FROM payments
            GROUP BY payment_status
            ORDER BY payment_status
        """)
        payment_metrics = cursor.fetchall()

        cursor.execute("""
            SELECT
                order_status,
                COUNT(*) AS order_count,
                COALESCE(SUM(total_amount), 0) AS order_value
            FROM orders
            GROUP BY order_status
            ORDER BY order_status
        """)
        order_status_metrics = cursor.fetchall()

        return serialize({
            "orders": order_metrics,
            "customers": customer_metrics,
            "products": product_metrics,
            "payments_by_status": payment_metrics,
            "orders_by_status": order_status_metrics,
        })

    except Exception:
        database_error()

    finally:
        close_db(connection, cursor)


# ============================================================
# 12. READ-ONLY SQL LAB
# ============================================================

class SQLRequest(BaseModel):
    query: str = Field(min_length=1, max_length=5000)


@app.post("/api/sql/query")
def execute_read_only_query(request: SQLRequest):
    query = request.query.strip()

    # Only one SELECT or WITH statement is accepted.
    if not re.match(r"^(SELECT|WITH)\b", query, re.IGNORECASE):
        raise HTTPException(
            status_code=400,
            detail="Only SELECT queries are allowed."
        )

    # Reject multiple statements and SQL comments.
    if ";" in query or "--" in query or "/*" in query or "*/" in query:
        raise HTTPException(
            status_code=400,
            detail="Multiple statements and SQL comments are not allowed."
        )

    forbidden = re.compile(
        r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|"
        r"REPLACE|RENAME|GRANT|REVOKE|CALL|EXECUTE|"
        r"INTO\s+OUTFILE|INTO\s+DUMPFILE|LOAD_FILE|"
        r"FOR\s+UPDATE|LOCK\s+IN\s+SHARE\s+MODE|"
        r"SLEEP|BENCHMARK)\b",
        re.IGNORECASE,
    )

    if forbidden.search(query):
        raise HTTPException(
            status_code=400,
            detail="This SQL operation is not permitted in the demo."
        )

    if "@" in query:
        raise HTTPException(
            status_code=400,
            detail="SQL session variables are not allowed."
        )

    # Add a row limit when the user has not supplied one.
    if not re.search(r"\bLIMIT\b", query, re.IGNORECASE):
        query = f"{query} LIMIT 200"

    connection = None
    cursor = None

    try:
        connection, cursor = get_db_cursor()

        cursor.execute("SET SESSION MAX_EXECUTION_TIME = 5000")
        cursor.execute(query)

        if cursor.description is None:
            raise HTTPException(
                status_code=400,
                detail="The query did not return a result set."
            )

        rows = cursor.fetchmany(201)
        columns = [column[0] for column in cursor.description]

        return {
            "columns": columns,
            "rows": serialize(rows[:200]),
            "returned_rows": min(len(rows), 200),
            "truncated": len(rows) > 200,
        }

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=400,
            detail="SQL query failed. Check the query and table names."
        )

    finally:
        close_db(connection, cursor)


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "application": "ShopFlow",
        "message": "ShopFlow API is running",
        "documentation": "/docs",
    }
