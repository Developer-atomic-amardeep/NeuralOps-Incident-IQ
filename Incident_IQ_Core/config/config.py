"""
Archestra Configuration
Centralized configuration for all Archestra agents and API settings.
"""
import os


# =============================================================================
# API CONFIGURATION
# =============================================================================

BASE_URL = os.getenv("ARCHESTRA_BASE_URL", "http://localhost:9000")
API_KEY = os.getenv("ARCHESTRA_API_KEY", "archestra_JKWpeQaTnHoIqavfncZYRtiSlzMITlGDjCHfPkOGZkjJTWZMirwcbrjiJsaKiyoK")
CHAT_API_KEY_ID = os.getenv("ARCHESTRA_CHAT_API_KEY_ID", "5cfe9ced-5d81-4e2c-80de-711d79e585d9")

# =============================================================================
# LLM CONFIGURATION
# =============================================================================

# Default model for multi-agent queries
MODEL = "gpt-5"
PROVIDER = "openai"

# Alternative model for single agent testing
MODEL_GPT4O = "gpt-4o"

# =============================================================================
# AGENT IDs
# =============================================================================

# Data-gathering agents
GITHUB_AGENT_ID = "9f26efa2-ade4-4bbe-808b-7d8fd4b11095"
AWS_CLOUDWATCH_AGENT_ID = "ae3e7cec-3d6c-42fd-b64f-635ab6d0d8a8"
SLACK_AGENT_ID = "27319db8-58a9-4a76-bc94-03b25bfce954"

# Reasoning/Analysis agent
REASONING_INVESTIGATOR_AGENT_ID = "b846cf5f-19a5-456d-81ea-711427fe30ba"

# =============================================================================
# DEFAULT AGENT MESSAGES
# =============================================================================

# Default prompts for testing and development
DEFAULT_GITHUB_MESSAGE = "List the last 4 commits from the repo 'hackfest-mono-repo' from my developer-atomic-amardeep's account, get the commits like any of the last ones no need to be specific for 24 hours only"

DEFAULT_CLOUDWATCH_MESSAGE = "List me the logs from the logs group of last 24hours from the log group /incident-iq/api-errors, get me all the logs no need to be specific on errors only, like the mannually added too will work."

DEFAULT_SLACK_MESSAGE = "Get me all the messages on the channel just-a-random-chit-chat, can be any message no need to be specific on the errors or something, look for last 36 hours"

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_base_config():
    """
    Get base configuration dictionary for Archestra clients.
    
    Returns:
        dict: Configuration with base_url, api_key, chat_api_key_id, model, provider
    """
    return {
        "base_url": BASE_URL,
        "api_key": API_KEY,
        "chat_api_key_id": CHAT_API_KEY_ID,
        "model": MODEL,
        "provider": PROVIDER
    }


def get_agent_config(agent_name: str) -> dict:
    """
    Get configuration for a specific agent.
    
    Args:
        agent_name: Name of the agent (e.g., 'github', 'cloudwatch', 'slack', 'reasoning')
        
    Returns:
        dict: Configuration with agent_id and default message
    """
    agents = {
        "github": {
            "agent_id": GITHUB_AGENT_ID,
            # "default_message": DEFAULT_GITHUB_MESSAGE
        },
        "cloudwatch": {
            "agent_id": AWS_CLOUDWATCH_AGENT_ID,
            # "default_message": DEFAULT_CLOUDWATCH_MESSAGE
        },
        "slack": {
            "agent_id": SLACK_AGENT_ID,
            # "default_message": DEFAULT_SLACK_MESSAGE
        },
        "reasoning": {
            "agent_id": REASONING_INVESTIGATOR_AGENT_ID,
            # "default_message": None
        }
    }
    
    return agents.get(agent_name.lower(), {})

