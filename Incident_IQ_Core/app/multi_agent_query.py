"""
Multi-Agent Query System with Reasoning Investigator

This module queries multiple Archestra agents in parallel and aggregates their responses.
Then sends all findings to a Reasoning Investigator agent for root cause analysis.

Agents: GITHUB_AGENT, AWS_CLOUDWATCH_AGENT, SLACK_AGENT -> REASONING_INVESTIGATOR_AGENT
"""

import httpx
import json
import uuid
import asyncio
from dataclasses import dataclass
from typing import List, Dict, Optional, Callable, AsyncGenerator, Any


@dataclass
class AgentConfig:
    """Configuration for an Archestra agent."""
    name: str
    agent_id: str
    message: str = ""


class ArchestraMultiAgentClient:
    """Async client for querying multiple Archestra agents in parallel."""
    
    def __init__(
        self,
        base_url: str = "http://localhost:9000",
        api_key: str = None,
        chat_api_key_id: str = None,
        model: str = "gpt-5",
        provider: str = "openai"
    ):
        """
        Initialize the Multi-Agent Client.
        
        Args:
            base_url: Archestra backend URL
            api_key: Your Archestra API key
            chat_api_key_id: The LLM API Key ID
            model: LLM model to use (default: gpt-5)
            provider: LLM provider (default: openai)
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.chat_api_key_id = chat_api_key_id
        self.model = model
        self.provider = provider
        
        self.headers = {
            "Authorization": api_key,
            "Content-Type": "application/json"
        }
    
    async def _create_conversation(self, client: httpx.AsyncClient, agent_id: str, title: str) -> str:
        """Create a conversation and return its ID."""
        url = f"{self.base_url}/api/chat/conversations"
        payload = {
            "agentId": agent_id,
            "title": title,
            "selectedModel": self.model,
            "selectedProvider": self.provider,
            "chatApiKeyId": self.chat_api_key_id
        }
        
        response = await client.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()["id"]
    
    async def _send_message_and_collect(
        self, 
        client: httpx.AsyncClient, 
        conversation_id: str, 
        message: str,
        on_text_delta: Optional[Callable[[str], None]] = None
    ) -> Dict:
        """Send message and collect the full response via SSE streaming."""
        url = f"{self.base_url}/api/chat"
        payload = {
            "id": conversation_id,
            "messages": [
                {
                    "id": f"msg-{uuid.uuid4().hex[:8]}",
                    "role": "user",
                    "content": message,
                    "parts": [{"type": "text", "text": message}]
                }
            ],
            "trigger": "submit-message"
        }
        
        text_parts = []
        tool_calls = []
        tool_outputs = []
        errors = []
        
        async with client.stream("POST", url, headers=self.headers, json=payload, timeout=300) as response:
            response.raise_for_status()
            
            async for line in response.aiter_lines():
                if line and line.startswith('data: '):
                    data = line[6:]
                    if data == '[DONE]':
                        break
                    try:
                        event = json.loads(data)
                        event_type = event.get("type", "")
                        
                        if event_type == "text-delta":
                            delta = event.get("delta", "")
                            text_parts.append(delta)
                            if on_text_delta:
                                on_text_delta(delta)
                        
                        elif event_type == "tool-input-available":
                            tool_calls.append({
                                "tool": event.get("toolName"),
                                "input": event.get("input"),
                                "toolCallId": event.get("toolCallId")
                            })
                        
                        elif event_type == "tool-output-available":
                            tool_outputs.append({
                                "toolCallId": event.get("toolCallId"),
                                "output": event.get("output")
                            })
                        
                        elif event_type == "tool-output-error":
                            errors.append(event.get("errorText", ""))
                    
                    except json.JSONDecodeError:
                        continue
        
        return {
            "text": "".join(text_parts),
            "tool_calls": tool_calls,
            "tool_outputs": tool_outputs,
            "errors": errors
        }
    
    async def query_agent(
        self, 
        agent_config: AgentConfig,
        on_text_delta: Optional[Callable[[str], None]] = None
    ) -> Dict:
        """
        Query a single agent and return the result.
        
        Args:
            agent_config: Configuration for the agent to query
            on_text_delta: Optional callback for streaming text deltas
            
        Returns:
            Dict with agent name, response text, tool calls, and errors
        """
        try:
            async with httpx.AsyncClient() as client:
                conversation_id = await self._create_conversation(
                    client,
                    agent_config.agent_id,
                    f"{agent_config.name} Query"
                )
                
                result = await self._send_message_and_collect(
                    client,
                    conversation_id, 
                    agent_config.message,
                    on_text_delta=on_text_delta
                )
                
                return {
                    "agent": agent_config.name,
                    "status": "success",
                    "response": result["text"],
                    "tool_calls": result["tool_calls"],
                    "tool_outputs": result["tool_outputs"],
                    "errors": result["errors"]
                }
        except Exception as e:
            return {
                "agent": agent_config.name,
                "status": "error",
                "error": str(e),
                "response": None,
                "tool_calls": [],
                "tool_outputs": [],
                "errors": []
            }
    
    async def query_all_agents(self, agents: List[AgentConfig]) -> List[Dict]:
        """
        Query multiple agents concurrently using asyncio.
        
        Args:
            agents: List of agent configurations
            
        Returns:
            List of results from all agents
        """
        tasks = [self.query_agent(agent) for agent in agents]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "agent": agents[i].name,
                    "status": "error",
                    "error": str(result),
                    "response": None,
                    "tool_calls": [],
                    "tool_outputs": [],
                    "errors": []
                })
            else:
                processed_results.append(result)
        
        return processed_results

    async def stream_agent(
        self,
        agent_config: AgentConfig,
        phase: int,
        queue: asyncio.Queue
    ) -> Dict:
        """
        Stream events from a single agent to a queue.
        
        Args:
            agent_config: Configuration for the agent
            phase: Phase number (1 or 2)
            queue: Async queue to put events into
            
        Returns:
            Final result dict with full response
        """
        agent_name = agent_config.name
        text_parts = []
        tool_calls = []
        tool_outputs = []
        errors = []
        
        try:
            async with httpx.AsyncClient() as client:
                await queue.put({
                    "event": "agent_start",
                    "agent": agent_name,
                    "phase": phase,
                    "data": {}
                })
                
                conversation_id = await self._create_conversation(
                    client,
                    agent_config.agent_id,
                    f"{agent_name} Query"
                )
                
                url = f"{self.base_url}/api/chat"
                payload = {
                    "id": conversation_id,
                    "messages": [
                        {
                            "id": f"msg-{uuid.uuid4().hex[:8]}",
                            "role": "user",
                            "content": agent_config.message,
                            "parts": [{"type": "text", "text": agent_config.message}]
                        }
                    ],
                    "trigger": "submit-message"
                }
                
                async with client.stream("POST", url, headers=self.headers, json=payload, timeout=300) as response:
                    response.raise_for_status()
                    
                    async for line in response.aiter_lines():
                        if line and line.startswith('data: '):
                            data = line[6:]
                            if data == '[DONE]':
                                break
                            try:
                                event = json.loads(data)
                                event_type = event.get("type", "")
                                
                                if event_type == "text-start":
                                    await queue.put({
                                        "event": "text_start",
                                        "agent": agent_name,
                                        "phase": phase,
                                        "data": {}
                                    })
                                
                                elif event_type == "text-delta":
                                    delta = event.get("delta", "")
                                    text_parts.append(delta)
                                    await queue.put({
                                        "event": "text_delta",
                                        "agent": agent_name,
                                        "phase": phase,
                                        "data": {"delta": delta}
                                    })
                                
                                elif event_type == "text-end":
                                    await queue.put({
                                        "event": "text_end",
                                        "agent": agent_name,
                                        "phase": phase,
                                        "data": {}
                                    })
                                
                                elif event_type == "tool-output-available":
                                    output = event.get("output", "")
                                    tool_outputs.append({
                                        "toolCallId": event.get("toolCallId"),
                                        "output": output
                                    })
                                    await queue.put({
                                        "event": "tool_output",
                                        "agent": agent_name,
                                        "phase": phase,
                                        "data": {
                                            "toolCallId": event.get("toolCallId"),
                                            "output": output
                                        }
                                    })
                                
                                elif event_type == "tool-input-available":
                                    tool_calls.append({
                                        "tool": event.get("toolName"),
                                        "input": event.get("input"),
                                        "toolCallId": event.get("toolCallId")
                                    })
                                
                                elif event_type == "tool-output-error":
                                    error_text = event.get("errorText", "")
                                    errors.append(error_text)
                                    await queue.put({
                                        "event": "error",
                                        "agent": agent_name,
                                        "phase": phase,
                                        "data": {"message": error_text}
                                    })
                            
                            except json.JSONDecodeError:
                                continue
                
                result = {
                    "agent": agent_name,
                    "status": "success",
                    "response": "".join(text_parts),
                    "tool_calls": tool_calls,
                    "tool_outputs": tool_outputs,
                    "errors": errors
                }
                
                await queue.put({
                    "event": "agent_complete",
                    "agent": agent_name,
                    "phase": phase,
                    "data": {"response": result["response"]}
                })
                
                return result
                
        except Exception as e:
            await queue.put({
                "event": "error",
                "agent": agent_name,
                "phase": phase,
                "data": {"message": str(e)}
            })
            await queue.put({
                "event": "agent_complete",
                "agent": agent_name,
                "phase": phase,
                "data": {"response": None, "error": str(e)}
            })
            return {
                "agent": agent_name,
                "status": "error",
                "error": str(e),
                "response": None,
                "tool_calls": [],
                "tool_outputs": [],
                "errors": []
            }

    async def stream_all_agents(
        self,
        agents: List[AgentConfig],
        phase: int = 1
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream events from multiple agents concurrently.
        
        Args:
            agents: List of agent configurations
            phase: Phase number
            
        Yields:
            Event dicts with agent tag
        """
        queue: asyncio.Queue = asyncio.Queue()
        results: List[Dict] = []
        
        async def run_agents():
            tasks = [
                self.stream_agent(agent, phase, queue)
                for agent in agents
            ]
            agent_results = await asyncio.gather(*tasks, return_exceptions=True)
            for i, result in enumerate(agent_results):
                if isinstance(result, Exception):
                    results.append({
                        "agent": agents[i].name,
                        "status": "error",
                        "error": str(result),
                        "response": None,
                        "tool_calls": [],
                        "tool_outputs": [],
                        "errors": []
                    })
                else:
                    results.append(result)
            await queue.put(None)
        
        task = asyncio.create_task(run_agents())
        
        while True:
            event = await queue.get()
            if event is None:
                break
            yield event
        
        await task
        
        yield {
            "event": "phase_complete",
            "phase": phase,
            "data": {"results": results}
        }


