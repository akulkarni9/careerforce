import { useState } from "react";
import type { ReactNode } from "react";
import ReactMarkdown from "react-markdown";

export function Panel({ title, subtitle, actions, children }: {
  readonly title: string;
  readonly subtitle?: string;
  readonly actions?: ReactNode;
  readonly children: ReactNode;
}) {
  return (
    <section className="flex h-full flex-col gap-3 overflow-y-auto bg-bg p-4 sm:gap-4 sm:p-6">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h2 className="text-[15px] font-semibold text-content">{title}</h2>
          {subtitle && <p className="mt-0.5 text-xs text-muted">{subtitle}</p>}
        </div>
        {actions}
      </div>
      {children}
    </section>
  );
}

export function PrimaryButton({ loading, children, onClick }: {
  readonly loading: boolean;
  readonly children: ReactNode;
  readonly onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      disabled={loading}
      className="inline-flex w-fit items-center gap-2 rounded-lg bg-accent px-6 py-2.5 text-sm font-medium text-white shadow-lg shadow-accent/20 transition hover:bg-accent-hover disabled:cursor-not-allowed disabled:opacity-50"
    >
      {loading && <Spinner />}
      {children}
    </button>
  );
}

export function Spinner() {
  return (
    <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
  );
}

export function ErrorMessage({ message }: { readonly message: string }) {
  return (
    <div className="flex items-start gap-2 rounded-lg border border-danger/30 bg-danger/10 px-3 py-2 text-[13px] text-danger">
      <span aria-hidden>⚠</span>
      <span>{message}</span>
    </div>
  );
}

export function LoadingRow({ label, seconds }: { readonly label: string; readonly seconds?: number }) {
  return (
    <div className="flex items-center gap-2.5 py-2 text-[13px] text-muted">
      <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-border border-t-accent" />
      <span>{label}</span>
      {seconds !== undefined && seconds > 0 && (
        <span className="rounded bg-surface px-1.5 py-0.5 font-mono text-xs text-muted">{seconds}s</span>
      )}
    </div>
  );
}

/**
 * Renders a colored match-score bar. Prefers the structured numeric `score`
 * (from the backend's JSON-mode extraction); falls back to parsing the
 * markdown critique if a valid score wasn't provided.
 */
export function MatchScoreBar({ markdown, score }: {
  readonly markdown?: string;
  readonly score?: number;
}) {
  let value = score;
  if (value === undefined || value < 0 || Number.isNaN(value)) {
    const match = markdown ? /match score[^\d]*(\d{1,3})\s*\/\s*100/i.exec(markdown) : null;
    if (!match) return null;
    value = Number.parseInt(match[1], 10);
  }
  value = Math.min(100, Math.max(0, value));

  let color = "bg-danger";
  if (value >= 80) color = "bg-emerald-500";
  else if (value >= 60) color = "bg-accent";
  else if (value >= 40) color = "bg-amber-500";

  return (
    <div className="rounded-lg border border-border bg-surface p-4">
      <div className="mb-2 flex items-baseline justify-between">
        <span className="text-xs font-semibold uppercase tracking-wider text-muted">Match Score</span>
        <span className="text-lg font-bold text-content">{value}<span className="text-sm text-muted">/100</span></span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-bg">
        <div className={`h-full rounded-full transition-all duration-700 ${color}`} style={{ width: `${value}%` }} />
      </div>
    </div>
  );
}

/**
 * Renders the resume critique's "Rewrite These Bullets" as a side-by-side
 * current-vs-rewrite diff. Returns null if the critique has no rewrite section.
 */
export function RewriteDiff({ markdown }: { readonly markdown: string }) {
  const items = parseRewrites(markdown);
  if (items.length === 0) return null;
  return (
    <div className="rounded-lg border border-border bg-surface">
      <div className="border-b border-border bg-bg px-4 py-2.5">
        <span className="text-xs font-semibold uppercase tracking-wider text-muted">
          Suggested Rewrites — Current vs. Improved
        </span>
      </div>
      <div className="flex flex-col gap-3 p-4">
        {items.map((item) => (
          <RewriteRow key={item.current} item={item} />
        ))}
      </div>
    </div>
  );
}

