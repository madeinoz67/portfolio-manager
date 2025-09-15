#!/usr/bin/env python3
"""
Database cleanup script to fix transaction_timestamp column issue
"""
import sqlite3
import os

db_path = 'development.db'

if not os.path.exists(db_path):
    print(f"Database {db_path} not found")
    exit(1)

# Connect to database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Check current table structure
    print("Current transactions table structure:")
    cursor.execute("PRAGMA table_info(transactions)")
    columns = cursor.fetchall()
    for col in columns:
        print(f"  {col}")

    # Check if transaction_timestamp column exists
    column_names = [col[1] for col in columns]
    if 'transaction_timestamp' in column_names:
        print("\nRemoving transaction_timestamp column...")

        # Get all data from transactions table
        cursor.execute("SELECT * FROM transactions")
        transactions_data = cursor.fetchall()

        # Get original column structure without transaction_timestamp
        original_columns = [col for col in columns if col[1] != 'transaction_timestamp']

        # Create new table without transaction_timestamp
        cursor.execute("DROP TABLE IF EXISTS transactions_backup")

        # Create the clean table structure
        create_sql = """
        CREATE TABLE transactions_backup (
            id TEXT PRIMARY KEY,
            portfolio_id TEXT NOT NULL,
            stock_id TEXT NOT NULL,
            transaction_type TEXT NOT NULL,
            quantity DECIMAL(12, 4) NOT NULL,
            price_per_share DECIMAL(10, 4) NOT NULL,
            total_amount DECIMAL(15, 2) NOT NULL,
            fees DECIMAL(10, 2) DEFAULT 0.00,
            transaction_date DATE NOT NULL,
            processed_date DATETIME,
            source_type TEXT NOT NULL,
            source_reference TEXT,
            broker_reference TEXT,
            notes TEXT,
            is_verified BOOLEAN DEFAULT 0,
            FOREIGN KEY(portfolio_id) REFERENCES portfolios(id),
            FOREIGN KEY(stock_id) REFERENCES stocks(id)
        )
        """
        cursor.execute(create_sql)

        # Copy data excluding transaction_timestamp column
        if transactions_data:
            # Find transaction_timestamp column index
            ts_index = None
            for i, col in enumerate(columns):
                if col[1] == 'transaction_timestamp':
                    ts_index = i
                    break

            # Copy data excluding transaction_timestamp column
            clean_data = []
            for row in transactions_data:
                clean_row = list(row)
                if ts_index is not None:
                    clean_row.pop(ts_index)
                clean_data.append(tuple(clean_row))

            # Insert clean data
            placeholders = ', '.join(['?' for _ in range(len(original_columns))])
            cursor.executemany(f"INSERT INTO transactions_backup VALUES ({placeholders})", clean_data)

        # Replace original table
        cursor.execute("DROP TABLE transactions")
        cursor.execute("ALTER TABLE transactions_backup RENAME TO transactions")

        print("Successfully removed transaction_timestamp column")
    else:
        print("transaction_timestamp column not found - database is clean")

    # Show final structure
    print("\nFinal transactions table structure:")
    cursor.execute("PRAGMA table_info(transactions)")
    columns = cursor.fetchall()
    for col in columns:
        print(f"  {col}")

    conn.commit()
    print("\nDatabase cleanup completed successfully")

except Exception as e:
    print(f"Error during cleanup: {e}")
    conn.rollback()
finally:
    conn.close()