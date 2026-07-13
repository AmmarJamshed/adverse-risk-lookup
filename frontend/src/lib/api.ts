import axios from "axios";
import { useAuthStore } from "../stores/auth";

const baseURL = import.meta.env.VITE_API_URL || "/api";

export const api = axios.create({
  baseURL: baseURL.endsWith("/v1") ? baseURL : `${baseURL.replace(/\/$/, "")}/v1`,
  timeout: 60000,
});

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  // Bypass ngrok free-tier browser warning interstitial for XHR
  config.headers["ngrok-skip-browser-warning"] = "true";
  return config;
});

api.interceptors.response.use(
  (r) => r,
  (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout();
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

export type DashboardStats = {
  totals: {
    articles: number;
    relevant: number;
    critical_alerts: number;
    emerging_risks: number;
  };
  countries: { name: string; count: number }[];
  severity: { name: string; count: number }[];
  categories: { name: string; count: number }[];
  languages: { name: string; count: number }[];
  sources: { name: string; count: number }[];
  todays_news_count: number;
};

export type Article = {
  id: string;
  title: string;
  title_en?: string;
  url: string;
  source_name?: string;
  language: string;
  country?: string;
  summary_executive?: string;
  summary_detailed?: string;
  content_original?: string;
  content_en?: string;
  severity?: string;
  severity_score: number;
  confidence: number;
  is_emerging: boolean;
  requires_escalation: boolean;
  risk_category?: string;
  banks: string[];
  regulators: string[];
  departments: string[];
  tags: string[];
  recommended_actions: Record<string, string[]>;
  processing_status: string;
  published_at?: string;
  created_at?: string;
  risk_matches?: Array<Record<string, unknown>>;
  ai_analysis?: Record<string, unknown>;
};
