import { useState } from "react";
import { Panel, PrimaryButton, ErrorMessage, LoadingRow, ResultCard } from "./ui";
import { useToast } from "./toast";
import { useElapsedSeconds, useLocalStorage } from "../hooks";
import { SHARED_KEYS, useSharedContext } from "../shared";
import { API_BASE } from "../api";

export interface ToolField {
  readonly name: string;
  readonly label: string;
  readonly type: "text" | "textarea" | "select";
  readonly placeholder?: string;
  readonly options?: readonly string[];
  readonly required?: boolean;
}

export interface PromptToolProps {
  readonly title: string;
  readonly subtitle: string;
  readonly endpoint: string;
  readonly fields: readonly ToolField[];
  readonly storageKey: string;
  readonly resultTitle: string;
  readonly submitLabel: string;
  readonly loadingLabel: string;
  /** When true, POST to `${endpoint}/stream` and render tokens as they arrive. */
  readonly stream?: boolean;
}

type FormState = Record<string, string>;

function initialForm(fields: readonly ToolField[], shared: FormState): FormState {
  const state: FormState = {};
  for (const f of fields) {
    if (SHARED_KEYS.has(f.name) && shared[f.name]) {
      state[f.name] = shared[f.name];
    } else {
      state[f.name] = f.type === "select" ? (f.options?.[0] ?? "") : "";
    }
  }
  return state;
}

/** Parse one SSE frame body and forward its chunk (throws on server error). */
function handleSSEFrame(frame: string, onChunk: (text: string) => void): void {
  const line = frame.startsWith("data:") ? frame.slice(5).trim() : frame.trim();
  if (!line) return;
  const evt = JSON.parse(line) as { chunk?: string; error?: string; done?: boolean };
  if (evt.error) throw new Error(evt.error);
  if (evt.chunk) onChunk(evt.chunk);
}

/** Read an SSE `data: {...}` stream, invoking onChunk for each text token. */
async function readSSE(
  response: Response,
  onChunk: (text: string) => void,
): Promise<void> {
  const reader = response.body?.getReader();
  if (!reader) throw new Error("Streaming not supported by this browser.");
  const decoder = new TextDecoder();
  let buffer = "";

  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    let sep = buffer.indexOf("\n\n");
    while (sep !== -1) {
      handleSSEFrame(buffer.slice(0, sep), onChunk);
      buffer = buffer.slice(sep + 2);
      sep = buffer.indexOf("\n\n");
    }
  }
}

export default function PromptTool(props: PromptToolProps) {
  const { title, subtitle, endpoint, fields, storageKey, resultTitle, submitLabel, loadingLabel, stream } = props;

  const { shared, mergeShared } = useSharedContext();
  const [form, setForm] = useState<FormState>(() => initialForm(fields, shared));
  const [prefilled] = useState<boolean>(() =>
    fields.some((f) => SHARED_KEYS.has(f.name) && !!shared[f.name]),
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult, clearResult] = useLocalStorage<string>(storageKey, "");

  const toast = useToast();
  const elapsed = useElapsedSeconds(loading);

  function update(name: string, value: string) {
    setForm((prev) => ({ ...prev, [name]: value }));
    if (SHARED_KEYS.has(name)) mergeShared({ [name]: value });
  }

  async function handleSubmit() {
    setError("");
    const missing = fields.find((f) => f.required && !form[f.name]?.trim());
    if (missing) {
      setError(`${missing.label} is required.`);
      return;
    }
    setLoading(true);
    try {
      if (stream) {
        const res = await fetch(`${API_BASE}${endpoint}/stream`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(form),
        });
        if (!res.ok) {
          const data = await res.json().catch(() => ({}));
          throw new Error(data.detail ?? `Server error ${res.status}`);
        }
        let acc = "";
        setResult("");
        await readSSE(res, (chunk) => {
          acc += chunk;
          setResult(acc);
        });
        toast.success(`${title} ready.`);
      } else {
        const res = await fetch(`${API_BASE}${endpoint}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(form),
        });
        if (!res.ok) {
          const data = await res.json().catch(() => ({}));
          throw new Error(data.detail ?? `Server error ${res.status}`);
        }
        const data = await res.json();
        setResult(data.result);
        toast.success(`${title} ready.`);
      }
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

  const inputClass =
    "w-full rounded-lg border border-border bg-surface p-3 text-[13px] text-content outline-none transition focus:border-accent";

  function renderField(f: ToolField) {
    if (f.type === "textarea") {
      return (
        <textarea
          placeholder={f.placeholder}
          value={form[f.name]}
          onChange={(e) => update(f.name, e.target.value)}
          onKeyDown={onKeyDown}
          className={`${inputClass} min-h-24 resize-y`}
        />
      );
    }
    if (f.type === "select") {
      return (
        <select
          value={form[f.name]}
          onChange={(e) => update(f.name, e.target.value)}
          className={inputClass}
        >
          {f.options?.map((opt) => (
            <option key={opt} value={opt}>{opt}</option>
          ))}
        </select>
      );
    }
    return (
      <input
        type="text"
        placeholder={f.placeholder}
        value={form[f.name]}
        onChange={(e) => update(f.name, e.target.value)}
        onKeyDown={onKeyDown}
        className={inputClass}
      />
    );
  }

  return (
    <Panel title={title} subtitle={subtitle}>
      {prefilled && (
        <p className="-mb-1 text-xs text-muted">
          <span className="text-accent">↺</span> Some fields were carried over from another tool — edit freely.
        </p>
      )}
      <div className="flex flex-col gap-3">
        {fields.map((f) => (
          <label key={f.name} className="flex flex-col gap-1.5">
            <span className="text-xs font-medium text-muted">
              {f.label}
              {f.required && <span className="text-danger"> *</span>}
            </span>
            {renderField(f)}
          </label>
        ))}
      </div>

      <div className="flex items-center gap-3">
        <PrimaryButton loading={loading} onClick={handleSubmit}>
          {loading ? "Working..." : submitLabel}
        </PrimaryButton>
        {result && !loading && (
          <button
            onClick={() => { clearResult(); toast.info("Cleared saved result."); }}
            className="text-xs text-muted underline-offset-2 transition hover:text-content hover:underline"
          >
            Clear result
          </button>
        )}
      </div>

      {error && <ErrorMessage message={error} />}
      {loading && !result && <LoadingRow label={loadingLabel} seconds={elapsed} />}
      {loading && result && stream && (
        <LoadingRow label="Streaming response..." seconds={elapsed} />
      )}
      {result && (
        <div className="mt-1 flex flex-col gap-4">
          <ResultCard title={resultTitle} content={result} />
        </div>
      )}
    </Panel>
  );
}
