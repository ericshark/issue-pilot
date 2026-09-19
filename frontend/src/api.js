export class ApiError extends Error {
  constructor(message, status, body) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.body = body;
  }
}

// The backend always answers with JSON, but an empty body or a proxy error
// page must not crash the caller, so parsing never throws.
function parseBody(text) {
  if (!text) return null;
  try {
    return JSON.parse(text);
  } catch {
    return null;
  }
}

async function toApiError(response) {
  const body = parseBody(await response.text());
  const detail = typeof body?.detail === "string" ? body.detail : "Request failed";
  return new ApiError(detail, response.status, body);
}

async function request(path, options = {}) {
  const response = await fetch(path, options);
  if (!response.ok) throw await toApiError(response);
  return parseBody(await response.text());
}

export async function listIssues() {
  const response = await request("/api/issues");
  return response.items;
}

export function createIssue(issue) {
  return request("/api/issues", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(issue),
  });
}

export function getIssue(issueId) {
  return request(`/api/issues/${issueId}`);
}

export function triageIssue(issueId) {
  return request(`/api/issues/${issueId}/triage`, { method: "POST" });
}

export function createConversation() {
  return request("/api/chat/conversations", { method: "POST" });
}

export async function listConversations() {
  const response = await request("/api/chat/conversations");
  return response.items;
}

export function getConversation(conversationId) {
  return request(`/api/chat/conversations/${conversationId}`);
}

// Parses one "event: x\ndata: {...}" block from the SSE body.
function parseEvent(block) {
  let type = "";
  let data = "";
  for (const line of block.split("\n")) {
    if (line.startsWith("event: ")) type = line.slice(7);
    else if (line.startsWith("data: ")) data = line.slice(6);
  }
  return { type, data: data ? JSON.parse(data) : null };
}

// Sends one turn and resolves with the stored ChatReply once the stream ends.
// onDelta receives each text chunk; onTool receives {name, input} per lookup.
// Pass an AbortSignal to stop reading when the caller no longer wants the reply.
export async function streamChatMessage(
  conversationId,
  content,
  { onDelta, onTool, signal },
) {
  const response = await fetch(`/api/chat/conversations/${conversationId}/messages`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content }),
    signal,
  });

  if (!response.ok) throw await toApiError(response);

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    let boundary = buffer.indexOf("\n\n");
    while (boundary !== -1) {
      const event = parseEvent(buffer.slice(0, boundary));
      buffer = buffer.slice(boundary + 2);

      if (event.type === "delta") {
        onDelta(event.data.text);
      } else if (event.type === "tool") {
        onTool?.(event.data);
      } else if (event.type === "done") {
        reader.cancel();
        return event.data;
      } else if (event.type === "error") {
        throw new ApiError(event.data.detail, 503, event.data);
      }

      boundary = buffer.indexOf("\n\n");
    }
  }

  throw new ApiError("The reply ended unexpectedly.", 0, null);
}
