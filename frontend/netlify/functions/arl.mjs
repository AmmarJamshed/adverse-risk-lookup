/**
 * Free serverless ARL API hosted on Netlify (no paid Docker host required).
 * Proxies routes under /.netlify/functions/arl/*
 */
import { SignJWT, jwtVerify } from "jose";
import { createHash, randomUUID } from "crypto";

const JWT_SECRET = new TextEncoder().encode(
  process.env.JWT_SECRET || "arl-free-netlify-demo-secret-change-me"
);
const DEMO_PASSWORD = "ChangeMe123!";
const DEMO_PASS_HASH = createHash("sha256").update(DEMO_PASSWORD).digest("hex");

const users = [
  {
    id: "11111111-1111-1111-1111-111111111111",
    email: "admin@arl.local",
    full_name: "ARL Administrator",
    role: "super_admin",
    department: "Operational Risk",
    is_active: true,
    preferences: {},
    password_hash: DEMO_PASS_HASH,
  },
];

const articles = [
  {
    id: "a1000000-0000-0000-0000-000000000001",
    title: "Major European Bank Hit by Ransomware Disruptions",
    title_en: "Major European Bank Hit by Ransomware Disruptions",
    url: "https://example.com/news/eu-bank-ransomware",
    source_type: "seed",
    source_name: "ARL Demo",
    language: "en",
    country: "Germany",
    region: "Europe",
    summary_executive:
      "EU bank suffered ransomware impacting payments and digital channels; regulators notified.",
    summary_detailed:
      "A large European banking group reported service outages after a ransomware attack targeted internal systems.",
    content_en:
      "A large European banking group reported service outages after a ransomware attack targeted internal systems. Card payments and mobile banking were intermittently unavailable.",
    content_original:
      "A large European banking group reported service outages after a ransomware attack targeted internal systems.",
    severity: "critical",
    severity_score: 92,
    urgency: "immediate",
    confidence: 0.91,
    is_relevant: true,
    is_emerging: false,
    requires_escalation: true,
    risk_category: "Cyber Risk",
    incident_type: "ransomware",
    banks: ["Example EU Bank"],
    regulators: ["BaFin", "ECB"],
    departments: ["Cybersecurity", "Operational Risk", "Digital Banking"],
    tags: ["ransomware", "cyber", "payments"],
    people: [],
    organizations: [],
    products: ["Cards", "Mobile Banking"],
    recommended_actions: {
      immediate: ["Activate cyber IR plan", "Notify risk committee"],
      short_term: ["Assess third-party exposure"],
      long_term: ["Enhance segmentation controls"],
    },
    suggested_controls: ["Network segmentation", "EDR"],
    affected_controls: ["SIEM monitoring"],
    processing_status: "matched",
    published_at: new Date().toISOString(),
    created_at: new Date().toISOString(),
    risk_matches: [
      {
        id: randomUUID(),
        risk_code: "OR-001",
        risk_name: "Cybersecurity Breach / Ransomware",
        similarity_score: 0.91,
        confidence: 0.9,
        reasoning:
          "Semantic overlap between ransomware outage narrative and cyber risk register entry OR-001.",
        matched_concepts: ["ransomware", "payments", "operational resilience"],
        matched_controls: ["SIEM monitoring", "EDR"],
        affected_kris: ["Critical vulnerabilities open > 30 days"],
        contributing_sentences: [
          "ransomware attack targeted internal systems",
          "Card payments and mobile banking were intermittently unavailable",
        ],
        contributing_words: ["ransomware", "payments", "outage"],
        affected_departments: ["Cybersecurity", "Operational Risk"],
      },
    ],
    ai_analysis: {},
  },
  {
    id: "a1000000-0000-0000-0000-000000000002",
    title: "Pakistan Authorities Probe Trade-Based Money Laundering Network",
    title_en: "Pakistan Authorities Probe Trade-Based Money Laundering Network",
    url: "https://example.com/news/pk-aml-probe",
    source_type: "seed",
    source_name: "ARL Demo",
    language: "en",
    country: "Pakistan",
    region: "South Asia",
    summary_executive:
      "TBML investigation in Pakistan implicates trade firms and banking channels.",
    summary_detailed:
      "Investigators uncovered a trade-based money laundering scheme involving import-export companies and commercial banks.",
    content_en:
      "Investigators in Pakistan uncovered a trade-based money laundering scheme involving import-export companies and multiple commercial banks.",
    content_original:
      "Investigators in Pakistan uncovered a trade-based money laundering scheme involving import-export companies and multiple commercial banks.",
    severity: "high",
    severity_score: 84,
    urgency: "high",
    confidence: 0.88,
    is_relevant: true,
    is_emerging: true,
    requires_escalation: true,
    risk_category: "AML",
    banks: [],
    regulators: ["SBP", "FMU"],
    departments: ["AML", "Compliance"],
    tags: ["aml", "tbml", "pakistan"],
    people: [],
    organizations: [],
    products: ["Trade Finance"],
    recommended_actions: {
      immediate: ["Review trade finance alerts"],
      short_term: ["Enhance TBML typology rules"],
      long_term: ["Staff training on trade documentation"],
    },
    suggested_controls: ["Transaction monitoring"],
    affected_controls: ["Sanctions screening"],
    processing_status: "matched",
    published_at: new Date().toISOString(),
    created_at: new Date().toISOString(),
    risk_matches: [],
    ai_analysis: {},
  },
  {
    id: "a1000000-0000-0000-0000-000000000003",
    title: "UAE Central Bank Warns on Cloud Concentration Risk",
    title_en: "UAE Central Bank Warns on Cloud Concentration Risk",
    url: "https://example.com/news/uae-cloud-risk",
    source_type: "seed",
    source_name: "ARL Demo",
    language: "en",
    country: "United Arab Emirates",
    region: "Middle East",
    summary_executive:
      "UAE regulator highlights cloud concentration and third-party resilience risks.",
    summary_detailed:
      "Guidance highlighting operational risks from concentrating critical banking workloads with a small number of cloud hyperscalers.",
    content_en:
      "The UAE central bank issued guidance highlighting operational risks from concentrating critical banking workloads with a small number of cloud hyperscalers.",
    content_original:
      "The UAE central bank issued guidance highlighting operational risks from concentrating critical banking workloads with a small number of cloud hyperscalers.",
    severity: "medium",
    severity_score: 62,
    urgency: "medium",
    confidence: 0.86,
    is_relevant: true,
    is_emerging: true,
    requires_escalation: false,
    risk_category: "Cloud Risk",
    banks: [],
    regulators: ["CBUAE"],
    departments: ["IT", "Vendor Management", "Operational Risk"],
    tags: ["cloud", "third-party", "uae"],
    people: [],
    organizations: [],
    products: [],
    recommended_actions: {
      immediate: ["Map critical cloud workloads"],
      short_term: ["Update exit strategies"],
      long_term: ["Multi-cloud resilience tests"],
    },
    suggested_controls: ["Exit plans", "SLA monitoring"],
    affected_controls: ["Due diligence"],
    processing_status: "matched",
    published_at: new Date().toISOString(),
    created_at: new Date().toISOString(),
    risk_matches: [],
    ai_analysis: {},
  },
];

