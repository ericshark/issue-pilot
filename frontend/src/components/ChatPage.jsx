import { useEffect, useRef, useState } from "react";

import {
  createConversation,
  getConversation,
  listConversations,
  streamChatMessage,
} from "../api.js";
import { absoluteTime, relativeTime } from "../lib/format.js";
import Button from "./Button.jsx";
import FlowField from "./FlowField.jsx";

const UNTITLED = "New chat";

function toolLabel({ name, input }) {
  switch (name) {
    case "get_issue":
      return `Read issue #${input.issue_id}`;
    case "search_issues":
      return `Searched issues for “${input.query}”`;
    case "list_issues":
      return "Listed recent issues";
    default:
      return name;
  }
}

export default function ChatPage({ notify, errorMessage }) {
  const [conversations, setConversations] = useState([]);
  const [loadingList, setLoadingList] = useState(true);
  const [activeId, setActiveId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [loadingThread, setLoadingThread] = useState(false);
  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState(false);
  const threadRef = useRef(null);
  const composerRef = useRef(null);

  useEffect(() => {
    let active = true;

    listConversations()
      .then((items) => {
        if (active) setConversations(items);
      })
      .catch((error) => {
        if (active) notify(errorMessage(error, "Could not load conversations."), "error");
      })
      .finally(() => {
        if (active) setLoadingList(false);
      });

    return () => {
      active = false;
    };
  }, [notify, errorMessage]);

  // Keep the newest turn in view as the thread grows or the reply lands.
  useEffect(() => {
    const thread = threadRef.current;
    if (thread) thread.scrollTop = thread.scrollHeight;
  }, [messages, sending]);

  async function openConversation(conversationId) {
    setActiveId(conversationId);
    setLoadingThread(true);

    try {
      const detail = await getConversation(conversationId);
      setMessages(detail.messages);
    } catch (error) {
      notify(errorMessage(error, "Could not load that conversation."), "error");
    } finally {
      setLoadingThread(false);
      composerRef.current?.focus();
    }
  }

  async function startConversation() {
    try {
      const created = await createConversation();
      setConversations((current) => [created, ...current]);
      setActiveId(created.id);
      setMessages([]);
      composerRef.current?.focus();
      return created.id;
    } catch (error) {
      notify(errorMessage(error, "Could not start a conversation."), "error");
      return null;
    }
  }

  async function send() {
    const content = draft.trim();
    if (!content || sending) return;

    const conversationId = activeId ?? (await startConversation());
    if (conversationId === null) return;

    // Both placeholders are swapped for the stored copies once the stream ends.
    const pending = { id: "pending", role: "user", content, pending: true };
    const streaming = {
      id: "streaming",
      role: "assistant",
      content: "",
      tools: [],
      streaming: true,
    };
    setMessages((current) => [...current, pending, streaming]);
    setDraft("");
    setSending(true);

    try {
      const patchStreaming = (update) =>
        setMessages((current) =>
          current.map((message) =>
            message.id === "streaming" ? { ...message, ...update(message) } : message,
          ),
        );

      const reply = await streamChatMessage(conversationId, content, {
        onDelta: (text) => patchStreaming((m) => ({ content: m.content + text })),
        onTool: (tool) => patchStreaming((m) => ({ tools: [...m.tools, tool] })),
      });

      // Tool activity is not stored, so it is carried over locally for this session only.
      setMessages((current) => {
        const streamed = current.find((message) => message.id === "streaming");
        return [
          ...current.filter((message) => message.id !== "pending" && message.id !== "streaming"),
          reply.user_message,
          { ...reply.assistant_message, tools: streamed?.tools ?? [] },
        ];
      });
      setConversations((current) =>
        current.map((conversation) =>
          conversation.id === conversationId && conversation.title === UNTITLED
            ? { ...conversation, title: titleFrom(content) }
            : conversation,
        ),
      );
    } catch (error) {
      setMessages((current) =>
        current.filter((message) => message.id !== "pending" && message.id !== "streaming"),
      );
      setDraft(content);
      notify(errorMessage(error, "Could not send that message."), "error");
    } finally {
      setSending(false);
      composerRef.current?.focus();
    }
  }

  function handleKeyDown(event) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      send();
    }
  }

  const active = conversations.find((conversation) => conversation.id === activeId);

  return (
    <div className="workspace">
      <aside className="sidebar" aria-label="Conversations">
        <div className="sidebar-head">
          <Button type="button" className="button-block" onClick={startConversation}>
            New chat
          </Button>
        </div>

        {loadingList ? (
          <p className="sidebar-note">Loading…</p>
        ) : conversations.length === 0 ? (
          <div className="empty empty-art">
            <FlowField className="empty-field" />
            <div className="empty-body">
              <p className="empty-title">No conversations yet</p>
              <p className="empty-copy">Start one and it will be saved here.</p>
            </div>
          </div>
        ) : (
          <ul className="issue-list">
            {conversations.map((conversation) => (
              <li key={conversation.id}>
                <button
                  type="button"
                  className="issue-row"
                  onClick={() => openConversation(conversation.id)}
                  aria-current={activeId === conversation.id ? "true" : undefined}
                >
                  <span className="issue-row-title">{conversation.title}</span>
                  <time
                    className="conversation-time"
                    dateTime={conversation.created_at}
                    title={absoluteTime(conversation.created_at)}
                  >
                    {relativeTime(conversation.created_at)}
                  </time>
                </button>
              </li>
            ))}
          </ul>
        )}

        <div className="sidebar-foot">
          <span>
            {conversations.length} {conversations.length === 1 ? "conversation" : "conversations"}
          </span>
        </div>
      </aside>

      <main className="main chat-main">
        {activeId === null ? (
          <div className="chat-empty">
            <FlowField className="chat-empty-field" />
            <div className="chat-empty-body">
              <h2 className="pane-title">Ask anything</h2>
              <p>Every conversation is saved, so you can pick it up again later.</p>
              <Button type="button" onClick={startConversation}>
                Start a conversation
              </Button>
            </div>
          </div>
        ) : (
          <>
            <div className="chat-thread" ref={threadRef}>
              <div className="chat-thread-inner">
                {loadingThread ? (
                  <p className="sidebar-note">Loading…</p>
                ) : messages.length === 0 ? (
                  <p className="chat-hint">
                    {active?.title === UNTITLED
                      ? "Send a message to begin."
                      : "This conversation is empty."}
                  </p>
                ) : (
                  messages.map((message) =>
                    message.streaming && !message.content && !message.tools?.length ? (
                      <div
                        key={message.id}
                        className="bubble bubble-assistant bubble-typing"
                        aria-label="Assistant is typing"
                      >
                        <span />
                        <span />
                        <span />
                      </div>
                    ) : (
                      <div
                        key={message.id}
                        className={[
                          "bubble",
                          `bubble-${message.role}`,
                          message.pending ? "bubble-pending" : "",
                          message.streaming ? "bubble-streaming" : "",
                        ]
                          .filter(Boolean)
                          .join(" ")}
                        aria-live={message.streaming ? "polite" : undefined}
                      >
                        {message.tools?.length > 0 && (
                          <ul className="tool-chips" aria-label="Lookups">
                            {message.tools.map((tool, index) => (
                              <li key={index} className="tool-chip">
                                <svg viewBox="0 0 16 16" aria-hidden="true">
                                  <circle cx="7" cy="7" r="4.2" fill="none" stroke="currentColor" strokeWidth="1.5" />
                                  <path d="m10.2 10.2 3 3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                                </svg>
                                {toolLabel(tool)}
                              </li>
                            ))}
                          </ul>
                        )}
                        {(message.content || !message.streaming) && <p>{message.content}</p>}
                      </div>
                    ),
                  )
                )}
              </div>
            </div>

            <form
              className="composer"
              onSubmit={(event) => {
                event.preventDefault();
                send();
              }}
            >
              <textarea
                ref={composerRef}
                value={draft}
                onChange={(event) => setDraft(event.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Message… (Enter to send, Shift+Enter for a new line)"
                rows={1}
                maxLength={8000}
                aria-label="Message"
                disabled={sending}
              />
              <Button type="submit" disabled={sending || !draft.trim()}>
                {sending ? "Sending…" : "Send"}
              </Button>
            </form>
          </>
        )}
      </main>
    </div>
  );
}

// Mirrors the backend's title rule so the sidebar updates without a refetch.
function titleFrom(content) {
  const firstLine = content.trim().split("\n")[0];
  return firstLine.length <= 60 ? firstLine : `${firstLine.slice(0, 59).trimEnd()}…`;
}