function RewriteRow({ item }: { readonly item: RewriteItem }) {
  const [copied, setCopied] = useState(false);
  async function copyRewrite() {
    try {
      await navigator.clipboard.writeText(item.rewrite);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1500);
    } catch {
      /* clipboard blocked — ignore */
    }
  }
  return (
    <div className="rounded-lg border border-border bg-bg p-3">
      {item.section && (
        <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted">{item.section}</p>
      )}
      <div className="grid gap-3 md:grid-cols-2">
        <div className="rounded-md border border-danger/25 bg-danger/5 p-3">
          <p className="mb-1 text-[10px] font-semibold uppercase tracking-wider text-danger/80">Current</p>
          <p className="text-[13px] leading-relaxed text-content/80 line-through decoration-danger/40">{item.current}</p>
        </div>
        <div className="rounded-md border border-emerald-500/30 bg-emerald-500/5 p-3">
          <div className="mb-1 flex items-center justify-between">
            <p className="text-[10px] font-semibold uppercase tracking-wider text-emerald-400">Rewrite</p>
            <button
              onClick={copyRewrite}
              className="rounded border border-emerald-500/30 px-1.5 py-0.5 text-[10px] text-emerald-400 transition hover:bg-emerald-500/10"
            >
              {copied ? "Copied" : "Copy"}
            </button>
          </div>
          <p className="text-[13px] leading-relaxed text-content">{item.rewrite}</p>
        </div>
      </div>
      {item.why && (
        <p className="mt-2 text-xs text-muted">
          <span className="font-medium text-content/70">Why:</span> {item.why}
        </p>
      )}
    </div>
  );
}

interface RewriteItem {
  section?: string;
  current: string;
  rewrite: string;
  why?: string;
}

function stripQuotes(s: string): string {
  return s.trim().replace(/^['"“”]/, "").replace(/['"“”]$/, "").trim();
}

/**
 * Extracts the "Rewrite These Bullets" entries from the resume critique markdown
 * so they can be shown as a current-vs-rewrite diff instead of plain prose.
 */
function parseRewrites(markdown: string): RewriteItem[] {
  const start = markdown.search(/##\s*Rewrite These Bullets/i);
  if (start === -1) return [];
  const rest = markdown.slice(start);
  const nextHeading = rest.indexOf("\n## ", 3);
  const body = nextHeading === -1 ? rest : rest.slice(0, nextHeading);

  const items: RewriteItem[] = [];
  let cur: Partial<RewriteItem> = {};
  const flush = () => {
    if (cur.current && cur.rewrite) items.push(cur as RewriteItem);
    cur = {};
  };

  for (const rawLine of body.split("\n")) {
    const m = /\*\*(Section|Current|Rewrite|Why):\*\*(.*)/i.exec(rawLine.trim());
    if (!m) continue;
    const key = m[1].toLowerCase();
    const val = m[2];
    if (key === "section") {
      flush();
      cur.section = stripQuotes(val);
    } else if (key === "current") {
      if (cur.current) flush();
      cur.current = stripQuotes(val);
    } else if (key === "rewrite") {
      cur.rewrite = stripQuotes(val);
    } else if (key === "why") {
      cur.why = val.trim();
    }
  }
  flush();
  return items;
}

function IconButton({ label, onClick, children }: {
  readonly label: string;
  readonly onClick: () => void;
  readonly children: ReactNode;
}) {
  return (
    <button
      title={label}
      aria-label={label}
      onClick={onClick}
      className="rounded-md border border-border bg-bg px-2 py-1 text-xs text-muted transition hover:border-accent hover:text-content"
    >
      {children}
    </button>
  );
}

export function ResultCard({ title, content, onCopy, onDownload }: {
  readonly title: string;
  readonly content: string;
  readonly onCopy?: () => void;
  readonly onDownload?: () => void;
}) {
  const [copied, setCopied] = useState(false);

  async function copy() {
    try {
      await navigator.clipboard.writeText(content);
      setCopied(true);
      onCopy?.();
      window.setTimeout(() => setCopied(false), 1500);
    } catch {
      /* clipboard blocked — ignore */
    }
  }

  function download() {
    const blob = new Blob([content], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${title.toLowerCase().replace(/\s+/g, "-")}.md`;
    a.click();
    URL.revokeObjectURL(url);
    onDownload?.();
  }

  return (
    <div className="overflow-hidden rounded-lg border border-border bg-surface">
      <div className="flex items-center justify-between border-b border-border bg-bg px-4 py-2.5">
        <span className="text-xs font-semibold uppercase tracking-wider text-muted">{title}</span>
        <div className="flex gap-1.5">
          <IconButton label="Copy markdown" onClick={copy}>{copied ? "Copied" : "Copy"}</IconButton>
          <IconButton label="Download .md" onClick={download}>Download</IconButton>
        </div>
      </div>
      <div className="prose prose-sm prose-invert max-w-none px-4 py-4 prose-headings:text-content prose-h2:text-sm prose-h3:text-[13px] prose-strong:text-accent prose-code:rounded prose-code:bg-bg prose-code:px-1.5 prose-code:py-0.5 prose-code:text-xs prose-code:before:content-none prose-code:after:content-none prose-a:text-accent">
        <ReactMarkdown>{content}</ReactMarkdown>
      </div>
    </div>
  );
}
