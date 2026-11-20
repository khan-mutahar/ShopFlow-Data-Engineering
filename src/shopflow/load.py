
from decimal import Decimal
from datetime import date, datetime

from shopflow.db import get_connection, close_connection


TABLE_CONFIG = {
    "Customers": {
        "table": "customers",
        "columns": [
            "customer_id", "first_name", "last_name",
            "email", "phone", "city", "state",
            "country", "signup_date"
        ],
        "primary_key": "customer_id"
    },
    "Products": {
        "table": "products",
        "columns": [
            "product_id", "product_name", "category",
            "brand", "price", "cost", "stock_quantity"
        ],
        "primary_key": "product_id"
    },
    "Orders": {
        "table": "orders",
        "columns": [
            "order_id", "customer_id", "order_date",
            "order_status", "total_amount"
        ],
        "primary_key": "order_id"
    },
    "Order Items": {
        "table": "order_items",
        "columns": [
            "order_item_id", "order_id", "product_id",
            "quantity", "unit_price", "discount"
        ],
        "primary_key": "order_item_id"
    },
    "Payments": {
        "table": "payments",
        "columns": [
            "payment_id", "order_id", "payment_method",
            "amount", "payment_status", "payment_date"
        ],
        "primary_key": "payment_id"
    }
}


def normalize_value(value):
    """Normalize Python, Pandas and MySQL values for comparison."""

    if value is None:
        return None

    # Convert Pandas timestamps to Python datetime.
    if hasattr(value, "to_pydatetime"):
        value = value.to_pydatetime()

    # Treat midnight datetimes and SQL dates consistently.
    if isinstance(value, datetime):
        if value.time().isoformat() == "00:00:00":
            return value.date()
        return value

    if isinstance(value, date):
        return value

    # Convert NumPy scalar values to native Python values.
    if hasattr(value, "item"):
        value = value.item()

    # Compare decimal and floating-point values accurately.
    if isinstance(value, (float, int)) and not isinstance(value, bool):
        return Decimal(str(value))

    if isinstance(value, Decimal):
        return value

    return value


def prepare_records(df, columns):
    """Convert DataFrame rows into MySQL-compatible records."""

    selected_df = df[columns].copy()

    selected_df = selected_df.astype(object).where(
        selected_df.notna(), None
    )

    return list(
        selected_df.itertuples(index=False, name=None)
    )


def insert_dataset(cursor, dataset_name, df):
    """Skip matching records, insert new ones, reject conflicts."""

    config = TABLE_CONFIG[dataset_name]

    table = config["table"]
    columns = config["columns"]
    primary_key = config["primary_key"]

    records = prepare_records(df, columns)

    if not records:
        return {"inserted": 0, "skipped": 0}

    column_names = ", ".join(columns)
    value_placeholders = ", ".join(["%s"] * len(columns))

    select_query = (
        f"SELECT {column_names} FROM {table} "
        f"WHERE {primary_key} = %s"
    )

    insert_query = (
        f"INSERT INTO {table} ({column_names}) "
        f"VALUES ({value_placeholders})"
    )

    pk_index = columns.index(primary_key)

    new_records = []
    skipped = 0

    for record in records:
        record_id = record[pk_index]

        cursor.execute(select_query, (record_id,))
        existing_record = cursor.fetchone()

        if existing_record is None:
            new_records.append(record)
            continue

        incoming = tuple(
            normalize_value(value) for value in record
        )

        existing = tuple(
            normalize_value(value) for value in existing_record
        )

        if incoming == existing:
            skipped += 1
        else:
            raise ValueError(
                f"Data conflict in {table}: "
                f"{primary_key}={record_id}. "
                "Existing database data differs from incoming data."
            )

    if new_records:
        cursor.executemany(insert_query, new_records)

    inserted = len(new_records)

    print(
        f"{dataset_name}: "
        f"{inserted} inserted, {skipped} skipped."
    )

    return {
        "inserted": inserted,
        "skipped": skipped
    }


def load_data(datasets):
    """Load all datasets safely inside one transaction."""

    connection = None
    cursor = None

    try:
        print("\n========== SHOPFLOW MYSQL LOAD ==========")

        connection = get_connection()
        connection.start_transaction()

        cursor = connection.cursor()

        load_summary = {}

        # Parent tables first, followed by child tables.
        for dataset_name in TABLE_CONFIG:

            if dataset_name not in datasets:
                raise KeyError(
                    f"Missing dataset: {dataset_name}"
                )

            load_summary[dataset_name] = insert_dataset(
                cursor,
                dataset_name,
                datasets[dataset_name]
            )

        connection.commit()

        print("\n========== LOAD SUMMARY ==========")

        total_inserted = 0
        total_skipped = 0

        for name, result in load_summary.items():
            print(
                f"{name}: "
                f"Inserted={result['inserted']}, "
                f"Skipped={result['skipped']}"
            )

            total_inserted += result["inserted"]
            total_skipped += result["skipped"]

        print("\nTotal inserted:", total_inserted)
        print("Total skipped:", total_skipped)
        print("Database load completed successfully!")

        return load_summary

    except Exception as error:

        if connection and connection.is_connected():
            connection.rollback()

        print("\nDatabase load failed:", error)
        print("Transaction rolled back.")

        raise

    finally:

        if cursor:
            cursor.close()

        if connection:
            close_connection(connection)
