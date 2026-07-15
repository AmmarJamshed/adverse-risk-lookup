import { useState } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, ApplicabilityInboxItem } from "../lib/api";

export default function ApplicabilityPage() {
  const qc = useQueryClient();
  const [filter, setFilter] = useState("under_review");
  const [flash, setFlash] = useState("");

  const { data = [], isLoading } = useQuery({
    queryKey: ["applicability", filter],
    queryFn: async () =>
      (
        await api.get<ApplicabilityInboxItem[]>("/applicability", {
          params: { status: filter || undefined },
        })
      ).data,
  });

  const assess = useMutation({
    mutationFn: async (payload: {
      horizon_id: string;
      candidate_id: string;
      decision: string;
      rationale?: string;
    }) => (await api.post("/applicability", payload)).data,
    onSuccess: (res) => {
      qc.invalidateQueries({ queryKey: ["applicability"] });
      qc.invalidateQueries({ queryKey: ["horizon"] });
      qc.invalidateQueries({ queryKey: ["obligations"] });
      qc.invalidateQueries({ queryKey: ["cases"] });
      qc.invalidateQueries({ queryKey: ["obl-stats"] });
      if (res.obligation && res.gap_case) {
        setFlash(`Created ${res.obligation.code} · Case ${res.gap_case.case_number}`);
      } else {
        setFlash("Decision saved.");
      }
    },
  });

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="arl-page-title">Applicability</h1>
          <p className="arl-page-sub">
            Decide which extracted requirements apply — applicable items create obligations and gap cases
          </p>
        </div>
        <select className="arl-input w-auto" value={filter} onChange={(e) => setFilter(e.target.value)}>
          <option value="under_review">Under review</option>
          <option value="applicable">Applicable</option>
          <option value="not_applicable">Not applicable</option>
          <option value="">All</option>
        </select>
      </div>

      {flash && (
        <div className="rounded-panel border border-brand/30 bg-brand-soft px-4 py-2 text-sm text-brand">
          {flash}
        </div>
      )}

      {isLoading && <p className="text-sm text-steel-500">Loading inbox…</p>}

      <div className="space-y-3">
        {data.map((row) => (
          <div key={`${row.horizon_id}-${row.candidate.id}`} className="arl-panel p-4">
            <div className="flex flex-wrap items-center gap-2 text-xs text-steel-500">
              <span className="arl-badge bg-brand-soft text-brand">{row.jurisdiction}</span>
              <span>{row.regulator}</span>
              <span className="font-mono">{row.reference}</span>
            </div>
            <Link
              to={`/horizon/${row.horizon_id}`}
              className="mt-1 block text-sm font-semibold text-navy-900 hover:text-brand dark:text-white"
            >
              {row.horizon_title}
            </Link>
            <p className="mt-2 text-sm text-steel-700 dark:text-steel-200">{row.candidate.text}</p>
            <p className="mt-1 text-xs text-steel-500">{row.candidate.rationale}</p>
            <div className="mt-3 flex flex-wrap gap-2">
              <button
                type="button"
                className="arl-btn-primary text-xs"
                disabled={assess.isPending}
                onClick={() =>
                  assess.mutate({
                    horizon_id: row.horizon_id,
                    candidate_id: row.candidate.id,
                    decision: "applicable",
                    rationale: row.candidate.rationale,
                  })
                }
              >
                Applicable → register & case
              </button>
              <button
                type="button"
                className="arl-btn-ghost text-xs"
                disabled={assess.isPending}
                onClick={() =>
                  assess.mutate({
                    horizon_id: row.horizon_id,
                    candidate_id: row.candidate.id,
                    decision: "not_applicable",
                  })
                }
              >
                Not applicable
              </button>
            </div>
          </div>
        ))}
        {!isLoading && data.length === 0 && (
          <p className="text-sm text-steel-500">No candidates in this filter.</p>
        )}
      </div>
    </div>
  );
}
