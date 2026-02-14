import json
import requests

URL = "http://34.203.243.44:8050/Investigator-Agent/stream"
OUTPUT_FILE = "investigator_stream_output.json"

payload = {
    "GITHUB_AGENT_PROMPT": "List the last 4 commits from the repo 'hackfest-mono-repo' from my developer-atomic-amardeep's account, get the commits like any of the last ones no need to be specific for 24 hours only",
    "SLACK_AGENT_PROMPT": "Get me all the messages on the channel just-a-random-chit-chat, can be any message no need to be specific on the errors or something, look for last 36 hours",
    "AWS_CLOUDWATCH_AGENT_PROMPT": "List me the logs from the logs group /aws/lambda/incidentiq-payment-service, dont be specific to get the logs from last 24 hours only.",
}

def main():
    events = []

    with requests.post(URL, json=payload, stream=True) as resp:
        resp.raise_for_status()
        for line in resp.iter_lines(decode_unicode=True):
            if not line:
                continue
            if line.startswith("data:"):
                data_str = line[len("data:"):].strip()
                if data_str == "[DONE]":
                    break
                try:
                    event = json.loads(data_str)
                except json.JSONDecodeError:
                    # if a non‑JSON line appears, skip it
                    continue
                events.append(event)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(events, f, indent=2)

if __name__ == "__main__":
    main()