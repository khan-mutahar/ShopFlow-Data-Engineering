
import os
import mysql.connector
from dotenv import load_dotenv

# Load environment variables from the project root .env file
load_dotenv()

connection = None

try:
    connection = mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE", "shopflow")
    )

    if connection.is_connected():
        print("Successfully connected to ShopFlow database!")

except mysql.connector.Error as error:
    print("Connection failed:", error)

finally:
    if connection is not None and connection.is_connected():
        connection.close()
        print("MySQL connection closed.")
