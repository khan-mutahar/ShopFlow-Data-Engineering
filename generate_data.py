from faker import Faker
import pandas as pd

fake = Faker()

customers = []

for i in range(10):
    customer = {
        "customer_id": f"C{i+1:04d}",
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "email": fake.email(),
        "phone": fake.phone_number(),
        "city": fake.city(),
        "state": fake.state(),
        "country": "India",
        "signup_date": fake.date_between(start_date="-2y", end_date="today")
    }

    customers.append(customer)

df = pd.DataFrame(customers)

df.to_csv("data/raw/customers.csv", index=False)

print("Customer data generated successfully!")

products = []

for i in range(20):
    product = {
        "product_id": f"P{i+1:04d}",
        "product_name": fake.word().title(),
        "category": fake.random_element(
            elements=("Electronics", "Clothing", "Footwear", "Books", "Home")
        ),
        "brand": fake.company(),
        "price": fake.random_int(min=100, max=50000),
        "cost": fake.random_int(min=50, max=30000),
        "stock_quantity": fake.random_int(min=0, max=500)
    }

    products.append(product)

products_df = pd.DataFrame(products)

products_df.to_csv("data/raw/products.csv", index=False)

print("Product data generated successfully!") 



# Generate orders
orders = []

customer_ids = [customer["customer_id"] for customer in customers]

for i in range(50):
    order = {
        "order_id": f"O{i+1:04d}",
        "customer_id": fake.random_element(elements=customer_ids),
        "order_date": fake.date_between(start_date="-1y", end_date="today"),
        "order_status": fake.random_element(
            elements=("Pending", "Processing", "Shipped", "Delivered", "Cancelled")
        ),
      
    }

    orders.append(order)

orders_df = pd.DataFrame(orders)

orders_df.to_csv("data/raw/orders.csv", index=False)

print("Order data generated successfully!")

# Generate order items

# Generate order items

order_items = []

order_ids = [order["order_id"] for order in orders]
product_ids = [product["product_id"] for product in products]

item_id = 1

for order_id in order_ids:

    number_of_items = fake.random_int(min=1, max=5)

    selected_products = fake.random_elements(
        elements=product_ids,
        length=number_of_items,
        unique=True
    )

    print(order_id, "Selected products:", len(selected_products))

    for product_id in selected_products:

        # Find the complete product record
        selected_product = next(
            product for product in products
            if product["product_id"] == product_id
        )

        item = {
            "order_item_id": f"OI{item_id:05d}",
            "order_id": order_id,
            "product_id": product_id,
            "quantity": fake.random_int(min=1, max=5),
            "unit_price": selected_product["price"],
            "discount": fake.random_int(min=0, max=30)
        }

        order_items.append(item)
        item_id += 1

print("Number of orders:", len(orders))
print("Number of order items:", len(order_items))

order_items_df = pd.DataFrame(order_items)

order_items_df.to_csv("data/raw/order_items.csv", index=False)

print("Order items data generated successfully!")



# Calculate order totals

for order in orders:

    order_total = 0

    for item in order_items:

        if item["order_id"] == order["order_id"]:

            line_total = (
                item["quantity"] *
                item["unit_price"] *
                (1 - item["discount"] / 100)
            )

            order_total += line_total

    order["total_amount"] = round(order_total, 2)

print("Order totals calculated successfully!")


# Save updated orders with calculated totals

orders_df = pd.DataFrame(orders)

orders_df.to_csv("data/raw/orders.csv", index=False)

print("Updated orders data saved successfully!")


# Generate payments
payments = []

for order in orders:
    payment = {
        "payment_id": f"PAY{len(payments) + 1:05d}",
        "order_id": order["order_id"],
        "payment_method": fake.random_element(
            elements=("UPI", "Credit Card", "Debit Card", "Net Banking", "COD")
        ),
        "amount": order["total_amount"],
        "payment_status": fake.random_element(
            elements=("Successful", "Successful", "Successful", "Failed", "Pending")
        ),
        "payment_date": order["order_date"]
    }

    payments.append(payment)

payments_df = pd.DataFrame(payments)

payments_df.to_csv("data/raw/payments.csv", index=False)

print("Payment data generated successfully!")