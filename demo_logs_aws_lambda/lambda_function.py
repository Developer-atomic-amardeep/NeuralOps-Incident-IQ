"""
IncidentIQ Demo App - Simulated Payment Processing Service

This Lambda function simulates a payment processing service with controllable
error scenarios for demonstrating IncidentIQ's incident correlation capabilities.

DEMO STORYLINE:
- A recent commit "optimized" the database connection pool settings
- This caused connection timeouts during peak load
- Team is discussing the issue in Slack
- IncidentIQ correlates CloudWatch errors → GitHub commit → Slack discussion
"""

import json
import logging
import random
import time
from datetime import datetime

# Configure logging for CloudWatch
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Simulated "configuration" that was changed in the problematic commit
DB_CONFIG = {
    "pool_size": 2,  # "Optimized" from 10 to 2 - THIS IS THE BUG!
    "timeout_ms": 1000,  # Reduced from 5000ms - ALSO A BUG!
    "max_retries": 1  # Reduced from 3 - YET ANOTHER BUG!
}

# Track "active connections" to simulate pool exhaustion
active_connections = 0


class DatabaseConnectionError(Exception):
    """Raised when database connection fails."""
    pass


class ConnectionPoolExhaustedError(Exception):
    """Raised when connection pool is exhausted."""
    pass


class PaymentProcessingError(Exception):
    """Raised when payment processing fails."""
    pass


def simulate_db_connection():
    """
    Simulates acquiring a database connection.
    With the "optimized" settings, this frequently fails.
    """
    global active_connections
    
    if active_connections >= DB_CONFIG["pool_size"]:
        raise ConnectionPoolExhaustedError(
            f"Connection pool exhausted! Active: {active_connections}, "
            f"Pool size: {DB_CONFIG['pool_size']}. "
            "Consider increasing pool_size in db_config.py (changed in commit abc1234)"
        )
    
    # Simulate connection delay
    delay = random.uniform(0.5, 2.0)
    if delay * 1000 > DB_CONFIG["timeout_ms"]:
        raise DatabaseConnectionError(
            f"Database connection timeout after {DB_CONFIG['timeout_ms']}ms. "
            f"Connection took {delay*1000:.0f}ms. "
            "Timeout setting may be too aggressive after recent optimization."
        )
    
    active_connections += 1
    return True


def release_connection():
    """Release a database connection back to the pool."""
    global active_connections
    if active_connections > 0:
        active_connections -= 1


def process_payment(payment_data: dict) -> dict:
    """
    Process a payment transaction.
    This is where errors manifest due to the DB config changes.
    """
    transaction_id = f"TXN-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}"
    
    logger.info(f"[{transaction_id}] Starting payment processing for amount: ${payment_data.get('amount', 0)}")
    
    try:
        # Step 1: Acquire DB connection
        logger.info(f"[{transaction_id}] Acquiring database connection from pool...")
        simulate_db_connection()
        
        # Step 2: Validate payment (simulated)
        time.sleep(0.1)
        logger.info(f"[{transaction_id}] Payment validation successful")
        
        # Step 3: Process transaction (simulated)
        time.sleep(0.2)
        
        # Random failure to simulate intermittent issues (30% chance)
        if random.random() < 0.3:
            raise PaymentProcessingError(
                f"[{transaction_id}] Payment processing failed: Database write timeout. "
                "This may be related to reduced connection pool affecting concurrent transactions."
            )
        
        logger.info(f"[{transaction_id}] Payment processed successfully")
        release_connection()
        
        return {
            "success": True,
            "transaction_id": transaction_id,
            "message": "Payment processed successfully"
        }
        
    except (DatabaseConnectionError, ConnectionPoolExhaustedError, PaymentProcessingError) as e:
        error_msg = str(e)
        logger.error(f"[{transaction_id}] PAYMENT_PROCESSING_ERROR: {error_msg}")
        logger.error(f"[{transaction_id}] DB_CONFIG: pool_size={DB_CONFIG['pool_size']}, timeout={DB_CONFIG['timeout_ms']}ms")
        logger.error(f"[{transaction_id}] Active connections: {active_connections}/{DB_CONFIG['pool_size']}")
        release_connection()
        raise
    except Exception as e:
        logger.error(f"[{transaction_id}] UNEXPECTED_ERROR: {str(e)}")
        release_connection()
        raise


