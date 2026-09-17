import { useCallback, useEffect, useMemo, useState } from "react";

import { ApiError, createIssue, getIssue, listIssues } from "./api.js";
import IssueDetail from "./components/IssueDetail.jsx";
import IssueForm from "./components/IssueForm.jsx";
import IssueList from "./components/IssueList.jsx";
import Button from "./components/Button.jsx";
import ChatPage from "./components/ChatPage.jsx";

const EMPTY_FORM = { title: "", description: "" };

function validationErrors(error) {
  if (!(error instanceof ApiError) || !Array.isArray(error.body?.detail)) {
    return {};
  }

  return error.body.detail.reduce((errors, item) => {
    const field = item.loc?.at(-1);
    if ((field === "title" || field === "description") && !errors[field]) {
      errors[field] = item.msg;
    }
    return errors;
  }, {});
}

function errorMessage(error, fallback) {
  return error instanceof ApiError && typeof error.body?.detail === "string"
    ? error.body.detail
    : fallback;
}

// The hash is the whole router: it survives reloads and gives the back button
// something to do without pulling in a routing library.
function pageFromHash() {
  return window.location.hash === "#/chat" ? "chat" : "issues";
}

function goTo(page) {
  window.location.hash = page === "chat" ? "#/chat" : "#/issues";
}

export default function App() {
  const [form, setForm] = useState(EMPTY_FORM);
  const [issues, setIssues] = useState([]);
  const [selectedIssue, setSelectedIssue] = useState(null);
  const [view, setView] = useState("compose");
  const [query, setQuery] = useState("");
  const [fieldErrors, setFieldErrors] = useState({});
  const [toast, setToast] = useState(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [loadingDetails, setLoadingDetails] = useState(false);
  const [page, setPage] = useState(pageFromHash);

  const notify = useCallback((text, tone = "success") => {
    setToast({ id: Date.now(), text, tone });
  }, []);

  useEffect(() => {
    const syncPage = () => setPage(pageFromHash());
    window.addEventListener("hashchange", syncPage);
    return () => window.removeEventListener("hashchange", syncPage);
  }, []);

  useEffect(() => {
    let active = true;

    listIssues()
      .then((items) => {
        if (active) setIssues(items);
      })
      .catch((error) => {
        if (active) notify(errorMessage(error, "Could not load issues."), "error");
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, []);

  // Toasts clear themselves; the id keeps repeat messages from reusing a stale timer.
  useEffect(() => {
    if (!toast) return undefined;
    const timer = setTimeout(() => setToast(null), 4500);
    return () => clearTimeout(timer);
  }, [toast]);

  const filteredIssues = useMemo(() => {
    const needle = query.trim().toLowerCase();
    if (!needle) return issues;

    return issues.filter(
      (issue) =>
        issue.title.toLowerCase().includes(needle) ||
        issue.description.toLowerCase().includes(needle) ||
        String(issue.id) === needle.replace("#", ""),
    );
  }, [issues, query]);

  function updateField(event) {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
    setFieldErrors((current) => ({ ...current, [name]: undefined }));
  }

  function startNewIssue() {
    setView("compose");
    setFieldErrors({});
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setFieldErrors({});

    const payload = {
      title: form.title.trim(),
      description: form.description.trim(),
    };
    const localErrors = {};

    if (!payload.title) localErrors.title = "Enter a title.";
    if (!payload.description) localErrors.description = "Enter a description.";
    if (Object.keys(localErrors).length) {
      setFieldErrors(localErrors);
      return;
    }

    setSubmitting(true);

    try {
      const created = await createIssue(payload);
      setIssues((current) => [created, ...current]);
      setSelectedIssue(created);
      setView("detail");
      setForm(EMPTY_FORM);
      notify(`Issue #${created.id} was saved.`);
    } catch (error) {
      const apiFieldErrors = validationErrors(error);
      setFieldErrors(apiFieldErrors);
      if (!Object.keys(apiFieldErrors).length) {
        notify(errorMessage(error, "Could not save the issue."), "error");
      }
    } finally {
      setSubmitting(false);
    }
  }

  async function handleSelect(issueId) {
    const known = issues.find((issue) => issue.id === issueId);
    if (known) setSelectedIssue(known);
    setView("detail");
    setLoadingDetails(true);

    try {
      setSelectedIssue(await getIssue(issueId));
    } catch (error) {
      notify(errorMessage(error, "Could not load that issue."), "error");
    } finally {
      setLoadingDetails(false);
    }
  }

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none">
              <path
                d="M12 2.5 21 7v10l-9 4.5L3 17V7z"
                stroke="currentColor"
                strokeWidth="1.6"
                strokeLinejoin="round"
              />
              <path d="m8.6 12 2.4 2.4 4.6-4.8" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </span>
          <span className="brand-text">
            <strong>IssuePilot</strong>
            <small>{page === "chat" ? "Assistant" : "Software issue intake"}</small>
          </span>
        </div>

        <div className="topbar-actions">
          {page === "chat" ? (
            <Button
              type="button"
              variant="ghost"
              className="button-compact"
              onClick={() => goTo("issues")}
            >
              Issues
            </Button>
          ) : (
            <>
              <Button
                type="button"
                variant="ghost"
                className="button-compact"
                onClick={() => goTo("chat")}
              >
                Chat
              </Button>
              <Button
                type="button"
                className="button-compact"
                onClick={startNewIssue}
                disabled={view === "compose"}
              >
                New issue
              </Button>
            </>
          )}
        </div>
      </header>

      {page === "chat" ? (
        <ChatPage notify={notify} errorMessage={errorMessage} />
      ) : (
      <div className="workspace">
        <IssueList
          issues={filteredIssues}
          totalCount={issues.length}
          query={query}
          onQueryChange={setQuery}
          loading={loading}
          selectedId={view === "detail" ? selectedIssue?.id : null}
          onSelect={handleSelect}
        />

        <main className="main">
          {view === "detail" && selectedIssue ? (
            <IssueDetail issue={selectedIssue} refreshing={loadingDetails} />
          ) : (
            <IssueForm
              form={form}
              fieldErrors={fieldErrors}
              submitting={submitting}
              onFieldChange={updateField}
              onSubmit={handleSubmit}
            />
          )}
        </main>
      </div>
      )}

      <div className="toast-region" role="status" aria-live="polite">
        {toast && (
          <div className={`toast toast-${toast.tone}`} key={toast.id}>
            {toast.text}
          </div>
        )}
      </div>
    </div>
  );
}
