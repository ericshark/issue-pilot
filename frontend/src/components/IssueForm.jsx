const TITLE_LIMIT = 120;
const DESCRIPTION_LIMIT = 5000;

// Counter turns amber in the last 10% of the budget so the cap is not a surprise.
function Counter({ value, limit }) {
  const near = value >= limit * 0.9;
  return (
    <span className={near ? "counter counter-near" : "counter"}>
      {value}/{limit}
    </span>
  );
}

export default function IssueForm({
  form,
  fieldErrors,
  submitting,
  onFieldChange,
  onSubmit,
}) {
  // Cmd/Ctrl+Enter submits from anywhere in the form, matching common issue trackers.
  function handleKeyDown(event) {
    if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
      event.preventDefault();
      onSubmit(event);
    }
  }

  return (
    <div className="pane">
      <div className="pane-head">
        <div>
          <h2 className="pane-title">New issue</h2>
          <p className="pane-subtitle">
            Describe what happened and what you expected instead.
          </p>
        </div>
      </div>

      <form className="issue-form" onSubmit={onSubmit} onKeyDown={handleKeyDown} noValidate>
        <div className="field">
          <div className="field-head">
            <label htmlFor="title">Title</label>
            <Counter value={form.title.length} limit={TITLE_LIMIT} />
          </div>
          <input
            id="title"
            name="title"
            value={form.title}
            onChange={onFieldChange}
            maxLength={TITLE_LIMIT}
            placeholder="Login button does nothing"
            autoComplete="off"
            aria-describedby={fieldErrors.title ? "title-error" : undefined}
            aria-invalid={Boolean(fieldErrors.title)}
          />
          {fieldErrors.title && (
            <p id="title-error" className="field-error" role="alert">
              {fieldErrors.title}
            </p>
          )}
        </div>

        <div className="field field-grow">
          <div className="field-head">
            <label htmlFor="description">Description</label>
            <Counter value={form.description.length} limit={DESCRIPTION_LIMIT} />
          </div>
          <textarea
            id="description"
            name="description"
            value={form.description}
            onChange={onFieldChange}
            maxLength={DESCRIPTION_LIMIT}
            placeholder={
              "Steps to reproduce\n1. …\n\nExpected\n…\n\nActual\n…"
            }
            aria-describedby={
              fieldErrors.description ? "description-error" : "description-help"
            }
            aria-invalid={Boolean(fieldErrors.description)}
          />
          {fieldErrors.description ? (
            <p id="description-error" className="field-error" role="alert">
              {fieldErrors.description}
            </p>
          ) : (
            <p id="description-help" className="field-help">
              Include what happened, what you expected, and how to reproduce it.
            </p>
          )}
        </div>

        <div className="form-actions">
          <span className="shortcut-hint">
            <kbd>⌘</kbd>
            <kbd>↵</kbd>
            to submit
          </span>
          <button className="button button-primary" type="submit" disabled={submitting}>
            {submitting ? "Saving…" : "Submit issue"}
          </button>
        </div>
      </form>
    </div>
  );
}
