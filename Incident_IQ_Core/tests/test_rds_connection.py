"""
Test script for Amazon RDS PostgreSQL connection.

This script tests the connection to an Amazon RDS PostgreSQL server using
environment variables for configuration.

Required environment variables:
    RDS_HOST: RDS endpoint hostname
    RDS_PORT: RDS port (default: 5432)
    RDS_DATABASE: Database name
    RDS_USER: Database username
    RDS_PASSWORD: Database password
"""

import os
import sys
from typing import Optional
from dotenv import load_dotenv
load_dotenv()

def test_rds_connection() -> bool:
    """
    Test connection to Amazon RDS PostgreSQL server.
    
    Returns:
        bool: True if connection successful, False otherwise
    """
    try:
        import psycopg2
        from psycopg2 import OperationalError
    except ImportError:
        print("ERROR: psycopg2 is not installed.")
        print("Please install it using: pip install psycopg2-binary")
        return False
    
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
        return False
    
    # Display connection info (without password)
    print("Testing RDS PostgreSQL connection...")
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Database: {database}")
    print(f"User: {user}")
    print()
    
    try:
        # Attempt connection
        print("Attempting to connect...")
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
            connect_timeout=10
        )
        
        # Test query
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        
        # Get database info
        cursor.execute("SELECT current_database(), current_user, inet_server_addr(), inet_server_port();")
        db_info = cursor.fetchone()
        
        # Close cursor and connection
        cursor.close()
        conn.close()
        
        # Display success message
        print("SUCCESS: Connection established!")
        print()
        print("Database Information:")
        print(f"  PostgreSQL Version: {version}")
        print(f"  Current Database: {db_info[0]}")
        print(f"  Current User: {db_info[1]}")
        print(f"  Server Address: {db_info[2]}")
        print(f"  Server Port: {db_info[3]}")
        
        return True
        
    except OperationalError as e:
        print(f"ERROR: Failed to connect to RDS PostgreSQL server.")
        print(f"Error details: {str(e)}")
        print()
        print("Common issues:")
        print("  - Check if RDS instance is running and accessible")
        print("  - Verify security group allows connections from your IP")
        print("  - Confirm credentials are correct")
        print("  - Ensure RDS endpoint hostname is correct")
        return False
        
    except Exception as e:
        print(f"ERROR: Unexpected error occurred: {str(e)}")
        return False


if __name__ == "__main__":
    success = test_rds_connection()
    sys.exit(0 if success else 1)

