// API Configuration
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api";

/**
 * Get authentication headers
 */
function getAuthHeaders(): HeadersInit {
  const token = sessionStorage.getItem("auth_token");
  const headers: HeadersInit = {};
  
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  
  return headers;
}

// Agent prompts - you can customize these
export const DEFAULT_PROMPTS = {
  GITHUB_AGENT_PROMPT: "List the last 4 commits from the repo 'hackfest-mono-repo' from my developer-atomic-amardeep's account, get the commits like any of the last ones no need to be specific for 24 hours only",
  AWS_CLOUDWATCH_AGENT_PROMPT: `We got the following error reported by pager duty to us kindly look into this what might be the possibilities of causing this by investigating the logs and changes on the related resources that are disturbed as per the pager duty. this is the time around which you need to investigate keep in mind that aws mcp tools works only with the UTC time and time to investigate is 11:30:00 UTC. the time given in pagerduty logs are IST time based. 
{ "incident_id": "PD-INC-99218", "status": "triggered", "service": "/aws/lambda/RevenueReconciliationEngine", "severity": "CRITICAL", "summary": "Critical Performance Degradation: RDS [prod-db-01]", "details": { "metric_name": "CPUUtilization", "threshold": "90%", "actual_value": "98.2%", "impact": "Revenue Reconciliation Engine failing SLAs", "last_success_run": "2026-02-14T16:30:00 IST (Duration: 24.0s)", "current_run_start": "2026-02-14T17:15:00 IST (Duration: 45.0s+)", "log_group": "/aws/lambda/RevenueReconciliationEngine", "region": "us-east-1" }, "timestamp": "2026-02-14T17:16:02 IST" }`,
  SLACK_AGENT_PROMPT: `we have got the following errors from the pager duty we need to find the relevant messages from the channels in the slack, which  points or hints to the problem reported by the pager duty.
{ "incident_id": "PD-INC-99218", "status": "triggered", "service": "incidentiq-payment-service", "severity": "CRITICAL", "summary": "Critical Performance Degradation: RDS [prod-db-01]", "details": { "metric_name": "CPUUtilization", "threshold": "90%", "actual_value": "98.2%", "impact": "Revenue Reconciliation Engine failing SLAs", "last_success_run": "2026-02-14T16:30:00 IST (Duration: 24.0s)", "current_run_start": "2026-02-14T17:15:00 IST (Duration: 45.0s+)", "log_group": "/aws/lambda/incidentiq-payment-service", "region": "us-east-1" }, "timestamp": "2026-02-14T17:16:02 IST" }`
};

export interface AgentLogEntry {
  id: string;
  timestamp: string;
  level: "info" | "warn" | "error" | "success";
  message: string;
}

export type LogUpdateAction = 
  | { type: "add"; logEntry: AgentLogEntry }
  | { type: "update"; id: string; updates: Partial<AgentLogEntry> };

export interface StreamEvent {
  event: "agent_start" | "tool_output" | "text_start" | "text_delta" | "text_end" | "agent_complete" | "phase_complete" | "error";
  agent: "GITHUB_AGENT" | "AWS_CLOUDWATCH_AGENT" | "SLACK_AGENT" | "REASONING_INVESTIGATOR";
  phase: 1 | 2;
  data: {
    delta?: string;
    response?: string;
    tool?: string;
    output?: string;
    message?: string;
    [key: string]: any;
  };
}

export type AgentType = "github" | "aws" | "slack";

/**
 * Health check endpoint
 */
export async function healthCheck(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/health_incident_iq`);
    const data = await response.json();
    return data.message === "app running successfully!";
  } catch (error) {
    console.error("Health check failed:", error);
    return false;
  }
}

/**
 * Verify token with backend
 */
export async function verifyToken(token: string): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/verify-token`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ token }),
    });
    return response.ok;
  } catch (error) {
    console.error("Token verification failed:", error);
    return false;
  }
}

/**
 * Map backend agent names to frontend agent types
 */
function mapAgentName(agent: string): AgentType | null {
  switch (agent) {
    case "GITHUB_AGENT":
      return "github";
    case "AWS_CLOUDWATCH_AGENT":
      return "aws";
    case "SLACK_AGENT":
      return "slack";
    default:
      return null;
  }
}

/**
 * Generate log message based on event type
 */
function generateLogMessage(event: StreamEvent): string {
  const { event: eventType, agent, data } = event;

  switch (eventType) {
    case "agent_start":
      return `Agent initialized and starting analysis...`;
    
    case "tool_output":
      if (data.tool) {
        return `Executing tool: ${data.tool}`;
      }
      if (data.output) {
        // Store full output - truncation will be handled in UI based on expanded state
        return `Tool output: ${data.output}`;
      }
      return `Tool execution in progress...`;
    
    case "text_delta":
      if (data.delta) {
        return data.delta;
      }
      return `Processing data...`;
    
    case "text_end":
      return `Agent stream completed.`;
    
    case "agent_complete":
      return `✓ Analysis complete`;
    
    case "error":
      return data.message || `Error occurred during processing`;
    
    default:
      return `Processing...`;
  }
}

/**
 * Determine log level based on content
 */
