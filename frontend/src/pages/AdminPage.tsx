import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";

export default function AdminPage() {
  const { data: users = [] } = useQuery({
    queryKey: ["admin-users"],
    queryFn: async () => (await api.get("/admin/users")).data,
  });
  const { data: jobs = [] } = useQuery({
    queryKey: ["admin-jobs"],
    queryFn: async () => (await api.get("/admin/jobs")).data,
  });
  const { data: roles } = useQuery({
    queryKey: ["admin-roles"],
    queryFn: async () => (await api.get("/admin/roles")).data,
  });

  return (
    <div className="space-y-4">
      <div>
        <h1 className="arl-page-title">Administration</h1>
        <p className="arl-page-sub">Users, roles, and job visibility for the obligations workstation</p>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="arl-table-wrap overflow-x-auto">
          <div className="border-b border-steel-200 bg-steel-50 px-4 py-2 dark:border-navy-700 dark:bg-navy-950">
            <h2 className="arl-section-label">Users</h2>
          </div>
          <table className="min-w-full text-sm">
            <thead className="text-[11px] font-semibold uppercase tracking-wide text-steel-500">
              <tr>
                <th className="px-4 py-2 text-left">Name</th>
                <th className="px-4 py-2 text-left">Email</th>
                <th className="px-4 py-2 text-left">Role</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-steel-100 dark:divide-navy-800">
              {users.map((u: { id: string; full_name: string; email: string; role: string }) => (
                <tr key={u.id}>
                  <td className="px-4 py-2.5 font-medium text-navy-900 dark:text-white">{u.full_name}</td>
                  <td className="px-4 py-2.5 text-steel-600">{u.email}</td>
                  <td className="px-4 py-2.5">
                    <span className="arl-badge bg-brand-soft text-brand">{u.role}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="arl-panel p-4">
          <h2 className="arl-section-label mb-3">Job Logs</h2>
          <div className="max-h-80 space-y-2 overflow-auto text-sm">
            {jobs.map((j: { id: string; job_name: string; status: string; duration_ms?: number }) => (
              <div key={j.id} className="rounded-panel border border-steel-200 p-2 dark:border-navy-700">
                <div className="font-medium text-navy-900 dark:text-white">{j.job_name}</div>
                <div className="text-xs text-steel-500">
                  {j.status} · {j.duration_ms ? `${Math.round(j.duration_ms)}ms` : "—"}
                </div>
              </div>
            ))}
            {jobs.length === 0 && <p className="text-steel-500">No scheduled jobs logged yet.</p>}
          </div>
        </div>
      </div>

      <div className="arl-panel p-4">
        <h2 className="arl-section-label mb-3">RBAC Roles</h2>
        <pre className="overflow-auto rounded-panel bg-steel-50 p-3 font-mono text-xs text-steel-700 dark:bg-navy-950 dark:text-steel-300">
          {JSON.stringify(roles, null, 2)}
        </pre>
      </div>
    </div>
  );
}
