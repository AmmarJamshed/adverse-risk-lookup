import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import {
  Chart as ChartJS,
  ArcElement,
  BarElement,
  CategoryScale,
  LinearScale,
  Tooltip,
  Legend,
} from "chart.js";
import { Doughnut, Bar } from "react-chartjs-2";
import { api, DashboardStats, Article } from "../lib/api";

ChartJS.register(ArcElement, BarElement, CategoryScale, LinearScale, Tooltip, Legend);

function StatCard({ label, value, hint }: { label: string; value: string | number; hint?: string }) {
  return (
    <div className="arl-panel animate-fade-up p-4">
      <div className="text-[11px] uppercase tracking-[0.16em] text-paper/45 light:text-ink-900/45">
        {label}
      </div>
      <div className="mt-2 font-display text-3xl font-semibold text-signal">{value}</div>
      {hint && <div className="mt-1 text-xs text-paper/50 light:text-ink-900/50">{hint}</div>}
    </div>
  );
}

const severityColor: Record<string, string> = {
  critical: "#c44b4b",
  high: "#c9852c",
  medium: "#3a7ca5",
  low: "#1f9d8a",
};

export default function DashboardPage() {
  const { data: stats } = useQuery({
    queryKey: ["dashboard-stats"],
    queryFn: async () => (await api.get<DashboardStats>("/dashboard/stats")).data,
  });

  const { data: articles = [] } = useQuery({
    queryKey: ["todays-articles"],
    queryFn: async () => (await api.get<Article[]>("/articles", { params: { limit: 8 } })).data,
  });

  const severityData = {
    labels: (stats?.severity || []).map((s) => s.name),
    datasets: [
      {
        data: (stats?.severity || []).map((s) => s.count),
        backgroundColor: (stats?.severity || []).map(
          (s) => severityColor[s.name] || "#3a7ca5"
        ),
        borderWidth: 0,
      },
    ],
  };

  const categoryData = {
    labels: (stats?.categories || []).slice(0, 8).map((c) => c.name),
    datasets: [
      {
        label: "Articles",
        data: (stats?.categories || []).slice(0, 8).map((c) => c.count),
        backgroundColor: "#1f9d8a",
        borderRadius: 6,
      },
    ],
  };

  return (
    <div className="space-y-6">
      <div className="animate-fade-up">
        <h1 className="font-display text-3xl font-semibold">Risk Intelligence Dashboard</h1>
        <p className="mt-1 text-sm text-paper/60 light:text-ink-900/60">
          Near real-time adverse media mapped to your operational risk register
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Today's News" value={stats?.todays_news_count ?? "—"} hint="Ingested today" />
        <StatCard
          label="Critical Alerts"
          value={stats?.totals.critical_alerts ?? "—"}
          hint="High & critical severity"
        />
        <StatCard
          label="Emerging Risks"
          value={stats?.totals.emerging_risks ?? "—"}
          hint="Themes without register match"
        />
        <StatCard
          label="Relevant Articles"
          value={stats?.totals.relevant ?? "—"}
          hint={`of ${stats?.totals.articles ?? 0} collected`}
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <div className="arl-panel p-4 lg:col-span-1">
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-paper/70 light:text-ink-900/70">
            Severity Distribution
          </h2>
          <div className="mx-auto max-w-[240px]">
            {(stats?.severity?.length || 0) > 0 ? (
              <Doughnut
                data={severityData}
                options={{ plugins: { legend: { position: "bottom", labels: { color: "#9fb2c7" } } } }}
              />
            ) : (
              <p className="py-10 text-center text-sm text-paper/50">No data yet</p>
            )}
          </div>
        </div>
        <div className="arl-panel p-4 lg:col-span-2">
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-paper/70 light:text-ink-900/70">
            Risk Categories
          </h2>
          {(stats?.categories?.length || 0) > 0 ? (
            <Bar
              data={categoryData}
              options={{
                responsive: true,
                plugins: { legend: { display: false } },
                scales: {
                  x: { ticks: { color: "#9fb2c7" }, grid: { color: "rgba(255,255,255,0.05)" } },
                  y: { ticks: { color: "#9fb2c7" }, grid: { color: "rgba(255,255,255,0.05)" } },
                },
              }}
            />
          ) : (
            <p className="py-10 text-center text-sm text-paper/50">No data yet</p>
          )}
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="arl-panel p-4">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-sm font-semibold uppercase tracking-wide text-paper/70 light:text-ink-900/70">
              Latest Adverse Media
            </h2>
            <Link to="/articles" className="text-xs text-signal hover:underline">
              View all
            </Link>
          </div>
          <div className="space-y-3">
            {articles.map((a) => (
              <Link
                key={a.id}
                to={`/articles/${a.id}`}
                className="block rounded-lg border border-white/5 bg-ink-900/40 p-3 transition hover:border-signal/30 light:border-ink-900/10 light:bg-paper"
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="text-sm font-medium">{a.title_en || a.title}</div>
                    <div className="mt-1 text-xs text-paper/50 light:text-ink-900/50">
                      {a.country || "Global"} · {a.risk_category || "Uncategorized"}
                    </div>
                  </div>
                  <span
                    className="shrink-0 rounded px-2 py-0.5 text-[10px] uppercase tracking-wide"
                    style={{
                      background: `${severityColor[a.severity || "low"] || "#3a7ca5"}33`,
                      color: severityColor[a.severity || "low"] || "#3a7ca5",
                    }}
                  >
                    {a.severity || "n/a"}
                  </span>
                </div>
              </Link>
            ))}
            {articles.length === 0 && (
              <p className="text-sm text-paper/50">No articles yet — start collectors from News Sources.</p>
            )}
          </div>
        </div>

        <div className="arl-panel p-4">
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-paper/70 light:text-ink-900/70">
            Top Countries · Languages · Sources
          </h2>
          <div className="grid gap-4 sm:grid-cols-3">
            {[
              { title: "Countries", rows: stats?.countries },
              { title: "Languages", rows: stats?.languages },
              { title: "Sources", rows: stats?.sources },
            ].map((block) => (
              <div key={block.title}>
                <div className="mb-2 text-xs font-semibold text-signal">{block.title}</div>
                <ul className="space-y-1.5 text-xs">
                  {(block.rows || []).slice(0, 6).map((r) => (
                    <li key={r.name} className="flex justify-between gap-2 text-paper/70 light:text-ink-900/70">
                      <span className="truncate">{r.name}</span>
                      <span className="font-mono text-paper/90 light:text-ink-900">{r.count}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