def trigger_error_scenario(scenario: str) -> dict:
    """
    Trigger specific error scenarios for demo purposes.
    """
    global active_connections
    
    if scenario == "pool_exhaustion":
        # Simulate pool exhaustion
        active_connections = DB_CONFIG["pool_size"]
        logger.error("ERROR: Connection pool exhausted - all connections in use")
        logger.error(f"CRITICAL: Pool size ({DB_CONFIG['pool_size']}) insufficient for current load")
        logger.error("HINT: Check recent commit 'Optimized database connection pool settings' - pool_size was reduced from 10 to 2")
        return {"error": "ConnectionPoolExhaustedError", "message": "All database connections in use"}
    
    elif scenario == "timeout":
        logger.error("ERROR: Database connection timeout after 1000ms")
        logger.error("CRITICAL: Connection timeout threshold too low for network latency")
        logger.error("HINT: timeout_ms was reduced from 5000 to 1000 in recent DB config optimization")
        return {"error": "DatabaseConnectionTimeout", "message": "Connection timed out"}
    
    elif scenario == "cascade_failure":
        # Simulate cascading failures
        logger.error("CRITICAL: Cascading failure detected in payment processing pipeline")
        logger.error("ERROR: Primary DB connection failed, attempting retry 1/1")
        logger.error("ERROR: Retry failed - max_retries (1) exhausted")
        logger.error("ALERT: max_retries was reduced from 3 to 1 in commit 'Optimized database connection pool settings'")
        logger.error("IMPACT: 47 transactions failed in last 5 minutes")
        return {"error": "CascadeFailure", "message": "Multiple systems affected"}
    
    elif scenario == "all":
        # Trigger all scenarios for comprehensive demo
        logger.error("="*50)
        logger.error("INCIDENT DETECTED: Payment Processing System Degradation")
        logger.error("="*50)
        logger.error("")
        logger.error("SYMPTOM 1: Connection Pool Exhaustion")
        logger.error(f"  - Current pool size: {DB_CONFIG['pool_size']} (was 10)")
        logger.error("  - Active connections: 2/2")
        logger.error("  - Waiting requests: 23")
        logger.error("")
        logger.error("SYMPTOM 2: Connection Timeouts")
        logger.error(f"  - Timeout threshold: {DB_CONFIG['timeout_ms']}ms (was 5000ms)")
        logger.error("  - Average connection time: 1200ms")
        logger.error("  - Timeout rate: 34%")
        logger.error("")
        logger.error("SYMPTOM 3: Failed Retries")
        logger.error(f"  - Max retries: {DB_CONFIG['max_retries']} (was 3)")
        logger.error("  - Transactions failing after first retry")
        logger.error("")
        logger.error("ROOT CAUSE HYPOTHESIS:")
        logger.error("  Recent commit 'Optimized database connection pool settings'")
        logger.error("  introduced aggressive resource limits that cannot handle")
        logger.error("  production traffic volume.")
        logger.error("")
        logger.error("AFFECTED METRICS:")
        logger.error("  - Error rate: 34% (baseline: 0.1%)")
        logger.error("  - P99 latency: 4500ms (baseline: 200ms)")
        logger.error("  - Failed transactions: 156 in last hour")
        logger.error("="*50)
        
        return {
            "error": "SystemDegradation",
            "message": "Multiple error scenarios triggered",
            "affected_systems": ["database", "payment_processing", "retry_logic"]
        }
    
    return {"error": "Unknown scenario", "message": f"Scenario '{scenario}' not recognized"}


def lambda_handler(event, context):
    """
    AWS Lambda handler function.
    
    Endpoints:
    - POST /payment - Process a payment (may fail based on current "buggy" config)
    - GET /health - Health check
    - POST /trigger-error - Trigger specific error scenarios for demo
    - GET /status - Get current system status
    """
    
    # Parse the request
    http_method = event.get('httpMethod', event.get('requestContext', {}).get('http', {}).get('method', 'GET'))
    path = event.get('path', event.get('rawPath', '/'))
    body = event.get('body', '{}')
    
    if isinstance(body, str):
        try:
            body = json.loads(body) if body else {}
        except json.JSONDecodeError:
            body = {}
    
    logger.info(f"Request: {http_method} {path}")
    
    try:
        # Health check endpoint
        if path == '/health' or path == '/':
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'status': 'healthy',
                    'service': 'payment-processing',
                    'version': '2.1.0',  # After the "optimization" commit
                    'db_config': DB_CONFIG,
                    'timestamp': datetime.now().isoformat()
                })
            }
        
        # System status endpoint
        elif path == '/status':
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'active_connections': active_connections,
                    'pool_size': DB_CONFIG['pool_size'],
                    'pool_utilization': f"{(active_connections/DB_CONFIG['pool_size'])*100:.1f}%",
                    'timeout_ms': DB_CONFIG['timeout_ms'],
                    'max_retries': DB_CONFIG['max_retries']
                })
            }
        
        # Trigger error scenarios for demo
        elif path == '/trigger-error':
            scenario = body.get('scenario', 'all')
            result = trigger_error_scenario(scenario)
            
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps(result)
            }
        
        # Payment processing endpoint
        elif path == '/payment':
            payment_data = {
                'amount': body.get('amount', 99.99),
                'currency': body.get('currency', 'USD'),
                'customer_id': body.get('customer_id', 'demo-customer')
            }
            
            result = process_payment(payment_data)
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps(result)
            }
        
        else:
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Not found', 'path': path})
            }
            
    except (DatabaseConnectionError, ConnectionPoolExhaustedError, PaymentProcessingError) as e:
        return {
            'statusCode': 503,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'error': type(e).__name__,
                'message': str(e),
                'hint': 'Check recent database configuration changes'
            })
        }
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'error': 'InternalServerError',
                'message': str(e)
            })
        }


# For local testing
if __name__ == "__main__":
    # Test the trigger-error endpoint
    test_event = {
        'httpMethod': 'POST',
        'path': '/trigger-error',
        'body': json.dumps({'scenario': 'all'})
    }
    
    result = lambda_handler(test_event, None)
    print(f"\nResponse: {result['statusCode']}")
    print(json.dumps(json.loads(result['body']), indent=2))

