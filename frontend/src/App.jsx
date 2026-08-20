import { useEffect, useState } from "react";

import { ApiError, createIssue, getIssue, listIssues } from "./api.js";

const EMPTY_FORM = { title: "", description: "" };

function formatTimestamp(timestamp) {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(timestamp));
}

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

export default function App() {
  const [form, setForm] = useState(EMPTY_FORM);
  const [issues, setIssues] = useState([]);
  const [selectedIssue, setSelectedIssue] = useState(null);
  const [fieldErrors, setFieldErrors] = useState({});
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [loadingDetails, setLoadingDetails] = useState(false);

  useEffect(() => {
    let active = true;

    listIssues()
      .then((items) => {
        if (active) setIssues(items);
      })
      .catch((error) => {
        if (active) setMessage(errorMessage(error, "Could not load issues."));
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, []);

  function updateField(event) {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
    setFieldErrors((current) => ({ ...current, [name]: undefined }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setMessage("");
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
      setForm(EMPTY_FORM);
      setMessage(`Issue #${created.id} was saved.`);
    } catch (error) {
      const apiFieldErrors = validationErrors(error);
      setFieldErrors(apiFieldErrors);
      if (!Object.keys(apiFieldErrors).length) {
        setMessage(errorMessage(error, "Could not save the issue."));
      }
    } finally {
      setSubmitting(false);
    }
  }

  async function handleSelect(issueId) {
    setLoadingDetails(true);
    setMessage("");

    try {
      setSelectedIssue(await getIssue(issueId));
    } catch (error) {
      setMessage(errorMessage(error, "Could not load that issue."));
    } finally {
      setLoadingDetails(false);
    }
  }

  return (
    <main className="page-shell">
      <header className="hero">
        <p className="eyebrow">Software issue intake</p>
        <h1>IssuePilot</h1>
        <p className="hero-copy">
          Capture a clear report now. AI-assisted triage comes in a later milestone.
        </p>
      </header>

      {message && <p className="status-message" role="status">{message}</p>}

      <section className="workspace" aria-label="Issue workspace">
        <section className="panel form-panel">
          <div className="section-heading">
            <p className="step">Step 1</p>
            <h2>Submit an issue</h2>
          </div>

          <form onSubmit={handleSubmit} noValidate>
            <label htmlFor="title">Title</label>
            <input
              id="title"
              name="title"
              value={form.title}
              onChange={updateField}
              maxLength={120}
              aria-describedby={fieldErrors.title ? "title-error" : undefined}
              aria-invalid={Boolean(fieldErrors.title)}
            />
            {fieldErrors.title && <p id="title-error" className="field-error">{fieldErrors.title}</p>}

            <label htmlFor="description">Description</label>
            <textarea
              id="description"
              name="description"
              value={form.description}
              onChange={updateField}
              maxLength={5000}
              rows={8}
              aria-describedby={fieldErrors.description ? "description-error" : "description-help"}
              aria-invalid={Boolean(fieldErrors.description)}
            />
            {fieldErrors.description ? (
              <p id="description-error" className="field-error">{fieldErrors.description}</p>
            ) : (
              <p id="description-help" className="field-help">Include what happened and what you expected.</p>
            )}

            <button className="primary-button" type="submit" disabled={submitting}>
              {submitting ? "Saving…" : "Submit issue"}
            </button>
          </form>
        </section>

        <section className="panel list-panel">
          <div className="section-heading heading-row">
            <div>
              <p className="step">Step 2</p>
              <h2>Review issues</h2>
            </div>
            <span className="count-badge">{issues.length}</span>
          </div>

          {loading ? (
            <p className="muted">Loading issues…</p>
          ) : issues.length === 0 ? (
            <div className="empty-state">
              <p>No issues yet.</p>
              <span>Your first report will appear here.</span>
            </div>
          ) : (
            <ul className="issue-list">
              {issues.map((issue) => (
                <li key={issue.id}>
                  <button
                    type="button"
                    className="issue-row"
                    onClick={() => handleSelect(issue.id)}
                    aria-pressed={selectedIssue?.id === issue.id}
                  >
                    <span className="issue-number">#{issue.id}</span>
                    <span>
                      <strong>{issue.title}</strong>
                      <small>{formatTimestamp(issue.created_at)}</small>
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </section>
      </section>

      {selectedIssue && (
        <section className="panel detail-panel" aria-live="polite">
          <p className="step">Selected issue</p>
          <div className="detail-heading">
            <h2>{selectedIssue.title}</h2>
            <span>#{selectedIssue.id}</span>
          </div>
          <time dateTime={selectedIssue.created_at}>
            {formatTimestamp(selectedIssue.created_at)}
          </time>
          <p className="description">{selectedIssue.description}</p>
          {loadingDetails && <p className="muted">Refreshing details…</p>}
        </section>
      )}
    </main>
  );
}
