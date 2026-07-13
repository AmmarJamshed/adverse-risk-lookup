import { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api, Article } from "../lib/api";

export default function ArticleDetailPage() {
  const { id } = useParams();
  const [langView, setLangView] = useState<"en" | "original">("en");
  const { data, isLoading } = useQuery({
    queryKey: ["article", id],
    queryFn: async () => (await api.get<Article>(`/articles/${id}`)).data,
    enabled: !!id,
  });

  if (isLoading || !data) {
    return <p className="text-sm text-paper/50">Loading article…</p>;
  }

  const actions = data.recommended_actions || {};

  return (
    <div className="space-y-6">
      <Link to="/articles" className="text-sm text-signal hover:underline">
        ← Back to Adverse Media
      </Link>
      <div className="arl-panel p-6 animate-fade-up">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <div className="text-[11px] uppercase tracking-[0.16em] text-signal">
              {data.severity} · Score {Math.round(data.severity_score)} · Confidence{" "}
              {Math.round((data.confidence || 0) * 100)}%
            </div>
            <h1 className="mt-2 font-display text-3xl font-semibold">
              {langView === "en" ? data.title_en || data.title : data.title}
            </h1>
            <p className="mt-2 text-sm text-paper/60 light:text-ink-900/60">
              {data.country || "Global"} · {data.risk_category} · {data.source_name}
            </p>
          </div>
          <button type="button" className="arl-btn-ghost" onClick={() => setLangView((v) => (v === "en" ? "original" : "en"))}>
            Language: {langView === "en" ? "English" : "Original"}
          </button>
        </div>

        <div className="mt-6 grid gap-4 lg:grid-cols-2">
          <section>
            <h2 className="text-xs uppercase tracking-wide text-paper/50">Executive Summary</h2>
            <p className="mt-2 text-sm leading-relaxed">{data.summary_executive}</p>
            <h2 className="mt-4 text-xs uppercase tracking-wide text-paper/50">Detailed Summary</h2>
            <p className="mt-2 text-sm leading-relaxed text-paper/80 light:text-ink-900/80">
              {data.summary_detailed ||
                (langView === "en" ? data.content_en : data.content_original) ||
                "—"}
            </p>
          </section>
          <section className="space-y-3 text-sm">
            <Meta label="Banks" value={(data.banks || []).join(", ") || "—"} />
            <Meta label="Regulators" value={(data.regulators || []).join(", ") || "—"} />
            <Meta label="Departments" value={(data.departments || []).join(", ") || "—"} />
            <Meta label="Tags" value={(data.tags || []).join(", ") || "—"} />
            <a href={data.url} target="_blank" rel="noreferrer" className="text-signal hover:underline">
              Open source article →
            </a>
          </section>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="arl-panel p-4">
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide">Recommended Actions</h2>
          {(["immediate", "short_term", "long_term"] as const).map((k) => (
            <div key={k} className="mb-3">
              <div className="text-xs uppercase text-signal">{k.replace("_", " ")}</div>
              <ul className="mt-1 list-disc space-y-1 pl-5 text-sm text-paper/75 light:text-ink-900/75">
                {(actions[k] || []).map((x) => (
                  <li key={x}>{x}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="arl-panel p-4">
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide">Explainable Risk Matches</h2>
          {(data.risk_matches || []).length === 0 && (
            <p className="text-sm text-paper/50">No semantic matches yet — upload a risk register and reprocess.</p>
          )}
          {(data.risk_matches || []).map((m) => (
            <div key={String(m.id)} className="mb-3 rounded-lg border border-white/10 p-3 light:border-ink-900/10">
              <div className="font-medium">
                {String(m.risk_code || "")} — {String(m.risk_name || "")}
              </div>
              <div className="mt-1 text-xs text-signal">
                Similarity {(Number(m.similarity_score) * 100).toFixed(1)}% · Confidence{" "}
                {(Number(m.confidence) * 100).toFixed(0)}%
              </div>
              <p className="mt-2 text-sm text-paper/75 light:text-ink-900/75">{String(m.reasoning || "")}</p>
              {Array.isArray(m.matched_concepts) && m.matched_concepts.length > 0 && (
                <div className="mt-2 text-xs text-paper/50">
                  Concepts: {(m.matched_concepts as string[]).join(", ")}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function Meta({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-[11px] uppercase tracking-wide text-paper/45">{label}</div>
      <div>{value}</div>
    </div>
  );
}
