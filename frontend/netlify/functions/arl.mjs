/**
 * Free serverless ARL API — Regulatory Obligations workflow demo.
 * Horizon scan → Applicability → Obligations register → Gap-analysis cases.
 * Also serves weekly scraped Trainings listings.
 */
import { SignJWT, jwtVerify } from "jose";
import { createHash, randomUUID } from "crypto";
import { readFileSync } from "fs";
import { dirname, join } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));

function loadTrainingsPayload() {
  try {
    const raw = readFileSync(join(__dirname, "trainings-data.json"), "utf8");
    return JSON.parse(raw);
  } catch {
    return { generated_at: null, countries: [], count: 0, trainings: [] };
  }
}

const JWT_SECRET = new TextEncoder().encode(
  process.env.JWT_SECRET || "arl-free-netlify-demo-secret-change-me"
);
const DEMO_PASSWORD = "ChangeMe123!";
const DEMO_PASS_HASH = createHash("sha256").update(DEMO_PASSWORD).digest("hex");
const now = () => new Date().toISOString();

const users = [
  {
    id: "11111111-1111-1111-1111-111111111111",
    email: "admin@arl.local",
    full_name: "ARL Administrator",
    role: "super_admin",
    department: "Compliance",
    is_active: true,
    preferences: {},
    password_hash: DEMO_PASS_HASH,
  },
];

const sources = [
  {
    id: "s1000000-0000-0000-0000-000000000001",
    name: "FCA Handbook / Publications",
    regulator: "FCA",
    jurisdiction: "UK",
    url: "https://www.fca.org.uk/news/rss.xml",
    category: "conduct",
    is_active: true,
    last_status: "seeded",
    success_count: 2,
    failure_count: 0,
  },
  {
    id: "s1000000-0000-0000-0000-000000000002",
    name: "FinCEN Guidance",
    regulator: "FinCEN",
    jurisdiction: "USA",
    url: "https://www.fincen.gov",
    category: "aml",
    is_active: true,
    last_status: "seeded",
    success_count: 1,
    failure_count: 0,
  },
  {
    id: "s1000000-0000-0000-0000-000000000003",
    name: "EU DORA / EBA Digests",
    regulator: "EBA",
    jurisdiction: "EU",
    url: "https://www.eba.europa.eu",
    category: "operational_resilience",
    is_active: true,
    last_status: "seeded",
    success_count: 1,
    failure_count: 0,
  },
  {
    id: "s1000000-0000-0000-0000-000000000004",
    name: "State Bank of Pakistan Circulars",
    regulator: "SBP",
    jurisdiction: "Pakistan",
    url: "https://www.sbp.org.pk",
    category: "aml_cft",
    is_active: true,
    last_status: "seeded",
    success_count: 1,
    failure_count: 0,
  },
  {
    id: "s1000000-0000-0000-0000-000000000005",
    name: "Federal Reserve Supervision",
    regulator: "Federal Reserve",
    jurisdiction: "USA",
    url: "https://www.federalreserve.gov/feeds/press_all.xml",
    category: "prudential",
    is_active: true,
    last_status: "seeded",
    success_count: 1,
    failure_count: 0,
  },
];

const policies = [
  {
    id: "p1000000-0000-0000-0000-000000000001",
    code: "POL-CD-01",
    title: "Consumer Duty Outcomes Framework",
    owner: "Conduct Risk",
    jurisdiction: "UK",
    status: "approved",
    summary: "Defines good customer outcomes, board reporting, and product governance.",
  },
  {
    id: "p1000000-0000-0000-0000-000000000002",
    code: "POL-OR-02",
    title: "Operational Resilience Policy",
    owner: "Operational Risk",
    jurisdiction: "UK",
    status: "approved",
    summary: "Important business services, impact tolerances, and scenario testing.",
  },
  {
    id: "p1000000-0000-0000-0000-000000000003",
    code: "POL-AML-01",
    title: "Group AML / CFT Policy",
    owner: "MLRO",
    jurisdiction: "Global",
    status: "approved",
    summary: "CDD, EDD, STR, and sanctions screening standards.",
  },
  {
    id: "p1000000-0000-0000-0000-000000000004",
    code: "POL-ICT-01",
    title: "ICT Risk & Third-Party Policy",
    owner: "CISO",
    jurisdiction: "EU",
    status: "approved",
    summary: "ICT risk management, incident classification, and critical ICT third parties.",
  },
  {
    id: "p1000000-0000-0000-0000-000000000005",
    code: "POL-TM-01",
    title: "Transaction Monitoring Standards",
    owner: "AML Operations",
    jurisdiction: "Pakistan",
    status: "approved",
    summary: "Alert handling SLAs, typology coverage, and quality assurance.",
  },
];

