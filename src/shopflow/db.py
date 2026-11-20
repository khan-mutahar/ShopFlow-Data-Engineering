import mysql.connector

from mysql.connector import Error
from shopflow.config import DB_CONFIG


def get_connection():
    """
    Establish and return a connection to the ShopFlow MySQL database.
    """

    try:
        connection = mysql.connector.connect(**DB_CONFIG)

        if connection.is_connected():
            print("MySQL database connected successfully!")
            return connection

    except Error as error:
        print(f"MySQL connection failed: {error}")
        raise

    raise ConnectionError("Could not establish MySQL connection.")


def close_connection(connection):
    """
    Safely close an existing MySQL connection.
    """

    if connection and connection.is_connected():
        connection.close()
        print("MySQL connection closed.")