const risks = [
  {
    id: "r1000000-0000-0000-0000-000000000001",
    risk_id: "OR-001",
    name: "Cybersecurity Breach / Ransomware",
    description:
      "Loss of confidentiality, integrity or availability of systems due to cyber attack including ransomware.",
    category: "Cyber Risk",
    owner: "CISO",
    department: "Cybersecurity",
    controls: ["SIEM monitoring", "EDR", "Patch management"],
    kris: ["Critical vulns open >30d"],
    residual_risk: "Medium",
    inherent_risk: "High",
    status: "open",
    is_active: true,
  },
  {
    id: "r1000000-0000-0000-0000-000000000002",
    risk_id: "OR-002",
    name: "AML / Sanctions Screening Failure",
    description: "Failure to detect ML/TF or sanctioned parties.",
    category: "AML",
    owner: "MLRO",
    department: "AML",
    controls: ["Transaction monitoring", "Sanctions screening"],
    kris: ["Alert backlog age"],
    residual_risk: "Medium",
    inherent_risk: "High",
    status: "open",
    is_active: true,
  },
];

const feeds = [
  {
    id: "f1000000-0000-0000-0000-000000000001",
    name: "Federal Reserve Press",
    url: "https://www.federalreserve.gov/feeds/press_all.xml",
    category: "central_bank",
    country: "United States",
    language: "en",
    is_active: true,
    last_status: "seeded",
    success_count: 1,
    failure_count: 0,
  },
];