const controls = [
  {
    id: "c1000000-0000-0000-0000-000000000001",
    code: "CTL-CD-10",
    title: "Consumer outcomes MI pack",
    policy_id: "p1000000-0000-0000-0000-000000000001",
    owner: "Conduct Risk",
    type: "detective",
    status: "operating",
  },
  {
    id: "c1000000-0000-0000-0000-000000000002",
    code: "CTL-OR-20",
    title: "IBS impact tolerance testing",
    policy_id: "p1000000-0000-0000-0000-000000000002",
    owner: "Operational Risk",
    type: "detective",
    status: "operating",
  },
  {
    id: "c1000000-0000-0000-0000-000000000003",
    code: "CTL-AML-30",
    title: "Sanctions & PEP screening",
    policy_id: "p1000000-0000-0000-0000-000000000003",
    owner: "MLRO",
    type: "preventive",
    status: "operating",
  },
  {
    id: "c1000000-0000-0000-0000-000000000004",
    code: "CTL-AML-31",
    title: "Transaction monitoring ruleset",
    policy_id: "p1000000-0000-0000-0000-000000000003",
    owner: "AML Operations",
    type: "detective",
    status: "operating",
  },
  {
    id: "c1000000-0000-0000-0000-000000000005",
    code: "CTL-ICT-40",
    title: "ICT incident classification & escalation",
    policy_id: "p1000000-0000-0000-0000-000000000004",
    owner: "CISO",
    type: "detective",
    status: "partial",
  },
  {
    id: "c1000000-0000-0000-0000-000000000006",
    code: "CTL-TP-50",
    title: "Critical ICT third-party register",
    policy_id: "p1000000-0000-0000-0000-000000000004",
    owner: "Vendor Management",
    type: "preventive",
    status: "gap",
  },
  {
    id: "c1000000-0000-0000-0000-000000000007",
    code: "CTL-TM-60",
    title: "TBML typology scenarios",
    policy_id: "p1000000-0000-0000-0000-000000000005",
    owner: "AML Operations",
    type: "detective",
    status: "partial",
  },
  {
    id: "c1000000-0000-0000-0000-000000000008",
    code: "CTL-GOV-70",
    title: "Board regulatory horizon report",
    policy_id: null,
    owner: "Company Secretariat",
    type: "governance",
    status: "operating",
  },
];

