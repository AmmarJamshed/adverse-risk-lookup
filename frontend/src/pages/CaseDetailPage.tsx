import { Link, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api, Control, GapCase, Policy } from "../lib/api";

export default function CaseDetailPage() {
  const { id } = useParams();
  const qc = useQueryClient();
  const [kind, setKind] = useState<"policy" | "control">("policy");
  const [refId, setRefId] = useState("");
  const [coverage, setCoverage] = useState("partial");
  const [notes, setNotes] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["case", id],
    queryFn: async () => (await api.get<GapCase>(`/cases/${id}`)).data,
    enabled: !!id,
  });
  const { data: library } = useQuery({
    queryKey: ["library"],
    queryFn: async () =>
      (await api.get<{ policies: Policy[]; controls: Control[] }>("/library")).data,
  });

  const mapMut = useMutation({
    mutationFn: async () =>
      (
        await api.post(`/cases/${id}/mappings`, {
          kind,
          ref_id: refId,
          coverage,
          notes,
        })
      ).data,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["case", id] });
      qc.invalidateQueries({ queryKey: ["cases"] });
      setNotes("");
      setRefId("");
    },
  });

  if (isLoading || !data) {
    return <p className="text-sm text-steel-500">Loading case…</p>;
  }

  const options = kind === "policy" ? library?.policies || [] : library?.controls || [];

  return (
    <div className="space-y-4">
      <Link to="/cases" className="text-sm font-medium text-brand hover:underline">
        ← Back to Gap Analysis Cases
      </Link>

      <div className="arl-panel p-5">
        <div className="flex flex-wrap gap-2">
          <span className="font-mono text-xs text-brand">{data.case_number}</span>
          <span className="arl-badge bg-brand-soft text-brand">{data.jurisdiction}</span>
          <span className="arl-badge bg-amber-50 text-hit-medium">{data.gap_status}</span>
        </div>
        <h1 className="mt-2 text-xl font-semibold text-navy-900 dark:text-white">{data.title}</h1>
        {data.obligation && (
          <div className="mt-3 rounded-panel border border-steel-200 bg-steel-50 p-3 text-sm dark:border-navy-700 dark:bg-navy-950">
            <div className="arl-section-label">Obligation</div>
            <div className="mt-1 font-mono text-xs text-brand">{data.obligation.code}</div>
            <p className="mt-1 text-steel-800 dark:text-steel-200">{data.obligation.statement}</p>
          </div>
        )}
        {data.remediation_notes && (
          <p className="mt-3 text-sm text-steel-600">Remediation: {data.remediation_notes}</p>
        )}
      </div>

      <div className="arl-panel p-4">
        <h2 className="arl-section-label mb-3">Mapped policies & controls</h2>
        <div className="space-y-2">
          {data.mappings.map((m) => (
            <div
              key={m.id}
              className="flex flex-wrap items-start justify-between gap-2 rounded-panel border border-steel-200 p-3 dark:border-navy-700"
            >
              <div>
                <div className="text-[11px] font-semibold uppercase text-steel-500">{m.kind}</div>
                <div className="font-mono text-xs text-brand">{m.ref_code}</div>
                <div className="text-sm font-medium text-navy-900 dark:text-white">{m.ref_title}</div>
                {m.notes && <p className="mt-1 text-xs text-steel-500">{m.notes}</p>}
              </div>
              <span className="arl-badge bg-steel-100 text-steel-700">{m.coverage}</span>
            </div>
          ))}
          {data.mappings.length === 0 && (
            <p className="text-sm text-steel-500">No mappings yet — attach a policy or control below.</p>
          )}
        </div>
      </div>

      <div className="arl-panel space-y-3 p-4">
        <h2 className="arl-section-label">Map to library</h2>
        <div className="grid gap-3 md:grid-cols-2">
          <select
            className="arl-input"
            value={kind}
            onChange={(e) => {
              setKind(e.target.value as "policy" | "control");
              setRefId("");
            }}
          >
            <option value="policy">Policy</option>
            <option value="control">Control</option>
          </select>
          <select className="arl-input" value={refId} onChange={(e) => setRefId(e.target.value)}>
            <option value="">Select {kind}…</option>
            {options.map((o) => (
              <option key={o.id} value={o.id}>
                {o.code} — {o.title}
              </option>
            ))}
          </select>
          <select className="arl-input" value={coverage} onChange={(e) => setCoverage(e.target.value)}>
            <option value="mapped">Coverage: mapped</option>
            <option value="partial">Coverage: partial</option>
            <option value="gap">Coverage: gap</option>
          </select>
          <input
            className="arl-input"
            placeholder="Notes"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
          />
        </div>
        <button
          type="button"
          className="arl-btn"
          disabled={!refId || mapMut.isPending}
          onClick={() => mapMut.mutate()}
        >
          Add mapping
        </button>
      </div>
    </div>
  );
}
