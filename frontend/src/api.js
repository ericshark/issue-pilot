export class ApiError extends Error {
  constructor(message, status, body) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.body = body;
  }
}

async function request(path, options = {}) {
  const response = await fetch(path, options);
  const text = await response.text();
  let body = null;

  if (text) {
    try {
      body = JSON.parse(text);
    } catch {
      body = null;
    }
  }

  if (!response.ok) {
    const detail = typeof body?.detail === "string" ? body.detail : "Request failed";
    throw new ApiError(detail, response.status, body);
  }

  return body;
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