function determineLogLevel(message: string, eventType: string): "info" | "warn" | "error" | "success" {
  const lowerMessage = message.toLowerCase();
  
  if (eventType === "agent_complete") {
    return "success";
  }
  
  if (lowerMessage.includes("error") || lowerMessage.includes("fail") || lowerMessage.includes("exception")) {
    return "error";
  }
  
  if (lowerMessage.includes("warn") || lowerMessage.includes("timeout") || lowerMessage.includes("slow")) {
    return "warn";
  }
  
  if (lowerMessage.includes("complete") || lowerMessage.includes("success") || lowerMessage.includes("✓")) {
    return "success";
  }
  
  return "info";
}

/**
 * Stream analysis from Investigator Agent
 */
export async function streamInvestigatorAnalysis(
  onEvent: (agentType: AgentType, action: LogUpdateAction) => void,
  onComplete: (finalResponse?: string) => void,
  onError: (error: Error) => void,
  customPrompts?: typeof DEFAULT_PROMPTS
): Promise<AbortController> {
  const controller = new AbortController();
  let finalResponse = "";

  // Track accumulated text and streaming log entry ID per agent
  const streamingText = new Map<AgentType, string>();
  const streamingLogIds = new Map<AgentType, string>();

  console.log("🚀 Starting stream to:", `${API_BASE_URL}/Investigator-Agent/stream`);
  console.log("📤 Sending prompts:", customPrompts || DEFAULT_PROMPTS);

  try {
    const response = await fetch(`${API_BASE_URL}/Investigator-Agent/stream`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...getAuthHeaders(),
      },
      body: JSON.stringify(customPrompts || DEFAULT_PROMPTS),
      signal: controller.signal,
    });

    console.log("📥 Response status:", response.status);
    console.log("📥 Response headers:", response.headers);

    if (!response.ok) {
      if (response.status === 401) {
        sessionStorage.removeItem("auth_token");
        window.location.reload();
      }
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error("Response body is null");
    }

    const decoder = new TextDecoder("utf-8");
    let buffer = "";

    // Read stream
    const processStream = async () => {
      try {
        while (true) {
          const { value, done } = await reader.read();
          
          if (done) {
            onComplete(finalResponse);
            break;
          }

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || ""; // Keep incomplete line in buffer

          for (const line of lines) {
            // Skip ping/heartbeat messages
            if (line.trim().startsWith(":")) {
              continue;
            }

            if (line.startsWith("data: ")) {
              const data = line.slice(6).trim();
              
              // Check for completion marker
              if (data === "[DONE]") {
                onComplete(finalResponse);
                return;
              }

              try {
                const event = JSON.parse(data) as StreamEvent;
                console.log("📨 SSE Event received:", event);
                
                // Handle phase 2 investigator response
                if (event.agent === "REASONING_INVESTIGATOR" && event.phase === 2) {
                  if (event.event === "agent_complete" && event.data.response) {
                    finalResponse = event.data.response;
                  }
                  continue; // Don't show investigator logs in agent columns
                }

                // Handle phase 1 agent events
                if (event.phase === 1) {
                  const agentType = mapAgentName(event.agent);
                  if (!agentType) continue;

                  // Handle text streaming events
                  if (event.event === "text_start") {
                    // Initialize streaming text for this agent
                    streamingText.set(agentType, "");
                    const logId = `streaming-${agentType}-${Date.now()}`;
                    streamingLogIds.set(agentType, logId);
                    
                    const logEntry: AgentLogEntry = {
                      id: logId,
                      timestamp: new Date().toLocaleTimeString('en-US', { 
                        hour12: false, 
                        hour: "2-digit", 
                        minute: "2-digit", 
                        second: "2-digit" 
                      }) + "." + String(Math.floor(Math.random() * 999)).padStart(3, '0'),
                      level: "info",
                      message: ""
                    };
                    
                    onEvent(agentType, { type: "add", logEntry });
                  }
                  else if (event.event === "text_delta" && event.data.delta) {
                    // Accumulate text delta
                    const currentText = streamingText.get(agentType) || "";
                    const newText = currentText + event.data.delta;
                    streamingText.set(agentType, newText);
                    
                    // Update the existing log entry
                    const logId = streamingLogIds.get(agentType);
                    if (logId) {
                      onEvent(agentType, {
                        type: "update",
                        id: logId,
                        updates: { message: newText }
                      });
                    }
                  }
                  else if (event.event === "text_end") {
                    // Finalize streaming text (optional - text is already accumulated)
                    streamingText.delete(agentType);
                    streamingLogIds.delete(agentType);
                  }
                  else {
                    // Handle other events (agent_start, tool_output, agent_complete, etc.)
                    const message = generateLogMessage(event);
                    const level = determineLogLevel(message, event.event);
                    
                    const logEntry: AgentLogEntry = {
                      id: Math.random().toString(36),
                      timestamp: new Date().toLocaleTimeString('en-US', { 
                        hour12: false, 
                        hour: "2-digit", 
                        minute: "2-digit", 
                        second: "2-digit" 
                      }) + "." + String(Math.floor(Math.random() * 999)).padStart(3, '0'),
                      level,
                      message
                    };

                    onEvent(agentType, { type: "add", logEntry });
                  }
                }

                // Detect completion
                if (event.event === "phase_complete" && event.phase === 2) {
                  onComplete(finalResponse);
                  return;
                }

              } catch (parseError) {
                console.warn("Failed to parse SSE event:", data, parseError);
              }
            }
          }
        }
      } catch (error) {
        if (error instanceof Error && error.name === "AbortError") {
          console.log("Stream aborted by user");
        } else {
          onError(error as Error);
        }
      }
    };

    processStream();
  } catch (error) {
    onError(error as Error);
  }

  return controller;
}