const emerging = [
  {
    id: "e1000000-0000-0000-0000-000000000001",
    title: "Trade-Based Money Laundering Typologies in South Asia",
    description:
      "Clustering of TBML investigations suggests elevated regional typology risk.",
    suggested_category: "AML",
    suggested_owner: "MLRO",
    suggested_controls: ["Enhanced trade invoice analytics"],
    confidence: 0.78,
    reasoning: "Repeated AML themes without exact risk register match density.",
    trend_analysis: { trajectory: "increasing", geography: ["Pakistan", "UAE"] },
    status: "recommended",
    article_count: 1,
  },
];

const notifications = [];
const alertSubs = [];

function json(statusCode, body) {
  return {
    statusCode,
    headers: {
      "Content-Type": "application/json",
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Headers": "Authorization, Content-Type, ngrok-skip-browser-warning",
      "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
    },
    body: JSON.stringify(body),
  };
}

function parseBody(event) {
  if (!event.body) return {};
  try {
    return JSON.parse(event.isBase64Encoded ? Buffer.from(event.body, "base64").toString() : event.body);
  } catch {
    return {};
  }
}

async function requireUser(event) {
  const auth = event.headers.authorization || event.headers.Authorization || "";
  const token = auth.startsWith("Bearer ") ? auth.slice(7) : null;
  if (!token) return null;
  try {
    const { payload } = await jwtVerify(token, JWT_SECRET);
    return users.find((u) => u.id === payload.sub) || null;
  } catch {
    return null;
  }
}

function stats() {
  const severity = {};
  const categories = {};
  const countries = {};
  const languages = {};
  const sources = {};
  for (const a of articles) {
    severity[a.severity] = (severity[a.severity] || 0) + 1;
    categories[a.risk_category] = (categories[a.risk_category] || 0) + 1;
    countries[a.country] = (countries[a.country] || 0) + 1;
    languages[a.language] = (languages[a.language] || 0) + 1;
    sources[a.source_name] = (sources[a.source_name] || 0) + 1;
  }
  const critical = articles.filter((a) => ["critical", "high"].includes(a.severity)).length;
  return {
    totals: {
      articles: articles.length,
      relevant: articles.length,
      critical_alerts: critical,
      emerging_risks: emerging.length,
    },
    countries: Object.entries(countries).map(([name, count]) => ({ name, count })),
    severity: Object.entries(severity).map(([name, count]) => ({ name, count })),
    categories: Object.entries(categories).map(([name, count]) => ({ name, count })),
    languages: Object.entries(languages).map(([name, count]) => ({ name, count })),
    sources: Object.entries(sources).map(([name, count]) => ({ name, count })),
    todays_news_count: articles.length,
  };
}

function pathOf(event) {
  const qs = event.queryStringParameters || {};
  if (qs.path) {
    let p = decodeURIComponent(qs.path);
    if (!p.startsWith("/")) p = "/" + p;
    return p.split("?")[0];
  }
  const raw = event.path || event.rawPath || "";
  let p = raw.replace(/^\/\.netlify\/functions\/arl\/?/, "/");
  if (p.includes("/api/v1")) p = p.slice(p.indexOf("/api/v1") + "/api/v1".length) || "/";
  if (!p.startsWith("/")) p = "/" + p;
  return p.split("?")[0] || "/";
}

