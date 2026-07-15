import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";

export default function EmergingPage() {
  const { data = [] } = useQuery({
    queryKey: ["emerging"],
    queryFn: async () => (await api.get("/emerging-risks")).data,
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-3xl font-semibold">Emerging Risks</h1>
        <p className="text-sm text-paper/60">
          Themes detected in adverse media that may require new risk register entries
        </p>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        {data.map((e: Record<string, unknown>) => (
          <div key={String(e.id)} className="arl-panel p-4">
            <div className="text-xs uppercase tracking-wide text-signal">
              {String(e.suggested_category || "Emerging")} · Confidence{" "}
              {Math.round(Number(e.confidence || 0) * 100)}%
            </div>
            <h2 className="mt-2 font-display text-xl">{String(e.title)}</h2>
            <p className="mt-2 text-sm text-paper/70">{String(e.description || "")}</p>
            <p className="mt-3 text-xs text-paper/50">{String(e.reasoning || "")}</p>
            <div className="mt-3 text-xs">
              Suggested owner: {String(e.suggested_owner || "—")} · Articles: {String(e.article_count || 0)}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
