#!/usr/bin/env python3
"""
Script to delete all transactions from the database
"""
import sqlite3
import os

# Get the database path
db_path = os.path.join(os.path.dirname(__file__), 'finance.db')

if not os.path.exists(db_path):
    print(f"Database not found at: {db_path}")
    exit(1)

# Connect to the database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Count transactions before deletion
    cursor.execute("SELECT COUNT(*) FROM transactions")
    count_before = cursor.fetchone()[0]
    print(f"Found {count_before} transactions in the database")

    # Delete all transactions
    cursor.execute("DELETE FROM transactions")
    conn.commit()

    # Verify deletion
    cursor.execute("SELECT COUNT(*) FROM transactions")
    count_after = cursor.fetchone()[0]

    print(f"Successfully deleted {count_before} transactions")
    print(f"Remaining transactions: {count_after}")

except Exception as e:
    print(f"Error deleting transactions: {e}")
    conn.rollback()
finally:
    conn.close()

print("\nDone! You can now upload your CSV file again.")
