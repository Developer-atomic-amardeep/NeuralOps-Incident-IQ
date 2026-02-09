#!/usr/bin/env python3
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""AWS CloudWatch MCP Server implementation.

A Model Context Protocol (MCP) server that provides tools for CloudWatch
by wrapping boto3 SDK functions for AWS CloudWatch services.
"""

import os
import sys


# Default configuration for StreamableHTTP transport
DEFAULT_HOST = os.getenv('MCP_HOST', '0.0.0.0')
DEFAULT_PORT = int(os.getenv('MCP_PORT', '8000'))


if __name__ == '__main__':
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(os.path.dirname(current_dir))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

from awslabs.cloudwatch_mcp_server.cloudwatch_alarms.tools import CloudWatchAlarmsTools
from awslabs.cloudwatch_mcp_server.cloudwatch_logs.tools import CloudWatchLogsTools
from awslabs.cloudwatch_mcp_server.cloudwatch_metrics.tools import CloudWatchMetricsTools
from fastmcp import FastMCP
from loguru import logger


mcp = FastMCP(
    name='awslabs.cloudwatch-mcp-server',
    instructions="""AWS CloudWatch MCP Server - Provides AWS CloudWatch tools through MCP.

Use this MCP server to run read-only commands and analyze CloudWatch Logs, Metrics, and Alarms.

Available components:

TOOLS:
- CloudWatch Logs: Discover log groups, run CloudWatch Log Insight Queries
- CloudWatch Metrics: Get information about system and application metrics
- CloudWatch Alarms: Retrieve all currently active alarms for operational awareness

When using these tools:
1. Start by discovering available log groups or metrics
2. Use Log Insights for interactive log analysis
3. Check active alarms for operational awareness
4. All operations are read-only and safe to execute

For log analysis:
1. Use discover_log_groups to find relevant log groups
2. Use run_log_insights_query to analyze log data
3. Results include region information for context

For metrics analysis:
1. Use get_metrics to discover available metrics
2. Use get_metric_data to retrieve metric values
3. Analyze trends and patterns in the data

For alarm monitoring:
1. Use get_active_alarms to see current alarm states
2. Review alarm history for recent changes
3. Check alarm configurations for thresholds
""",
)

# Initialize and register CloudWatch tools
try:
    cloudwatch_logs_tools = CloudWatchLogsTools()
    cloudwatch_logs_tools.register(mcp)
    logger.info('CloudWatch Logs tools registered successfully')
    cloudwatch_metrics_tools = CloudWatchMetricsTools()
    cloudwatch_metrics_tools.register(mcp)
    logger.info('CloudWatch Metrics tools registered successfully')
    cloudwatch_alarms_tools = CloudWatchAlarmsTools()
    cloudwatch_alarms_tools.register(mcp)
    logger.info('CloudWatch Alarms tools registered successfully')
except Exception as e:
    logger.error(f'Error initializing CloudWatch tools: {str(e)}')
    raise


def main():
    """Main entry point for the server."""
    logger.info(f'Starting StreamableHTTP server on {DEFAULT_HOST}:{DEFAULT_PORT}')

    # Start the MCP server with StreamableHTTP transport
    mcp.run(
        transport='streamable-http',
        host=DEFAULT_HOST,
        port=DEFAULT_PORT,
    )


if __name__ == '__main__':
    main()