/** Horizon scan items with embedded candidates */
let horizonItems = [
  {
    id: "h1000000-0000-0000-0000-000000000001",
    title: "FCA Dear CEO: Consumer Duty — Fair Value & Ongoing Outcomes Monitoring",
    jurisdiction: "UK",
    regulator: "FCA",
    instrument_type: "supervisory_communication",
    reference: "FCA-DC-2024-CD-01",
    published_at: "2024-11-12T00:00:00.000Z",
    summary:
      "Expects firms to evidence fair value assessments, board-level outcomes MI, and timely remediation of foreseeable harm.",
    body: "Firms must demonstrate that products deliver fair value, that Consumer Duty outcomes are monitored with board MI, and that foreseeable harm is remediated promptly.",
    source_id: "s1000000-0000-0000-0000-000000000001",
    source_name: "FCA Handbook / Publications",
    status: "assessed",
    priority: "high",
    tags: ["consumer_duty", "conduct", "fair_value"],
    candidates: [
      {
        id: "cand-uk-01",
        text: "Maintain documented fair value assessments for relevant products at least annually.",
        theme: "Fair value",
        applicability: "applicable",
        rationale:
          "UK retail bank with savings and cards — Consumer Duty fair value rules clearly apply.",
        suggested_owner: "Conduct Risk",
      },
      {
        id: "cand-uk-02",
        text: "Provide board-level Consumer Duty outcomes MI covering foreseeable harm and remediation status.",
        theme: "Governance MI",
        applicability: "applicable",
        rationale: "Board outcomes reporting is mandatory under Consumer Duty for retail banks.",
        suggested_owner: "Conduct Risk",
      },
      {
        id: "cand-uk-03",
        text: "Extend same MI framework to pure wholesale markets activity with no retail customers.",
        theme: "Scope carve-out",
        applicability: "not_applicable",
        rationale: "Demo institution has limited wholesale-only desk; carve-out documented.",
        suggested_owner: "Conduct Risk",
      },
    ],
    created_at: now(),
  },
  {
    id: "h1000000-0000-0000-0000-000000000002",
    title: "PRA Operational Resilience — Impact Tolerance Testing Reminder",
    jurisdiction: "UK",
    regulator: "PRA",
    instrument_type: "prudential_guidance",
    reference: "PRA-OR-2024-03",
    published_at: "2024-09-01T00:00:00.000Z",
    summary:
      "Firms must evidence severe-but-plausible scenario testing against impact tolerances for important business services.",
    body: "Update IBS maps, reconfirm impact tolerances, and evidence scenario testing including third-party dependencies.",
    source_id: "s1000000-0000-0000-0000-000000000001",
    source_name: "FCA Handbook / Publications",
    status: "pending_assessment",
    priority: "high",
    tags: ["operational_resilience", "ibs"],
    candidates: [
      {
        id: "cand-uk-04",
        text: "Complete severe-but-plausible scenario tests for each important business service within the annual cycle.",
        theme: "Scenario testing",
        applicability: "under_review",
        rationale: "Awaiting confirmation of current IBS inventory completeness.",
        suggested_owner: "Operational Risk",
      },
    ],
    created_at: now(),
  },
  {
    id: "h1000000-0000-0000-0000-000000000003",
    title: "FinCEN Advisory: Updated Red Flags for Trade-Based Money Laundering",
    jurisdiction: "USA",
    regulator: "FinCEN",
    instrument_type: "advisory",
    reference: "FINCEN-ADV-TBML-2024",
    published_at: "2024-10-05T00:00:00.000Z",
    summary:
      "Highlights TBML red flags for financial institutions with trade finance and correspondent activity.",
    body: "Institutions should refresh typologies, SAR narratives, and staff training for TBML indicators involving under/over-invoicing and unusual shipping routes.",
    source_id: "s1000000-0000-0000-0000-000000000002",
    source_name: "FinCEN Guidance",
    status: "assessed",
    priority: "medium",
    tags: ["aml", "tbml"],
    candidates: [
      {
        id: "cand-us-01",
        text: "Update transaction monitoring scenarios to cover FinCEN TBML red flags for trade finance.",
        theme: "Monitoring typologies",
        applicability: "applicable",
        rationale: "Group maintains USD correspondent and trade finance books exposing US-touched flows.",
        suggested_owner: "MLRO",
      },
      {
        id: "cand-us-02",
        text: "File structural changes under SEC reporting for TBML advisory alone.",
        theme: "Disclosure",
        applicability: "not_applicable",
        rationale: "Advisory does not create SEC disclosure obligations for this advisory alone.",
        suggested_owner: "Legal",
      },
    ],
    created_at: now(),
  },
  {
    id: "h1000000-0000-0000-0000-000000000004",
    title: "Federal Reserve SR Letter: Third-Party Risk Management Expectations",
    jurisdiction: "USA",
    regulator: "Federal Reserve",
    instrument_type: "sr_letter",
    reference: "SR-23-4-REF",
    published_at: "2024-06-18T00:00:00.000Z",
    summary: "Reinforces due diligence, ongoing monitoring, and contingency planning for critical third parties.",
    body: "Banks should inventory critical third parties, complete risk-tiered due diligence, and maintain exit plans.",
    source_id: "s1000000-0000-0000-0000-000000000005",
    source_name: "Federal Reserve Supervision",
    status: "pending_assessment",
    priority: "medium",
    tags: ["third_party", "vendor"],
    candidates: [
      {
        id: "cand-us-03",
        text: "Maintain a risk-tiered inventory of critical third parties with annual due diligence refresh.",
        theme: "Vendor inventory",
        applicability: "under_review",
        rationale: "US branch exposure requires mapping against SR expectations.",
        suggested_owner: "Vendor Management",
      },
    ],
    created_at: now(),
  },
  {
    id: "h1000000-0000-0000-0000-000000000005",
    title: "DORA — ICT Risk Management Framework Articulation (Articles 5–16)",
    jurisdiction: "EU",
    regulator: "EBA",
    instrument_type: "regulation",
    reference: "EU-DORA-ART5-16",
    published_at: "2024-01-17T00:00:00.000Z",
    summary:
      "Requires documented ICT risk management framework, incident classification, and oversight of critical ICT third-party providers.",
    body: "Financial entities must implement ICT risk strategies, detection/response capabilities, and contractual arrangements for critical ICT providers.",
    source_id: "s1000000-0000-0000-0000-000000000003",
    source_name: "EU DORA / EBA Digests",
    status: "assessed",
    priority: "critical",
    tags: ["dora", "ict", "resilience"],
    candidates: [
      {
        id: "cand-eu-01",
        text: "Maintain an ICT risk management framework covering identification, protection, detection, response and recovery.",
        theme: "ICT framework",
        applicability: "applicable",
        rationale: "EU-licensed entity in scope of DORA for ICT risk management.",
        suggested_owner: "CISO",
      },
      {
        id: "cand-eu-02",
        text: "Operate ICT-related incident classification, notification and reporting aligned to DORA timelines.",
        theme: "Incident reporting",
        applicability: "applicable",
        rationale: "Major ICT incidents must meet DORA classification and competent authority reporting.",
        suggested_owner: "CISO",
      },
      {
        id: "cand-eu-03",
        text: "Register and oversee critical ICT third-party providers with exit strategies.",
        theme: "Critical ICT TPP",
        applicability: "applicable",
        rationale: "Cloud concentration for core banking platforms creates critical ICT TPP exposure.",
        suggested_owner: "Vendor Management",
      },
    ],
    created_at: now(),
  },
  {
    id: "h1000000-0000-0000-0000-000000000006",
    title: "SBP Circular: Enhanced AML/CFT Controls for Trade-Based Transactions",
    jurisdiction: "Pakistan",
    regulator: "SBP",
    instrument_type: "circular",
    reference: "SBP-BPRD-AML-2024-XX",
    published_at: "2024-08-22T00:00:00.000Z",
    summary:
      "Requires reinforced CDD on trade counterparties, documentation authenticity checks, and TM coverage for TBML.",
    body: "Banks shall strengthen trade finance CDD, verify shipping/invoice consistency, and ensure monitoring scenarios address TBML patterns prevalent in the region.",
    source_id: "s1000000-0000-0000-0000-000000000004",
    source_name: "State Bank of Pakistan Circulars",
    status: "assessed",
    priority: "high",
    tags: ["aml", "tbml", "sbp"],
    candidates: [
      {
        id: "cand-pk-01",
        text: "Enhance CDD for trade finance customers including beneficial ownership and counterparty verification.",
        theme: "Trade CDD",
        applicability: "applicable",
        rationale: "Pakistan operations include active trade finance book subject to SBP circular.",
        suggested_owner: "MLRO",
      },
      {
        id: "cand-pk-02",
        text: "Implement and test TBML-focused transaction monitoring scenarios with QA sampling.",
        theme: "TM scenarios",
        applicability: "applicable",
        rationale: "Circular explicitly requires TBML monitoring coverage.",
        suggested_owner: "AML Operations",
      },
    ],
    created_at: now(),
  },
  {
    id: "h1000000-0000-0000-0000-000000000007",
    title: "ECB Guide on Cloud Outsourcing — Concentration Risk Addendum",
    jurisdiction: "EU",
    regulator: "ECB",
    instrument_type: "guide",
    reference: "ECB-CLOUD-ADD-2024",
    published_at: "2024-05-09T00:00:00.000Z",
    summary: "Emphasis on concentration risk, multi-vendor strategies, and board oversight of cloud exit plans.",
    body: "Significant institutions should quantify concentration to hyperscalers and demonstrate credible exit / substitution strategies.",
    source_id: "s1000000-0000-0000-0000-000000000003",
    source_name: "EU DORA / EBA Digests",
    status: "pending_assessment",
    priority: "medium",
    tags: ["cloud", "outsourcing"],
    candidates: [
      {
        id: "cand-eu-04",
        text: "Quantify cloud concentration and maintain tested exit strategies for material workloads.",
        theme: "Cloud concentration",
        applicability: "under_review",
        rationale: "May overlap with DORA critical ICT TPP work — assess duplication vs enhancement.",
        suggested_owner: "CISO",
      },
    ],
    created_at: now(),
  },
  {
    id: "h1000000-0000-0000-0000-000000000008",
    title: "OCC Bulletin: Model Risk Management Refresh for BSA/AML Models",
    jurisdiction: "USA",
    regulator: "OCC",
    instrument_type: "bulletin",
    reference: "OCC-2024-MRM-AML",
    published_at: "2024-07-30T00:00:00.000Z",
    summary: "Reminds banks of MRM expectations for BSA/AML models including ongoing monitoring and outcomes analysis.",
    body: "AML models require clear documentation, challenger processes where material, and periodic outcomes analysis.",
    source_id: "s1000000-0000-0000-0000-000000000002",
    source_name: "FinCEN Guidance",
    status: "pending_assessment",
    priority: "low",
    tags: ["model_risk", "aml"],
    candidates: [
      {
        id: "cand-us-04",
        text: "Document BSA/AML model inventory with MRM tiering and outcomes analysis cadence.",
        theme: "Model inventory",
        applicability: "under_review",
        rationale: "US AML models may fall under OCC MRM expectations depending on charter footprint.",
        suggested_owner: "Model Risk",
      },
    ],
    created_at: now(),
  },
];