def build_investigation_prompt(results: List[Dict]) -> str:
    """
    Build the investigation prompt with all agent findings.
    
    Args:
        results: List of results from data-gathering agents
        
    Returns:
        Formatted prompt for the reasoning investigator
    """
    prompt = """# Incident Investigation Request

You are an expert Site Reliability Engineer investigating a production incident.
Below are findings from three different data sources. Your task is to:

1. CORRELATE the evidence across all sources
2. IDENTIFY the root cause of the incident
3. EXPLAIN the chain of events that led to the issue
4. RECOMMEND specific remediation actions

---

## Evidence from Data Sources

"""
    
    for result in results:
        agent_name = result.get('agent', 'Unknown Agent')
        status = result.get('status', 'unknown')
        
        prompt += f"### {agent_name}\n"
        prompt += f"**Status:** {status}\n\n"
        
        if status == 'success':
            response = result.get('response', 'No response')
            prompt += f"**Findings:**\n{response}\n\n"
        else:
            error = result.get('error', 'Unknown error')
            prompt += f"**Error:** {error}\n\n"
        
        prompt += "---\n\n"
    
    prompt += """## Your Analysis

Please provide:

### 1. Root Cause Identification
What is the primary cause of this incident? Be specific.

### 2. Evidence Correlation
How do the findings from CloudWatch, GitHub, and Slack connect?
Show the timeline and causal chain.

### 3. Timeline of Events
Reconstruct what happened in chronological order.

### 4. Recommended Actions
What specific steps should be taken to resolve this incident?
List in order of priority.

### 5. Prevention
How can similar incidents be prevented in the future?

---

Important: Base your analysis ONLY on the evidence provided. Be direct and actionable.
"""
    
    return prompt
