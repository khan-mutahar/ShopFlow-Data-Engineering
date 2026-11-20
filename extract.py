
import os
import pandas as pd


# ============================================================
# STEP 1: EXTRACT DATA
# ============================================================

def extract_data():

    customers = pd.read_csv("data/raw/customers.csv")
    products = pd.read_csv("data/raw/products.csv")
    orders = pd.read_csv("data/raw/orders.csv")
    order_items = pd.read_csv("data/raw/order_items.csv")
    payments = pd.read_csv("data/raw/payments.csv")

    print("\nAll five datasets extracted successfully!")

    return customers, products, orders, order_items, payments


# ============================================================
# STEP 2: CREATE DATASET COLLECTION
# ============================================================

def create_datasets(customers, products, orders, order_items, payments):

    datasets = {
        "Customers": customers,
        "Products": products,
        "Orders": orders,
        "Order Items": order_items,
        "Payments": payments
    }

    return datasets


# ============================================================
# STEP 3: DATA PROFILING
# ============================================================

def profile_data(datasets):

    for name, df in datasets.items():

        print("\n==============================")
        print(f"DATASET: {name}")
        print("==============================")

        print("\nFirst 5 Rows:")
        print(df.head())

        print("\nShape (Rows, Columns):")
        print(df.shape)

        print("\nColumn Names:")
        print(df.columns.tolist())

        print("\nData Types:")
        print(df.dtypes)

        print("\nMissing Values:")
        print(df.isnull().sum())

        print("\nDuplicate Rows:")
        print(df.duplicated().sum())


# ============================================================
# STEP 4: DATA TRANSFORMATION
# ============================================================

def transform_data(customers, products, orders, payments):

    # Convert date columns
    customers["signup_date"] = pd.to_datetime(customers["signup_date"])
    orders["order_date"] = pd.to_datetime(orders["order_date"])
    payments["payment_date"] = pd.to_datetime(payments["payment_date"])

    # Standardise text columns
    customers["city"] = customers["city"].str.strip().str.title()
    customers["state"] = customers["state"].str.strip().str.title()

    products["category"] = products["category"].str.strip().str.title()

    orders["order_status"] = orders["order_status"].str.strip().str.title()

    payments["payment_method"] = payments["payment_method"].str.strip().str.title()
    payments["payment_status"] = payments["payment_status"].str.strip().str.title()

    print("\nData transformation completed successfully!")

    return customers, products, orders, payments


# ============================================================
# STEP 5: VERIFY TRANSFORMATIONS
# ============================================================

def verify_transformations(datasets):

    print("\n========== TRANSFORMED DATA TYPES ==========")

    for name, df in datasets.items():

        print(f"\n{name}")
        print(df.dtypes)


# ============================================================
# STEP 6: PRIMARY KEY VALIDATION
# ============================================================

def validate_primary_keys(datasets):

    primary_keys = {
        "Customers": (datasets["Customers"], "customer_id"),
        "Products": (datasets["Products"], "product_id"),
        "Orders": (datasets["Orders"], "order_id"),
        "Order Items": (datasets["Order Items"], "order_item_id"),
        "Payments": (datasets["Payments"], "payment_id")
    }

    print("\n========== PRIMARY KEY VALIDATION ==========")

    for name, (df, key) in primary_keys.items():

        duplicate_count = df[key].duplicated().sum()
        missing_count = df[key].isnull().sum()

        print(f"\nDataset: {name}")
        print(f"Primary Key: {key}")
        print(f"Duplicate IDs: {duplicate_count}")
        print(f"Missing IDs: {missing_count}")

        if duplicate_count == 0 and missing_count == 0:
            print("Status: PASSED")
        else:
            print("Status: FAILED")


# ============================================================
# STEP 7: FOREIGN KEY VALIDATION
# ============================================================

def validate_foreign_keys(customers, products, orders, order_items, payments):

    foreign_keys = [
        ("Orders", orders, "customer_id", customers, "customer_id"),
        ("Order Items", order_items, "order_id", orders, "order_id"),
        ("Order Items", order_items, "product_id", products, "product_id"),
        ("Payments", payments, "order_id", orders, "order_id")
    ]

    print("\n========== FOREIGN KEY VALIDATION ==========")

    for child_name, child_df, fk, parent_df, pk in foreign_keys:

        invalid_values = child_df[
            ~child_df[fk].isin(parent_df[pk])
        ]

        invalid_count = len(invalid_values)

        print(f"\nDataset: {child_name}")
        print(f"Foreign Key: {fk}")
        print(f"Invalid References: {invalid_count}")

        if invalid_count == 0:
            print("Status: PASSED")
        else:
            print("Status: FAILED")


# ============================================================
# STEP 8: BUSINESS RULE VALIDATION
# ============================================================

def validate_business_rules(products, order_items, payments):

    print("\n========== BUSINESS RULE VALIDATION ==========")

    # Product validation
    invalid_products = products[
        (products["price"] < 0) |
        (products["cost"] < 0) |
        (products["stock_quantity"] < 0)
    ]

    # Order item validation
    invalid_order_items = order_items[
        (order_items["quantity"] <= 0) |
        (order_items["unit_price"] < 0) |
        (order_items["discount"] < 0) |
        (order_items["discount"] > 100)
    ]

    # Payment validation
    invalid_payments = payments[
        payments["amount"] < 0
    ]

    print("Invalid Products:", len(invalid_products))
    print("Invalid Order Items:", len(invalid_order_items))
    print("Invalid Payments:", len(invalid_payments))