let obligations = [
  {
    id: "o1000000-0000-0000-0000-000000000001",
    code: "OBL-UK-001",
    statement: "Maintain documented fair value assessments for relevant products at least annually.",
    jurisdiction: "UK",
    regulator: "FCA",
    theme: "Fair value",
    owner: "Conduct Risk",
    status: "open",
    source_horizon_id: "h1000000-0000-0000-0000-000000000001",
    source_candidate_id: "cand-uk-01",
    source_reference: "FCA-DC-2024-CD-01",
    due_date: "2025-06-30",
    created_at: now(),
  },
  {
    id: "o1000000-0000-0000-0000-000000000002",
    code: "OBL-UK-002",
    statement:
      "Provide board-level Consumer Duty outcomes MI covering foreseeable harm and remediation status.",
    jurisdiction: "UK",
    regulator: "FCA",
    theme: "Governance MI",
    owner: "Conduct Risk",
    status: "open",
    source_horizon_id: "h1000000-0000-0000-0000-000000000001",
    source_candidate_id: "cand-uk-02",
    source_reference: "FCA-DC-2024-CD-01",
    due_date: "2025-03-31",
    created_at: now(),
  },
  {
    id: "o1000000-0000-0000-0000-000000000003",
    code: "OBL-US-001",
    statement: "Update transaction monitoring scenarios to cover FinCEN TBML red flags for trade finance.",
    jurisdiction: "USA",
    regulator: "FinCEN",
    theme: "Monitoring typologies",
    owner: "MLRO",
    status: "open",
    source_horizon_id: "h1000000-0000-0000-0000-000000000003",
    source_candidate_id: "cand-us-01",
    source_reference: "FINCEN-ADV-TBML-2024",
    due_date: "2025-04-30",
    created_at: now(),
  },
  {
    id: "o1000000-0000-0000-0000-000000000004",
    code: "OBL-EU-001",
    statement:
      "Maintain an ICT risk management framework covering identification, protection, detection, response and recovery.",
    jurisdiction: "EU",
    regulator: "EBA",
    theme: "ICT framework",
    owner: "CISO",
    status: "open",
    source_horizon_id: "h1000000-0000-0000-0000-000000000005",
    source_candidate_id: "cand-eu-01",
    source_reference: "EU-DORA-ART5-16",
    due_date: "2025-01-17",
    created_at: now(),
  },
  {
    id: "o1000000-0000-0000-0000-000000000005",
    code: "OBL-EU-002",
    statement: "Operate ICT-related incident classification, notification and reporting aligned to DORA timelines.",
    jurisdiction: "EU",
    regulator: "EBA",
    theme: "Incident reporting",
    owner: "CISO",
    status: "open",
    source_horizon_id: "h1000000-0000-0000-0000-000000000005",
    source_candidate_id: "cand-eu-02",
    source_reference: "EU-DORA-ART5-16",
    due_date: "2025-01-17",
    created_at: now(),
  },
  {
    id: "o1000000-0000-0000-0000-000000000006",
    code: "OBL-EU-003",
    statement: "Register and oversee critical ICT third-party providers with exit strategies.",
    jurisdiction: "EU",
    regulator: "EBA",
    theme: "Critical ICT TPP",
    owner: "Vendor Management",
    status: "open",
    source_horizon_id: "h1000000-0000-0000-0000-000000000005",
    source_candidate_id: "cand-eu-03",
    source_reference: "EU-DORA-ART5-16",
    due_date: "2025-01-17",
    created_at: now(),
  },
  {
    id: "o1000000-0000-0000-0000-000000000007",
    code: "OBL-PK-001",
    statement:
      "Enhance CDD for trade finance customers including beneficial ownership and counterparty verification.",
    jurisdiction: "Pakistan",
    regulator: "SBP",
    theme: "Trade CDD",
    owner: "MLRO",
    status: "open",
    source_horizon_id: "h1000000-0000-0000-0000-000000000006",
    source_candidate_id: "cand-pk-01",
    source_reference: "SBP-BPRD-AML-2024-XX",
    due_date: "2025-02-28",
    created_at: now(),
  },
  {
    id: "o1000000-0000-0000-0000-000000000008",
    code: "OBL-PK-002",
    statement: "Implement and test TBML-focused transaction monitoring scenarios with QA sampling.",
    jurisdiction: "Pakistan",
    regulator: "SBP",
    theme: "TM scenarios",
    owner: "AML Operations",
    status: "open",
    source_horizon_id: "h1000000-0000-0000-0000-000000000006",
    source_candidate_id: "cand-pk-02",
    source_reference: "SBP-BPRD-AML-2024-XX",
    due_date: "2025-02-28",
    created_at: now(),
  },
];

