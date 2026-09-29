"""Generates 4 fictional supplier RFP PDFs used to exercise the app end-to-end.
Run once: python sample_rfps/generate_sample_pdfs.py
"""
import os

from fpdf import FPDF

OUT_DIR = os.path.dirname(os.path.abspath(__file__))


def render(filename: str, title: str, sections: dict):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_margins(15, 15, 15)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(0, 10, title)
    pdf.ln(2)

    for heading, body in sections.items():
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(0, 8, heading)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(0, 6, body)
        pdf.ln(3)

    pdf.output(os.path.join(OUT_DIR, filename))
    print(f"Wrote {filename}")


PROPOSALS = {
    "apex_systems.pdf": (
        "Apex Systems - RFP Response: Enterprise Procurement Platform",
        {
            "Executive Summary": (
                "Apex Systems proposes a cloud-native procurement platform built on a microservices "
                "architecture with proven scalability to 50,000+ concurrent users. We understand the "
                "requirement for a resilient, auditable, and secure evaluation system."
            ),
            "Proposed Solution & Implementation Approach": (
                "Architecture uses Kubernetes-orchestrated microservices, event-driven integration via "
                "Kafka, and a PostgreSQL cluster with read replicas. REST and GraphQL APIs support "
                "integration with existing ERP systems. Horizontal auto-scaling is configured for peak load."
            ),
            "Timeline, Team Structure, and Milestones": (
                "18-week delivery: Weeks 1-3 discovery and architecture sign-off, Weeks 4-10 core build, "
                "Weeks 11-14 integration and security testing, Weeks 15-18 UAT and go-live. Team of 9: "
                "1 delivery lead, 2 architects, 4 engineers, 1 QA lead, 1 security engineer."
            ),
            "Price Table with Assumptions": (
                "License + implementation: $420,000 (Year 1), $95,000/year thereafter. Assumes standard "
                "integration scope (3 systems), 40 named admin users, and client-provided test environments. "
                "Change requests billed at $185/hour."
            ),
            "Security, Compliance, and Risk Controls": (
                "SOC 2 Type II certified, ISO 27001 certified. Data encrypted at rest (AES-256) and in "
                "transit (TLS 1.3). Full audit logging with 7-year retention. Annual third-party penetration "
                "testing with reports available on request. Role-based access control with SSO/SAML support."
            ),
            "Support Model, Relevant Experience, and References": (
                "24/7 tier-1 support with a 1-hour critical response SLA. Delivered similar platforms for "
                "3 Fortune 500 procurement teams in the last 4 years. References available from a global "
                "logistics client and a national retail chain upon request."
            ),
        },
    ),
    "brightpath_tech.pdf": (
        "BrightPath Tech - RFP Response: Procurement Evaluation Tool",
        {
            "Executive Summary": (
                "BrightPath Tech offers the fastest and most affordable path to a working procurement "
                "evaluation tool, ideal for teams who need to move quickly without a large budget."
            ),
            "Proposed Solution & Implementation Approach": (
                "A single Django monolith backed by PostgreSQL, deployed on a managed hosting provider. "
                "Core scoring and leaderboard features are included; advanced integrations are handled "
                "case-by-case after launch."
            ),
            "Timeline, Team Structure, and Milestones": (
                "6-week delivery: Week 1 kickoff, Weeks 2-4 build, Week 5 client review, Week 6 launch. "
                "Team of 3: 1 developer-lead, 1 developer, 1 part-time project coordinator."
            ),
            "Price Table with Assumptions": (
                "Flat fee: $65,000 total, no ongoing license fee for year 1, $18,000/year support "
                "thereafter. Assumes client handles user training internally. Pricing valid for 30 days."
            ),
            "Security, Compliance, and Risk Controls": (
                "Standard hosting-provider security features (managed firewall, automatic OS patching). "
                "We are in the process of evaluating SOC 2 certification. Data is encrypted in transit. "
                "Detailed compliance documentation is not yet finalized."
            ),
            "Support Model, Relevant Experience, and References": (
                "Business-hours email support. This would be our first project of this exact scope; "
                "we have delivered smaller internal tools for two regional retail clients. References "
                "can be provided on request but are limited in number."
            ),
        },
    ),
    "nexaworks.pdf": (
        "NexaWorks - RFP Response: Supplier Evaluation & Ranking System",
        {
            "Executive Summary": (
                "NexaWorks proposes a balanced, well-governed delivery combining solid technical design "
                "with an unusually detailed implementation plan and support model tailored to procurement teams."
            ),
            "Proposed Solution & Implementation Approach": (
                "Modular service architecture (FastAPI backend, React frontend, SQLite for pilot / "
                "PostgreSQL for production) with clear separation between LLM-assisted scoring and "
                "deterministic ranking logic, matching industry best practice for explainable AI systems."
            ),
            "Timeline, Team Structure, and Milestones": (
                "12-week delivery with a detailed RACI matrix: Weeks 1-2 requirements workshops, Weeks "
                "3-8 iterative build with bi-weekly demos, Weeks 9-10 hardening and load testing, Weeks "
                "11-12 UAT, training, and go-live support. Team of 6 with a named risk owner and weekly "
                "status reporting cadence."
            ),
            "Price Table with Assumptions": (
                "$210,000 fixed-price implementation, $48,000/year support and maintenance. Includes 2 "
                "integration endpoints and up to 25 hours of post-launch training. Assumptions and "
                "exclusions listed in Appendix A of the full proposal."
            ),
            "Security, Compliance, and Risk Controls": (
                "ISO 27001 aligned controls, encrypted storage, quarterly access reviews, and a documented "
                "incident response runbook. Formal SOC 2 certification targeted for next fiscal year."
            ),
            "Support Model, Relevant Experience, and References": (
                "Dedicated named support engineer plus 12-hour-response SLA, with a documented escalation "
                "path. Delivered 5 comparable evaluation/ranking systems in the last 3 years, including one "
                "for a mid-market industrial distributor. Three references available with contact details "
                "on request, including one same-industry reference."
            ),
        },
    ),
    "orbit_digital.pdf": (
        "Orbit Digital - RFP Response: Vendor Assessment Platform",
        {
            "Executive Summary": (
                "Orbit Digital brings over a decade of experience delivering vendor assessment tools for "
                "enterprise procurement teams, with deep domain expertise and a strong reference base."
            ),
            "Proposed Solution & Implementation Approach": (
                "We will build on our existing vendor-assessment framework, adapted to the client's "
                "criteria model. Integration approach will be finalized collaboratively during discovery; "
                "specific integration patterns and API contracts will be confirmed once existing client "
                "systems are reviewed."
            ),
            "Timeline, Team Structure, and Milestones": (
                "14-week delivery: Weeks 1-4 discovery and framework adaptation, Weeks 5-11 build, Weeks "
                "12-14 UAT and launch. Team of 5, led by a principal consultant with 10+ years in "
                "procurement technology."
            ),
            "Price Table with Assumptions": (
                "$260,000 implementation, $60,000/year ongoing support. Assumes existing framework covers "
                "80% of requirements; remaining 20% scoped as change orders at $175/hour."
            ),
            "Security, Compliance, and Risk Controls": (
                "SOC 2 Type I certified (Type II in progress). Standard encryption at rest and in transit. "
                "Access control via role-based permissions. Incident response process exists internally but "
                "was not detailed in this response."
            ),
            "Support Model, Relevant Experience, and References": (
                "Business-hours support with a 4-hour response SLA. Delivered 8+ vendor assessment "
                "platforms across procurement, facilities, and IT sourcing teams over the past decade. "
                "Four references available immediately, including two multi-year repeat clients."
            ),
        },
    ),
}


def main():
    for filename, (title, sections) in PROPOSALS.items():
        render(filename, title, sections)


if __name__ == "__main__":
    main()
