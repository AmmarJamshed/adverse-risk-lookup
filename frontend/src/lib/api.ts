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
    horizon_items: number;
    pending_assessment: number;
    obligations: number;
    open_cases: number;
    gap_or_partial: number;
    under_review_candidates: number;
  };
  jurisdictions: { name: string; count: number }[];
  gap_status: { name: string; count: number }[];
  case_status: { name: string; count: number }[];
};

export type ObligationCandidate = {
  id: string;
  text: string;
  theme?: string;
  applicability: "applicable" | "not_applicable" | "under_review" | string;
  rationale?: string;
  suggested_owner?: string;
  assessed_by?: string;
  assessed_at?: string;
};

export type HorizonItem = {
  id: string;
  title: string;
  jurisdiction: string;
  regulator: string;
  instrument_type?: string;
  reference?: string;
  published_at?: string;
  summary?: string;
  body?: string;
  source_id?: string;
  source_name?: string;
  status: string;
  priority?: string;
  tags?: string[];
  candidates: ObligationCandidate[];
  created_at?: string;
};

export type Obligation = {
  id: string;
  code: string;
  statement: string;
  jurisdiction: string;
  regulator: string;
  theme?: string;
  owner: string;
  status: string;
  source_horizon_id?: string;
  source_candidate_id?: string;
  source_reference?: string;
  due_date?: string;
  created_at?: string;
};

export type Policy = {
  id: string;
  code: string;
  title: string;
  owner: string;
  jurisdiction: string;
  status: string;
  summary?: string;
};

export type Control = {
  id: string;
  code: string;
  title: string;
  policy_id?: string | null;
  owner: string;
  type: string;
  status: string;
};

export type CaseMapping = {
  id: string;
  kind: "policy" | "control" | string;
  ref_id: string;
  ref_code: string;
  ref_title: string;
  coverage: string;
  notes?: string;
};

export type GapCase = {
  id: string;
  case_number: string;
  obligation_id: string;
  title: string;
  status: string;
  gap_status: string;
  owner: string;
  jurisdiction: string;
  remediation_notes?: string;
  mappings: CaseMapping[];
  created_at?: string;
  obligation?: Obligation | null;
};

export type ApplicabilityInboxItem = {
  horizon_id: string;
  horizon_title: string;
  jurisdiction: string;
  regulator: string;
  reference?: string;
  priority?: string;
  candidate: ObligationCandidate;
};

export type RegulatorySource = {
  id: string;
  name: string;
  regulator: string;
  jurisdiction: string;
  url: string;
  category: string;
  is_active: boolean;
  last_status?: string;
  success_count: number;
  failure_count: number;
};

export type Training = {
  id: string;
  title: string;
  description?: string;
  country: string;
  city?: string;
  location_name?: string;
  organizer?: string;
  start_date?: string | null;
  end_date?: string | null;
  price?: string;
  register_url: string;
  source?: string;
  scraped_at?: string;
};
