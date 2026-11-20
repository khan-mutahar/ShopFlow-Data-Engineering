
-- ============================================================
-- PROJECT: SHOPFLOW
-- DOMAIN: E-COMMERCE DATA ENGINEERING
-- DATABASE: MySQL
-- PURPOSE: Store and manage e-commerce datasets
-- ============================================================


-- ============================================================
-- SECTION 1: DATABASE CREATION
-- ============================================================

-- Create the ShopFlow database if it does not exist.
CREATE DATABASE IF NOT EXISTS shopflow;

-- Select ShopFlow as the active database.
USE shopflow;


-- ============================================================
-- SECTION 2: CREATE CUSTOMERS TABLE
-- ============================================================

-- Stores customer personal and registration information.
-- Primary Key: customer_id

CREATE TABLE IF NOT EXISTS customers (
    customer_id VARCHAR(20) NOT NULL PRIMARY KEY,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    email VARCHAR(100),
    phone VARCHAR(20),
    city VARCHAR(50),
    state VARCHAR(50),
    country VARCHAR(50),
    signup_date DATE
);


-- ============================================================
-- SECTION 3: CREATE PRODUCTS TABLE
-- ============================================================

-- Stores product catalogue and inventory information.
-- Primary Key: product_id

CREATE TABLE IF NOT EXISTS products (
    product_id VARCHAR(20) NOT NULL PRIMARY KEY,
    product_name VARCHAR(100),
    category VARCHAR(50),
    brand VARCHAR(50),
    price DECIMAL(10,2),
    cost DECIMAL(10,2),
    stock_quantity INT
);


-- ============================================================
-- SECTION 4: CREATE ORDERS TABLE
-- ============================================================

-- Stores customer order information.
-- Primary Key: order_id
-- Foreign Key: customer_id references customers.customer_id

CREATE TABLE IF NOT EXISTS orders (
    order_id VARCHAR(20) NOT NULL PRIMARY KEY,
    customer_id VARCHAR(20),
    order_date DATE,
    order_status VARCHAR(30),
    total_amount DECIMAL(10,2),

    CONSTRAINT fk_orders_customers
    FOREIGN KEY (customer_id)
    REFERENCES customers(customer_id)
);


-- ============================================================
-- SECTION 5: CREATE ORDER_ITEMS TABLE
-- ============================================================

-- Stores individual products belonging to each order.
-- Primary Key: order_item_id
-- Foreign Keys:
-- order_id references orders.order_id
-- product_id references products.product_id

CREATE TABLE IF NOT EXISTS order_items (
    order_item_id VARCHAR(20) NOT NULL PRIMARY KEY,
    order_id VARCHAR(20),
    product_id VARCHAR(20),
    quantity INT,
    unit_price DECIMAL(10,2),
    discount DECIMAL(5,2),

    CONSTRAINT fk_order_items_orders
    FOREIGN KEY (order_id)
    REFERENCES orders(order_id),

    CONSTRAINT fk_order_items_products
    FOREIGN KEY (product_id)
    REFERENCES products(product_id)
);


-- ============================================================
-- SECTION 6: CREATE PAYMENTS TABLE
-- ============================================================

-- Stores payment information associated with orders.
-- Primary Key: payment_id
-- Foreign Key: order_id references orders.order_id

CREATE TABLE IF NOT EXISTS payments (
    payment_id VARCHAR(20) NOT NULL PRIMARY KEY,
    order_id VARCHAR(20),
    payment_method VARCHAR(30),
    amount DECIMAL(10,2),
    payment_status VARCHAR(30),
    payment_date DATE,

    CONSTRAINT fk_payments_orders
    FOREIGN KEY (order_id)
    REFERENCES orders(order_id)
);


-- ============================================================
-- SECTION 7: VERIFY DATABASE TABLES
-- ============================================================

-- Display all tables available in ShopFlow.

SHOW TABLES;


-- ============================================================
-- SECTION 8: VERIFY TABLE STRUCTURES
-- ============================================================

-- DESCRIBE displays column names, data types and key information.

DESCRIBE customers;
DESCRIBE products;
DESCRIBE orders;
DESCRIBE order_items;
DESCRIBE payments;


-- ============================================================
-- SECTION 9: VERIFY PRIMARY AND FOREIGN KEY RELATIONSHIPS
-- ============================================================

-- Check all foreign key relationships in ShopFlow.
-- information_schema stores MySQL database metadata.

SELECT
    TABLE_NAME,
    CONSTRAINT_NAME,
    COLUMN_NAME,
    REFERENCED_TABLE_NAME,
    REFERENCED_COLUMN_NAME
FROM information_schema.KEY_COLUMN_USAGE
WHERE TABLE_SCHEMA = 'shopflow'
AND REFERENCED_TABLE_NAME IS NOT NULL
ORDER BY TABLE_NAME;


-- ============================================================
-- SECTION 10: VERIFY ID COLUMN DATA TYPES
-- ============================================================

-- All IDs use VARCHAR(20) because source IDs contain letters
-- and numbers, such as C0001, P0001 and O00001.

SELECT
    TABLE_NAME,
    COLUMN_NAME,
    COLUMN_TYPE,
    COLUMN_KEY
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = 'shopflow'
AND COLUMN_NAME IN (
    'customer_id',
    'product_id',
    'order_id',
    'order_item_id',
    'payment_id'
)
ORDER BY TABLE_NAME, ORDINAL_POSITION;


-- ============================================================
-- SECTION 11: VERIFY RECORD COUNTS
-- ============================================================

-- COUNT(*) returns the total number of records in each table.

SELECT COUNT(*) AS total_customers
FROM customers;

SELECT COUNT(*) AS total_products
FROM products;

SELECT COUNT(*) AS total_orders
FROM orders;

SELECT COUNT(*) AS total_order_items
FROM order_items;

SELECT COUNT(*) AS total_payments
FROM payments;


-- ============================================================
-- SECTION 12: VIEW TABLE DATA
-- ============================================================

-- Display customer records.

SELECT * FROM customers;

-- Display product records.

SELECT * FROM products;

-- Display order records.

SELECT * FROM orders;

-- Display order item records.

SELECT * FROM order_items;

-- Display payment records.

SELECT * FROM payments;


-- ============================================================
-- END OF SHOPFLOW DATABASE SCRIPT
-- ============================================================
