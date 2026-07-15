import { Link, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api, HorizonItem } from "../lib/api";

export default function HorizonDetailPage() {
  const { id } = useParams();
  const qc = useQueryClient();
  const [msg, setMsg] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["horizon", id],
    queryFn: async () => (await api.get<HorizonItem>(`/horizon/${id}`)).data,
    enabled: !!id,
  });

  const assess = useMutation({
    mutationFn: async (payload: {
      candidate_id: string;
      decision: string;
      rationale?: string;
    }) =>
      (
        await api.post("/applicability", {
          horizon_id: id,
          ...payload,
        })
      ).data,
    onSuccess: (res) => {
      qc.invalidateQueries({ queryKey: ["horizon"] });
      qc.invalidateQueries({ queryKey: ["applicability"] });
      qc.invalidateQueries({ queryKey: ["obligations"] });
      qc.invalidateQueries({ queryKey: ["cases"] });
      qc.invalidateQueries({ queryKey: ["obl-stats"] });
      if (res.obligation && res.gap_case) {
        setMsg(
          `Created ${res.obligation.code} and opened case ${res.gap_case.case_number}.`
        );
      } else {
        setMsg("Applicability updated.");
      }
    },
  });

  if (isLoading || !data) {
    return <p className="text-sm text-steel-500">Loading instrument…</p>;
  }

  return (
    <div className="space-y-4">
      <Link to="/" className="text-sm font-medium text-brand hover:underline">
        ← Back to Horizon Scan
      </Link>

      <div className="arl-panel p-5">
        <div className="flex flex-wrap gap-2">
          <span className="arl-badge bg-brand-soft text-brand">{data.jurisdiction}</span>
          <span className="arl-badge bg-steel-100 text-steel-700">{data.regulator}</span>
          <span className="font-mono text-[11px] text-steel-500">{data.reference}</span>
        </div>
        <h1 className="mt-2 text-xl font-semibold tracking-tight text-navy-900 dark:text-white">
          {data.title}
        </h1>
        <p className="mt-2 text-sm text-steel-600 dark:text-steel-300">{data.summary}</p>
        <p className="mt-3 text-sm leading-relaxed text-steel-700 dark:text-steel-200">{data.body}</p>
      </div>

      {msg && (
        <div className="rounded-panel border border-brand/30 bg-brand-soft px-4 py-3 text-sm text-brand">
          {msg}{" "}
          {assess.data?.gap_case?.id && (
            <Link className="font-semibold underline" to={`/cases/${assess.data.gap_case.id}`}>
              Open case →
            </Link>
          )}
        </div>
      )}

      <div className="arl-panel p-4">
        <h2 className="arl-section-label mb-3">Extracted obligation candidates</h2>
        <div className="space-y-3">
          {data.candidates.map((c) => (
            <div
              key={c.id}
              className="rounded-panel border border-steel-200 p-4 dark:border-navy-700"
            >
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div className="min-w-0 flex-1">
                  <div className="text-xs font-semibold uppercase tracking-wide text-brand">
                    {c.theme || "Requirement"}
                  </div>
                  <p className="mt-1 text-sm text-navy-900 dark:text-white">{c.text}</p>
                  <p className="mt-2 text-xs text-steel-500">{c.rationale}</p>
                  <div className="mt-2 text-[11px] text-steel-500">
                    Suggested owner: {c.suggested_owner || "—"} · Current:{" "}
                    <span className="font-semibold">{c.applicability.replace(/_/g, " ")}</span>
                  </div>
                </div>
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                <button
                  type="button"
                  className="arl-btn-primary text-xs"
                  disabled={assess.isPending}
                  onClick={() =>
                    assess.mutate({
                      candidate_id: c.id,
                      decision: "applicable",
                      rationale: c.rationale,
                    })
                  }
                >
                  Mark applicable → create obligation & case
                </button>
                <button
                  type="button"
                  className="arl-btn-ghost text-xs"
                  disabled={assess.isPending}
                  onClick={() =>
                    assess.mutate({
                      candidate_id: c.id,
                      decision: "not_applicable",
                      rationale: c.rationale || "Documented as out of scope.",
                    })
                  }
                >
                  Not applicable
                </button>
                <button
                  type="button"
                  className="arl-btn-ghost text-xs"
                  disabled={assess.isPending}
                  onClick={() =>
                    assess.mutate({
                      candidate_id: c.id,
                      decision: "under_review",
                      rationale: "Parked for further analysis.",
                    })
                  }
                >
                  Under review
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