export async function handler(event) {
  if (event.httpMethod === "OPTIONS") return json(204, {});

  const method = event.httpMethod;
  const path = pathOf(event);
  const qs = event.queryStringParameters || {};

  if (method === "GET" && (path === "/health" || path === "/" || path === "" || path.endsWith("/health"))) {
    return json(200, {
      status: "ok",
      service: "Adverse Risk Lookup",
      hosting: "netlify-functions-free",
      tagline: "Transforming Global Banking News into Actionable Risk Intelligence",
    });
  }

  if (method === "POST" && path === "/auth/login") {
    const body = parseBody(event);
    const user = users.find((u) => u.email === String(body.email || "").toLowerCase());
    const hash = createHash("sha256").update(String(body.password || "")).digest("hex");
    if (!user || hash !== user.password_hash) return json(401, { detail: "Invalid credentials" });
    const access_token = await new SignJWT({ role: user.role, email: user.email })
      .setProtectedHeader({ alg: "HS256" })
      .setSubject(user.id)
      .setExpirationTime("8h")
      .sign(JWT_SECRET);
    return json(200, { access_token, token_type: "bearer" });
  }

  if (method === "GET" && path === "/auth/me") {
    const user = await requireUser(event);
    if (!user) return json(401, { detail: "Not authenticated" });
    const { password_hash, ...safe } = user;
    return json(200, safe);
  }

  const user = await requireUser(event);
  if (!user && path !== "/health") {
    // Allow health only; everything else needs auth
    if (!(method === "GET" && path === "/health")) {
      return json(401, { detail: "Not authenticated" });
    }
  }

  if (method === "GET" && path === "/dashboard/stats") return json(200, stats());
  if (method === "GET" && path === "/dashboard/heatmap") {
    const cells = {};
    for (const a of articles) {
      cells[a.country] = cells[a.country] || {};
      cells[a.country][a.risk_category] = (cells[a.country][a.risk_category] || 0) + 1;
    }
    return json(200, { cells });
  }

  if (method === "GET" && path === "/articles") {
    let rows = [...articles];
    if (qs.severity) rows = rows.filter((a) => a.severity === qs.severity);
    if (qs.country) rows = rows.filter((a) => (a.country || "").toLowerCase().includes(qs.country.toLowerCase()));
    if (qs.q) {
      const q = qs.q.toLowerCase();
      rows = rows.filter(
        (a) =>
          (a.title_en || a.title).toLowerCase().includes(q) ||
          (a.summary_executive || "").toLowerCase().includes(q)
      );
    }
    return json(200, rows);
  }

  if (method === "GET" && path.startsWith("/articles/")) {
    const id = path.split("/")[2];
    const art = articles.find((a) => a.id === id);
    if (!art) return json(404, { detail: "Article not found" });
    return json(200, art);
  }

  if (method === "GET" && path === "/risks") return json(200, risks);
  if (method === "GET" && path === "/feeds") return json(200, feeds);
  if (method === "GET" && path === "/emerging-risks") return json(200, emerging);
  if (method === "GET" && path === "/notifications") return json(200, notifications);
  if (method === "GET" && path === "/alerts/subscriptions") return json(200, alertSubs);
  if (method === "POST" && path === "/alerts/subscriptions") {
    const body = parseBody(event);
    const sub = { id: randomUUID(), ...body, is_active: true };
    alertSubs.push(sub);
    return json(200, sub);
  }
  if (method === "GET" && path === "/admin/users") {
    return json(
      200,
      users.map(({ password_hash, ...u }) => u)
    );
  }
  if (method === "GET" && path === "/admin/jobs") return json(200, []);
  if (method === "GET" && path === "/admin/roles") {
    return json(200, { super_admin: ["*"], viewer: ["articles:read", "risks:read"] });
  }
  if (method === "POST" && path === "/assistant") {
    const body = parseBody(event);
    const q = String(body.question || "").toLowerCase();
    const s = stats();
    if (q.includes("cyber")) {
      const cyber = articles.filter((a) => (a.risk_category || "").toLowerCase().includes("cyber"));
      return json(200, {
        answer: cyber.map((a) => `• [${a.severity}] ${a.title_en}`).join("\n") || "No cyber items.",
        context_used: true,
      });
    }
    return json(200, {
      answer: `ARL free demo snapshot — Relevant: ${s.totals.relevant}, Critical/High: ${s.totals.critical_alerts}, Emerging: ${s.totals.emerging_risks}.`,
      context_used: true,
    });
  }

  if (method === "GET" && (path === "/reports/pdf" || path === "/reports/excel" || path === "/reports/word")) {
    return json(200, {
      detail: "Report downloads require the full Docker API. This free Netlify demo serves interactive dashboards only.",
    });
  }

  if (method === "POST" && path === "/feeds/collect-newsapi") {
    return json(200, { created: 0, detail: "News collection runs on the full API worker. Demo data is preloaded." });
  }

  return json(404, { detail: `Not found: ${method} ${path}` });
}
