
import pandas as pd
import mysql.connector
import os
from getpass import getpass


# =====================================================
# STEP 1: DATABASE CONFIGURATION
# =====================================================

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": os.getenv("MYSQL_PASSWORD") or getpass("Enter MySQL password: "),
    "database": "shopflow"
}


# =====================================================
# STEP 2: DATASET CONFIGURATION
# =====================================================

DATASETS = {
    "customers": {
        "file": "data/processed/customers.csv",
        "columns": [
            "customer_id", "first_name", "last_name",
            "email", "phone", "city", "state",
            "country", "signup_date"
        ]
    },

    "products": {
        "file": "data/processed/products.csv",
        "columns": [
            "product_id", "product_name", "category",
            "brand", "price", "cost", "stock_quantity"
        ]
    },

    "orders": {
        "file": "data/processed/orders.csv",
        "columns": [
            "order_id", "customer_id", "order_date",
            "order_status", "total_amount"
        ]
    },

    "order_items": {
        "file": "data/processed/order_items.csv",
        "columns": [
            "order_item_id", "order_id", "product_id",
            "quantity", "unit_price", "discount"
        ]
    },

    "payments": {
        "file": "data/processed/payments.csv",
        "columns": [
            "payment_id", "order_id", "payment_method",
            "amount", "payment_status", "payment_date"
        ]
    }
}


# =====================================================
# STEP 3: READ PROCESSED CSV FILES
# =====================================================

def read_datasets():

    datasets = {}

    print("\n========== READING CSV FILES ==========")

    for table_name, config in DATASETS.items():

        df = pd.read_csv(config["file"])

        # Check that all required columns exist
        missing_columns = set(config["columns"]) - set(df.columns)

        if missing_columns:
            raise ValueError(
                f"{table_name}: Missing columns {missing_columns}"
            )

        # Keep only the required columns in the correct order
        df = df[config["columns"]]

        datasets[table_name] = df

        print(
            f"{table_name}: {len(df)} records loaded from CSV"
        )

    return datasets


# =====================================================
# STEP 4: CONVERT PANDAS VALUES FOR MYSQL
# =====================================================

def convert_value(value):

    # Convert missing values into SQL NULL
    if pd.isna(value):
        return None

    # Convert Pandas timestamps into Python dates
    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime()

    # Convert NumPy values into native Python values
    if hasattr(value, "item"):
        value = value.item()

    return value


def prepare_records(df):

    records = []

    for row in df.itertuples(index=False, name=None):

        converted_row = tuple(
            convert_value(value) for value in row
        )

        records.append(converted_row)

    return records


# =====================================================
# STEP 5: INSERT DATA INTO MYSQL
# =====================================================

def insert_data(cursor, table_name, df, columns):

    placeholders = ", ".join(["%s"] * len(columns))

    column_names = ", ".join(columns)

    insert_query = f"""
        INSERT INTO {table_name} ({column_names})
        VALUES ({placeholders})
    """

    records = prepare_records(df)

    if records:
        cursor.executemany(insert_query, records)

    print(
        f"{table_name}: {len(records)} records inserted"
    )


# =====================================================
# STEP 6: CLEAR OLD DATA
# =====================================================

def clear_existing_data(cursor):

    print("\n========== CLEARING OLD DATA ==========")

    # Child tables must be cleared before parent tables
    deletion_order = [
        "order_items",
        "payments",
        "orders",
        "customers",
        "products"
    ]

    for table_name in deletion_order:

        cursor.execute(f"DELETE FROM {table_name}")

        print(f"{table_name}: Existing records cleared")


# =====================================================
# STEP 7: VERIFY MYSQL RECORD COUNTS
# =====================================================

def verify_data(cursor, datasets):

    print("\n========== MYSQL DATA VERIFICATION ==========")

    all_passed = True

    for table_name, df in datasets.items():

        cursor.execute(
            f"SELECT COUNT(*) FROM {table_name}"
        )

        actual_count = cursor.fetchone()[0]

        expected_count = len(df)

        if actual_count == expected_count:
            status = "PASSED"
        else:
            status = "FAILED"
            all_passed = False

        print(
            f"{table_name}: "
            f"CSV = {expected_count}, "
            f"MySQL = {actual_count} "
            f"--> {status}"
        )

    if not all_passed:
        raise ValueError("Record count verification failed!")

    print("\nAll five tables verified successfully!")


# =====================================================
# STEP 8: MAIN ETL LOAD FUNCTION
# =====================================================

def main():

    connection = None
    cursor = None

    try:

        print("\n======================================")
        print("       SHOPFLOW MYSQL LOADER")
        print("======================================")

        # Read all datasets
        datasets = read_datasets()

        # Connect to MySQL
        print("\nConnecting to MySQL...")

        connection = mysql.connector.connect(**DB_CONFIG)

        cursor = connection.cursor()

        print("Successfully connected to ShopFlow database!")

        # Start one transaction
        connection.start_transaction()

        # Remove old records
        clear_existing_data(cursor)

        print("\n========== INSERTING NEW DATA ==========")

        # Parent tables first, child tables afterwards
        loading_order = [
            "customers",
            "products",
            "orders",
            "order_items",
            "payments"
        ]

        for table_name in loading_order:

            insert_data(
                cursor,
                table_name,
                datasets[table_name],
                DATASETS[table_name]["columns"]
            )

        # Verify before committing
        verify_data(cursor, datasets)

        # Save all changes
        connection.commit()

        print("\n======================================")
        print("SHOPFLOW DATA LOADING COMPLETED!")
        print("All five datasets loaded successfully.")
        print("======================================")


    except Exception as error:

        if connection and connection.is_connected():

            connection.rollback()

            print("\nTransaction rolled back!")

        print("\nERROR:", error)


    finally:

        if cursor:
            cursor.close()

        if connection and connection.is_connected():

            connection.close()

            print("\nMySQL connection closed.")


# =====================================================
# STEP 9: EXECUTION STARTING POINT
# =====================================================

if __name__ == "__main__":
    main()
