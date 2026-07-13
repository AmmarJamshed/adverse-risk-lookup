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
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-3xl font-semibold">Administration</h1>
        <p className="text-sm text-paper/60">Users, roles, schedulers, prompts, and audit visibility</p>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="arl-panel overflow-x-auto p-4">
          <h2 className="mb-3 text-sm font-semibold uppercase">Users</h2>
          <table className="min-w-full text-sm">
            <thead className="text-xs uppercase text-paper/50">
              <tr>
                <th className="py-2 text-left">Name</th>
                <th className="py-2 text-left">Email</th>
                <th className="py-2 text-left">Role</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u: { id: string; full_name: string; email: string; role: string }) => (
                <tr key={u.id} className="border-t border-white/5">
                  <td className="py-2">{u.full_name}</td>
                  <td className="py-2">{u.email}</td>
                  <td className="py-2">{u.role}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="arl-panel p-4">
          <h2 className="mb-3 text-sm font-semibold uppercase">Job Logs</h2>
          <div className="max-h-80 space-y-2 overflow-auto text-sm">
            {jobs.map((j: { id: string; job_name: string; status: string; duration_ms?: number }) => (
              <div key={j.id} className="rounded border border-white/10 p-2">
                <div className="font-medium">{j.job_name}</div>
                <div className="text-xs text-paper/50">
                  {j.status} · {j.duration_ms ? `${Math.round(j.duration_ms)}ms` : "—"}
                </div>
              </div>
            ))}
            {jobs.length === 0 && <p className="text-paper/50">No scheduled jobs logged yet.</p>}
          </div>
        </div>
      </div>

      <div className="arl-panel p-4">
        <h2 className="mb-3 text-sm font-semibold uppercase">RBAC Roles</h2>
        <pre className="overflow-auto text-xs text-paper/70">{JSON.stringify(roles, null, 2)}</pre>
      </div>
    </div>
  );
}
