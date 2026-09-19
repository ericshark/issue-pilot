import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError, createIssue, streamChatMessage } from "./api.js";

// Builds a Response whose body arrives in the given chunks, so tests can put
// an SSE boundary in the middle of a chunk or split one event across two.
function sseResponse(chunks, { status = 200 } = {}) {
  const encoder = new TextEncoder();
  const body = new ReadableStream({
    start(controller) {
      for (const chunk of chunks) controller.enqueue(encoder.encode(chunk));
      controller.close();
    },
  });
  return new Response(body, { status, headers: { "Content-Type": "text/event-stream" } });
}

const event = (name, data) => `event: ${name}\ndata: ${JSON.stringify(data)}\n\n`;

afterEach(() => vi.unstubAllGlobals());

describe("request", () => {
  it("returns the parsed body on success", async () => {
    vi.stubGlobal("fetch", async () => Response.json({ id: 1 }, { status: 201 }));

    await expect(createIssue({ title: "t", description: "d" })).resolves.toEqual({
      id: 1,
    });
  });

  it("throws an ApiError carrying the backend detail", async () => {
    vi.stubGlobal(
      "fetch",
      async () =>
        new Response(JSON.stringify({ detail: "Issue not found" }), { status: 404 }),
    );

    const error = await createIssue({}).catch((caught) => caught);
    expect(error).toBeInstanceOf(ApiError);
    expect(error.status).toBe(404);
    expect(error.message).toBe("Issue not found");
  });

  it("falls back to a generic message when the body is not JSON", async () => {
    vi.stubGlobal("fetch", async () => new Response("<html>502</html>", { status: 502 }));

    const error = await createIssue({}).catch((caught) => caught);
    expect(error.message).toBe("Request failed");
    expect(error.body).toBeNull();
  });
});

describe("streamChatMessage", () => {
  const reply = {
    user_message: { id: 1, role: "user", content: "Hi" },
    assistant_message: { id: 2, role: "assistant", content: "Hello" },
    conversation: { id: 7, title: "Hi" },
  };

  it("dispatches delta and tool events and resolves with done", async () => {
    vi.stubGlobal("fetch", async () =>
      sseResponse([
        event("delta", { text: "Hel" }),
        event("tool", { name: "get_issue", input: { issue_id: 1 } }),
        event("delta", { text: "lo" }) + event("done", reply),
      ]),
    );
    const onDelta = vi.fn();
    const onTool = vi.fn();

    await expect(streamChatMessage(7, "Hi", { onDelta, onTool })).resolves.toEqual(reply);

    expect(onDelta.mock.calls).toEqual([["Hel"], ["lo"]]);
    expect(onTool).toHaveBeenCalledWith({ name: "get_issue", input: { issue_id: 1 } });
  });

  it("reassembles an event split across chunks", async () => {
    const whole = event("delta", { text: "split" }) + event("done", reply);
    vi.stubGlobal("fetch", async () =>
      sseResponse([whole.slice(0, 20), whole.slice(20)]),
    );
    const onDelta = vi.fn();

    await streamChatMessage(7, "Hi", { onDelta });

    expect(onDelta).toHaveBeenCalledWith("split");
  });

  it("rejects with the error event's detail", async () => {
    vi.stubGlobal("fetch", async () =>
      sseResponse([
        event("delta", { text: "partial" }),
        event("error", { detail: "Boom" }),
      ]),
    );

    const error = await streamChatMessage(7, "Hi", { onDelta() {} }).catch((c) => c);
    expect(error).toBeInstanceOf(ApiError);
    expect(error.message).toBe("Boom");
  });

  it("rejects when the stream ends without done", async () => {
    vi.stubGlobal("fetch", async () => sseResponse([event("delta", { text: "x" })]));

    await expect(streamChatMessage(7, "Hi", { onDelta() {} })).rejects.toThrow(
      "The reply ended unexpectedly.",
    );
  });

  it("surfaces a non-OK response as an ApiError before streaming", async () => {
    vi.stubGlobal("fetch", async () =>
      sseResponse([JSON.stringify({ detail: "No key" })], { status: 503 }),
    );

    const error = await streamChatMessage(7, "Hi", { onDelta() {} }).catch((c) => c);
    expect(error.status).toBe(503);
    expect(error.message).toBe("No key");
  });

  it("forwards the abort signal to fetch", async () => {
    const fetchMock = vi.fn(async () => sseResponse([event("done", reply)]));
    vi.stubGlobal("fetch", fetchMock);
    const controller = new AbortController();

    await streamChatMessage(7, "Hi", { onDelta() {}, signal: controller.signal });

    expect(fetchMock.mock.calls[0][1].signal).toBe(controller.signal);
  });
});
