
def validate_primary_keys(datasets):
    """Check missing and duplicate primary keys."""

    primary_keys = {
        "Customers": (datasets["Customers"], "customer_id"),
        "Products": (datasets["Products"], "product_id"),
        "Orders": (datasets["Orders"], "order_id"),
        "Order Items": (datasets["Order Items"], "order_item_id"),
        "Payments": (datasets["Payments"], "payment_id"),
    }

    results = []

    print("\n========== PRIMARY KEY VALIDATION ==========")

    for name, (df, key) in primary_keys.items():
        duplicates = df[key].duplicated().sum()
        missing = df[key].isnull().sum()

        passed = duplicates == 0 and missing == 0
        results.append(passed)

        print(f"\n{name}")
        print(f"Duplicate IDs: {duplicates}")
        print(f"Missing IDs: {missing}")
        print(f"Status: {'PASSED' if passed else 'FAILED'}")

    return all(results)


def validate_foreign_keys(datasets):
    """Check whether foreign keys have valid parent references."""

    foreign_keys = [
        ("Orders", "customer_id", "Customers", "customer_id"),
        ("Order Items", "order_id", "Orders", "order_id"),
        ("Order Items", "product_id", "Products", "product_id"),
        ("Payments", "order_id", "Orders", "order_id"),
    ]

    results = []

    print("\n========== FOREIGN KEY VALIDATION ==========")

    for child_name, fk, parent_name, pk in foreign_keys:
        child_df = datasets[child_name]
        parent_df = datasets[parent_name]

        invalid = (
            child_df[fk].isnull()
            | ~child_df[fk].isin(parent_df[pk])
        )

        invalid_count = invalid.sum()
        passed = invalid_count == 0
        results.append(passed)

        print(f"\nDataset: {child_name}")
        print(f"Foreign Key: {fk}")
        print(f"Invalid References: {invalid_count}")
        print(f"Status: {'PASSED' if passed else 'FAILED'}")

    return all(results)


def validate_business_rules(datasets):
    """Check basic product, order-item and payment rules."""

    products = datasets["Products"]
    order_items = datasets["Order Items"]
    payments = datasets["Payments"]

    invalid_products = products[
        (products["price"] < 0)
        | (products["cost"] < 0)
        | (products["stock_quantity"] < 0)
    ]

    invalid_order_items = order_items[
        (order_items["quantity"] <= 0)
        | (order_items["unit_price"] < 0)
        | (order_items["discount"] < 0)
        | (order_items["discount"] > 100)
    ]

    invalid_payments = payments[payments["amount"] < 0]

    results = [
        len(invalid_products) == 0,
        len(invalid_order_items) == 0,
        len(invalid_payments) == 0,
    ]

    print("\n========== BUSINESS RULE VALIDATION ==========")
    print("Invalid Products:", len(invalid_products))
    print("Invalid Order Items:", len(invalid_order_items))
    print("Invalid Payments:", len(invalid_payments))

    return all(results)


def validate_product_prices(datasets):
    """Compare order item prices against product prices."""

    order_items = datasets["Order Items"]
    products = datasets["Products"]

    check = order_items.merge(
        products[["product_id", "price"]],
        on="product_id",
        how="left"
    )

    mismatches = check[
        (check["unit_price"] - check["price"]).abs() > 0.01
    ]

    print("\n========== PRODUCT PRICE VALIDATION ==========")
    print("Total Order Items:", len(order_items))
    print("Price Mismatches:", len(mismatches))

    return len(mismatches) == 0


def validate_order_totals(datasets):
    """Compare calculated order totals with stored order totals."""

    orders = datasets["Orders"]
    order_items = datasets["Order Items"].copy()

    order_items["line_total"] = (
        order_items["quantity"]
        * order_items["unit_price"]
        * (1 - order_items["discount"] / 100)
    )

    calculated_totals = (
        order_items.groupby("order_id")["line_total"]
        .sum()
        .reset_index()
    )

    check = orders.merge(
        calculated_totals,
        on="order_id",
        how="left"
    )

    check["line_total"] = check["line_total"].fillna(0)

    mismatches = check[
        (check["total_amount"] - check["line_total"]).abs() > 0.01
    ]

    print("\n========== ORDER TOTAL VALIDATION ==========")
    print("Total Orders:", len(orders))
    print("Mismatched Orders:", len(mismatches))

    return len(mismatches) == 0


def validate_payment_amounts(datasets):
    """Compare payment amounts with corresponding order totals."""

    payments = datasets["Payments"]
    orders = datasets["Orders"]

    check = payments.merge(
        orders[["order_id", "total_amount"]],
        on="order_id",
        how="left"
    )

    mismatches = check[
        (check["amount"] - check["total_amount"]).abs() > 0.01
    ]

    print("\n========== PAYMENT AMOUNT VALIDATION ==========")
    print("Total Payments:", len(payments))
    print("Mismatched Payments:", len(mismatches))

    return len(mismatches) == 0


def run_all_validations(datasets):
    """Run all validation checks and return the overall result."""

    results = {
        "Primary Keys": validate_primary_keys(datasets),
        "Foreign Keys": validate_foreign_keys(datasets),
        "Business Rules": validate_business_rules(datasets),
        "Product Prices": validate_product_prices(datasets),
        "Order Totals": validate_order_totals(datasets),
        "Payment Amounts": validate_payment_amounts(datasets),
    }

    print("\n========== FINAL DATA QUALITY RESULT ==========")

    for name, passed in results.items():
        print(f"{name}: {'PASSED' if passed else 'FAILED'}")

    overall_status = all(results.values())

    print(
        "\nOverall Status:",
        "PASSED" if overall_status else "FAILED"
    )

    return overall_status
