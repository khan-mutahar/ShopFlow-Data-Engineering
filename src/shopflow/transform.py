
import pandas as pd


def transform_data(datasets):
    """
    Clean and standardise the extracted datasets.
    """

    # Work on copies so raw extracted data remains unchanged.
    datasets = {
        name: df.copy()
        for name, df in datasets.items()
    }

    customers = datasets["Customers"]
    products = datasets["Products"]
    orders = datasets["Orders"]
    payments = datasets["Payments"]

    # 1. Convert date columns
    customers["signup_date"] = pd.to_datetime(
        customers["signup_date"]
    )

    orders["order_date"] = pd.to_datetime(
        orders["order_date"]
    )

    payments["payment_date"] = pd.to_datetime(
        payments["payment_date"]
    )

    # 2. Standardise customer information
    customers["city"] = (
        customers["city"].str.strip().str.title()
    )

    customers["state"] = (
        customers["state"].str.strip().str.title()
    )

    # 3. Standardise product information
    products["category"] = (
        products["category"].str.strip().str.title()
    )

    # 4. Standardise order information
    orders["order_status"] = (
        orders["order_status"].str.strip().str.title()
    )

    # 5. Standardise payment information
    payments["payment_method"] = (
        payments["payment_method"].str.strip().str.title()
    )

    payments["payment_status"] = (
        payments["payment_status"].str.strip().str.title()
    )

    print("\nData transformation completed successfully!")

    return datasets
