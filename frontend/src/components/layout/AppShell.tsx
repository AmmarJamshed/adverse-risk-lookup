import { NavLink } from "react-router-dom";
import {
  Radar,
  ClipboardCheck,
  BookMarked,
  Briefcase,
  Library,
  Rss,
  GraduationCap,
  Settings,
  Moon,
  Sun,
  LogOut,
  Menu,
} from "lucide-react";
import { useState } from "react";
import { useAuthStore } from "../../stores/auth";
import { useThemeStore } from "../../stores/theme";

const nav = [
  { to: "/", label: "Horizon Scan", icon: Radar },
  { to: "/applicability", label: "Applicability", icon: ClipboardCheck },
  { to: "/obligations", label: "Obligations Register", icon: BookMarked },
  { to: "/cases", label: "Gap Analysis Cases", icon: Briefcase },
  { to: "/library", label: "Policies & Controls", icon: Library },
  { to: "/trainings", label: "Trainings", icon: GraduationCap },
  { to: "/sources", label: "Regulatory Sources", icon: Rss },
  { to: "/admin", label: "Administration", icon: Settings },
];
export function AppShell({ children }: { children: React.ReactNode }) {
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const theme = useThemeStore((s) => s.theme);
  const toggleTheme = useThemeStore((s) => s.toggle);
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="min-h-screen bg-steel-50 text-steel-900 dark:bg-navy-950 dark:text-steel-100">
      <div className="flex min-h-screen">
        <aside
          className={`${
            mobileOpen ? "translate-x-0" : "-translate-x-full"
          } fixed inset-y-0 left-0 z-40 w-[248px] border-r border-navy-800 bg-navy-900 text-white transition-transform md:static md:translate-x-0`}
        >
          <div className="flex h-14 items-center gap-3 border-b border-white/10 px-4">
            <div className="flex h-8 w-8 items-center justify-center rounded-sm bg-brand text-xs font-bold tracking-tight">
              ARL
            </div>
            <div className="min-w-0">
              <div className="truncate text-sm font-semibold leading-tight">Adverse Risk Lookup</div>
              <div className="truncate text-[10px] uppercase tracking-[0.14em] text-white/50">
                Obligations · GRC
              </div>
            </div>
          </div>

          <div className="border-b border-white/10 px-4 py-3">
            <div className="text-[10px] font-semibold uppercase tracking-[0.14em] text-white/40">
              Workspace
            </div>
            <div className="mt-1 truncate text-xs text-white/75">Demo Financial Group</div>
            <div className="mt-0.5 truncate text-[10px] text-white/45">UK · USA · EU · Pakistan</div>
          </div>

          <nav className="space-y-0.5 p-2">
            {nav.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === "/"}
                onClick={() => setMobileOpen(false)}
                className={({ isActive }) =>
                  `flex items-center gap-2.5 rounded-sm px-3 py-2 text-[13px] transition ${
                    isActive
                      ? "bg-brand text-white"
                      : "text-white/70 hover:bg-white/5 hover:text-white"
                  }`
                }
              >
                <item.icon className="h-4 w-4 shrink-0 opacity-90" />
                <span className="truncate">{item.label}</span>
              </NavLink>
            ))}
          </nav>

          <div className="absolute bottom-0 left-0 right-0 border-t border-white/10 p-3 text-[10px] text-white/40">
            v2.0 · Regulatory obligations workstation
          </div>
        </aside>

        {mobileOpen && (
          <button
            type="button"
            className="fixed inset-0 z-30 bg-navy-950/40 md:hidden"
            aria-label="Close menu"
            onClick={() => setMobileOpen(false)}
          />
        )}

        <div className="flex min-w-0 flex-1 flex-col">
          <header className="sticky top-0 z-20 flex h-14 items-center justify-between border-b border-steel-200 bg-white px-4 dark:border-navy-800 dark:bg-navy-900 md:px-5">
            <div className="flex items-center gap-3">
              <button
                type="button"
                className="arl-btn-ghost md:hidden"
                onClick={() => setMobileOpen(true)}
                aria-label="Open menu"
              >
                <Menu className="h-4 w-4" />
              </button>
              <div>
                <div className="text-[11px] font-semibold uppercase tracking-[0.12em] text-steel-400">
                  Obligations workflow
                </div>
                <div className="text-sm font-medium text-navy-900 dark:text-white">
                  Scan → Assess → Register → Gap analysis
                </div>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <span className="hidden items-center gap-1.5 rounded-sm border border-steel-200 bg-steel-50 px-2 py-1 text-[11px] font-semibold text-hit-low sm:inline-flex dark:border-navy-700 dark:bg-navy-950">
                <span className="h-1.5 w-1.5 rounded-full bg-hit-low" />
                SYSTEM ONLINE
              </span>
              <button type="button" className="arl-btn-ghost" onClick={toggleTheme} aria-label="Toggle theme">
                {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
              </button>
              <div className="hidden border-l border-steel-200 pl-3 text-right dark:border-navy-700 sm:block">
                <div className="text-sm font-semibold text-navy-900 dark:text-white">{user?.full_name}</div>
                <div className="text-[11px] uppercase tracking-wide text-steel-500">
                  {user?.role?.replace(/_/g, " ")}
                </div>
              </div>
              <button type="button" className="arl-btn-ghost" onClick={logout} title="Sign out">
                <LogOut className="h-4 w-4" />
              </button>
            </div>
          </header>

          <main className="flex-1 p-4 md:p-5">{children}</main>

          <footer className="border-t border-steel-200 bg-white px-5 py-2 text-[11px] text-steel-500 dark:border-navy-800 dark:bg-navy-900 dark:text-steel-400">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <span>© {new Date().getFullYear()} Adverse Risk Lookup</span>
              <span>UK · USA · EU · Pakistan · Audit-ready obligations</span>
            </div>
          </footer>
        </div>
      </div>
    </div>
  );
}
