import os
import time
import json
import psycopg2 # Use pymysql if using MySQL
from datetime import datetime

# CONFIGURATION - Simulated from your GitHub PR #402
COMMIT_HASH = "d92f1a8" 
QUERY_NAME = "Monthly_Revenue_Audit_Full_Scan"

def lambda_handler(event, context):
    db_host = os.environ['DB_HOST']
    db_name = os.environ['DB_NAME']
    db_user = os.environ['DB_USER']
    db_pass = os.environ['DB_PASS']

    # 1. Start Telemetry
    start_time = time.time()
    
    log_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "event": "QUERY_START",
        "commit_hash": COMMIT_HASH,
        "query_name": QUERY_NAME,
        "status": "IN_PROGRESS"
    }
    print(json.dumps(log_data))

    try:
        # 2. Connect to RDS
        conn = psycopg2.connect(
            host=db_host,
            database=db_name,
            user=db_user,
            password=db_pass,
            connect_timeout=5
        )
        cur = conn.cursor()

        # 3. The "Heavy" Query (Force a full table scan and sort)
        # This is what you "merged" in your GitHub PR
        heavy_query = """
            SELECT category, SUM(amount), COUNT(*) 
            FROM transactions 
            GROUP BY category 
            ORDER BY SUM(amount) DESC;
        """
        cur.execute(heavy_query)
        result = cur.fetchall()
        
        cur.close()
        conn.close()

        # 4. End Telemetry
        end_time = time.time()
        duration = round(end_time - start_time, 2)

        final_log = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": "QUERY_COMPLETE",
            "commit_hash": COMMIT_HASH,
            "duration_seconds": duration,
            "rows_processed": len(result),
            "performance_state": "OPTIMAL" if duration < 5 else "DEGRADED"
        }
        
        # Explicit warning for the AI to latch onto
        if duration > 5:
            final_log["alert"] = "LATENCY_THRESHOLD_EXCEEDED"
            final_log["potential_cause"] = "Resource starvation or missing index"

        print(json.dumps(final_log))

    except Exception as e:
        print(json.dumps({
            "timestamp": datetime.utcnow().isoformat(),
            "event": "QUERY_FAILURE",
            "commit_hash": COMMIT_HASH,
            "error": str(e),
            "remediation_hint": "Check RDS instance health and credit balance"
        }))
        raise e