let gapCases = [
  {
    id: "g1000000-0000-0000-0000-000000000001",
    case_number: "GAP-2024-0001",
    obligation_id: "o1000000-0000-0000-0000-000000000001",
    title: "Gap analysis — Fair value assessments (Consumer Duty)",
    status: "in_progress",
    gap_status: "partial",
    owner: "Conduct Risk",
    jurisdiction: "UK",
    remediation_notes: "Product packs exist for savings; cards fair-value pack overdue.",
    mappings: [
      {
        id: "m1",
        kind: "policy",
        ref_id: "p1000000-0000-0000-0000-000000000001",
        ref_code: "POL-CD-01",
        ref_title: "Consumer Duty Outcomes Framework",
        coverage: "partial",
        notes: "Policy covers outcomes; fair-value assessment schedule needs explicit annex.",
      },
      {
        id: "m2",
        kind: "control",
        ref_id: "c1000000-0000-0000-0000-000000000001",
        ref_code: "CTL-CD-10",
        ref_title: "Consumer outcomes MI pack",
        coverage: "mapped",
        notes: "MI includes fair-value exceptions for savings book.",
      },
    ],
    created_at: now(),
  },
  {
    id: "g1000000-0000-0000-0000-000000000002",
    case_number: "GAP-2024-0002",
    obligation_id: "o1000000-0000-0000-0000-000000000002",
    title: "Gap analysis — Board Consumer Duty outcomes MI",
    status: "open",
    gap_status: "mapped",
    owner: "Conduct Risk",
    jurisdiction: "UK",
    remediation_notes: "",
    mappings: [
      {
        id: "m3",
        kind: "control",
        ref_id: "c1000000-0000-0000-0000-000000000001",
        ref_code: "CTL-CD-10",
        ref_title: "Consumer outcomes MI pack",
        coverage: "mapped",
        notes: "Quarterly board pack in place.",
      },
      {
        id: "m4",
        kind: "control",
        ref_id: "c1000000-0000-0000-0000-000000000008",
        ref_code: "CTL-GOV-70",
        ref_title: "Board regulatory horizon report",
        coverage: "mapped",
        notes: "Horizon report includes Consumer Duty section.",
      },
    ],
    created_at: now(),
  },
  {
    id: "g1000000-0000-0000-0000-000000000003",
    case_number: "GAP-2024-0003",
    obligation_id: "o1000000-0000-0000-0000-000000000003",
    title: "Gap analysis — FinCEN TBML monitoring scenarios",
    status: "in_progress",
    gap_status: "partial",
    owner: "MLRO",
    jurisdiction: "USA",
    remediation_notes: "Add shipping-route anomaly scenarios.",
    mappings: [
      {
        id: "m5",
        kind: "policy",
        ref_id: "p1000000-0000-0000-0000-000000000003",
        ref_code: "POL-AML-01",
        ref_title: "Group AML / CFT Policy",
        coverage: "mapped",
        notes: "Policy mandates typology refresh.",
      },
      {
        id: "m6",
        kind: "control",
        ref_id: "c1000000-0000-0000-0000-000000000004",
        ref_code: "CTL-AML-31",
        ref_title: "Transaction monitoring ruleset",
        coverage: "partial",
        notes: "Invoice mismatch covered; routing anomalies incomplete.",
      },
    ],
    created_at: now(),
  },
  {
    id: "g1000000-0000-0000-0000-000000000004",
    case_number: "GAP-2024-0004",
    obligation_id: "o1000000-0000-0000-0000-000000000004",
    title: "Gap analysis — DORA ICT risk framework",
    status: "in_progress",
    gap_status: "partial",
    owner: "CISO",
    jurisdiction: "EU",
    remediation_notes: "Align ICT policy annex wording to DORA Articles 5–16.",
    mappings: [
      {
        id: "m7",
        kind: "policy",
        ref_id: "p1000000-0000-0000-0000-000000000004",
        ref_code: "POL-ICT-01",
        ref_title: "ICT Risk & Third-Party Policy",
        coverage: "partial",
        notes: "Policy exists; DORA crosswalk incomplete.",
      },
    ],
    created_at: now(),
  },
  {
    id: "g1000000-0000-0000-0000-000000000005",
    case_number: "GAP-2024-0005",
    obligation_id: "o1000000-0000-0000-0000-000000000005",
    title: "Gap analysis — DORA ICT incident reporting",
    status: "open",
    gap_status: "partial",
    owner: "CISO",
    jurisdiction: "EU",
    remediation_notes: "Classification matrix needs DORA severity classes.",
    mappings: [
      {
        id: "m8",
        kind: "control",
        ref_id: "c1000000-0000-0000-0000-000000000005",
        ref_code: "CTL-ICT-40",
        ref_title: "ICT incident classification & escalation",
        coverage: "partial",
        notes: "Escalation paths exist; DORA clocks not wired.",
      },
    ],
    created_at: now(),
  },
  {
    id: "g1000000-0000-0000-0000-000000000006",
    case_number: "GAP-2024-0006",
    obligation_id: "o1000000-0000-0000-0000-000000000006",
    title: "Gap analysis — Critical ICT third parties",
    status: "open",
    gap_status: "gap",
    owner: "Vendor Management",
    jurisdiction: "EU",
    remediation_notes: "Critical ICT TPP register not yet established.",
    mappings: [
      {
        id: "m9",
        kind: "control",
        ref_id: "c1000000-0000-0000-0000-000000000006",
        ref_code: "CTL-TP-50",
        ref_title: "Critical ICT third-party register",
        coverage: "gap",
        notes: "Control marked gap — register empty.",
      },
    ],
    created_at: now(),
  },
  {
    id: "g1000000-0000-0000-0000-000000000007",
    case_number: "GAP-2024-0007",
    obligation_id: "o1000000-0000-0000-0000-000000000007",
    title: "Gap analysis — SBP trade finance CDD",
    status: "in_progress",
    gap_status: "partial",
    owner: "MLRO",
    jurisdiction: "Pakistan",
    remediation_notes: "Refresh trade counterparty checklist.",
    mappings: [
      {
        id: "m10",
        kind: "policy",
        ref_id: "p1000000-0000-0000-0000-000000000003",
        ref_code: "POL-AML-01",
        ref_title: "Group AML / CFT Policy",
        coverage: "mapped",
        notes: "Group policy includes trade CDD chapter.",
      },
    ],
    created_at: now(),
  },
  {
    id: "g1000000-0000-0000-0000-000000000008",
    case_number: "GAP-2024-0008",
    obligation_id: "o1000000-0000-0000-0000-000000000008",
    title: "Gap analysis — SBP TBML TM scenarios",
    status: "open",
    gap_status: "partial",
    owner: "AML Operations",
    jurisdiction: "Pakistan",
    remediation_notes: "Localise FinCEN red flags to SBP circular examples.",
    mappings: [
      {
        id: "m11",
        kind: "control",
        ref_id: "c1000000-0000-0000-0000-000000000007",
        ref_code: "CTL-TM-60",
        ref_title: "TBML typology scenarios",
        coverage: "partial",
        notes: "Scenarios drafted; QA sampling not live.",
      },
      {
        id: "m12",
        kind: "policy",
        ref_id: "p1000000-0000-0000-0000-000000000005",
        ref_code: "POL-TM-01",
        ref_title: "Transaction Monitoring Standards",
        coverage: "mapped",
        notes: "Standards require annual typology review.",
      },
    ],
    created_at: now(),
  },
];

