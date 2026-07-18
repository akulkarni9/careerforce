import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import { Panel, PrimaryButton, ErrorMessage } from "./ui";
import { useToast } from "./toast";
import { useLocalStorage } from "../hooks";
import { API_BASE } from "../api";

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
}

interface Session {
  threadId: string | null;
  messages: ChatMessage[];
}

const EMPTY: Session = { threadId: null, messages: [] };

let msgCounter = 0;
function newId(): string {
  msgCounter += 1;
  return `m${Date.now()}-${msgCounter}`;
}

async function postTurn(body: Record<string, string>): Promise<{ thread_id: string; reply: string }> {
  const res = await fetch(`${API_BASE}/api/mock-interview`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail ?? `Server error ${res.status}`);
  }
  return res.json();
}

export default function MockInterviewUI() {
  const [session, setSession, clearSession] = useLocalStorage<Session>("ja:interview", EMPTY);
  const [jd, setJd] = useState("");
  const [draft, setDraft] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);
  const toast = useToast();

  const started = session.threadId !== null;

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [session.messages, loading]);

  async function start() {
    setError("");
    setLoading(true);
    try {
      const data = await postTurn({ jd_text: jd });
      setSession({ threadId: data.thread_id, messages: [{ id: newId(), role: "assistant", content: data.reply }] });
      toast.success("Interview started.");
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Something went wrong.";
      setError(msg);
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  }

  async function send() {
    const text = draft.trim();
    if (!text || !session.threadId) return;
    setError("");
    setDraft("");
    const optimistic: ChatMessage[] = [...session.messages, { id: newId(), role: "user", content: text }];
    setSession({ ...session, messages: optimistic });
    setLoading(true);
    try {
      const data = await postTurn({ thread_id: session.threadId, message: text });
      setSession({ threadId: data.thread_id, messages: [...optimistic, { id: newId(), role: "assistant", content: data.reply }] });
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
      send();
    }
  }

  function reset() {
    clearSession();
    setJd("");
    setDraft("");
    setError("");
    toast.info("Interview reset.");
  }

  return (
    <Panel
      title="Mock Interview"
      subtitle="A conversational interviewer with memory, grounded in your resume"
      actions={
        started && (
          <button
            onClick={reset}
            className="shrink-0 rounded-md border border-border px-2.5 py-1 text-xs text-muted transition hover:border-danger hover:text-danger"
          >
            End &amp; reset
          </button>
        )
      }
    >
      {!started ? (
        <>
          <label className="flex flex-col gap-1.5">
            <span className="text-xs font-medium text-muted">Job description (optional — tailors the interview)</span>
            <textarea
              placeholder="Paste the JD you want to be interviewed for..."
              value={jd}
              onChange={(e) => setJd(e.target.value)}
              className="min-h-32 w-full resize-y rounded-lg border border-border bg-surface p-3 text-[13px] text-content outline-none transition focus:border-accent"
            />
          </label>
          <PrimaryButton loading={loading} onClick={start}>
            {loading ? "Starting..." : "Start interview"}
          </PrimaryButton>
          {error && <ErrorMessage message={error} />}
        </>
      ) : (
        <>
          <div
            ref={scrollRef}
            className="flex max-h-[52vh] min-h-64 flex-col gap-3 overflow-y-auto rounded-lg border border-border bg-bg p-4"
          >
            {session.messages.map((m) => (
              <div
                key={m.id}
                className={`max-w-[85%] rounded-lg px-3 py-2 text-[13px] ${
                  m.role === "user"
                    ? "self-end bg-accent text-white"
                    : "self-start border border-border bg-surface text-content"
                }`}
              >
                {m.role === "assistant" ? (
                  <div className="prose prose-sm prose-invert max-w-none prose-p:my-1 prose-strong:text-accent prose-blockquote:my-1 prose-blockquote:border-accent prose-ul:my-1">
                    <ReactMarkdown>{m.content}</ReactMarkdown>
                  </div>
                ) : (
                  m.content
                )}
              </div>
            ))}
            {loading && (
              <div className="self-start flex items-center gap-2 rounded-lg border border-border bg-surface px-3 py-2 text-[13px] text-muted">
                <span className="inline-block h-3.5 w-3.5 animate-spin rounded-full border-2 border-border border-t-accent" />
                <span>Interviewer is thinking...</span>
              </div>
            )}
          </div>

          {error && <ErrorMessage message={error} />}

          <div className="flex flex-col gap-2">
            <textarea
              placeholder="Type your answer...  (⌘/Ctrl + Enter to send). Type 'summary' to wrap up."
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={onKeyDown}
              className="min-h-20 w-full resize-y rounded-lg border border-border bg-surface p-3 text-[13px] text-content outline-none transition focus:border-accent"
            />
            <div className="flex justify-end">
              <PrimaryButton loading={loading} onClick={send}>Send</PrimaryButton>
            </div>
          </div>
        </>
      )}
    </Panel>
  );
}
