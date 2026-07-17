import { useEffect, useRef, useState } from "react";
import type { ReactNode } from "react";
import JobApplicationUI from "./components/JobApplicationUI";
import CareerAdvisorUI from "./components/CareerAdvisorUI";
import MockInterviewUI from "./components/MockInterviewUI";
import PromptTool from "./components/PromptTool";

interface Tool {
  readonly id: string;
  readonly label: string;
  readonly icon: string;
  readonly group: string;
  readonly render: () => ReactNode;
}

const TOOLS: readonly Tool[] = [
  {
    id: "job",
    label: "Job Application",
    icon: "📋",
    group: "Apply",
    render: () => <JobApplicationUI />,
  },
  {
    id: "cover-letter",
    label: "Cover Letter",
    icon: "✉️",
    group: "Apply",
    render: () => (
      <PromptTool
        title="Cover Letter Generator"
        subtitle="A tailored letter from your resume and the job description"
        endpoint="/api/cover-letter"
        stream
        storageKey="ja:cover-letter"
        resultTitle="Cover Letter"
        submitLabel="Generate letter"
        loadingLabel="Writing a tailored cover letter..."
        fields={[
          { name: "jd_text", label: "Job description", type: "textarea", required: true, placeholder: "Paste the JD..." },
          { name: "tone", label: "Tone", type: "select", options: ["professional and confident", "warm and enthusiastic", "concise and direct", "formal"] },
          { name: "extra", label: "Anything to emphasise (optional)", type: "textarea", placeholder: "e.g. relocation, a specific project, career pivot..." },
        ]}
      />
    ),
  },
  {
    id: "networking",
    label: "Networking Message",
    icon: "🤝",
    group: "Apply",
    render: () => (
      <PromptTool
        title="Networking Message Writer"
        subtitle="Outreach that gets replies — recruiters, referrals, connections"
        endpoint="/api/networking-message"
        stream
        storageKey="ja:networking"
        resultTitle="Outreach Message"
        submitLabel="Write message"
        loadingLabel="Drafting your outreach..."
        fields={[
          { name: "recipient", label: "Recipient", type: "select", options: ["recruiter", "hiring manager", "referral (someone at the company)", "new connection", "former colleague"] },
          { name: "platform", label: "Platform", type: "select", options: ["LinkedIn", "email", "LinkedIn connection note"] },
          { name: "company", label: "Target company", type: "text", placeholder: "e.g. Stripe" },
          { name: "role", label: "Target role", type: "text", placeholder: "e.g. Senior Backend Engineer" },
          { name: "context", label: "Context / goal", type: "textarea", required: true, placeholder: "Why are you reaching out? Any connection or hook?" },
        ]}
      />
    ),
  },
  {
    id: "advisor",
    label: "Career Advisor",
    icon: "🧭",
    group: "Grow",
    render: () => <CareerAdvisorUI />,
  },
  {
    id: "skill-gap",
    label: "Skill Gap Plan",
    icon: "📈",
    group: "Grow",
    render: () => (
      <PromptTool
        title="Skill Gap Learning Plan"
        subtitle="A week-by-week plan to close the gap to your target role"
        endpoint="/api/skill-gap-plan"
        stream
        storageKey="ja:skill-gap"
        resultTitle="Learning Plan"
        submitLabel="Build my plan"
        loadingLabel="Analysing gaps and building a plan..."
        fields={[
          { name: "target_role", label: "Target role", type: "text", required: true, placeholder: "e.g. Machine Learning Engineer" },
          { name: "jd_text", label: "Target job description (optional)", type: "textarea", placeholder: "Paste a JD for the role you want..." },
        ]}
      />
    ),
  },
  {
    id: "interview",
    label: "Mock Interview",
    icon: "🎤",
    group: "Prepare",
    render: () => <MockInterviewUI />,
  },
  {
    id: "research",
    label: "Company Research",
    icon: "🔎",
    group: "Prepare",
    render: () => (
      <PromptTool
        title="Company & Role Research Brief"
        subtitle="Prep brief: likely stack, priorities, smart questions, red flags"
        endpoint="/api/company-research"
        stream
        storageKey="ja:research"
        resultTitle="Research Brief"
        submitLabel="Build brief"
        loadingLabel="Assembling your research brief..."
        fields={[
          { name: "company", label: "Company", type: "text", placeholder: "e.g. Datadog" },
          { name: "role", label: "Role", type: "text", placeholder: "e.g. Staff Engineer" },
          { name: "jd_text", label: "Job description (optional but recommended)", type: "textarea", placeholder: "Paste the JD for a sharper brief..." },
        ]}
      />
    ),
  },
  {
    id: "negotiation",
    label: "Salary Negotiation",
    icon: "💰",
    group: "Prepare",
    render: () => (
      <PromptTool
        title="Salary Negotiation Coach"
        subtitle="Strategy and scripts to negotiate your offer confidently"
        endpoint="/api/salary-negotiation"
        stream
        storageKey="ja:negotiation"
        resultTitle="Negotiation Plan"
        submitLabel="Coach me"
        loadingLabel="Building your negotiation strategy..."
        fields={[
          { name: "role", label: "Role / level", type: "text", placeholder: "e.g. Senior Engineer, L5" },
          { name: "location", label: "Location / remote", type: "text", placeholder: "e.g. Remote (US), or NYC" },
          { name: "offer", label: "Offer details", type: "textarea", required: true, placeholder: "Base, bonus, equity, sign-on..." },
          { name: "competing", label: "Your leverage (optional)", type: "textarea", placeholder: "Competing offers, current comp, urgency, unique skills..." },
        ]}
      />
    ),
  },
];

