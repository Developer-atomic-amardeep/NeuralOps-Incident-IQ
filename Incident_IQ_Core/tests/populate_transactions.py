"""
Script to populate transactions table with test data.

This script creates a transactions table and inserts 1 million rows
5 times, showing the row count after each successful insert.
"""

import os
import sys
import time
from dotenv import load_dotenv

load_dotenv()


def get_db_connection():
    """
    Create and return a database connection.
    
    Returns:
        psycopg2.connection: Database connection object
    """
    try:
        import psycopg2
        from psycopg2 import OperationalError
    except ImportError:
        print("ERROR: psycopg2 is not installed.")
        print("Please install it using: pip install psycopg2-binary")
        sys.exit(1)
    
    # Get connection parameters from environment variables
    host = os.getenv("RDS_HOST")
    port = os.getenv("RDS_PORT", "5432")
    database = os.getenv("RDS_DATABASE")
    user = os.getenv("RDS_USER")
    password = os.getenv("RDS_PASSWORD")
    
    # Validate required parameters
    missing_params = []
    if not host:
        missing_params.append("RDS_HOST")
    if not database:
        missing_params.append("RDS_DATABASE")
    if not user:
        missing_params.append("RDS_USER")
    if not password:
        missing_params.append("RDS_PASSWORD")
    
    if missing_params:
        print("ERROR: Missing required environment variables:")
        for param in missing_params:
            print(f"  - {param}")
        print("\nPlease set the required environment variables before running this script.")
        sys.exit(1)
    
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
            connect_timeout=10
        )
        return conn
    except Exception as e:
        print(f"ERROR: Failed to connect to RDS PostgreSQL server: {str(e)}")
        sys.exit(1)


def get_row_count(cursor):
    """
    Get the current row count from the transactions table.
    
    Args:
        cursor: Database cursor object
        
    Returns:
        int: Number of rows in the transactions table
    """
    cursor.execute("SELECT COUNT(*) FROM transactions;")
    return cursor.fetchone()[0]


def create_table(cursor):
    """
    Create the transactions table if it doesn't exist.
    
    Args:
        cursor: Database cursor object
    """
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS transactions (
        id SERIAL PRIMARY KEY,
        user_id INT,
        amount DECIMAL(10, 2),
        category TEXT,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    print("Creating transactions table (if not exists)...")
    cursor.execute(create_table_sql)
    print("Table created successfully.\n")


def insert_data(cursor, iteration):
    """
    Insert 1 million rows into the transactions table.
    
    Args:
        cursor: Database cursor object
        iteration: Current iteration number (1-5)
    """
    insert_sql = """
    INSERT INTO transactions (user_id, amount, category, description, created_at)
    SELECT 
        (random() * 10000)::int, 
        (random() * 500)::decimal, 
        (ARRAY['Retail', 'Food', 'Travel', 'Software', 'Hardware'])[floor(random()*5)+1],
        md5(random()::text),
        now() - (random() * interval '30 days')
    FROM generate_series(1, 1000000);
    """
    
    print(f"Inserting 1,000,000 rows (Iteration {iteration}/5)...")
    start_time = time.time()
    cursor.execute(insert_sql)
    elapsed_time = time.time() - start_time
    print(f"Insert completed in {elapsed_time:.2f} seconds.")


def main():
    """
    Main function to execute the data population script.
    """
    print("=" * 60)
    print("Transactions Table Population Script")
    print("=" * 60)
    print()
    
    # Connect to database
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Create table
        create_table(cursor)
        conn.commit()
        
        # Get initial row count
        initial_count = get_row_count(cursor)
        print(f"Initial row count: {initial_count:,}")
        print()
        
        # Execute insert 5 times
        for i in range(1, 6):
            print(f"{'=' * 60}")
            print(f"Iteration {i}/5")
            print(f"{'=' * 60}")
            
            insert_data(cursor, i)
            conn.commit()
            
            # Get row count after insert
            row_count = get_row_count(cursor)
            print(f"SUCCESS: Total rows in transactions table: {row_count:,}")
            print()
            
            # Small delay between iterations
            if i < 5:
                time.sleep(1)
        
        # Final summary
        final_count = get_row_count(cursor)
        rows_added = final_count - initial_count
        print(f"{'=' * 60}")
        print("Summary")
        print(f"{'=' * 60}")
        print(f"Initial row count: {initial_count:,}")
        print(f"Final row count: {final_count:,}")
        print(f"Total rows added: {rows_added:,}")
        print(f"Expected rows added: 5,000,000")
        print()
        
        if rows_added == 5000000:
            print("SUCCESS: All 5 iterations completed successfully!")
        else:
            print(f"WARNING: Expected 5,000,000 rows but got {rows_added:,} rows.")
        
    except Exception as e:
        print(f"ERROR: An error occurred: {str(e)}")
        conn.rollback()
        sys.exit(1)
    finally:
        cursor.close()
        conn.close()
        print("Database connection closed.")


if __name__ == "__main__":
    main()

