import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api, Article } from "../lib/api";

export default function ArticlesPage() {
  const [langView, setLangView] = useState<"en" | "original">("en");
  const [severity, setSeverity] = useState("");
  const { data = [], isLoading } = useQuery({
    queryKey: ["articles", severity],
    queryFn: async () =>
      (
        await api.get<Article[]>("/articles", {
          params: { limit: 50, severity: severity || undefined },
        })
      ).data,
  });

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="font-display text-3xl font-semibold">Adverse Media</h1>
          <p className="text-sm text-paper/60 light:text-ink-900/60">AI-filtered banking & financial risk news</p>
        </div>
        <div className="flex gap-2">
          <select className="arl-input w-auto" value={severity} onChange={(e) => setSeverity(e.target.value)}>
            <option value="">All severities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
          <button
            type="button"
            className="arl-btn-ghost"
            onClick={() => setLangView((v) => (v === "en" ? "original" : "en"))}
          >
            Show: {langView === "en" ? "English" : "Original"}
          </button>
        </div>
      </div>

      {isLoading && <p className="text-sm text-paper/50">Loading…</p>}

      <div className="space-y-3">
        {data.map((a) => (
          <Link key={a.id} to={`/articles/${a.id}`} className="arl-panel block p-4 transition hover:border-signal/30">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div className="min-w-0 flex-1">
                <h2 className="text-base font-semibold">
                  {langView === "en" ? a.title_en || a.title : a.title}
                </h2>
                <p className="mt-2 line-clamp-2 text-sm text-paper/65 light:text-ink-900/65">
                  {a.summary_executive || "No summary"}
                </p>
                <div className="mt-3 flex flex-wrap gap-2 text-[11px] text-paper/50 light:text-ink-900/50">
                  <span>{a.country || "Global"}</span>
                  <span>·</span>
                  <span>{a.risk_category || "—"}</span>
                  <span>·</span>
                  <span className="uppercase">{a.language}</span>
                  <span>·</span>
                  <span>{a.source_name || a.processing_status}</span>
                </div>
              </div>
              <div className="text-right">
                <div className="rounded bg-signal/15 px-2 py-1 text-xs uppercase text-signal">
                  {a.severity || "n/a"} · {Math.round(a.severity_score)}
                </div>
                {a.requires_escalation && (
                  <div className="mt-2 text-[10px] uppercase tracking-wide text-signal-danger">Escalation</div>
                )}
              </div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
