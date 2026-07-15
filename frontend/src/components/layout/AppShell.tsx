import { NavLink } from "react-router-dom";
import {
  Activity,
  AlertTriangle,
  Bell,
  Bot,
  FileBarChart2,
  LayoutDashboard,
  Newspaper,
  Radar,
  Rss,
  Search,
  Settings,
  Shield,
  Moon,
  Sun,
  LogOut,
} from "lucide-react";
import { useAuthStore } from "../../stores/auth";
import { useThemeStore } from "../../stores/theme";

const nav = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/articles", label: "Adverse Media", icon: Newspaper },
  { to: "/search", label: "Global Search", icon: Search },
  { to: "/risks", label: "Risk Register", icon: Shield },
  { to: "/emerging", label: "Emerging Risks", icon: Radar },
  { to: "/feeds", label: "News Sources", icon: Rss },
  { to: "/alerts", label: "Alerts", icon: Bell },
  { to: "/reports", label: "Reports", icon: FileBarChart2 },
  { to: "/assistant", label: "AI Assistant", icon: Bot },
  { to: "/admin", label: "Administration", icon: Settings },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const theme = useThemeStore((s) => s.theme);
  const toggleTheme = useThemeStore((s) => s.toggle);

  return (
    <div className="min-h-screen bg-mesh text-paper light:bg-mesh-light light:text-ink-900">
      <div className="arl-grid-bg min-h-screen">
        <div className="mx-auto flex min-h-screen max-w-[1600px]">
          <aside className="hidden w-64 shrink-0 border-r border-white/10 bg-ink-950/70 p-4 md:block light:border-ink-900/10 light:bg-white/80">
            <div className="mb-8 animate-fade-up">
              <div className="flex items-center gap-2">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-signal/20 text-signal">
                  <Activity className="h-5 w-5" />
                </div>
                <div>
                  <div className="font-display text-lg font-semibold tracking-tight">ARL</div>
                  <div className="text-[10px] uppercase tracking-[0.18em] text-paper/50 light:text-ink-900/50">
                    Adverse Risk Lookup
                  </div>
                </div>
              </div>
              <p className="mt-3 text-[11px] leading-relaxed text-paper/55 light:text-ink-900/55">
                Transforming Global Banking News into Actionable Risk Intelligence
              </p>
            </div>
            <nav className="space-y-1">
              {nav.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.to === "/"}
                  className={({ isActive }) =>
                    `flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition ${
                      isActive
                        ? "bg-signal/15 text-signal"
                        : "text-paper/70 hover:bg-white/5 hover:text-paper light:text-ink-800 light:hover:bg-ink-900/5"
                    }`
                  }
                >
                  <item.icon className="h-4 w-4" />
                  {item.label}
                </NavLink>
              ))}
            </nav>
          </aside>

          <div className="flex min-w-0 flex-1 flex-col">
            <header className="sticky top-0 z-20 flex items-center justify-between border-b border-white/10 bg-ink-950/80 px-4 py-3 backdrop-blur light:border-ink-900/10 light:bg-white/90 md:px-6">
              <div className="flex items-center gap-2 text-xs text-paper/60 light:text-ink-900/60">
                <span className="inline-flex items-center gap-1 rounded-md bg-signal/15 px-2 py-1 text-signal">
                  <span className="h-1.5 w-1.5 animate-pulse-soft rounded-full bg-signal" />
                  LIVE MONITORING
                </span>
                <span className="hidden sm:inline">Enterprise GRC Intelligence</span>
              </div>
              <div className="flex items-center gap-2">
                <button type="button" className="arl-btn-ghost" onClick={toggleTheme} aria-label="Toggle theme">
                  {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
                </button>
                <div className="hidden text-right sm:block">
                  <div className="text-sm font-medium">{user?.full_name}</div>
                  <div className="text-[11px] uppercase tracking-wide text-paper/50 light:text-ink-900/50">
                    {user?.role?.replace("_", " ")}
                  </div>
                </div>
                <button type="button" className="arl-btn-ghost" onClick={logout} title="Sign out">
                  <LogOut className="h-4 w-4" />
                </button>
              </div>
            </header>

            <main className="flex-1 p-4 md:p-6">{children}</main>

            <footer className="border-t border-white/10 px-6 py-3 text-[11px] text-paper/40 light:border-ink-900/10 light:text-ink-900/40">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span>Adverse Risk Lookup © {new Date().getFullYear()}</span>
                <span className="inline-flex items-center gap-1">
                  <AlertTriangle className="h-3 w-3" /> Explainable AI · Multilingual · Cloud Ready
                </span>
              </div>
            </footer>
          </div>
        </div>
      </div>
    </div>
  );
}
