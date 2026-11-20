
import logging
import time

from shopflow.extract import extract_data
from shopflow.transform import transform_data
from shopflow.validate import run_all_validations
from shopflow.load import load_data
from shopflow.config import LOG_DIR

from shopflow.monitoring import (
    start_pipeline_run,
    start_stage,
    finish_stage,
    finish_pipeline_run
)


def setup_logging():
    """Configure logging to write pipeline activity to a file."""

    LOG_DIR.mkdir(parents=True, exist_ok=True)

    log_file = LOG_DIR / "pipeline.log"

    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        force=True
    )

    return logging.getLogger("ShopFlow")


def execute_stage(run_id, stage_name, operation, describe_result, logger):
    """Execute an ETL stage and record its status and duration."""

    stage_id, stage_started = start_stage(run_id, stage_name)

    try:
        result = operation()

        details = describe_result(result)

        finish_stage(
            stage_id,
            stage_started,
            status="SUCCESS",
            details=details
        )

        logger.info(
            "%s stage completed: %s",
            stage_name,
            details
        )

        return result

    except Exception as error:

        try:
            finish_stage(
                stage_id,
                stage_started,
                status="FAILED",
                error_message=str(error)
            )

        except Exception:
            logger.exception(
                "Failed to record stage failure: %s",
                stage_name
            )

        logger.exception("%s stage failed.", stage_name)

        raise


def validate_step(datasets):
    """Run all data quality validations."""

    validation_passed = run_all_validations(datasets)

    if not validation_passed:
        raise ValueError(
            "Data quality validation failed. Loading stopped."
        )

    return validation_passed


def run_pipeline():
    """Execute the complete ShopFlow ETL pipeline with monitoring."""

    logger = setup_logging()

    start_time = time.time()

    total_inserted = 0
    total_skipped = 0

    print("\n======================================")
    print("       SHOPFLOW ETL PIPELINE")
    print("======================================")

    # Create a new pipeline execution record.
    run_id, pipeline_started = start_pipeline_run()

    print("Run ID:", run_id)

    logger.info(
        "Pipeline execution started. Run ID: %s",
        run_id
    )

    try:

        # STEP 1: EXTRACT
        print("\n[1/4] Extracting raw datasets...")

        datasets = execute_stage(
            run_id,
            "EXTRACT",
            extract_data,
            lambda data: "; ".join(
                f"{name}: {df.shape[0]} rows, {df.shape[1]} columns"
                for name, df in data.items()
            ),
            logger
        )

        # STEP 2: TRANSFORM
        print("\n[2/4] Transforming datasets...")

        datasets = execute_stage(
            run_id,
            "TRANSFORM",
            lambda: transform_data(datasets),
            lambda data: (
                f"Successfully transformed {len(data)} datasets."
            ),
            logger
        )

        # STEP 3: VALIDATE
        print("\n[3/4] Running data quality checks...")

        execute_stage(
            run_id,
            "VALIDATE",
            lambda: validate_step(datasets),
            lambda result: "All data quality checks passed.",
            logger
        )

        # STEP 4: LOAD
        print("\n[4/4] Loading data into MySQL...")

        load_summary = execute_stage(
            run_id,
            "LOAD",
            lambda: load_data(datasets),
            lambda summary: (
                f"Successfully processed {len(summary)} tables."
            ),
            logger
        )

        # Calculate inserted and skipped records.
        total_inserted = sum(
            result["inserted"]
            for result in load_summary.values()
        )

        total_skipped = sum(
            result["skipped"]
            for result in load_summary.values()
        )

        duration = round(time.time() - start_time, 2)

        # Update overall pipeline execution.
        finish_pipeline_run(
            run_id,
            pipeline_started,
            status="SUCCESS",
            records_inserted=total_inserted,
            records_skipped=total_skipped
        )

        print("\n======================================")
        print("       PIPELINE COMPLETED")
        print("======================================")

        print("Status: SUCCESS")
        print("Run ID:", run_id)
        print("Records inserted:", total_inserted)
        print("Records skipped:", total_skipped)
        print("Execution time:", duration, "seconds")

        logger.info(
            "Pipeline completed successfully. "
            "Run ID=%s, Inserted=%s, Skipped=%s, Duration=%s seconds",
            run_id,
            total_inserted,
            total_skipped,
            duration
        )

        return {
            "run_id": run_id,
            "status": "SUCCESS",
            "inserted": total_inserted,
            "skipped": total_skipped,
            "duration_seconds": duration
        }

    except Exception as error:

        duration = round(time.time() - start_time, 2)

        print("\n======================================")
        print("       PIPELINE FAILED")
        print("======================================")

        print("Run ID:", run_id)
        print("Error:", error)
        print("Execution time:", duration, "seconds")

        logger.exception("Pipeline execution failed.")

        # Record the failed pipeline execution.
        try:
            finish_pipeline_run(
                run_id,
                pipeline_started,
                status="FAILED",
                records_inserted=total_inserted,
                records_skipped=total_skipped,
                error_message=str(error)
            )

        except Exception:
            logger.exception(
                "Failed to update pipeline execution history."
            )

        raise


if __name__ == "__main__":
    run_pipeline()
