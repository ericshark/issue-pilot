import { absoluteTime, relativeTime } from "../lib/format.js";
import TriagePanel from "./TriagePanel.jsx";

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

      <TriagePanel key={issue.id} issueId={issue.id} />
    </div>
  );
}