let oblSeq = 9;
let gapSeq = 9;

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

function dashboardStats() {
  const byJ = {};
  for (const h of horizonItems) {
    byJ[h.jurisdiction] = (byJ[h.jurisdiction] || 0) + 1;
  }
  const pending = horizonItems.filter((h) => h.status === "pending_assessment").length;
  const underReview = horizonItems.reduce(
    (n, h) => n + h.candidates.filter((c) => c.applicability === "under_review").length,
    0
  );
  const gaps = gapCases.filter((c) => c.gap_status === "gap" || c.gap_status === "partial").length;
  return {
    totals: {
      horizon_items: horizonItems.length,
      pending_assessment: pending,
      obligations: obligations.length,
      open_cases: gapCases.filter((c) => c.status !== "closed").length,
      gap_or_partial: gaps,
      under_review_candidates: underReview,
    },
    jurisdictions: Object.entries(byJ).map(([name, count]) => ({ name, count })),
    gap_status: ["mapped", "partial", "gap"].map((name) => ({
      name,
      count: gapCases.filter((c) => c.gap_status === name).length,
    })),
    case_status: ["open", "in_progress", "closed"].map((name) => ({
      name,
      count: gapCases.filter((c) => c.status === name).length,
    })),
  };
}

function nextObligationCode(jurisdiction) {
  const prefix = { UK: "UK", USA: "US", EU: "EU", Pakistan: "PK" }[jurisdiction] || "XX";
  const code = `OBL-${prefix}-${String(oblSeq).padStart(3, "0")}`;
  oblSeq += 1;
  return code;
}

