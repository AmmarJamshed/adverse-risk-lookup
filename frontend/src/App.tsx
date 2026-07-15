import { Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "./components/layout/AppShell";
import { useAuthStore } from "./stores/auth";
import { useThemeStore } from "./stores/theme";
import LoginPage from "./pages/LoginPage";
import HorizonScanPage from "./pages/HorizonScanPage";
import HorizonDetailPage from "./pages/HorizonDetailPage";
import ApplicabilityPage from "./pages/ApplicabilityPage";
import ObligationsPage from "./pages/ObligationsPage";
import CasesPage from "./pages/CasesPage";
import CaseDetailPage from "./pages/CaseDetailPage";
import LibraryPage from "./pages/LibraryPage";
import SourcesPage from "./pages/SourcesPage";
import TrainingsPage from "./pages/TrainingsPage";
import AdminPage from "./pages/AdminPage";

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const token = useAuthStore((s) => s.token);
  if (!token) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

export default function App() {
  const theme = useThemeStore((s) => s.theme);
  if (typeof document !== "undefined") {
    document.documentElement.classList.toggle("dark", theme === "dark");
    document.documentElement.classList.toggle("light", theme === "light");
  }

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/*"
        element={
          <PrivateRoute>
            <AppShell>
              <Routes>
                <Route path="/" element={<HorizonScanPage />} />
                <Route path="/horizon/:id" element={<HorizonDetailPage />} />
                <Route path="/applicability" element={<ApplicabilityPage />} />
                <Route path="/obligations" element={<ObligationsPage />} />
                <Route path="/cases" element={<CasesPage />} />
                <Route path="/cases/:id" element={<CaseDetailPage />} />
                <Route path="/library" element={<LibraryPage />} />
                <Route path="/sources" element={<SourcesPage />} />
                <Route path="/trainings" element={<TrainingsPage />} />
                <Route path="/admin" element={<AdminPage />} />
              </Routes>
            </AppShell>
          </PrivateRoute>
        }
      />
    </Routes>
  );
}
