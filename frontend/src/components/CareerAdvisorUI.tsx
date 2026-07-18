import { useState } from "react";
import { Panel, PrimaryButton, ErrorMessage, LoadingRow, ResultCard } from "./ui";
import { useToast } from "./toast";
import { useElapsedSeconds, useLocalStorage } from "../hooks";
import { API_BASE } from "../api";

export default function CareerAdvisorUI() {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [advice, setAdvice, clearAdvice] = useLocalStorage<string>("ja:advice", "");

  const toast = useToast();
  const elapsed = useElapsedSeconds(loading);

  async function handleSubmit() {
    setError("");
    if (!query.trim()) { setError("Enter a career question first."); return; }
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE}/api/career-advice`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail ?? `Server error ${res.status}`);
      }
      const data = await res.json();
      setAdvice(data.advice);
      toast.success("Advice ready.");
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Something went wrong.";
      setError(msg);
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  }

  function onKeyDown(e: React.KeyboardEvent) {
    if ((e.metaKey || e.ctrlKey) && e.key === "Enter" && !loading) {
      e.preventDefault();
      handleSubmit();
    }
  }

  return (
    <Panel title="Career Advisor" subtitle="RAG-grounded advice based on your resume and market data">
      <textarea
        placeholder="Ask a career question — e.g. 'What skills should I build to move into ML engineering in 2025?'  (⌘/Ctrl + Enter)"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onKeyDown={onKeyDown}
        className="min-h-28 w-full resize-y rounded-lg border border-border bg-surface p-3 text-[13px] text-content outline-none transition focus:border-accent"
      />

      <div className="flex items-center gap-3">
        <PrimaryButton loading={loading} onClick={handleSubmit}>
          {loading ? "Thinking..." : "Get Advice"}
        </PrimaryButton>
        {advice && !loading && (
          <button
            onClick={() => { clearAdvice(); toast.info("Cleared saved advice."); }}
            className="text-xs text-muted underline-offset-2 transition hover:text-content hover:underline"
          >
            Clear result
          </button>
        )}
      </div>

      {error && <ErrorMessage message={error} />}

      {loading && <LoadingRow label="Searching knowledge base and generating advice..." seconds={elapsed} />}

      {advice && (
        <div className="mt-1 flex flex-col gap-4">
          <ResultCard title="Career Advice" content={advice} />
        </div>
      )}
    </Panel>
  );
}
