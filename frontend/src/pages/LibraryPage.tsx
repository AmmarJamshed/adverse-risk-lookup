import { useQuery } from "@tanstack/react-query";
import { api, Control, Policy } from "../lib/api";

export default function LibraryPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["library"],
    queryFn: async () =>
      (await api.get<{ policies: Policy[]; controls: Control[] }>("/library")).data,
  });

  return (
    <div className="space-y-4">
      <div>
        <h1 className="arl-page-title">Policies & Controls</h1>
        <p className="arl-page-sub">
          Institution inventory used to map coverage against each regulatory obligation
        </p>
      </div>

      {isLoading && <p className="text-sm text-steel-500">Loading library…</p>}

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="arl-table-wrap">
          <div className="border-b border-steel-200 bg-steel-50 px-4 py-2 dark:border-navy-700 dark:bg-navy-950">
            <h2 className="arl-section-label">Policies</h2>
          </div>
          <div className="divide-y divide-steel-100 dark:divide-navy-800">
            {(data?.policies || []).map((p) => (
              <div key={p.id} className="px-4 py-3">
                <div className="font-mono text-xs text-brand">{p.code}</div>
                <div className="text-sm font-semibold text-navy-900 dark:text-white">{p.title}</div>
                <div className="mt-1 text-xs text-steel-500">
                  {p.jurisdiction} · {p.owner} · {p.status}
                </div>
                {p.summary && <p className="mt-1 text-xs text-steel-600">{p.summary}</p>}
              </div>
            ))}
          </div>
        </div>

        <div className="arl-table-wrap">
          <div className="border-b border-steel-200 bg-steel-50 px-4 py-2 dark:border-navy-700 dark:bg-navy-950">
            <h2 className="arl-section-label">Controls</h2>
          </div>
          <div className="divide-y divide-steel-100 dark:divide-navy-800">
            {(data?.controls || []).map((c) => (
              <div key={c.id} className="px-4 py-3">
                <div className="font-mono text-xs text-brand">{c.code}</div>
                <div className="text-sm font-semibold text-navy-900 dark:text-white">{c.title}</div>
                <div className="mt-1 text-xs text-steel-500">
                  {c.type} · {c.owner} · {c.status}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
