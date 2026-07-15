import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api, DashboardStats, HorizonItem } from "../lib/api";

function priorityBadge(p?: string) {
  const s = (p || "medium").toLowerCase();
  const cls =
    s === "critical"
      ? "bg-red-50 text-hit-critical"
      : s === "high"
        ? "bg-orange-50 text-hit-high"
        : s === "low"
          ? "bg-teal-50 text-hit-low"
          : "bg-amber-50 text-hit-medium";
  return <span className={`arl-badge ${cls}`}>{s}</span>;
}

export default function HorizonScanPage() {
  const [jurisdiction, setJurisdiction] = useState("");
  const { data: stats } = useQuery({
    queryKey: ["obl-stats"],
    queryFn: async () => (await api.get<DashboardStats>("/dashboard/stats")).data,
  });
  const { data: items = [], isLoading } = useQuery({
    queryKey: ["horizon", jurisdiction],
    queryFn: async () =>
      (
        await api.get<HorizonItem[]>("/horizon", {
          params: { jurisdiction: jurisdiction || undefined },
        })
      ).data,
  });

  const t = stats?.totals;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="arl-page-title">Horizon Scan</h1>
          <p className="arl-page-sub">
            Regulatory change across UK, USA, EU, and Pakistan — assessed into obligations
          </p>
        </div>
        <select
          className="arl-input w-auto"
          value={jurisdiction}
          onChange={(e) => setJurisdiction(e.target.value)}
        >
          <option value="">All jurisdictions</option>
          <option value="UK">UK</option>
          <option value="USA">USA</option>
          <option value="EU">EU</option>
          <option value="Pakistan">Pakistan</option>
        </select>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {[
          ["Horizon items", t?.horizon_items ?? "—"],
          ["Pending assessment", t?.pending_assessment ?? "—"],
          ["Obligations", t?.obligations ?? "—"],
          ["Open gap cases", t?.open_cases ?? "—"],
        ].map(([label, value]) => (
          <div key={label} className="arl-kpi">
            <div className="arl-section-label">{label}</div>
            <div className="mt-2 text-2xl font-semibold text-navy-900 dark:text-white">{value}</div>
          </div>
        ))}
      </div>

      {stats?.jurisdictions && (
        <div className="arl-panel flex flex-wrap gap-2 p-3">
          <span className="arl-section-label mr-2 self-center">Coverage</span>
          {stats.jurisdictions.map((j) => (
            <span key={j.name} className="arl-badge bg-brand-soft text-brand">
              {j.name}: {j.count}
            </span>
          ))}
        </div>
      )}

      {isLoading && <p className="text-sm text-steel-500">Loading horizon…</p>}

      <div className="arl-table-wrap">
        <div className="hidden grid-cols-[1fr_90px_100px_100px_110px] gap-3 border-b border-steel-200 bg-steel-50 px-4 py-2 text-[11px] font-semibold uppercase tracking-wide text-steel-500 dark:border-navy-700 dark:bg-navy-950 md:grid">
          <div>Instrument</div>
          <div>Jurisdiction</div>
          <div>Regulator</div>
          <div>Priority</div>
          <div>Status</div>
        </div>
        <div className="divide-y divide-steel-100 dark:divide-navy-800">
          {items.map((h) => (
            <Link
              key={h.id}
              to={`/horizon/${h.id}`}
              className="grid gap-2 px-4 py-3 transition hover:bg-steel-50 dark:hover:bg-navy-800/50 md:grid-cols-[1fr_90px_100px_100px_110px] md:items-center"
            >
              <div className="min-w-0">
                <div className="truncate text-sm font-semibold text-navy-900 dark:text-white">{h.title}</div>
                <div className="mt-1 line-clamp-1 text-xs text-steel-500">
                  {h.reference} · {h.candidates?.length || 0} candidates
                </div>
              </div>
              <div className="text-xs text-steel-600">{h.jurisdiction}</div>
              <div className="text-xs text-steel-600">{h.regulator}</div>
              <div>{priorityBadge(h.priority)}</div>
              <div>
                <span className="arl-badge bg-steel-100 text-steel-700 dark:bg-navy-800 dark:text-steel-200">
                  {h.status.replace(/_/g, " ")}
                </span>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
