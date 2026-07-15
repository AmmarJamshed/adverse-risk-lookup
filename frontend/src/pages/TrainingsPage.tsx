import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ExternalLink, GraduationCap } from "lucide-react";
import { api, Training } from "../lib/api";

const COUNTRIES = [
  "Saudi Arabia",
  "Bahrain",
  "Qatar",
  "Oman",
  "Germany",
  "France",
  "Czech Republic",
  "Netherlands",
  "Canada",
  "Japan",
  "Malaysia",
  "Singapore",
];

function formatWhen(iso?: string | null) {
  if (!iso) return "Date TBA";
  try {
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return iso;
    return d.toLocaleString(undefined, {
      weekday: "short",
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

export default function TrainingsPage() {
  const [country, setCountry] = useState("");
  const [q, setQ] = useState("");

  const { data, isLoading, error } = useQuery({
    queryKey: ["trainings"],
    queryFn: async () =>
      (
        await api.get<{
          generated_at?: string;
          count: number;
          trainings: Training[];
          countries?: string[];
        }>("/trainings")
      ).data,
  });

  const rows = useMemo(() => {
    let list = data?.trainings || [];
    if (country) list = list.filter((t) => t.country === country);
    if (q.trim()) {
      const needle = q.trim().toLowerCase();
      list = list.filter(
        (t) =>
          t.title.toLowerCase().includes(needle) ||
          (t.description || "").toLowerCase().includes(needle) ||
          (t.organizer || "").toLowerCase().includes(needle) ||
          (t.city || "").toLowerCase().includes(needle)
      );
    }
    return list;
  }, [data, country, q]);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="arl-page-title">Trainings</h1>
          <p className="arl-page-sub">
            Sanitized listings for Saudi Arabia, Bahrain, Qatar, Oman, Germany, France, Czech
            Republic, Netherlands, Canada, Japan, Malaysia, and Singapore — each button opens the
            registration page
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs text-steel-500">
          <GraduationCap className="h-4 w-4 text-brand" />
          {data?.count ?? 0} events
          {data?.generated_at ? ` · updated ${new Date(data.generated_at).toLocaleDateString()}` : ""}
        </div>
      </div>

      <div className="arl-panel grid gap-3 p-4 md:grid-cols-[200px_1fr]">
        <select className="arl-input" value={country} onChange={(e) => setCountry(e.target.value)}>
          <option value="">All countries</option>
          {COUNTRIES.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
        <input
          className="arl-input"
          placeholder="Search title, organizer, city…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
      </div>

      {isLoading && <p className="text-sm text-steel-500">Loading trainings…</p>}
      {error && (
        <p className="text-sm text-hit-critical">Could not load trainings. Try again after the weekly scrape.</p>
      )}

      <div className="space-y-3">
        {rows.map((t) => (
          <article key={t.id} className="arl-panel p-4">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap gap-2">
                  <span className="arl-badge bg-brand-soft text-brand">{t.country}</span>
                  {t.city && <span className="arl-badge bg-steel-100 text-steel-700">{t.city}</span>}
                  {t.source && (
                    <span className="arl-badge bg-steel-100 text-steel-600">{t.source}</span>
                  )}
                </div>
                <h2 className="mt-2 text-base font-semibold text-navy-900 dark:text-white">{t.title}</h2>
                <p className="mt-1 text-xs text-steel-500">
                  {formatWhen(t.start_date)}
                  {t.location_name ? ` · ${t.location_name}` : ""}
                  {t.organizer ? ` · ${t.organizer}` : ""}
                  {t.price ? ` · ${t.price}` : ""}
                </p>
                {t.description && (
                  <p className="mt-2 text-sm leading-relaxed text-steel-700 dark:text-steel-300">
                    {t.description}
                  </p>
                )}
              </div>
              <a
                href={t.register_url}
                target="_blank"
                rel="noopener noreferrer"
                className="arl-btn-primary shrink-0 text-xs"
              >
                Register
                <ExternalLink className="h-3.5 w-3.5" />
              </a>
            </div>
          </article>
        ))}
        {!isLoading && rows.length === 0 && (
          <p className="text-sm text-steel-500">No trainings match this filter.</p>
        )}
      </div>
    </div>
  );
}
