const relativeFormatter = new Intl.RelativeTimeFormat(undefined, { numeric: "auto" });

const absoluteFormatter = new Intl.DateTimeFormat(undefined, {
  dateStyle: "medium",
  timeStyle: "short",
});

// Ordered largest-first so the first unit that fits wins.
const UNITS = [
  ["year", 31_536_000],
  ["month", 2_592_000],
  ["week", 604_800],
  ["day", 86_400],
  ["hour", 3_600],
  ["minute", 60],
];

export function absoluteTime(timestamp) {
  return absoluteFormatter.format(new Date(timestamp));
}

export function relativeTime(timestamp) {
  const deltaSeconds = (new Date(timestamp).getTime() - Date.now()) / 1000;
  const magnitude = Math.abs(deltaSeconds);

  if (magnitude < 45) {
    return "just now";
  }

  for (const [unit, seconds] of UNITS) {
    if (magnitude >= seconds) {
      return relativeFormatter.format(Math.round(deltaSeconds / seconds), unit);
    }
  }

  return relativeFormatter.format(Math.round(deltaSeconds / 60), "minute");
}

export function excerpt(text, limit = 120) {
  const collapsed = text.replace(/\s+/g, " ").trim();
  return collapsed.length > limit ? `${collapsed.slice(0, limit).trimEnd()}…` : collapsed;
}