# ============================================================
# STEP 9: PRODUCT PRICE VALIDATION
# ============================================================

def validate_product_prices(order_items, products):

    print("\n========== PRODUCT PRICE VALIDATION ==========")

    product_price_check = order_items.merge(
        products[["product_id", "price"]],
        on="product_id",
        how="left"
    )

    product_price_check["price_difference"] = (
        product_price_check["unit_price"] -
        product_price_check["price"]
    )

    mismatched_prices = product_price_check[
        product_price_check["price_difference"] != 0
    ]

    print("Total Order Items:", len(order_items))
    print("Price Mismatches:", len(mismatched_prices))

    print(
        mismatched_prices[
            ["product_id", "unit_price", "price"]
        ].head(10)
    )


# ============================================================
# STEP 10: ORDER TOTAL VALIDATION
# ============================================================

def validate_order_totals(orders, order_items):

    # Calculate total for each order item
    order_items["line_total"] = (
        order_items["quantity"] *
        order_items["unit_price"] *
        (1 - order_items["discount"] / 100)
    )

    # Calculate total amount for each order
    calculated_totals = (
        order_items.groupby("order_id")["line_total"]
        .sum()
        .reset_index()
    )

    # Compare calculated totals with orders.csv
    order_total_check = orders.merge(
        calculated_totals,
        on="order_id",
        how="left"
    )

    order_total_check["difference"] = (
        order_total_check["total_amount"] -
        order_total_check["line_total"]
    )

    mismatched_orders = order_total_check[
        order_total_check["difference"].abs() > 0.01
    ]

    print("\n========== ORDER TOTAL VALIDATION ==========")
    print("Total Orders:", len(orders))
    print("Mismatched Orders:", len(mismatched_orders))

    print(
        mismatched_orders[
            ["order_id", "total_amount", "line_total", "difference"]
        ].head(10)
    )


# ============================================================
# STEP 11: PAYMENT AMOUNT VALIDATION
# ============================================================

def validate_payment_amounts(payments, orders):

    payment_check = payments.merge(
        orders[["order_id", "total_amount"]],
        on="order_id",
        how="left"
    )

    payment_check["difference"] = (
        payment_check["amount"] - payment_check["total_amount"]
    )

    mismatched_payments = payment_check[
        payment_check["difference"].abs() > 0.01
    ]

    print("\n========== PAYMENT VALIDATION ==========")
    print("Total Payments:", len(payments))
    print("Mismatched Payments:", len(mismatched_payments))

    print(
        mismatched_payments[
            ["order_id", "amount", "total_amount", "difference"]
        ].head(10)
    )


# ============================================================
# STEP 12: LOAD PROCESSED DATA
# ============================================================

def load_data(datasets):

    os.makedirs("data/processed", exist_ok=True)

    processed_files = {
        "Customers": "data/processed/customers.csv",
        "Products": "data/processed/products.csv",
        "Orders": "data/processed/orders.csv",
        "Order Items": "data/processed/order_items.csv",
        "Payments": "data/processed/payments.csv"
    }

    for name, file_path in processed_files.items():

        datasets[name].to_csv(file_path, index=False)

    print("\n========== DATA LOADING ==========")
    print("All five processed datasets saved successfully!")

    return processed_files


# ============================================================
# STEP 13: PROCESSED DATA VERIFICATION
# ============================================================

def verify_processed_data(datasets, processed_files):

    print("\n========== PROCESSED DATA VERIFICATION ==========")

    for name, file_path in processed_files.items():

        processed_df = pd.read_csv(file_path)
        original_df = datasets[name]

        print(f"\nDataset: {name}")
        print("Original Rows:", len(original_df))
        print("Processed Rows:", len(processed_df))

        if (
            len(original_df) == len(processed_df)
            and list(original_df.columns) == list(processed_df.columns)
        ):
            print("Verification: PASSED")
        else:
            print("Verification: FAILED")


# ============================================================
# STEP 14: MAIN PIPELINE EXECUTION
# ============================================================

def main():

    print("\n========================================")
    print("       SHOPFLOW ETL PIPELINE STARTED")
    print("========================================")

    # Extract
    customers, products, orders, order_items, payments = extract_data()

    # Create dataset collection
    datasets = create_datasets(
        customers, products, orders, order_items, payments
    )

    # Profile raw data
    profile_data(datasets)

    # Transform
    customers, products, orders, payments = transform_data(
        customers, products, orders, payments
    )

    # Refresh dataset collection with transformed DataFrames
    datasets = create_datasets(
        customers, products, orders, order_items, payments
    )

    # Verify transformations
    verify_transformations(datasets)

    # Validate primary keys
    validate_primary_keys(datasets)

    # Validate foreign keys
    validate_foreign_keys(
        customers, products, orders, order_items, payments
    )

    # Validate business rules
    validate_business_rules(products, order_items, payments)

    # Cross-table validations
    validate_product_prices(order_items, products)

    validate_order_totals(orders, order_items)

    validate_payment_amounts(payments, orders)

    # Load processed data
    processed_files = load_data(datasets)

    # Verify processed data
    verify_processed_data(datasets, processed_files)

    print("\n========================================")
    print("       SHOPFLOW ETL PIPELINE FINISHED")
    print("========================================")


# ============================================================
# RUN PIPELINE
# ============================================================

if __name__ == "__main__":
    main()
