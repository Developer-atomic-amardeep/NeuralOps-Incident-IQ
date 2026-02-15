import json
import asyncio
import uvicorn
from config import config
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
from app.multi_agent_query import (
    ArchestraMultiAgentClient, 
    AgentConfig, 
    build_investigation_prompt
)

api = FastAPI()
security = HTTPBearer(auto_error=False)

api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class UserPromptInput(BaseModel):
    GITHUB_AGENT_PROMPT: str
    SLACK_AGENT_PROMPT: str
    AWS_CLOUDWATCH_AGENT_PROMPT: str


class TokenVerifyRequest(BaseModel):
    token: str


async def verify_token(credentials: HTTPAuthorizationCredentials | None = Depends(security)):
    """Dependency to verify authentication token."""
    if not config.AUTH_TOKEN:
        return True
    
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if credentials.credentials != config.AUTH_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return True


@api.get('/health_incident_iq')
async def get_health():
    return {"message": "app running successfully!"}


@api.post('/verify-token')
async def verify_token_endpoint(request: TokenVerifyRequest):
    """Verify if the provided token is valid."""
    if not config.AUTH_TOKEN:
        return {"valid": True, "message": "Authentication not configured"}
    
    if request.token == config.AUTH_TOKEN:
        return {"valid": True, "message": "Token is valid"}
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


@api.post('/Investigator-Agent')
async def invoke_investigator_api(prompt: UserPromptInput, _: bool = Depends(verify_token)):
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
            message=prompt.GITHUB_AGENT_PROMPT,
            model=config.MODEL_GPT5_MINI,
            provider=config.PROVIDER
        ),
        AgentConfig(
            name="AWS_CLOUDWATCH_AGENT",
            agent_id=config.AWS_CLOUDWATCH_AGENT_ID,
            message=prompt.AWS_CLOUDWATCH_AGENT_PROMPT,
            model=config.MODEL_GPT5_MINI,
            provider=config.PROVIDER
        ),
        AgentConfig(
            name="SLACK_AGENT",
            agent_id=config.SLACK_AGENT_ID,
            message=prompt.SLACK_AGENT_PROMPT,
            model=config.MODEL_GPT5_MINI,
            provider=config.PROVIDER
        ),
    ]

    data_results = await client.query_all_agents(data_agents)

    investigation_prompt = build_investigation_prompt(data_results)
    
    reasoning_agent = AgentConfig(
        name="REASONING_INVESTIGATOR_AGENT",
        agent_id=config.REASONING_INVESTIGATOR_AGENT_ID,
        message=investigation_prompt,
        model=config.MODEL,
        provider=config.PROVIDER
    )
    
    investigation_result = await client.query_agent(reasoning_agent)

    return {
        "data_results": data_results,
        "investigation_result": investigation_result
    }


@api.post('/Investigator-Agent/stream')
async def invoke_investigator_api_stream(prompt: UserPromptInput, _: bool = Depends(verify_token)):
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
                message=prompt.GITHUB_AGENT_PROMPT,
                model=config.MODEL_GPT5_MINI,
                provider=config.PROVIDER
            ),
            AgentConfig(
                name="AWS_CLOUDWATCH_AGENT",
                agent_id=config.AWS_CLOUDWATCH_AGENT_ID,
                message=prompt.AWS_CLOUDWATCH_AGENT_PROMPT,
                model=config.MODEL_GPT5_MINI,
                provider=config.PROVIDER
            ),
            AgentConfig(
                name="SLACK_AGENT",
                agent_id=config.SLACK_AGENT_ID,
                message=prompt.SLACK_AGENT_PROMPT,
                model=config.MODEL_GPT5_MINI,
                provider=config.PROVIDER
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
            message=investigation_prompt,
            model=config.MODEL,
            provider=config.PROVIDER
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
