"""Database seed: admin user, sample risks, RSS feeds, demo articles."""

from __future__ import annotations

from datetime import datetime, timezone

from app.core.database import Base, SessionLocal, engine, init_vector_extension
from app.core.security import hash_password
from app.models import (
    AlertSubscription,
    Article,
    EmergingRisk,
    Organization,
    PromptTemplate,
    Risk,
    RSSFeed,
    User,
)
from app.prompts import load_prompt
from app.services.embedding_service import get_embeddings


DEFAULT_FEEDS = [
    {
        "name": "Federal Reserve Press",
        "url": "https://www.federalreserve.gov/feeds/press_all.xml",
        "category": "central_bank",
        "country": "United States",
        "language": "en",
    },
    {
        "name": "SEC News Digests",
        "url": "https://www.sec.gov/news/pressreleases.rss",
        "category": "regulator",
        "country": "United States",
        "language": "en",
    },
    {
        "name": "BIS Speeches",
        "url": "https://www.bis.org/doclist/cbspeeches.rss",
        "category": "regulator",
        "country": "International",
        "language": "en",
    },
    {
        "name": "CISA Alerts",
        "url": "https://www.cisa.gov/cybersecurity-advisories/all.xml",
        "category": "cyber",
        "country": "United States",
        "language": "en",
    },
    {
        "name": "ECB Press",
        "url": "https://www.ecb.europa.eu/rss/press.html",
        "category": "central_bank",
        "country": "European Union",
        "language": "en",
    },
]

SAMPLE_RISKS = [
    {
        "risk_id": "OR-001",
        "name": "Cybersecurity Breach / Ransomware",
        "description": "Loss of confidentiality, integrity or availability of systems due to cyber attack including ransomware affecting core banking or payment systems.",
        "category": "Cyber Risk",
        "owner": "CISO",
        "department": "Cybersecurity",
        "controls": ["SIEM monitoring", "EDR", "Patch management", "Network segmentation"],
        "kris": ["Critical vulnerabilities open > 30 days", "Phishing click rate"],
        "inherent_risk": "High",
        "residual_risk": "Medium",
        "status": "open",
    },
    {
        "risk_id": "OR-002",
        "name": "AML / Sanctions Screening Failure",
        "description": "Failure to detect money laundering, terrorist financing, or sanctioned parties in customer onboarding or transaction monitoring.",
        "category": "AML",
        "owner": "MLRO",
        "department": "AML",
        "controls": ["Transaction monitoring", "Sanctions screening", "CDD/EDD"],
        "kris": ["Alert backlog age", "False positive rate"],
        "inherent_risk": "High",
        "residual_risk": "Medium",
        "status": "open",
    },
    {
        "risk_id": "OR-003",
        "name": "Payment System Outage",
        "description": "Disruption to payment rails, cards, RTP, or correspondent banking causing customer harm and regulatory scrutiny.",
        "category": "Operational Resilience",
        "owner": "Head of Payments",
        "department": "Digital Banking",
        "controls": ["Redundancy", "Failover tests", "Incident response"],
        "kris": ["Payment success rate", "MTTR"],
        "inherent_risk": "High",
        "residual_risk": "Medium",
        "status": "open",
    },
    {
        "risk_id": "OR-004",
        "name": "Third-Party / Cloud Provider Failure",
        "description": "Concentration or operational failure of critical cloud or fintech vendors impacting bank services.",
        "category": "Third Party Risk",
        "owner": "Vendor Risk Manager",
        "department": "Vendor Management",
        "controls": ["Due diligence", "Exit plans", "SLA monitoring"],
        "kris": ["Critical vendors without BCP test"],
        "inherent_risk": "High",
        "residual_risk": "Medium",
        "status": "open",
    },
    {
        "risk_id": "OR-005",
        "name": "Internal / External Fraud",
        "description": "Fraudulent transactions, account takeover, social engineering, or insider fraud causing financial loss.",
        "category": "Fraud Risk",
        "owner": "Head of Fraud",
        "department": "Fraud",
        "controls": ["Fraud rules engine", "MFA", "Transaction limits"],
        "kris": ["Fraud loss rate", "ATO incidents"],
        "inherent_risk": "High",
        "residual_risk": "Medium",
        "status": "open",
    },
    {
        "risk_id": "OR-006",
        "name": "Regulatory Compliance Breach",
        "description": "Failure to meet local or international banking regulations leading to fines, remediation, or license risk.",
        "category": "Compliance Risk",
        "owner": "Chief Compliance Officer",
        "department": "Compliance",
        "controls": ["Regulatory change management", "Policy attestations"],
        "kris": ["Open regulatory findings"],
        "inherent_risk": "High",
        "residual_risk": "Medium",
        "status": "open",
    },
]

