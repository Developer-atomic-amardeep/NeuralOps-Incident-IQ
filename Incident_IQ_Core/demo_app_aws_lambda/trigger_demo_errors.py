"""
Trigger Demo Errors for IncidentIQ

This script triggers realistic error scenarios that will appear in CloudWatch logs.
Can be used:
1. Locally (logs to console, simulating what would go to CloudWatch)
2. Against deployed Lambda (actual CloudWatch logs)

Usage:
    python trigger_demo_errors.py --local              # Test locally
    python trigger_demo_errors.py --lambda-url <URL>   # Trigger deployed Lambda
    python trigger_demo_errors.py --cloudwatch         # Push directly to CloudWatch
"""

import argparse
import json
import time
import random
import boto3
import requests
from datetime import datetime
from lambda_function import lambda_handler

# Your CloudWatch log group (must match what your Lambda uses or create custom)
LOG_GROUP_NAME = "/incident-iq/api-errors"


def trigger_local_errors():
    """Trigger errors locally for testing."""
    print("="*60)
    print("TRIGGERING LOCAL ERROR SIMULATION")
    print("="*60)
    
    # Simulate multiple failed payment attempts
    for i in range(5):
        print(f"\n--- Payment Attempt {i+1} ---")
        event = {
            'httpMethod': 'POST',
            'path': '/payment',
            'body': json.dumps({
                'amount': random.uniform(10, 500),
                'customer_id': f'customer-{random.randint(1000, 9999)}'
            })
        }
        result = lambda_handler(event, None)
        print(f"Status: {result['statusCode']}")
        
        time.sleep(0.5)
    
    # Trigger comprehensive error scenario
    print("\n--- Triggering All Error Scenarios ---")
    event = {
        'httpMethod': 'POST',
        'path': '/trigger-error',
        'body': json.dumps({'scenario': 'all'})
    }
    lambda_handler(event, None)


def trigger_lambda_errors(lambda_url: str):
    """Trigger errors against deployed Lambda via API Gateway."""
    print("="*60)
    print(f"TRIGGERING ERRORS ON DEPLOYED LAMBDA")
    print(f"URL: {lambda_url}")
    print("="*60)
    
    # Trigger the comprehensive error scenario
    try:
        response = requests.post(
            f"{lambda_url.rstrip('/')}/trigger-error",
            json={'scenario': 'all'},
            timeout=30
        )
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Error calling Lambda: {e}")
    
    # Also trigger some payment failures
    print("\n--- Triggering Payment Failures ---")
    for i in range(3):
        try:
            response = requests.post(
                f"{lambda_url.rstrip('/')}/payment",
                json={'amount': random.uniform(10, 500)},
                timeout=30
            )
            print(f"Payment {i+1}: Status {response.status_code}")
        except Exception as e:
            print(f"Payment {i+1} error: {e}")
        time.sleep(1)


