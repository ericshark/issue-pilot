import { absoluteTime, relativeTime } from "../lib/format.js";

export default function IssueDetail({ issue, refreshing }) {
  return (
    <div className="pane">
      <div className="pane-head">
        <div className="detail-heading">
          <span className="issue-id issue-id-lg">#{issue.id}</span>
          <h2 className="pane-title">{issue.title}</h2>
        </div>
        {refreshing && <span className="pane-note">Refreshing…</span>}
      </div>

      <div className="detail-meta">
        <time dateTime={issue.created_at}>{absoluteTime(issue.created_at)}</time>
        <span className="dot" aria-hidden="true" />
        <span>{relativeTime(issue.created_at)}</span>
      </div>

      <div className="detail-body">
        <p className="detail-label">Description</p>
        <p className="detail-description">{issue.description}</p>
      </div>

      <div className="triage-placeholder">
        <span className="triage-badge">Coming soon</span>
        <p>AI-assisted triage will summarize and categorize this issue in a later milestone.</p>
      </div>
    </div>
  );
}
