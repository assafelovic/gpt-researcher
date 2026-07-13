"""Build the realistic internal-documents corpus for the hybrid benchmark.

Takes the four ground-truth documents in ``internal_docs_src/`` and produces
``internal_docs/``, a corpus shaped like a real company document share:

- The fact documents are converted to the formats such documents actually
  ship in: PDF (board memo, ops report), DOCX (product brief) and markdown
  (company overview).
- Distractor documents (HR policies, IT runbooks, meeting notes, marketing
  copy) are added across subdirectories, none of which contain checkpoint
  facts.
- Stale near-miss documents (2024/2025 ops reports and an outdated product
  one-pager) contain earlier versions of the same metrics, so answering with
  the wrong vintage of a fact is penalized by the grader.

Deterministic: running it twice produces the same corpus.

Usage: python deep_agents/benchmark_data/build_corpus.py
"""

import shutil
from pathlib import Path

import pymupdf
from docx import Document

SRC = Path(__file__).parent / "internal_docs_src"
OUT = Path(__file__).parent / "internal_docs"


def write_pdf(text: str, path: Path) -> None:
    doc = pymupdf.open()
    lines = text.splitlines()
    per_page = 52
    for start in range(0, len(lines), per_page):
        page = doc.new_page()
        page.insert_text(
            (54, 60),
            "\n".join(lines[start : start + per_page]),
            fontsize=10,
            fontname="helv",
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(path))
    doc.close()


def write_docx(text: str, path: Path) -> None:
    doc = Document()
    for line in text.splitlines():
        doc.add_paragraph(line)
    path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(path))