DEMO_ARTICLES = [
    {
        "title": "Major European Bank Hit by Ransomware Disruptions",
        "title_en": "Major European Bank Hit by Ransomware Disruptions",
        "url": "https://example.com/news/eu-bank-ransomware",
        "content_en": "A large European banking group reported service outages after a ransomware attack targeted internal systems. Card payments and mobile banking were intermittently unavailable. Regulators were notified under operational resilience rules.",
        "summary_executive": "EU bank suffered ransomware impacting payments and digital channels; regulators notified.",
        "country": "Germany",
        "region": "Europe",
        "language": "en",
        "severity": "critical",
        "severity_score": 92,
        "risk_category": "Cyber Risk",
        "banks": ["Example EU Bank"],
        "regulators": ["BaFin", "ECB"],
        "departments": ["Cybersecurity", "Operational Risk", "Digital Banking"],
        "tags": ["ransomware", "cyber", "payments"],
        "is_relevant": True,
        "is_emerging": False,
        "requires_escalation": True,
        "confidence": 0.91,
        "processing_status": "matched",
        "recommended_actions": {
            "immediate": ["Activate cyber IR plan", "Notify risk committee"],
            "short_term": ["Assess third-party exposure"],
            "long_term": ["Enhance segmentation controls"],
        },
    },
    {
        "title": "Pakistan Authorities Probe Trade-Based Money Laundering Network",
        "title_en": "Pakistan Authorities Probe Trade-Based Money Laundering Network",
        "url": "https://example.com/news/pk-aml-probe",
        "content_en": "Investigators in Pakistan uncovered a trade-based money laundering scheme involving import-export companies and multiple commercial banks. Suspicious trade invoices allegedly masked illicit fund flows.",
        "summary_executive": "TBML investigation in Pakistan implicates trade firms and banking channels.",
        "country": "Pakistan",
        "region": "South Asia",
        "language": "en",
        "severity": "high",
        "severity_score": 84,
        "risk_category": "AML",
        "banks": [],
        "regulators": ["SBP", "FMU"],
        "departments": ["AML", "Compliance"],
        "tags": ["aml", "tblm", "pakistan"],
        "is_relevant": True,
        "is_emerging": True,
        "requires_escalation": True,
        "confidence": 0.88,
        "processing_status": "matched",
        "recommended_actions": {
            "immediate": ["Review trade finance alerts"],
            "short_term": ["Enhance TBML typology rules"],
            "long_term": ["Staff training on trade documentation"],
        },
    },
    {
        "title": "UAE Central Bank Warns on Cloud Concentration Risk",
        "title_en": "UAE Central Bank Warns on Cloud Concentration Risk",
        "url": "https://example.com/news/uae-cloud-risk",
        "content_en": "The UAE central bank issued guidance highlighting operational risks from concentrating critical banking workloads with a small number of cloud hyperscalers.",
        "summary_executive": "UAE regulator highlights cloud concentration and third-party resilience risks.",
        "country": "United Arab Emirates",
        "region": "Middle East",
        "language": "en",
        "severity": "medium",
        "severity_score": 62,
        "risk_category": "Cloud Risk",
        "banks": [],
        "regulators": ["CBUAE"],
        "departments": ["IT", "Vendor Management", "Operational Risk"],
        "tags": ["cloud", "third-party", "uae"],
        "is_relevant": True,
        "is_emerging": True,
        "requires_escalation": False,
        "confidence": 0.86,
        "processing_status": "matched",
        "recommended_actions": {
            "immediate": ["Map critical cloud workloads"],
            "short_term": ["Update exit strategies"],
            "long_term": ["Multi-cloud resilience tests"],
        },
    },
]


