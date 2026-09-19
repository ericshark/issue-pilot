import { absoluteTime, excerpt, relativeTime } from "../lib/format.js";
import FlowField from "./FlowField.jsx";

function Skeleton() {
  return (
    <ul className="issue-list" aria-hidden="true">
      {[0, 1, 2, 3].map((row) => (
        <li key={row} className="skeleton-row">
          <div className="skeleton skeleton-line skeleton-title" />
          <div className="skeleton skeleton-line skeleton-body" />
        </li>
      ))}
    </ul>
  );
}

export default function IssueList({
  issues,
  totalCount,
  query,
  onQueryChange,
  loading,
  selectedId,
  onSelect,
}) {
  return (
    <aside className="sidebar" aria-label="Issues">
      <div className="sidebar-head">
        <div className="search">
          <svg className="search-icon" viewBox="0 0 20 20" aria-hidden="true">
            <circle
              cx="9"
              cy="9"
              r="5.5"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.7"
            />
            <path
              d="M13.2 13.2 17 17"
              stroke="currentColor"
              strokeWidth="1.7"
              strokeLinecap="round"
            />
          </svg>
          <input
            type="search"
            value={query}
            onChange={(event) => onQueryChange(event.target.value)}
            placeholder="Search issues"
            aria-label="Search issues"
          />
        </div>
      </div>

      {loading ? (
        <Skeleton />
      ) : totalCount === 0 ? (
        <div className="empty empty-art">
          <FlowField className="empty-field" />
          <div className="empty-body">
            <p className="empty-title">No issues yet</p>
            <p className="empty-copy">Your first report will show up here.</p>
          </div>
        </div>
      ) : issues.length === 0 ? (
        <div className="empty">
          <p className="empty-title">No matches</p>
          <p className="empty-copy">Nothing matches “{query}”. Try a different search.</p>
        </div>
      ) : (
        <ul className="issue-list">
          {issues.map((issue) => (
            <li key={issue.id}>
              <button
                type="button"
                className="issue-row"
                onClick={() => onSelect(issue.id)}
                aria-current={selectedId === issue.id ? "true" : undefined}
              >
                <span className="issue-row-top">
                  <span className="issue-id">#{issue.id}</span>
                  <time
                    dateTime={issue.created_at}
                    title={absoluteTime(issue.created_at)}
                  >
                    {relativeTime(issue.created_at)}
                  </time>
                </span>
                <span className="issue-row-title">{issue.title}</span>
                <span className="issue-row-excerpt">{excerpt(issue.description)}</span>
              </button>
            </li>
          ))}
        </ul>
      )}

      <div className="sidebar-foot">
        <span>
          {loading
            ? "Loading…"
            : query
              ? `${issues.length} of ${totalCount} shown`
              : `${totalCount} ${totalCount === 1 ? "issue" : "issues"}`}
        </span>
      </div>
    </aside>
  );
}
