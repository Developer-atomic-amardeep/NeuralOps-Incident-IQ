import json
import asyncio
import uvicorn
import httpx
from config import config
from fastapi import FastAPI
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
from app.multi_agent_query import (
    ArchestraMultiAgentClient, 
    AgentConfig, 
    build_investigation_prompt
)

api = FastAPI()


class UserPromptInput(BaseModel):
    GITHUB_AGENT_PROMPT: str
    SLACK_AGENT_PROMPT: str
    AWS_CLOUDWATCH_AGENT_PROMPT: str


@api.get('/health_incident_iq')
async def get_health():
    return {"message": "app running successfully!"}


@api.get('/debug/config')
async def debug_config():
    """Debug endpoint to check if environment variables are loaded correctly."""
    return {
        "base_url": config.BASE_URL,
        "api_key_set": bool(config.API_KEY),
        "api_key_length": len(config.API_KEY) if config.API_KEY else 0,
        "api_key_prefix": config.API_KEY[:20] + "..." if config.API_KEY and len(config.API_KEY) > 20 else config.API_KEY,
        "chat_api_key_id_set": bool(config.CHAT_API_KEY_ID),
        "chat_api_key_id": config.CHAT_API_KEY_ID,
        "github_agent_id": config.GITHUB_AGENT_ID,
        "cloudwatch_agent_id": config.AWS_CLOUDWATCH_AGENT_ID,
        "slack_agent_id": config.SLACK_AGENT_ID,
        "reasoning_agent_id": config.REASONING_INVESTIGATOR_AGENT_ID
    }


@api.get('/debug/test-archestra-connection')
async def test_archestra_connection():
    """Test connectivity and authentication with archestra-platform using all possible URL variations."""
    import socket
    
    # Get archestra-platform container IP if possible
    archestra_ip = None
    try:
        archestra_ip = socket.gethostbyname("archestra-platform")
    except:
        pass
    
    # All possible URL variations to test
    url_variants = [
        ("archestra-platform:9000", "http://archestra-platform:9000"),
        ("localhost:9000", "http://localhost:9000"),
        ("127.0.0.1:9000", "http://127.0.0.1:9000"),
    ]
    
    if archestra_ip:
        url_variants.append((f"{archestra_ip}:9000", f"http://{archestra_ip}:9000"))
    
    # Add current config URL if not already in list
    if config.BASE_URL not in [url for _, url in url_variants]:
        url_variants.insert(0, ("config.BASE_URL", config.BASE_URL))
    
    results = {
        "current_config_base_url": config.BASE_URL,
        "archestra_container_ip": archestra_ip,
        "api_key_set": bool(config.API_KEY),
        "tests": {}
    }
    
    headers = {
        "Authorization": config.API_KEY,
        "Content-Type": "application/json"
    }
    
    # Test each URL variant
    for variant_name, base_url in url_variants:
        test_result = {
            "url": base_url,
            "connectivity": {},
            "authentication": {}
        }
        
        # Test 1: Basic connectivity (health check)
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Try /health endpoint first
                try:
                    response = await client.get(f"{base_url}/health", follow_redirects=True, timeout=5.0)
                    test_result["connectivity"] = {
                        "status": "success",
                        "status_code": response.status_code,
                        "message": f"Can reach {variant_name}",
                        "response_preview": response.text[:100] if response.text else None
                    }
                except:
                    # If /health doesn't exist, try root
                    try:
                        response = await client.get(f"{base_url}/", follow_redirects=True, timeout=5.0)
                        test_result["connectivity"] = {
                            "status": "success",
                            "status_code": response.status_code,
                            "message": f"Can reach {variant_name} (root endpoint)",
                            "response_preview": response.text[:100] if response.text else None
                        }
                    except Exception as e:
                        test_result["connectivity"] = {
                            "status": "failed",
                            "error": str(e),
                            "message": f"Cannot reach {variant_name}"
                        }
        except httpx.ConnectError as e:
            test_result["connectivity"] = {
                "status": "failed",
                "error": str(e),
                "message": f"Cannot connect to {variant_name} - network/DNS issue"
            }
        except Exception as e:
            test_result["connectivity"] = {
                "status": "error",
                "error": str(e),
                "message": f"Unexpected error connecting to {variant_name}"
            }
        
        # Test 2: API authentication (only if connectivity worked)
        if test_result["connectivity"].get("status") == "success":
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(
                        f"{base_url}/api/chat/conversations",
                        headers=headers,
                        timeout=5.0
                    )
                    test_result["authentication"] = {
                        "status": "success" if response.status_code == 200 else "failed",
                        "status_code": response.status_code,
                        "message": "Authentication successful" if response.status_code == 200 else f"Auth failed: {response.status_code}",
                        "response_preview": response.text[:200] if response.text else None
                    }
            except httpx.HTTPStatusError as e:
                test_result["authentication"] = {
                    "status": "failed",
                    "status_code": e.response.status_code,
                    "error": str(e),
                    "message": f"HTTP error: {e.response.status_code}",
                    "response_preview": e.response.text[:200] if e.response.text else None
                }
            except Exception as e:
                test_result["authentication"] = {
                    "status": "error",
                    "error": str(e),
                    "message": f"Error testing authentication on {variant_name}"
                }
        else:
            test_result["authentication"] = {
                "status": "skipped",
                "message": "Skipped - connectivity test failed"
            }
        
        results["tests"][variant_name] = test_result
    
    # Summary: Find which URLs work
    working_urls = []
    for variant_name, test_result in results["tests"].items():
        if test_result.get("authentication", {}).get("status") == "success":
            working_urls.append({
                "name": variant_name,
                "url": test_result["url"],
                "status_code": test_result.get("authentication", {}).get("status_code")
            })
    
    results["summary"] = {
        "working_urls": working_urls,
        "recommended_url": working_urls[0]["url"] if working_urls else None
    }
    
    # Add debug info about the API key being used
    results["debug_info"] = {
        "api_key_length": len(config.API_KEY) if config.API_KEY else 0,
        "api_key_prefix": config.API_KEY[:15] + "..." if config.API_KEY and len(config.API_KEY) > 15 else config.API_KEY,
        "api_key_suffix": "..." + config.API_KEY[-10:] if config.API_KEY and len(config.API_KEY) > 10 else config.API_KEY,
        "authorization_header_format": f"Authorization: {config.API_KEY[:15]}..." if config.API_KEY else "Authorization: (empty)",
        "note": "If authentication fails, verify the API key in Archestra UI: Settings > Your Account > API Keys"
    }
    
    return results


