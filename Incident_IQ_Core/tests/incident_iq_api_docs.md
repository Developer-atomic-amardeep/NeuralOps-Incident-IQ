## Incident IQ Core API Reference

### GET `/health_incident_iq`

- **Description**: Simple health-check endpoint to verify that the Incident IQ Core service is running.
- **Method**: `GET`
- **Request body**: None
- **Query params**: None
- **Response (200)**:

```json
{
  "message": "app running successfully!"
}
```

- **Example frontend call (fetch)**:

```ts
const res = await fetch('http://<backend-host>:8050/health_incident_iq');
const data = await res.json();
```

---

### POST `/Investigator-Agent/stream`

- **Description**: Server-Sent Events (SSE) streaming endpoint that orchestrates multiple data agents and a reasoning investigator agent, streaming events back to the client.
- **Method**: `POST`
- **Request body (JSON)**: Must match the `UserPromptInput` model:

```json
{
  "GITHUB_AGENT_PROMPT": "Prompt for the GitHub agent",
  "SLACK_AGENT_PROMPT": "Prompt for the Slack agent",
  "AWS_CLOUDWATCH_AGENT_PROMPT": "Prompt for the CloudWatch agent"
}
```

- **Response type**: SSE stream (`text/event-stream`) with incremental `data:` chunks encoded as JSON strings, plus a final `[DONE]` marker.

- **Example frontend call using `fetch` streaming (TypeScript/JavaScript)**:

```ts
const controller = new AbortController();

async function callInvestigatorStream() {
  const res = await fetch('http://<backend-host>:8050/Investigator-Agent/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      GITHUB_AGENT_PROMPT: '...',
      SLACK_AGENT_PROMPT: '...',
      AWS_CLOUDWATCH_AGENT_PROMPT: '...'
    }),
    signal: controller.signal
  });

  const reader = res.body!.getReader();
  const decoder = new TextDecoder('utf-8');

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    const chunk = decoder.decode(value, { stream: true });
    // Handle each SSE chunk (parse lines starting with "data:")
    console.log(chunk);
  }
}

// To stop streaming:
// controller.abort();
```