def seed() -> None:
    with engine.begin() as conn:
        init_vector_extension(conn)
        Base.metadata.create_all(bind=conn)

    db = SessionLocal()
    try:
        org = db.query(Organization).filter(Organization.name == "Demo Financial Group").first()
        if not org:
            org = Organization(
                name="Demo Financial Group",
                org_type="bank",
                country="Pakistan",
                settings={"theme": "enterprise"},
            )
            db.add(org)
            db.flush()

        admin = db.query(User).filter(User.email == "admin@arl.local").first()
        if not admin:
            admin = User(
                organization_id=org.id,
                email="admin@arl.local",
                full_name="ARL Administrator",
                hashed_password=hash_password("ChangeMe123!"),
                role="super_admin",
                department="Operational Risk",
            )
            db.add(admin)
            db.flush()

        if not db.query(User).filter(User.email == "risk@arl.local").first():
            db.add(
                User(
                    organization_id=org.id,
                    email="risk@arl.local",
                    full_name="Risk Manager",
                    hashed_password=hash_password("ChangeMe123!"),
                    role="risk_manager",
                    department="Operational Risk",
                )
            )

        emb = get_embeddings()
        for item in SAMPLE_RISKS:
            if db.query(Risk).filter(Risk.risk_id == item["risk_id"]).first():
                continue
            text = f"{item['name']}. {item['description']}. {item['category']}"
            db.add(
                Risk(
                    organization_id=org.id,
                    embedding=emb.embed(text),
                    **item,
                )
            )

        for feed in DEFAULT_FEEDS:
            if db.query(RSSFeed).filter(RSSFeed.url == feed["url"]).first():
                continue
            db.add(RSSFeed(**feed))

        for art in DEMO_ARTICLES:
            if db.query(Article).filter(Article.url == art["url"]).first():
                continue
            text = f"{art['title_en']}. {art['content_en']}"
            import hashlib

            article = Article(
                source_type="seed",
                source_name="ARL Demo",
                url_hash=hashlib.sha256(art["url"].encode()).hexdigest(),
                content_original=art["content_en"],
                published_at=datetime.now(timezone.utc),
                embedding=emb.embed(text),
                **{k: v for k, v in art.items()},
            )
            db.add(article)

        for key in ["analyze_article", "translate", "explain_match", "emerging_risk", "assistant"]:
            if db.query(PromptTemplate).filter(PromptTemplate.key == key).first():
                continue
            db.add(
                PromptTemplate(
                    key=key,
                    name=key.replace("_", " ").title(),
                    content=load_prompt(key),
                    description=f"System prompt: {key}",
                )
            )

        if admin and not db.query(AlertSubscription).filter(AlertSubscription.user_id == admin.id).first():
            db.add(
                AlertSubscription(
                    user_id=admin.id,
                    name="Critical Cyber & AML",
                    conditions={"severity_min": "high"},
                    channels=["dashboard", "email"],
                )
            )

        if not db.query(EmergingRisk).first():
            db.add(
                EmergingRisk(
                    title="Trade-Based Money Laundering Typologies in South Asia",
                    description="Clustering of TBML investigations suggests elevated regional typology risk.",
                    suggested_category="AML",
                    suggested_owner="MLRO",
                    suggested_controls=["Enhanced trade invoice analytics", "Dual control on LC discrepancies"],
                    confidence=0.78,
                    reasoning="Repeated AML themes without exact risk register match density.",
                    trend_analysis={"trajectory": "increasing", "geography": ["Pakistan", "UAE"]},
                    theme_key="aml_tbml_south_asia",
                    article_ids=[],
                )
            )

        db.commit()
        print("Seed complete. Login: admin@arl.local / ChangeMe123!")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