def write_md(text: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


# ---------------------------------------------------------------------------
# Stale near-miss documents: earlier vintages of the fact documents. Their
# numbers are deliberately different from the 2026 ground truth.
# ---------------------------------------------------------------------------

STALE_OPS_2024 = """# Q1 2024 Operations Report - Veltrix Dynamics

**Internal - Confidential | Prepared by: COO office, April 2024**

## Fleet performance

- Deployed fleet: 1,180 VLX-400 robots across 21 customer sites
- Fleet availability: 98.4% (target: 98.5%) - missed due to winter incidents
- Average picks per robot per hour: 118

## Revenue

- Q1 2024 revenue: $7.9M (Q1 2023: $4.6M)
- RaaS annual recurring revenue (ARR): $14.2M exiting Q1
- Gross margin: 33% blended

## Key risks tracked

1. Concentration: top 3 customers = 61% of ARR.
2. Series B proceeds ($34.5M, Feb 2024) fund roughly 20 months of runway.
"""

STALE_OPS_2025 = """# Q1 2025 Operations Report - Veltrix Dynamics

**Internal - Confidential | Prepared by: COO office, April 2025**

## Fleet performance

- Deployed fleet: 1,960 VLX-400 robots across 33 customer sites
- Fleet availability: 98.9%
- Mean time between failures (MTBF): 2,010 hours
- Average picks per robot per hour: 131

## Revenue

- Q1 2025 revenue: $12.8M (Q1 2024: $7.9M, +62% YoY)
- RaaS annual recurring revenue (ARR): $27.5M exiting Q1
- Gross margin: 37% blended

## Key risks tracked

1. Concentration: top 3 customers = 52% of ARR.
2. Series C fundraise planned for H2 2025; target $60-70M.
"""

STALE_PRODUCT_2025 = """# VLX-500 Concept One-Pager (v0.2 - SUPERSEDED)

**Internal - Confidential | Product team, June 2025**

NOTE: early concept figures - superseded by the 2026 product brief.

- Target launch: Q2 2026 (aggressive) at list price $52,000
- Payload target: 800 kg
- Cold rating target: -25C (parity with VLX-400)
- Battery: 10h Li-ion, swappable
- Fleet software: VeltrixOS 4.x compatible mode only
"""

# ---------------------------------------------------------------------------
# Distractor documents: realistic internal noise, no checkpoint facts.
# ---------------------------------------------------------------------------

DISTRACTORS = {
    "hr/remote_work_policy.md": """# Remote & Hybrid Work Policy

**HR - effective January 2026**

Veltrix Dynamics operates a hybrid model: employees work from the office at
least two days per week (Tuesday is the anchor day in every location).
Fully-remote arrangements require VP approval and are reviewed annually.

Office locations: Rotterdam (Van Nelle Campus), Atlanta, Nagoya. Employees
may work up to 20 days per year from another country within their tax
region. Equipment budget: EUR 900 per employee per two years.
""",
    "hr/onboarding_checklist.md": """# New Hire Onboarding Checklist

- Day 1: badge, laptop (see IT runbook), buddy assignment, HR intro
- Week 1: security training, warehouse safety certification (mandatory for
  all roles, including office staff), intro to VeltrixOS demo environment
- Month 1: 30-day check-in with manager, benefits enrollment deadline
- Month 3: probation review

Buddy program: every new hire is paired with a colleague from a different
team for the first 90 days.
""",
    "hr/annual_leave_faq.md": """# Annual Leave FAQ

- EU employees: 28 days statutory + 3 company days (Christmas week).
- US employees: 22 days PTO, no carry-over beyond 5 days.
- Japan employees: per local statutory schedule plus company days.
- Leave requests above 10 consecutive working days need manager approval
  four weeks in advance.
- Unused company days do not roll over.
""",
    "it/laptop_runbook.md": """# IT Runbook: Laptop Provisioning

Standard issue: 14" laptop, 32GB RAM. Engineering may request 64GB.
All machines are enrolled in MDM before handover; disk encryption and
screen-lock policy (5 minutes) are enforced centrally.

VPN: WireGuard profiles are issued per-device. Access to the fleet
telemetry environment additionally requires a hardware security key.

Loaner pool: 6 machines in Rotterdam, 3 in Atlanta, 2 in Nagoya.
""",
    "it/incident_process.md": """# IT Incident Process

Severity levels:

- SEV-1: production fleet impact at one or more customer sites. Page the
  on-call fleet engineer immediately; customer comms within 60 minutes.
- SEV-2: internal systems down (ERP, CI, telemetry lag > 30 min).
- SEV-3: degraded internal tooling, next business day.

Post-mortems are mandatory for SEV-1/SEV-2 within five working days,
blameless format, filed in the engineering wiki.
""",
    "it/access_review_2026.md": """# Quarterly Access Review - Q1 2026

Completed February 2026. 412 accounts reviewed across ERP, telemetry,
code hosting and the customer support desk. 23 stale accounts disabled
(mostly contractors from the 2025 warehouse commissioning wave).
Two privilege escalations flagged and reverted. Next review: May 2026.
""",
    "marketing/brand_guidelines.md": """# Veltrix Brand Guidelines (excerpt)

Primary color: Veltrix Blue (#1B4FD8). Secondary: Arctic White, Signal
Amber. The wordmark is always set in Grotesk Bold; never stretch or
recolor the robot glyph.

Tone of voice: precise, warm, no robot puns in customer-facing copy.
Product names are always hyphenated: VLX-400, VLX-500.
""",
    "marketing/event_calendar_2026.md": """# 2026 Event Calendar - Marketing

- LogiMAT Stuttgart (March): 54 sqm booth, VLX-400 live demo cell
- MODEX Atlanta (April): joint booth with cold-chain integrator partner
- CeMAT Asia (November): first Nagoya-led presence, focus on Japan market
- Customer advisory board: June (Rotterdam), December (virtual)

Budget note: event spend is tracked under MKT-EVT; Q1 actuals came in 8%
under plan.
""",
    "marketing/website_faq_draft.md": """# Website FAQ draft (public-safe)

Q: What does Veltrix build?
A: Autonomous mobile robots and fleet software for warehouse and
cold-chain logistics.

Q: Where does Veltrix operate?
A: Europe, North America and Japan, with 24/7 fleet support.

Q: Can I see a demo?
A: Yes - book via the website; demos run at the Rotterdam experience
center and at LogiMAT/MODEX.

(Do NOT publish pricing, fleet counts or customer names without comms
approval.)
""",
    "finance/expense_policy.md": """# Expense Policy (2026)

- Flights under 4 hours: economy. Above: premium economy with VP approval.
- Hotel caps: EUR 180 (EU), USD 240 (US), JPY 28,000 (Japan) per night.
- Team events: EUR 60 per person per quarter.
- Customer entertainment requires pre-approval above EUR 150.
- All expenses filed within 30 days; quarterly compliance spot-checks.
""",
    "finance/erp_migration_notes.md": """# ERP Migration - Status Notes (March 2026)

Migration from legacy system to the new ERP is in phase 2 of 3.
Purchasing and inventory modules are live; revenue recognition cutover is
planned for the summer close. Known issue: intercompany eliminations for
the Nagoya entity still require a manual journal each month.

Finance headcount during migration: +2 temporary contractors through
September 2026.
""",
    "engineering/veltrixos_release_notes_5_0_beta.md": """# VeltrixOS 5.0 (beta) - Release Notes

Highlights:

- New traffic manager with intersection auctions (up to 18% throughput
  gain in simulation on dense layouts)
- Multi-floor support (elevator integration) enters closed beta
- Fleet dashboard: new cold-chain telemetry panel (battery thermal
  derating, door-open events)
- Breaking change: the v4 REST telemetry API is deprecated; sunset target
  is mid-2027.

Beta sites: 3 (all EU). GA targeted alongside the VLX-500 program.
""",
    "engineering/simulation_cluster_usage.md": """# Simulation Cluster - Usage Guidelines

The path-planning simulation cluster (128 nodes) is shared between the
traffic-manager team and the perception team. Book via the scheduler;
jobs above 200 node-hours need team-lead signoff. Nightly regression
suite has priority between 01:00-05:00 CET.

Storage: scenario bundles are retained for 90 days, results for 1 year.
""",
    "engineering/oncall_rotation.md": """# Fleet On-Call Rotation

Follow-the-sun: Rotterdam covers 06:00-18:00 CET, Atlanta 12:00-24:00
EST, Nagoya covers the remainder. Handover call at each boundary with a
written summary in the on-call channel.

Escalation: fleet engineer -> site reliability lead -> VP Engineering.
Compensation: per company policy, one day off per full on-call week.
""",
    "sales/discount_approval_matrix.md": """# Discount Approval Matrix (2026)

- Up to 5%: account executive discretion
- 5-12%: regional sales director
- 12-20%: VP Sales
- Above 20%: CEO + CFO joint approval, deal desk memo required

RaaS contracts: any deviation from standard 36-month term or SLA
requires deal desk review regardless of discount level.
""",
    "sales/customer_reference_program.md": """# Customer Reference Program

Reference customers receive early access to roadmap briefings and an
annual executive dinner. In exchange they commit to two analyst calls
and one public case study per year.

Current program size: 9 accounts (6 EU, 2 US, 1 JP). Target for 2026:
12 accounts. Owner: field marketing.
""",
    "ops/warehouse_safety_bulletin_march2026.md": """# Warehouse Safety Bulletin - March 2026

Reminder: high-visibility vests are mandatory in all robot operating
zones, including during demos. Pedestrian walkways are repainted at the
Rotterdam experience center; induction for visitors now includes the
updated zone map.

Near-miss reports in February: 3 (all pedestrian pathway violations, no
contact events). Corrective action: additional signage at zone
crossings.
""",
    "ops/site_commissioning_playbook.md": """# Site Commissioning Playbook (v3)

Standard commissioning timeline for a 60-robot site is six weeks:

1. Week 1: site survey validation, network install (private 5GHz mesh)
2. Weeks 2-3: floor mapping, traffic zones, charger placement
3. Week 4: staged rollout (20% fleet), picker training
4. Weeks 5-6: full rollout, hypercare, SLA baseline measurement

Cold-storage sites add one week for thermal soak testing and battery
derating calibration.
""",
    "legal/dpa_template_notes.md": """# DPA Template - Negotiation Notes

Our standard data processing agreement covers fleet telemetry and
warehouse-worker interaction events (anonymized). Common redlines:

- Sub-processor list change notice: we offer 30 days (customers ask 60)
- Telemetry retention: standard 24 months (negotiable to 12)
- EU data residency: available on the premium fleet plan only

Escalate any request to process worker video beyond safety events.
""",
    "board/board_minutes_2024_06.md": """# Board Minutes - June 2024 (excerpt, approved)

Attendees: full board. Topics:

- Series B deployment update: hiring plan tracking, EU expansion on plan
- US market entry approved: Atlanta office to open Q4 2024
- Early VLX-500 concept discussion: board asks for cold-chain
  differentiation to remain the core thesis
- Next fundraise: revisit market conditions in mid-2025

(Current-year board materials live in the 2026 strategy memo.)
""",
}


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    src = {p.name: p.read_text(encoding="utf-8") for p in SRC.glob("*.md")}

    # Fact documents in realistic formats.
    write_pdf(src["board_memo_2026_strategy.md"], OUT / "board" / "board_memo_2026_strategy.pdf")
    write_pdf(src["q1_2026_ops_report.md"], OUT / "ops" / "q1_2026_ops_report.pdf")
    write_docx(src["vlx500_product_brief.md"], OUT / "product" / "vlx500_product_brief.docx")
    write_md(src["company_overview.md"], OUT / "company_overview.md")

    # Stale near-miss vintages.
    write_pdf(STALE_OPS_2024, OUT / "ops" / "archive" / "q1_2024_ops_report.pdf")
    write_pdf(STALE_OPS_2025, OUT / "ops" / "archive" / "q1_2025_ops_report.pdf")
    write_md(STALE_PRODUCT_2025, OUT / "product" / "archive" / "vlx500_concept_2025_superseded.md")

    # Distractors.
    for rel, text in DISTRACTORS.items():
        write_md(text, OUT / rel)

    n = sum(1 for _ in OUT.rglob("*") if _.is_file())
    print(f"Corpus built: {n} files in {OUT}")


if __name__ == "__main__":
    main()
