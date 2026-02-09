"""
Archestra Chat API Client

This module provides a simple interface to interact with Archestra agents
via the Chat API. It handles conversation creation and message streaming.
"""

import requests
import json
import uuid
from typing import Generator, Optional
import sys
from pathlib import Path

# Add parent directory to path for config import
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import config


class ArchestraChatClient:
    """Client for interacting with Archestra Chat API."""
    
    def __init__(
        self,
        base_url: str = "http://localhost:9000",
        api_key: str = None,
        agent_id: str = None,
        chat_api_key_id: str = None,
        model: str = "gpt-4o",
        provider: str = "openai"
    ):
        """
        Initialize the Archestra Chat Client.
        
        Args:
            base_url: Archestra backend URL (default: http://localhost:9000)
            api_key: Your Archestra API key (from Settings > Your Account > API Keys)
            agent_id: The agent ID to chat with
            chat_api_key_id: The LLM API Key ID (from Settings > LLM API Keys)
            model: LLM model to use (default: gpt-4o)
            provider: LLM provider (default: openai)
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.agent_id = agent_id
        self.chat_api_key_id = chat_api_key_id
        self.model = model
        self.provider = provider
        self.conversation_id = None
        
        self.headers = {
            "Authorization": api_key,  # No "Bearer" prefix for Archestra API keys
            "Content-Type": "application/json"
        }
    
    def create_conversation(self, title: str = "API Conversation") -> dict:
        """
        Create a new conversation with the agent.
        
        Args:
            title: Title for the conversation
            
        Returns:
            Conversation object with id, agentId, etc.
        """
        url = f"{self.base_url}/api/chat/conversations"
        payload = {
            "agentId": self.agent_id,
            "title": title,
            "selectedModel": self.model,
            "selectedProvider": self.provider,
            "chatApiKeyId": self.chat_api_key_id
        }
        
        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        
        conversation = response.json()
        self.conversation_id = conversation["id"]
        return conversation
    
    def send_message(self, message: str, conversation_id: str = None) -> Generator[dict, None, None]:
        """
        Send a message and stream the response.
        
        Args:
            message: The message to send
            conversation_id: Optional conversation ID (uses current if not provided)
            
        Yields:
            Parsed SSE events from the stream
        """
        conv_id = conversation_id or self.conversation_id
        if not conv_id:
            raise ValueError("No conversation ID. Call create_conversation() first.")
        
        url = f"{self.base_url}/api/chat"
        payload = {
            "id": conv_id,
            "messages": [
                {
                    "id": f"msg-{uuid.uuid4().hex[:8]}",
                    "role": "user",
                    "content": message,
                    "parts": [
                        {
                            "type": "text",
                            "text": message
                        }
                    ]
                }
            ],
            "trigger": "submit-message"
        }
        
        response = requests.post(
            url, 
            headers=self.headers, 
            json=payload, 
            stream=True,
            timeout=120
        )
        response.raise_for_status()
        
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    data = line_str[6:]  # Remove 'data: ' prefix
                    if data == '[DONE]':
                        break
                    try:
                        yield json.loads(data)
                    except json.JSONDecodeError:
                        continue
    
    def send_message_and_get_text(self, message: str, conversation_id: str = None) -> str:
        """
        Send a message and return the complete text response.
        
        Args:
            message: The message to send
            conversation_id: Optional conversation ID
            
        Returns:
            Complete text response from the agent
        """
        text_parts = []
        tool_calls = []
        
        for event in self.send_message(message, conversation_id):
            event_type = event.get("type", "")
            
            if event_type == "text-delta":
                text_parts.append(event.get("delta", ""))
            elif event_type == "tool-input-available":
                tool_calls.append({
                    "tool": event.get("toolName"),
                    "input": event.get("input")
                })
            elif event_type == "tool-output-error":
                print(f"[WARN] Tool error: {event.get('errorText', '')[:200]}...")
        
        return "".join(text_parts)
    
    def chat(self, message: str) -> str:
        """
        Simple chat interface - creates conversation if needed and sends message.
        
        Args:
            message: The message to send
            
        Returns:
            Agent's response text
        """
        if not self.conversation_id:
            self.create_conversation()
        
        return self.send_message_and_get_text(message)


def main():
    """Example usage of the Archestra Chat Client."""
    
    # Create client using centralized configuration
    client = ArchestraChatClient(
        base_url=config.BASE_URL,
        api_key=config.API_KEY,
        agent_id=config.GITHUB_AGENT_ID,
        chat_api_key_id=config.CHAT_API_KEY_ID,
        model=config.MODEL_GPT4O,
        provider=config.PROVIDER
    )
    
    # Create a conversation
    print("[*] Creating conversation...")
    conversation = client.create_conversation("GitHub Commits Analysis")
    print(f"[OK] Conversation created: {conversation['id']}")
    
    # Send a message
    print("\n[*] Sending message...")
    message = "List the last 4 commits from the repo 'sentinel-hackfest-mono-repo' from my account only, i.e developer-atomic-amardeep"  # Use a public repo!
    
    print(f"User: {message}\n")
    print("Agent: ", end="", flush=True)
    
    # Stream the response
    for event in client.send_message(message):
        event_type = event.get("type", "")
        
        if event_type == "text-delta":
            print(event.get("delta", ""), end="", flush=True)
        elif event_type == "tool-input-available":
            tool_name = event.get("toolName", "").split("__")[-1]
            print(f"\n[TOOL] Calling: {tool_name}", flush=True)
        elif event_type == "tool-output-error":
            print(f"\n[WARN] Tool error", flush=True)
    
    print("\n\n[DONE]")


if __name__ == "__main__":
    main()

