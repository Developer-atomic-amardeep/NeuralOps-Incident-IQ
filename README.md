# NeuralOps-Incident-IQ
This repo contains all the codebase to run and test our Incident IQ project made for hackathon 2 fast 2 MCP hosted by wemakedevs.

## Current progress
So far, a custom streamable HTTP-based MCP server for AWS has been created. Most of the implementation is adapted from AWS's public GitHub repository, where the original MCP server used local stdio transport. The transport layer has been refactored to use HTTP with streaming, which is more suitable for hosting the MCP server remotely.

## Running the AWS MCP server via Docker
If you wish to use the AWS MCP server independently, you can run it in Docker.

Basic prerequisites before running the container:
- Docker is installed and the `docker` command works from your terminal.
- The `cloudwatch-mcp-server` image is available locally (built or pulled).
- You have valid AWS credentials (access key ID and secret access key) with the required permissions.

To build the Docker image locally (from the Dockerfile at `mcp/src/cloudwatch-mcp-server/Dockerfile`), run:

```bash
docker build -t cloudwatch-mcp-server -f mcp/src/cloudwatch-mcp-server/Dockerfile .
```

Example `docker run` command (simplified one-liner):

```bash
docker run -d --env AWS_REGION=us-east-1 --env AWS_ACCESS_KEY_ID=<your_aws_key_id> --env AWS_SECRET_ACCESS_KEY=<your_aws_secret_access_key> --env MCP_HOST=0.0.0.0 --env MCP_PORT=8000 -p 8000:8000 --name cloudwatch-mcp-server cloudwatch-mcp-server
```