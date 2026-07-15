import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api, GapCase } from "../lib/api";

function gapBadge(s: string) {
  const cls =
    s === "gap"
      ? "bg-red-50 text-hit-critical"
      : s === "partial"
        ? "bg-amber-50 text-hit-medium"
        : "bg-teal-50 text-hit-low";
  return <span className={`arl-badge ${cls}`}>{s}</span>;
}

export default function CasesPage() {
  const [gapStatus, setGapStatus] = useState("");
  const { data = [], isLoading } = useQuery({
    queryKey: ["cases", gapStatus],
    queryFn: async () =>
      (
        await api.get<GapCase[]>("/cases", {
          params: { gap_status: gapStatus || undefined },
        })
      ).data,
  });

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="arl-page-title">Gap Analysis Cases</h1>
          <p className="arl-page-sub">
            One case per applicable obligation — map policies and controls to each requirement
          </p>
        </div>
        <select className="arl-input w-auto" value={gapStatus} onChange={(e) => setGapStatus(e.target.value)}>
          <option value="">All gap statuses</option>
          <option value="mapped">Mapped</option>
          <option value="partial">Partial</option>
          <option value="gap">Gap</option>
        </select>
      </div>

      {isLoading && <p className="text-sm text-steel-500">Loading cases…</p>}

      <div className="arl-table-wrap">
        <div className="divide-y divide-steel-100 dark:divide-navy-800">
          {data.map((c) => (
            <Link
              key={c.id}
              to={`/cases/${c.id}`}
              className="flex flex-wrap items-center justify-between gap-3 px-4 py-3 transition hover:bg-steel-50 dark:hover:bg-navy-800/40"
            >
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-mono text-xs text-brand">{c.case_number}</span>
                  <span className="arl-badge bg-steel-100 text-steel-600">{c.jurisdiction}</span>
                </div>
                <div className="mt-1 truncate text-sm font-semibold text-navy-900 dark:text-white">
                  {c.title}
                </div>
                <div className="mt-1 text-xs text-steel-500">
                  {c.obligation?.code || c.obligation_id} · Owner {c.owner} · {c.mappings?.length || 0}{" "}
                  mappings
                </div>
              </div>
              <div className="flex items-center gap-2">
                {gapBadge(c.gap_status)}
                <span className="text-[11px] uppercase text-steel-500">{c.status.replace(/_/g, " ")}</span>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