def push_to_cloudwatch():
    """
    Push demo error logs directly to CloudWatch.
    Use this if Lambda deployment isn't ready but you need CloudWatch logs for demo.
    """
    print("="*60)
    print("PUSHING DEMO ERRORS DIRECTLY TO CLOUDWATCH")
    print(f"Log Group: {LOG_GROUP_NAME}")
    print("="*60)
    
    client = boto3.client('logs', region_name='us-east-1')  # Adjust region as needed
    
    # Ensure log group exists
    try:
        client.create_log_group(logGroupName=LOG_GROUP_NAME)
        print(f"Created log group: {LOG_GROUP_NAME}")
    except client.exceptions.ResourceAlreadyExistsException:
        print(f"Log group already exists: {LOG_GROUP_NAME}")
    
    # Create log stream for this demo run
    log_stream_name = f"incidentiq-demo-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    try:
        client.create_log_stream(
            logGroupName=LOG_GROUP_NAME,
            logStreamName=log_stream_name
        )
        print(f"Created log stream: {log_stream_name}")
    except Exception as e:
        print(f"Error creating log stream: {e}")
        return
    
    # Demo error logs that tell a story
    timestamp = int(time.time() * 1000)
    
    log_events = [
        {
            'timestamp': timestamp,
            'message': json.dumps({
                'level': 'INFO',
                'service': 'payment-processing',
                'message': 'Service started, loading configuration...',
                'version': '2.1.0'
            })
        },
        {
            'timestamp': timestamp + 1000,
            'message': json.dumps({
                'level': 'INFO',
                'service': 'payment-processing',
                'message': 'DB config loaded: pool_size=2, timeout_ms=1000, max_retries=1',
                'note': 'Config updated in commit: Optimized database connection pool settings'
            })
        },
        {
            'timestamp': timestamp + 5000,
            'message': json.dumps({
                'level': 'WARN',
                'service': 'payment-processing',
                'message': 'Connection pool utilization at 100%',
                'active_connections': 2,
                'pool_size': 2
            })
        },
        {
            'timestamp': timestamp + 6000,
            'message': json.dumps({
                'level': 'ERROR',
                'service': 'payment-processing',
                'error': 'ConnectionPoolExhaustedError',
                'message': 'Connection pool exhausted! Active: 2, Pool size: 2',
                'transaction_id': 'TXN-20260208-1234',
                'hint': 'pool_size was reduced from 10 to 2 in recent optimization commit'
            })
        },
        {
            'timestamp': timestamp + 7000,
            'message': json.dumps({
                'level': 'ERROR',
                'service': 'payment-processing',
                'error': 'DatabaseConnectionTimeout',
                'message': 'Database connection timeout after 1000ms. Connection took 1847ms.',
                'transaction_id': 'TXN-20260208-1235',
                'hint': 'timeout_ms reduced from 5000 to 1000 in db_config optimization'
            })
        },
        {
            'timestamp': timestamp + 8000,
            'message': json.dumps({
                'level': 'ERROR',
                'service': 'payment-processing',
                'error': 'PaymentProcessingError',
                'message': 'Payment processing failed after exhausting retries',
                'transaction_id': 'TXN-20260208-1236',
                'retries_attempted': 1,
                'max_retries': 1,
                'hint': 'max_retries reduced from 3 to 1'
            })
        },
        {
            'timestamp': timestamp + 10000,
            'message': json.dumps({
                'level': 'CRITICAL',
                'service': 'payment-processing',
                'alert': 'INCIDENT_DETECTED',
                'message': 'Payment Processing System Degradation',
                'error_rate': '34%',
                'baseline_error_rate': '0.1%',
                'failed_transactions_last_hour': 156,
                'p99_latency_ms': 4500,
                'baseline_p99_latency_ms': 200,
                'probable_cause': 'Recent commit "Optimized database connection pool settings" introduced aggressive resource limits',
                'affected_config': {
                    'pool_size': {'current': 2, 'previous': 10},
                    'timeout_ms': {'current': 1000, 'previous': 5000},
                    'max_retries': {'current': 1, 'previous': 3}
                }
            })
        },
        {
            'timestamp': timestamp + 12000,
            'message': json.dumps({
                'level': 'ERROR',
                'service': 'payment-processing',
                'error': 'CascadeFailure',
                'message': 'Cascading failure: 47 transactions failed in last 5 minutes',
                'impacted_customers': 42,
                'estimated_revenue_impact': '$4,250.00'
            })
        }
    ]
    
    # Push logs to CloudWatch
    try:
        response = client.put_log_events(
            logGroupName=LOG_GROUP_NAME,
            logStreamName=log_stream_name,
            logEvents=log_events
        )
        print(f"\nSuccessfully pushed {len(log_events)} log events to CloudWatch!")
        print(f"Log Stream: {log_stream_name}")
        print("\nLogs contain error correlation hints pointing to:")
        print("  - Commit: 'Optimized database connection pool settings'")
        print("  - Config changes: pool_size 10→2, timeout 5000→1000, retries 3→1")
        
    except Exception as e:
        print(f"Error pushing logs: {e}")


def main():
    parser = argparse.ArgumentParser(description='Trigger demo errors for IncidentIQ')
    parser.add_argument('--local', action='store_true', help='Run locally (console output)')
    parser.add_argument('--lambda-url', type=str, help='API Gateway URL for deployed Lambda')
    parser.add_argument('--cloudwatch', action='store_true', help='Push logs directly to CloudWatch')
    
    args = parser.parse_args()
    
    if args.local:
        trigger_local_errors()
    elif args.lambda_url:
        trigger_lambda_errors(args.lambda_url)
    elif args.cloudwatch:
        push_to_cloudwatch()
    else:
        print("No mode specified. Use --local, --lambda-url <URL>, or --cloudwatch")
        print("\nQuick demo (local):")
        trigger_local_errors()


if __name__ == "__main__":
    main()

