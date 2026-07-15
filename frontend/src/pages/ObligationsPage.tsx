import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api, GapCase, Obligation } from "../lib/api";

export default function ObligationsPage() {
  const [jurisdiction, setJurisdiction] = useState("");
  const { data = [], isLoading } = useQuery({
    queryKey: ["obligations", jurisdiction],
    queryFn: async () =>
      (
        await api.get<Obligation[]>("/obligations", {
          params: { jurisdiction: jurisdiction || undefined },
        })
      ).data,
  });
  const { data: cases = [] } = useQuery({
    queryKey: ["cases"],
    queryFn: async () => (await api.get<GapCase[]>("/cases")).data,
  });

  function caseFor(oblId: string) {
    return cases.find((c) => c.obligation_id === oblId);
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="arl-page-title">Obligations Register</h1>
          <p className="arl-page-sub">
            Auto-created when candidates are marked applicable — one structured obligation per requirement
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

      {isLoading && <p className="text-sm text-steel-500">Loading register…</p>}

      <div className="arl-table-wrap overflow-x-auto">
        <table className="min-w-full text-left text-sm">
          <thead className="border-b border-steel-200 bg-steel-50 text-[11px] font-semibold uppercase tracking-wide text-steel-500 dark:border-navy-700 dark:bg-navy-950">
            <tr>
              <th className="px-4 py-2.5">Code</th>
              <th className="px-4 py-2.5">Statement</th>
              <th className="px-4 py-2.5">Jurisdiction</th>
              <th className="px-4 py-2.5">Owner</th>
              <th className="px-4 py-2.5">Due</th>
              <th className="px-4 py-2.5">Gap case</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-steel-100 dark:divide-navy-800">
            {data.map((o) => {
              const c = caseFor(o.id);
              return (
                <tr key={o.id} className="hover:bg-steel-50 dark:hover:bg-navy-800/40">
                  <td className="px-4 py-2.5 font-mono text-xs text-brand">{o.code}</td>
                  <td className="max-w-md px-4 py-2.5 text-navy-900 dark:text-white">{o.statement}</td>
                  <td className="px-4 py-2.5 text-steel-600">{o.jurisdiction}</td>
                  <td className="px-4 py-2.5 text-steel-600">{o.owner}</td>
                  <td className="px-4 py-2.5 font-mono text-xs text-steel-500">{o.due_date || "—"}</td>
                  <td className="px-4 py-2.5">
                    {c ? (
                      <Link to={`/cases/${c.id}`} className="text-sm font-medium text-brand hover:underline">
                        {c.case_number}
                      </Link>
                    ) : (
                      "—"
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
