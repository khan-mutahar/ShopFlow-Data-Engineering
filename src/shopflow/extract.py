
import pandas as pd

from shopflow.config import RAW_DATA_DIR


def extract_data():
    """
    Read all five raw CSV files and return them as a dictionary
    of Pandas DataFrames.
    """

    file_paths = {
        "Customers": "customers.csv",
        "Products": "products.csv",
        "Orders": "orders.csv",
        "Order Items": "order_items.csv",
        "Payments": "payments.csv",
    }

    datasets = {}

    for name, file_name in file_paths.items():
        file_path = RAW_DATA_DIR / file_name
        datasets[name] = pd.read_csv(file_path)

    print("\nAll five datasets extracted successfully!")

    return datasets


def profile_data(datasets):
    """
    Display basic information about each extracted dataset.
    """

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
