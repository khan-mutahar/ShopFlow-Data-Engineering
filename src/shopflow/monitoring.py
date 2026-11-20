
import uuid
from datetime import datetime

from shopflow.db import get_connection, close_connection


def create_monitoring_tables():
    """Create pipeline monitoring tables if they do not exist."""

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pipeline_runs (
                run_id VARCHAR(36) PRIMARY KEY,
                status VARCHAR(20) NOT NULL,
                started_at DATETIME(6) NOT NULL,
                finished_at DATETIME(6),
                duration_seconds DECIMAL(10,3),
                records_inserted INT DEFAULT 0,
                records_skipped INT DEFAULT 0,
                error_message TEXT,
                INDEX idx_pipeline_started (started_at),
                INDEX idx_pipeline_status (status)
            ) ENGINE=InnoDB
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pipeline_stage_runs (
                stage_id BIGINT AUTO_INCREMENT PRIMARY KEY,
                run_id VARCHAR(36) NOT NULL,
                stage_name VARCHAR(50) NOT NULL,
                status VARCHAR(20) NOT NULL,
                started_at DATETIME(6) NOT NULL,
                finished_at DATETIME(6),
                duration_seconds DECIMAL(10,3),
                details TEXT,
                error_message TEXT,

                CONSTRAINT fk_stage_pipeline
                    FOREIGN KEY (run_id)
                    REFERENCES pipeline_runs(run_id)
                    ON DELETE CASCADE,

                INDEX idx_stage_run (run_id)
            ) ENGINE=InnoDB
        """)

        connection.commit()

        print("Pipeline monitoring tables are ready.")

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        close_connection(connection)


def start_pipeline_run():
    """Create a new pipeline execution record."""

    run_id = str(uuid.uuid4())
    started_at = datetime.now()

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            INSERT INTO pipeline_runs (
                run_id,
                status,
                started_at
            )
            VALUES (%s, %s, %s)
        """, (
            run_id,
            "RUNNING",
            started_at
        ))

        connection.commit()

        return run_id, started_at

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        close_connection(connection)


def start_stage(run_id, stage_name):
    """Record the beginning of an ETL stage."""

    started_at = datetime.now()

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            INSERT INTO pipeline_stage_runs (
                run_id,
                stage_name,
                status,
                started_at
            )
            VALUES (%s, %s, %s, %s)
        """, (
            run_id,
            stage_name,
            "RUNNING",
            started_at
        ))

        stage_id = cursor.lastrowid

        connection.commit()

        return stage_id, started_at

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        close_connection(connection)


def finish_stage(
    stage_id,
    started_at,
    status,
    details=None,
    error_message=None
):
    """Save the result and duration of an ETL stage."""

    finished_at = datetime.now()

    duration = (
        finished_at - started_at
    ).total_seconds()

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            UPDATE pipeline_stage_runs
            SET
                status = %s,
                finished_at = %s,
                duration_seconds = %s,
                details = %s,
                error_message = %s
            WHERE stage_id = %s
        """, (
            status,
            finished_at,
            duration,
            details,
            error_message,
            stage_id
        ))

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        close_connection(connection)


def finish_pipeline_run(
    run_id,
    started_at,
    status,
    records_inserted=0,
    records_skipped=0,
    error_message=None
):
    """Save the final pipeline execution result."""

    finished_at = datetime.now()

    duration = (
        finished_at - started_at
    ).total_seconds()

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            UPDATE pipeline_runs
            SET
                status = %s,
                finished_at = %s,
                duration_seconds = %s,
                records_inserted = %s,
                records_skipped = %s,
                error_message = %s
            WHERE run_id = %s
        """, (
            status,
            finished_at,
            duration,
            records_inserted,
            records_skipped,
            error_message,
            run_id
        ))

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        close_connection(connection)