@api.post('/Investigator-Agent')
async def invoke_investigator_api(prompt: UserPromptInput):
    """Non-streaming endpoint that returns full results."""
    client = ArchestraMultiAgentClient(
        base_url=config.BASE_URL,
        api_key=config.API_KEY,
        chat_api_key_id=config.CHAT_API_KEY_ID,
        model=config.MODEL,
        provider=config.PROVIDER
    )

    data_agents = [
        AgentConfig(
            name="GITHUB_AGENT",
            agent_id=config.GITHUB_AGENT_ID,
            message=prompt.GITHUB_AGENT_PROMPT
        ),
        AgentConfig(
            name="AWS_CLOUDWATCH_AGENT",
            agent_id=config.AWS_CLOUDWATCH_AGENT_ID,
            message=prompt.AWS_CLOUDWATCH_AGENT_PROMPT
        ),
        AgentConfig(
            name="SLACK_AGENT",
            agent_id=config.SLACK_AGENT_ID,
            message=prompt.SLACK_AGENT_PROMPT
        ),
    ]

    data_results = await client.query_all_agents(data_agents)

    investigation_prompt = build_investigation_prompt(data_results)
    
    reasoning_agent = AgentConfig(
        name="REASONING_INVESTIGATOR_AGENT",
        agent_id=config.REASONING_INVESTIGATOR_AGENT_ID,
        message=investigation_prompt
    )
    
    investigation_result = await client.query_agent(reasoning_agent)

    return {
        "data_results": data_results,
        "investigation_result": investigation_result
    }


@api.post('/Investigator-Agent/stream')
async def invoke_investigator_api_stream(prompt: UserPromptInput):
    """SSE streaming endpoint that streams all events."""
    
    async def event_generator():
        client = ArchestraMultiAgentClient(
            base_url=config.BASE_URL,
            api_key=config.API_KEY,
            chat_api_key_id=config.CHAT_API_KEY_ID,
            model=config.MODEL,
            provider=config.PROVIDER
        )

        data_agents = [
            AgentConfig(
                name="GITHUB_AGENT",
                agent_id=config.GITHUB_AGENT_ID,
                message=prompt.GITHUB_AGENT_PROMPT
            ),
            AgentConfig(
                name="AWS_CLOUDWATCH_AGENT",
                agent_id=config.AWS_CLOUDWATCH_AGENT_ID,
                message=prompt.AWS_CLOUDWATCH_AGENT_PROMPT
            ),
            AgentConfig(
                name="SLACK_AGENT",
                agent_id=config.SLACK_AGENT_ID,
                message=prompt.SLACK_AGENT_PROMPT
            ),
        ]

        # Phase 1: Stream events from all data-gathering agents
        data_results = []
        async for event in client.stream_all_agents(data_agents, phase=1):
            if event["event"] == "phase_complete":
                data_results = event["data"]["results"]
            yield {"data": json.dumps(event)}

        # Phase 2: Stream events from Reasoning Investigator
        investigation_prompt = build_investigation_prompt(data_results)
        
        reasoning_agent = AgentConfig(
            name="REASONING_INVESTIGATOR",
            agent_id=config.REASONING_INVESTIGATOR_AGENT_ID,
            message=investigation_prompt
        )

        queue: asyncio.Queue = asyncio.Queue()
        
        async def run_investigator():
            await client.stream_agent(reasoning_agent, phase=2, queue=queue)
            await queue.put(None)
        
        task = asyncio.create_task(run_investigator())
        
        while True:
            event = await queue.get()
            if event is None:
                break
            yield {"data": json.dumps(event)}
        
        await task
        
        yield {"data": json.dumps({
            "event": "phase_complete",
            "phase": 2,
            "data": {}
        })}
        
        yield {"data": "[DONE]"}

    return EventSourceResponse(event_generator())


if __name__ == "__main__":
    uvicorn.run(api, host="0.0.0.0", port=8050)