const GROUP_ORDER = ["Apply", "Prepare", "Grow"] as const;

export default function App() {
  const [activeId, setActiveId] = useState<string>(TOOLS[0].id);
  const active = TOOLS.find((t) => t.id === activeId) ?? TOOLS[0];
  const [resumeName, setResumeName] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    fetch("/api/resume-info")
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => d && setResumeName(d.filename))
      .catch(() => {});
  }, []);

  async function handleResumeUpload(file: File | undefined) {
    if (!file) return;
    setUploading(true);
    try {
      const form = new FormData();
      form.append("file", file);
      const res = await fetch("/api/upload-resume", { method: "POST", body: form });
      if (!res.ok) {
        const d = await res.json().catch(() => ({}));
        alert(d.detail ?? "Upload failed");
        return;
      }
      const d = await res.json();
      setResumeName(d.filename);
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="flex h-full flex-col">
      <header className="flex items-center gap-3 border-b border-border px-6 py-4">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-accent to-accent-hover text-sm font-bold text-white shadow-lg shadow-accent/20">
          CF
        </div>
        <div>
          <h1 className="text-base font-semibold tracking-tight text-content">CareerForge</h1>
          <p className="text-xs text-muted">AI-powered application &amp; career toolkit</p>
        </div>
        <div className="ml-auto">
          <input
            ref={fileRef}
            type="file"
            accept=".docx,.pdf"
            className="hidden"
            onChange={(e) => handleResumeUpload(e.target.files?.[0])}
          />
          <button
            onClick={() => fileRef.current?.click()}
            disabled={uploading}
            className={`rounded-full border px-3 py-1.5 text-xs transition ${
              resumeName ? "border-accent/40 text-accent" : "border-border text-muted hover:text-content hover:border-accent"
            }`}
          >
            {uploading ? "Uploading..." : resumeName ? `📄 ${resumeName}` : "Upload Resume"}
          </button>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        <nav className="w-56 shrink-0 overflow-y-auto border-r border-border bg-surface/40 px-3 py-4">
          {GROUP_ORDER.map((group) => (
            <div key={group} className="mb-4">
              <p className="mb-1.5 px-2 text-[10px] font-semibold uppercase tracking-wider text-muted">{group}</p>
              <div className="flex flex-col gap-0.5">
                {TOOLS.filter((t) => t.group === group).map((t) => (
                  <button
                    key={t.id}
                    onClick={() => setActiveId(t.id)}
                    className={`flex items-center gap-2.5 rounded-lg px-2.5 py-2 text-left text-[13px] transition ${
                      t.id === activeId
                        ? "bg-accent/15 font-medium text-content"
                        : "text-muted hover:bg-surface hover:text-content"
                    }`}
                  >
                    <span className="text-base leading-none">{t.icon}</span>
                    {t.label}
                  </button>
                ))}
              </div>
            </div>
          ))}
        </nav>

        <main className="flex-1 overflow-hidden">
          {active.render()}
        </main>
      </div>
    </div>
  );
}