function applyApplicability(horizonId, candidateId, decision, rationale, assessor) {
  const item = horizonItems.find((h) => h.id === horizonId);
  if (!item) return { error: "Horizon item not found", status: 404 };
  const cand = item.candidates.find((c) => c.id === candidateId);
  if (!cand) return { error: "Candidate not found", status: 404 };

  cand.applicability = decision;
  if (rationale) cand.rationale = rationale;
  cand.assessed_by = assessor;
  cand.assessed_at = now();

  const allDecided = item.candidates.every((c) => c.applicability !== "under_review");
  if (allDecided) item.status = "assessed";
  else if (item.status === "pending_assessment") item.status = "in_assessment";

  let obligation = null;
  let gapCase = null;

  if (decision === "applicable") {
    const existing = obligations.find(
      (o) => o.source_horizon_id === horizonId && o.source_candidate_id === candidateId
    );
    if (existing) {
      obligation = existing;
      gapCase = gapCases.find((g) => g.obligation_id === existing.id) || null;
    } else {
      obligation = {
        id: randomUUID(),
        code: nextObligationCode(item.jurisdiction),
        statement: cand.text,
        jurisdiction: item.jurisdiction,
        regulator: item.regulator,
        theme: cand.theme,
        owner: cand.suggested_owner || "Compliance",
        status: "open",
        source_horizon_id: item.id,
        source_candidate_id: cand.id,
        source_reference: item.reference,
        due_date: new Date(Date.now() + 90 * 86400000).toISOString().slice(0, 10),
        created_at: now(),
      };
      obligations.push(obligation);

      gapCase = {
        id: randomUUID(),
        case_number: `GAP-2024-${String(gapSeq).padStart(4, "0")}`,
        obligation_id: obligation.id,
        title: `Gap analysis — ${cand.theme || obligation.code}`,
        status: "open",
        gap_status: "gap",
        owner: obligation.owner,
        jurisdiction: obligation.jurisdiction,
        remediation_notes: "",
        mappings: [],
        created_at: now(),
      };
      gapSeq += 1;
      gapCases.push(gapCase);
    }
  }

  return { item, candidate: cand, obligation, gap_case: gapCase };
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
      tagline: "Horizon scanning to obligations and gap analysis",
      mode: "regulatory_obligations",
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
  if (!user) return json(401, { detail: "Not authenticated" });

  if (method === "GET" && path === "/dashboard/stats") return json(200, dashboardStats());

  if (method === "GET" && path === "/sources") return json(200, sources);
  if (method === "POST" && path === "/sources") {
    const body = parseBody(event);
    const row = {
      id: randomUUID(),
      name: body.name || "New source",
      regulator: body.regulator || "",
      jurisdiction: body.jurisdiction || "",
      url: body.url || "",
      category: body.category || "general",
      is_active: true,
      last_status: "created",
      success_count: 0,
      failure_count: 0,
    };
    sources.push(row);
    return json(200, row);
  }

  if (method === "GET" && path === "/horizon") {
    let rows = [...horizonItems];
    if (qs.jurisdiction) rows = rows.filter((h) => h.jurisdiction === qs.jurisdiction);
    if (qs.status) rows = rows.filter((h) => h.status === qs.status);
    if (qs.q) {
      const q = qs.q.toLowerCase();
      rows = rows.filter(
        (h) =>
          h.title.toLowerCase().includes(q) ||
          (h.summary || "").toLowerCase().includes(q) ||
          (h.reference || "").toLowerCase().includes(q)
      );
    }
    return json(200, rows);
  }

  if (method === "GET" && path.startsWith("/horizon/")) {
    const id = path.split("/")[2];
    const item = horizonItems.find((h) => h.id === id);
    if (!item) return json(404, { detail: "Not found" });
    return json(200, item);
  }

  if (method === "GET" && path === "/applicability") {
    const inbox = [];
    for (const h of horizonItems) {
      for (const c of h.candidates) {
        if (!qs.status || c.applicability === qs.status) {
          inbox.push({
            horizon_id: h.id,
            horizon_title: h.title,
            jurisdiction: h.jurisdiction,
            regulator: h.regulator,
            reference: h.reference,
            priority: h.priority,
            candidate: c,
          });
        }
      }
    }
    return json(200, inbox);
  }

  if (method === "POST" && path === "/applicability") {
    const body = parseBody(event);
    const decision = String(body.decision || "").toLowerCase();
    if (!["applicable", "not_applicable", "under_review"].includes(decision)) {
      return json(400, { detail: "decision must be applicable | not_applicable | under_review" });
    }
    const result = applyApplicability(
      body.horizon_id,
      body.candidate_id,
      decision,
      body.rationale,
      user.full_name
    );
    if (result.error) return json(result.status, { detail: result.error });
    return json(200, result);
  }

  if (method === "GET" && path === "/obligations") {
    let rows = [...obligations];
    if (qs.jurisdiction) rows = rows.filter((o) => o.jurisdiction === qs.jurisdiction);
    if (qs.status) rows = rows.filter((o) => o.status === qs.status);
    return json(200, rows);
  }

  if (method === "GET" && path.startsWith("/obligations/")) {
    const id = path.split("/")[2];
    const row = obligations.find((o) => o.id === id);
    if (!row) return json(404, { detail: "Not found" });
    return json(200, row);
  }

  if (method === "GET" && path === "/policies") return json(200, policies);
  if (method === "GET" && path === "/controls") return json(200, controls);

  if (method === "GET" && path === "/library") {
    return json(200, { policies, controls });
  }

  if (method === "GET" && path === "/cases") {
    let rows = [...gapCases];
    if (qs.jurisdiction) rows = rows.filter((c) => c.jurisdiction === qs.jurisdiction);
    if (qs.gap_status) rows = rows.filter((c) => c.gap_status === qs.gap_status);
    if (qs.status) rows = rows.filter((c) => c.status === qs.status);
    return json(
      200,
      rows.map((c) => ({
        ...c,
        obligation: obligations.find((o) => o.id === c.obligation_id) || null,
      }))
    );
  }

  if (method === "GET" && path.startsWith("/cases/") && !path.endsWith("/mappings")) {
    const id = path.split("/")[2];
    const row = gapCases.find((c) => c.id === id);
    if (!row) return json(404, { detail: "Not found" });
    return json(200, {
      ...row,
      obligation: obligations.find((o) => o.id === row.obligation_id) || null,
    });
  }

  if (method === "POST" && /^\/cases\/[^/]+\/mappings$/.test(path)) {
    const id = path.split("/")[2];
    const row = gapCases.find((c) => c.id === id);
    if (!row) return json(404, { detail: "Not found" });
    const body = parseBody(event);
    const kind = body.kind === "control" ? "control" : "policy";
    const ref =
      kind === "policy"
        ? policies.find((p) => p.id === body.ref_id)
        : controls.find((c) => c.id === body.ref_id);
    if (!ref) return json(400, { detail: "ref_id not found in library" });
    const mapping = {
      id: randomUUID(),
      kind,
      ref_id: ref.id,
      ref_code: ref.code,
      ref_title: ref.title,
      coverage: body.coverage || "partial",
      notes: body.notes || "",
    };
    row.mappings.push(mapping);
    if (body.gap_status) row.gap_status = body.gap_status;
    else {
      const coverages = row.mappings.map((m) => m.coverage);
      if (coverages.every((c) => c === "mapped")) row.gap_status = "mapped";
      else if (coverages.some((c) => c === "gap")) row.gap_status = "gap";
      else row.gap_status = "partial";
    }
    if (body.remediation_notes != null) row.remediation_notes = body.remediation_notes;
    if (row.status === "open") row.status = "in_progress";
    return json(200, {
      ...row,
      obligation: obligations.find((o) => o.id === row.obligation_id) || null,
    });
  }

  if (method === "PATCH" && path.startsWith("/cases/")) {
    const id = path.split("/")[2];
    const row = gapCases.find((c) => c.id === id);
    if (!row) return json(404, { detail: "Not found" });
    const body = parseBody(event);
    if (body.status) row.status = body.status;
    if (body.gap_status) row.gap_status = body.gap_status;
    if (body.remediation_notes != null) row.remediation_notes = body.remediation_notes;
    return json(200, row);
  }

  if (method === "GET" && path === "/trainings") {
    const payload = loadTrainingsPayload();
    let rows = [...(payload.trainings || [])];
    if (qs.country) rows = rows.filter((t) => t.country === qs.country);
    if (qs.q) {
      const q = String(qs.q).toLowerCase();
      rows = rows.filter(
        (t) =>
          (t.title || "").toLowerCase().includes(q) ||
          (t.description || "").toLowerCase().includes(q) ||
          (t.organizer || "").toLowerCase().includes(q) ||
          (t.city || "").toLowerCase().includes(q)
      );
    }
    return json(200, {
      generated_at: payload.generated_at || null,
      countries: payload.countries || [],
      count: rows.length,
      trainings: rows,
    });
  }

  if (method === "GET" && path === "/admin/users") {
    return json(
      200,
      users.map(({ password_hash, ...u }) => u)
    );
  }
  if (method === "GET" && path === "/admin/jobs") return json(200, []);
  if (method === "GET" && path === "/admin/roles") {
    return json(200, {
      super_admin: ["*"],
      compliance_officer: ["horizon:read", "applicability:write", "obligations:read", "cases:write"],
      viewer: ["horizon:read", "obligations:read", "cases:read"],
    });
  }

  return json(404, { detail: `Not found: ${method} ${path}` });
}
