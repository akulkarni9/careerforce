import { useEffect, useRef, useState } from "react";
import {
  Panel,
  PrimaryButton,
  ErrorMessage,
  LoadingRow,
  ResultCard,
  MatchScoreBar,
  RewriteDiff,
} from "./ui";
import { useToast } from "./toast";
import { useElapsedSeconds, useLocalStorage } from "../hooks";
import { useSharedContext } from "../shared";

type InputMode = "text" | "image";

interface AnalysisResult {
  structured_jd: string;
  critique: string;
  match_score: number;
  prep: string;
}

interface ResumeInfo {
  loaded: boolean;
  filename: string | null;
}

export default function JobApplicationUI() {
  const { shared, mergeShared } = useSharedContext();
  const [mode, setMode] = useState<InputMode>("text");
  const [jdText, setJdText] = useState(() => shared.jd_text ?? "");
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult, clearResult] = useLocalStorage<AnalysisResult | null>("ja:analysis", null);
  const [resume, setResume] = useState<ResumeInfo | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const toast = useToast();
  const elapsed = useElapsedSeconds(loading);

  useEffect(() => {
    fetch("/api/resume-info")
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => d && setResume(d))
      .catch(() => setResume(null));
  }, []);

  useEffect(() => {
    if (!imageFile) { setImagePreview(null); return; }
    const url = URL.createObjectURL(imageFile);
    setImagePreview(url);
    return () => URL.revokeObjectURL(url);
  }, [imageFile]);

  function pickImage(file: File | null) {
    if (file && !file.type.startsWith("image/")) {
      toast.error("Please choose an image file (PNG, JPG, WEBP).");
      return;
    }
    setImageFile(file);
  }

  async function handleSubmit() {
    setError("");
    setLoading(true);

    try {
      const form = new FormData();
      if (mode === "text") {
        if (!jdText.trim()) { setError("Paste a job description first."); setLoading(false); return; }
        form.append("jd_text", jdText);
        mergeShared({ jd_text: jdText });
      } else {
        if (!imageFile) { setError("Upload a JD image first."); setLoading(false); return; }
        form.append("jd_image", imageFile);
      }

      const res = await fetch("/api/analyze-job", { method: "POST", body: form });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail ?? `Server error ${res.status}`);
      }
      setResult(await res.json());
      toast.success("Analysis complete.");
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

  const tabClass = (active: boolean) =>
    `rounded-lg border px-4 py-1.5 text-[13px] transition ${
      active
        ? "border-accent bg-accent text-white"
        : "border-border bg-transparent text-muted hover:text-content"
    }`;

  return (
    <Panel
      title="Job Application"
      subtitle="Analyse a JD against your resume and get interview prep"
      actions={
        <span
          className={`shrink-0 rounded-full border px-2.5 py-1 text-xs ${
            resume?.loaded ? "border-accent/40 text-accent" : "border-border text-muted"
          }`}
          title={resume?.loaded ? "Resume loaded from backend data/" : "No resume found in data/"}
        >
          {resume?.loaded ? `📄 ${resume.filename}` : "No resume loaded"}
        </span>
      }
    >
      <div className="flex gap-2">
        <button className={tabClass(mode === "text")} onClick={() => setMode("text")}>Paste JD</button>
        <button className={tabClass(mode === "image")} onClick={() => setMode("image")}>Upload Image</button>
      </div>

      {mode === "text" ? (
        <textarea
          placeholder="Paste the job description here...  (⌘/Ctrl + Enter to analyse)"
          value={jdText}
          onChange={(e) => setJdText(e.target.value)}
          onKeyDown={onKeyDown}
          className="min-h-40 w-full resize-y rounded-lg border border-border bg-surface p-3 text-[13px] text-content outline-none transition focus:border-accent"
        />
      ) : (
        <label
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragging(false);
            pickImage(e.dataTransfer.files?.[0] ?? null);
          }}
          className={`flex min-h-32 cursor-pointer flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed p-4 transition ${
            dragging || imageFile ? "border-accent bg-accent/5" : "border-border hover:border-accent"
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            className="hidden"
            onChange={(e) => pickImage(e.target.files?.[0] ?? null)}
          />
          {imagePreview ? (
            <>
              <img src={imagePreview} alt="JD preview" className="max-h-40 rounded-md border border-border object-contain" />
              <span className="text-xs font-medium text-accent">{imageFile?.name}</span>
            </>
          ) : (
            <>
              <span className="text-[13px] text-muted">Drag &amp; drop or click to upload JD image</span>
              <span className="text-xs text-muted">PNG, JPG, WEBP</span>
            </>
          )}
        </label>
      )}

      <div className="flex items-center gap-3">
        <PrimaryButton loading={loading} onClick={handleSubmit}>
          {loading ? "Analysing..." : "Analyse"}
        </PrimaryButton>
        {result && !loading && (
          <button
            onClick={() => { clearResult(); toast.info("Cleared saved analysis."); }}
            className="text-xs text-muted underline-offset-2 transition hover:text-content hover:underline"
          >
            Clear result
          </button>
        )}
      </div>

      {error && <ErrorMessage message={error} />}

      {loading && (
        <LoadingRow label="Running 3-node chain — this takes a minute with a 26B model..." seconds={elapsed} />
      )}

      {result && (
        <div className="mt-1 flex flex-col gap-4">
          <MatchScoreBar markdown={result.critique} score={result.match_score} />
          <ResultCard title="JD Analysis" content={result.structured_jd} />
          <RewriteDiff markdown={result.critique} />
          <ResultCard title="Resume Critique" content={result.critique} />
          <ResultCard title="Interview Prep" content={result.prep} />
        </div>
      )}
    </Panel>
  );
}
