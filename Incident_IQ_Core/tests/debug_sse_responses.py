"""
Debug script to capture and display all raw SSE responses from Archestra Chat API.

This script sends a test message and prints every event received with full details.
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path for config import
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import config
from tests.archestra_chat_api import ArchestraChatClient


def pretty_print_event(event_num: int, event: dict):
    """Pretty print an SSE event with all its fields."""
    print(f"\n{'='*80}")
    print(f"EVENT #{event_num}")
    print(f"{'='*80}")
    print(json.dumps(event, indent=2, ensure_ascii=False))
    print(f"{'='*80}")


def capture_all_events():
    """Capture and display all SSE events from a test conversation."""
    
    # Create client using centralized configuration
    print("="*80)
    print("ARCHESTRA SSE RESPONSE DEBUGGER")
    print("="*80)
    print(f"Starting at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Base URL: {config.BASE_URL}")
    print(f"Agent ID: {config.GITHUB_AGENT_ID}")
    print("="*80)
    
    client = ArchestraChatClient(
        base_url=config.BASE_URL,
        api_key=config.API_KEY,
        agent_id=config.GITHUB_AGENT_ID,
        chat_api_key_id=config.CHAT_API_KEY_ID,
        model=config.MODEL_GPT4O,
        provider=config.PROVIDER
    )
    
    # Create conversation
    print("\n[*] Creating conversation...")
    conversation = client.create_conversation("Debug SSE Responses")
    print(f"[OK] Conversation ID: {conversation['id']}")
    
    # Test message
    test_message = "List the last 3 commits from the repo 'sentinel-hackfest-mono-repo' from my account developer-atomic-amardeep"
    print(f"\n[*] Sending message: '{test_message}'")
    print("\n" + "="*80)
    print("STREAMING EVENTS:")
    print("="*80)
    
    # Capture all events
    events_log = []
    event_types_count = {}
    event_num = 0
    text_streaming = False
    
    try:
        for event in client.send_message(test_message):
            event_num += 1
            events_log.append(event)
            
            # Track event types
            event_type = event.get("type", "unknown")
            event_types_count[event_type] = event_types_count.get(event_type, 0) + 1
            
            # Handle text-delta differently - stream it
            if event_type == "text-delta":
                if not text_streaming:
                    print("\n[STREAMING TEXT]:", end=" ", flush=True)
                    text_streaming = True
                print(event.get("delta", ""), end="", flush=True)
            else:
                # For non-text events, show full details
                if text_streaming:
                    print("\n")  # End the streaming text line
                    text_streaming = False
                pretty_print_event(event_num, event)
            
    except Exception as e:
        if text_streaming:
            print("\n")
        print(f"\n[ERROR] Exception occurred: {e}")
    
    # End streaming text if still active
    if text_streaming:
        print("\n")
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total events received: {event_num}")
    print(f"\nEvent types breakdown:")
    for event_type, count in sorted(event_types_count.items()):
        print(f"  - {event_type}: {count}")
    
    # Save to file
    output_file = "sse_events_log.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "config": {
                "agent_id": config.GITHUB_AGENT_ID,
                "model": config.MODEL_GPT4O,
                "provider": config.PROVIDER
            },
            "message": test_message,
            "total_events": event_num,
            "event_types_count": event_types_count,
            "events": events_log
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n[OK] Full event log saved to: {output_file}")
    print(f"[DONE] Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    capture_all_events()

