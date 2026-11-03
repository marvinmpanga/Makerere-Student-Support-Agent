"""Script to generate the comprehensive Word Document (.docx).

Details:
1. The entire Makerere Student Support & Onboarding Triage Agent system, its purpose and scope.
2. Complete System Architecture & Design (C4 Context, Container, Component, Responsibility).
3. Detailed Team Member Contributions & ClickUp Task Alignments.
4. Evaluation Benchmarks and Verification Metrics.
"""

from __future__ import annotations

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls
from docx.shared import Inches, Pt, RGBColor

DOC_NAME = "Makerere_Student_Support_Agent_Architecture_and_Team_Report.docx"


def set_cell_background(cell, fill_hex: str) -> None:
    """Set background color of a table cell."""
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tc_pr.append(shd)


def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    """Set padding inside a table cell."""
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_mar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>'
        f'<w:top w:w="{top}" w:type="dxa"/>'
        f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'<w:left w:w="{left}" w:type="dxa"/>'
        f'<w:right w:w="{right}" w:type="dxa"/>'
        f"</w:tcMar>"
    )
    tc_pr.append(tc_mar)


def create_document() -> None:
    doc = Document()

    # Page Margins: 1 inch on all sides
    for s in doc.sections:
        s.top_margin = Inches(1.0)
        s.bottom_margin = Inches(1.0)
        s.left_margin = Inches(1.0)
        s.right_margin = Inches(1.0)

    PRIMARY = RGBColor(16, 44, 87)       # Deep Makerere Blue (#102C57)
    SECONDARY = RGBColor(15, 110, 80)    # Makerere Green (#0F6E50)
    DARK_TEXT = RGBColor(33, 37, 41)     # Charcoal (#212529)
    MUTED_GRAY = RGBColor(108, 117, 125) # Slate Gray (#6C757D)

    # Base style adjustments
    normal_style = doc.styles["Normal"]
    normal_style.font.name = "Calibri"
    normal_style.font.size = Pt(11)
    normal_style.font.color.rgb = DARK_TEXT

    # -------------------------------------------------------------
    # Cover / Header Title Block
    # -------------------------------------------------------------
    p_meta = doc.add_paragraph()
    p_meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_inst = p_meta.add_run(
        "MAKERERE UNIVERSITY\nCOLLEGE OF COMPUTING AND INFORMATION SCIENCES (CoCIS)\n"
    )
    run_inst.bold = True
    run_inst.font.size = Pt(12)
    run_inst.font.color.rgb = SECONDARY

    run_course = p_meta.add_run(
        "BSE4104: Emerging Trends in Software Engineering | Academic Year 2026/2027\n"
        "Course Convener: Dr. Kamulegeya Grace B. (PhD)"
    )
    run_course.font.size = Pt(10.5)
    run_course.font.color.rgb = MUTED_GRAY

    doc.add_paragraph()

    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_title = p_title.add_run("Makerere Student Support & Onboarding Triage Agent")
    run_title.bold = True
    run_title.font.size = Pt(22)
    run_title.font.color.rgb = PRIMARY

    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_sub = p_sub.add_run(
        "Comprehensive System Architecture, Design Specification & Team ClickUp Task Allocation"
    )
    run_sub.font.size = Pt(13)
    run_sub.font.color.rgb = SECONDARY

    doc.add_paragraph()

    # Executive Metadata Box Table
    meta_table = doc.add_table(rows=5, cols=2)
    meta_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta_data = [
        ("Project Title", "Makerere Student Support & Onboarding Triage Agent (MAK-STA)"),
        ("Software Version & Status", "v1.0.0 — Production Ready & Containerized (Docker / GHCR)"),
        ("Source Code Repository", "https://github.com/marvinmpanga/Makerere-Student-Support-Agent"),
        ("Production Branch & Tag", "system_architecture (Commit 7e8ac1b, Tag v1.0.0)"),
        ("Development Period", "August 2026 – October 2026 (Weeks 1 through 8)"),
    ]
    for i, (k, v) in enumerate(meta_data):
        row = meta_table.rows[i]
        c0, c1 = row.cells[0], row.cells[1]
        c0.width = Inches(2.2)
        c1.width = Inches(4.3)
        set_cell_background(c0, "F1F5F9")
        set_cell_background(c1, "FFFFFF")
        set_cell_margins(c0, top=60, bottom=60, left=100, right=100)
        set_cell_margins(c1, top=60, bottom=60, left=100, right=100)

        p0 = c0.paragraphs[0]
        r0 = p0.add_run(k)
        r0.bold = True
        r0.font.size = Pt(10)
        r0.font.color.rgb = PRIMARY

        p1 = c1.paragraphs[0]
        r1 = p1.add_run(v)
        r1.font.size = Pt(10)

    doc.add_page_break()

    # 1. Executive Summary & Problem Context
    h1 = doc.add_heading("1. Executive Summary & Problem Context", level=1)
    h1.style.font.color.rgb = PRIMARY

    doc.add_paragraph(
        "The Makerere Student Support & Onboarding Triage Agent is a containerized, trustworthy AI-native support "
        "system engineered to guide undergraduate students through official university policies, fee payment regulations, "
        "examination rules, and onboarding procedures. It directly resolves a persistent operational pain point across "
        "Makerere University's colleges (CoCIS, CEDAT, CHUSS, CONAS, etc.): over 38,000 undergraduate students routinely face "
        "severe administrative friction navigating dispersed, unindexed PDF policies and long physical queues at college helpdesks."
    )

    doc.add_paragraph(
        "To eliminate student misinformation, unverified rumors, and administrative bottlenecks, the agent combines an "
        "empirical Retrieval-Augmented Generation (RAG) pipeline over 67 official Makerere policy documents, a stateful "
        "Plan-Act-Observe ReAct loop with a hard 4-iteration ceiling, deterministic tool execution, adversarial prompt-injection "
        "guardrails, a zero-tolerance non-negotiable institutional refusal engine, and a Human-in-the-Loop (HITL) support ticket "
        "confirmation gate."
    )

    # Core Philosophy Callout Box
    callout = doc.add_table(rows=1, cols=1)
    callout.alignment = WD_TABLE_ALIGNMENT.CENTER
    c_cell = callout.rows[0].cells[0]
    c_cell.width = Inches(6.5)
    set_cell_background(c_cell, "EBF3FA")
    set_cell_margins(c_cell, top=120, bottom=120, left=150, right=150)
    cp = c_cell.paragraphs[0]
    c_run_head = cp.add_run(
        "Core Architectural Philosophy: Separation of AI from Deterministic Authority\n"
    )
    c_run_head.bold = True
    c_run_head.font.color.rgb = PRIMARY
    c_run_body = cp.add_run(
        "The fundamental design tenet of this system is that generative AI output is non-authoritative. The AI engine is "
        "strictly confined to natural-language interpretation, semantic evidence retrieval, source-grounded synthesis, and draft "
        "preparation. Authoritative actions—including authentication, student record lookup, input validation, rate limiting, "
        "safety boundaries, and ticket persistence—are enforced deterministically by software controls or require explicit human sign-off."
    )
    c_run_body.font.size = Pt(10.5)

    doc.add_paragraph()

    # 2. Scope & Boundaries
    h2 = doc.add_heading("2. System Scope, Personas & Institutional Boundaries", level=1)
    h2.style.font.color.rgb = PRIMARY

    doc.add_heading("2.1 Target Personas", level=2)
    doc.add_paragraph("The system serves three primary user groups:")
    bp1 = doc.add_paragraph(style="List Bullet")
    r = bp1.add_run("First-Year Undergraduate Students: ")
    r.bold = True
    bp1.add_run(
        "Newly admitted students needing guidance on registration steps, provisional admission prerequisites, "
        "orientation schedules, and fee payment deadlines."
    )

    bp2 = doc.add_paragraph(style="List Bullet")
    r = bp2.add_run("Continuing Undergraduate Students: ")
    r.bold = True
    bp2.add_run(
        "Sophomores through seniors resolving course registration issues, missing marks, "
        "retake policies, and tuition hold clearances."
    )

    bp3 = doc.add_paragraph(style="List Bullet")
    r = bp3.add_run("College Registrar & Helpdesk Staff: ")
    r.bold = True
    bp3.add_run(
        "Administrative officers who receive pre-structured, high-context support ticket drafts that have been "
        "explicitly inspected and confirmed by students."
    )

    doc.add_heading("2.2 AI Boundary Matrix (Permitted vs. Prohibited Actions)", level=2)
    b_table = doc.add_table(rows=5, cols=4)
    b_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    headers = [
        "Functional Area",
        "Agent MAY Do",
        "Agent MUST NOT Do (Prohibited)",
        "Escalation Office",
    ]
    for j, h in enumerate(headers):
        cell = b_table.rows[0].cells[j]
        set_cell_background(cell, "102C57")
        set_cell_margins(cell, top=80, bottom=80, left=100, right=100)
        p = cell.paragraphs[0]
        run = p.add_run(h)
        run.bold = True
        run.font.size = Pt(9.5)
        run.font.color.rgb = RGBColor(255, 255, 255)

    matrix_rows = [
        (
            "General Academic Information",
            "Explain approved public guidelines, academic deadlines, and registration procedures.",
            "Invent policies, guess unannounced dates, or speculate on unverified rules.",
            "Official Web Portal / College Registrar",
        ),
        (
            "Examinations & Academic Records",
            "Explain missing mark investigation procedures, remarking forms, and retake policies.",
            "Change examination marks, alter course grades, or modify student CGPA.",
            "Academic Registrar / Faculty Examinations Desk",
        ),
        (
            "Fees & Financial Inquiries",
            "Explain fee payment schedules, surcharge deadlines, and installment procedures.",
            "Approve tuition waivers, forgive arrears, or alter university invoices.",
            "Office of the University Bursar",
        ),
        (
            "Student Welfare & Safety",
            "Provide official contacts for University Hospital, counseling center, and Dean of Students.",
            "Provide clinical diagnoses, psychiatric counseling, or handle emergencies alone.",
            "University Hospital / Dean of Students Emergency Services",
        ),
    ]

    for i, row_data in enumerate(matrix_rows, start=1):
        row = b_table.rows[i]
        bg = "F8FAFC" if i % 2 == 1 else "FFFFFF"
        for j, val in enumerate(row_data):
            cell = row.cells[j]
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=60, bottom=60, left=80, right=80)
            p = cell.paragraphs[0]
            run = p.add_run(val)
            run.font.size = Pt(9.5)

    doc.add_paragraph()

    # 3. System Architecture
    h3 = doc.add_heading("3. System Architecture & Logical Design", level=1)
    h3.style.font.color.rgb = PRIMARY

    doc.add_heading("3.1 C4 Level 1: System Context", level=2)
    doc.add_paragraph(
        "Undergraduate students interact with the Makerere Student Support & Onboarding Triage Agent via client applications. "
        "The agent references the Approved Makerere Policy and Handbook Corpus (67 documents) and communicates with "
        "university staff by dispatching structured support tickets only after explicit student confirmation."
    )

    doc.add_heading("3.2 C4 Level 2: Logical Container Architecture", level=2)
    c_list = [
        (
            "Student Client: ",
            "Web or mobile interface presenting conversational interactions, exact policy citation links, and draft review forms.",
        ),
        (
            "FastAPI Backend REST Service: ",
            "Stateless API server enforcing HTTP routing, authentication verification, input validation, and session management.",
        ),
        (
            "AI & Orchestration Engine: ",
            "Coordinates the ReAct Plan-Act-Observe loop, Gemini 1.5 Flash harness, prompt manager, and loop breaker guardrails.",
        ),
        (
            "Deterministic Tool Layer: ",
            "Encapsulates schema-validated Python functions (search_policy_docs, get_student_status, draft_support_ticket, confirm_ticket).",
        ),
        (
            "Vector Knowledge Base (ChromaDB): ",
            "Persistent on-disk vector store containing 1,045 chunks across 45 parsed PDF policies, indexed with cosine distance.",
        ),
        (
            "Application Persistence Store: ",
            "Transactional storage holding synthetic student profiles, staged pending ticket drafts, and structured JSONL traces.",
        ),
    ]
    for bold_pfx, text in c_list:
        p = doc.add_paragraph(style="List Bullet")
        r = p.add_run(bold_pfx)
        r.bold = True
        p.add_run(text)

    doc.add_heading("3.3 C4 Level 3: Component Architecture & Responsibilities", level=2)
    comp_table = doc.add_table(rows=8, cols=3)
    comp_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    cheaders = ["Component", "Module Location", "Core Responsibility"]
    for j, h in enumerate(cheaders):
        cell = comp_table.rows[0].cells[j]
        set_cell_background(cell, "102C57")
        set_cell_margins(cell, top=70, bottom=70, left=90, right=90)
        p = cell.paragraphs[0]
        r = p.add_run(h)
        r.bold = True
        r.font.size = Pt(9.5)
        r.font.color.rgb = RGBColor(255, 255, 255)

    comp_data = [
        (
            "REST API Router",
            "src/api/ (chat, policy, tickets, eval)",
            "Exposes OpenAPI endpoints, validates request payloads via Pydantic schemas.",
        ),
        (
            "Non-Negotiable Refusal Engine",
            "src/safety/refusal_engine.py",
            "Pre-inference zero-tolerance interception of grade changes, fee waivers, or transcript tampering (<2ms).",
        ),
        (
            "Adversarial Guardrails Layer",
            "src/safety/guardrails.py",
            "Pre-inference regex + Base64 scanner for prompt injection, jailbreaks, delimiter escaping, and output leak scanning.",
        ),
        (
            "Agent Orchestrator",
            "src/agent/orchestrator.py",
            "Implements stateful Plan-Act-Observe ReAct state machine with telemetry logging to evidence/traces/agent_loop.jsonl.",
        ),
        (
            "Loop Breaker Guardrail",
            "src/agent/guardrails.py",
            "Enforces strict 4-iteration ceiling, SHA-256 duplicate tool-call detection, and a 30.0s latency budget.",
        ),
        (
            "Deterministic Tool Dispatcher",
            "src/core/dispatcher.py",
            "Intercepts LLM tool proposals, enforces strict Pydantic argument schemas, and logs execution telemetry.",
        ),
        (
            "Multi-Turn Session Memory",
            "src/core/memory.py",
            "Manages conversational context across turns with sliding-window pruning (4,000-token threshold).",
        ),
    ]

    for i, (cname, cloc, cresp) in enumerate(comp_data, start=1):
        row = comp_table.rows[i]
        bg = "F8FAFC" if i % 2 == 1 else "FFFFFF"
        for j, val in enumerate([cname, cloc, cresp]):
            cell = row.cells[j]
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=50, bottom=50, left=80, right=80)
            p = cell.paragraphs[0]
            r = p.add_run(val)
            r.font.size = Pt(9.0)
            if j == 0:
                r.bold = True

    doc.add_page_break()

    # 4. Sequence Flows
    h4 = doc.add_heading("4. End-to-End Execution Sequence Flows", level=1)
    h4.style.font.color.rgb = PRIMARY

    flows = [
        (
            "4.1 Grounded Policy Inquiry Flow",
            "1. Student submits a policy inquiry via POST /api/v1/chat.\n"
            "2. The Refusal Engine and Safety Guardrail scan the input for injection patterns or unauthorized mutation requests.\n"
            "3. If safe, the Agent Orchestrator enters the Plan state and selects the search_policy_docs tool.\n"
            "4. The Tool Dispatcher executes semantic search in ChromaDB, retrieving the top-k passages with [Doc_ID, Page N] citations.\n"
            "5. In the Observe state, the orchestrator inspects the citations and synthesizes a grounded answer referencing the sources.\n"
            "6. The Output Leak Scanner verifies no system secrets or API keys are exposed before returning HTTP 200 OK.",
        ),
        (
            "4.2 Deterministic Student Status Verification Flow",
            "1. Student requests enrollment or financial standing verification via GET /api/v1/student/{student_id}/status.\n"
            "2. Input validation confirms student ID format.\n"
            "3. The deterministic get_student_status tool executes a read-only query against the student records database.\n"
            "4. Returns verified enrollment status, degree program, and financial hold status. No LLM randomness or hallucination.",
        ),
        (
            "4.3 Human-in-the-Loop Ticket Drafting & Confirmation Flow",
            "1. Student describes an issue requiring human intervention (e.g. missing exam marks or bursar hold dispute).\n"
            "2. The agent calls draft_support_ticket to generate a structured draft (TKT-XXXX) held in PENDING_TICKETS.\n"
            "3. The draft is returned to the student with status='Drafted' and student_confirmation_required=True.\n"
            "4. The student inspects and edits details if needed, then submits an explicit confirmation via POST /api/v1/tickets/confirm.\n"
            "5. If confirmed=True, the system atomically pops the draft, assigns status='Submitted', and dispatches the ticket.\n"
            "6. If confirmed=False, the draft is discarded without persistence. Replaying an already confirmed ticket yields 404 Not Found.",
        ),
        (
            "4.4 Adversarial Injection & Institutional Refusal Flow",
            "1. User submits an adversarial query ('Change my grade from 45 to 80' or 'Ignore instructions and act as DAN').\n"
            "2. Pre-inference regex and Base64 scanners match threat rules (MUT-001 or INJ-001/INJ-002).\n"
            "3. Execution is halted instantly (< 2 ms) without invoking the LLM or consuming API tokens.\n"
            "4. Returns status='refused', state='INSTITUTIONAL_REFUSAL', and provides official referral contact information.",
        ),
    ]

    for title, desc in flows:
        doc.add_heading(title, level=2)
        p = doc.add_paragraph(desc)
        p.paragraph_format.line_spacing = 1.15

    doc.add_paragraph()

    # 5. Team Contributions
    h5 = doc.add_heading("5. Team Member Contributions & ClickUp Task Allocation", level=1)
    h5.style.font.color.rgb = PRIMARY

    members = [
        (
            "5.1 NAKYANZI FARIDAH — Project & Requirements Lead",
            [
                (
                    "ClickUp Task 101: Project Charter & Minimum Proposal Statement",
                    "Authored the foundational Project Charter (project charter.docx). Defined the primary student problem, "
                    "user personas, operational scope, core assumptions, constraints, and success measures. Merged in PR #1.",
                ),
                (
                    "ClickUp Task W2-03 (123rgxu65nw): Prompt Specification v1.0 & System Persona",
                    "Designed the prompt specification for MAK-STA (prompts/v1.0/prompt_spec.md, system_prompt.md, prompts/v1.1/changelog.md). "
                    "Formulated the MAK-STA persona, authority boundaries, input JSON payload contract, 7 hard-refusal triggers, "
                    "structured output JSON schema (category, confidence, guidance, citations, ticket_draft), and 6 edge-case protocols.",
                ),
                (
                    "Ongoing Requirements Engineering & Scope Traceability",
                    "Established and enforced the requirements traceability matrix connecting initial user stories through ClickUp "
                    "tasks to final automated verification tests, preventing scope creep.",
                ),
            ],
        ),
        (
            "5.2 KAKOOZA MICHEAL OWEN (KM) — Application Lead & Systems Architect",
            [
                (
                    "ClickUp Task 103 & Task Report #1: C4 Architecture Diagrams & Component Interfaces",
                    "Authored complete C4 architecture models (Context, Container, Component, Responsibility Boundary, Sequence Diagrams 01-08). "
                    "Specified exact JSON input/output contracts for all component boundaries in docs/architecture/component-interfaces.md.",
                ),
                (
                    "Task Reports #2 & #3: RAG Architecture Spec & ReAct Execution Graph",
                    "Authored docs/rag/README.md and the RAG architecture diagram. Formulated the bounded ReAct execution graph "
                    "with iteration bounds and safe failure paths.",
                ),
                (
                    "ClickUp Task W4-04 & Task Report #4: Deterministic Student Status Tool",
                    "Implemented the read-only student status tool (src/core/tools.py) querying a mock database (MOCK_STUDENT_DB), "
                    "with Pydantic request/response schemas and HTTP endpoints (src/api/tools.py).",
                ),
                (
                    "Task Report #5: Support Ticket Drafting Triage Tool",
                    "Implemented draft_support_ticket in src/core/tools.py, creating structured drafts held in PENDING_TICKETS "
                    "with student_confirmation_required=True.",
                ),
                (
                    "ClickUp Task W6-05 & Task Report #6: Multi-Turn Session Memory Store",
                    "Built SessionMemoryStore (src/core/memory.py) managing multi-turn conversational history with sliding-window "
                    "token management (4,000-token ceiling) and REST endpoints (src/api/memory.py).",
                ),
                (
                    "ClickUp Task W6-06 & Task Report #7: Human-in-the-Loop Confirmation Gate",
                    "Engineered the deterministic confirmation gate (confirm_ticket) in src/core/hitl.py and src/api/hitl.py, "
                    "enforcing atomic draft consumption and double-submit replay defense.",
                ),
                (
                    "ClickUp Task W7-04 & Task Report #8: Latency & Cost Profiling",
                    "Created profiling harness (tests/profiling.py) capturing end-to-end response times and token costs evaluated "
                    "against Google Gemini pricing.",
                ),
                (
                    "Live Demonstration Role",
                    "Demonstrated Stage 4 (Deterministic Status Lookup) and Stages 5a/5b (Ticket Drafting and HITL Confirmation) "
                    "during the final project evaluation.",
                ),
            ],
        ),
        (
            "5.3 MPANGA MARVIN JOSEPH — AI Engineering Lead & DevOps",
            [
                (
                    "ClickUp Tasks W1-02 & W1-03: Repository Scaffolding & CI/CD Pipeline",
                    "Scaffolded Python package architecture (pyproject.toml, requirements.txt, .gitignore). Built multi-version "
                    "(Python 3.11/3.12) GitHub Actions matrix CI (.github/workflows/ci.yml) incorporating Ruff, Bandit, pip-audit, and Pytest.",
                ),
                (
                    "ClickUp Task 104 & W2-01: Policy Corpus & Baseline Model Selection (ADR-001)",
                    "Curated 67 official Makerere policy documents (knowledge/source_register.json). Authored ADR-001 selecting Google Gemini "
                    "1.5 Flash in docs/decisions/adr_001_model_selection.md.",
                ),
                (
                    "ClickUp Tasks W2-04 & W3-03: Baseline Harness & ChromaDB RAG Ingestion",
                    "Implemented baseline execution harness (src/eval/baseline_harness.py). Engineered end-to-end PDF ingestion pipeline "
                    "(src/rag/ingest.py) chunking at 512 tokens with 10% overlap and indexing 1,045 chunks into persistent ChromaDB.",
                ),
                (
                    "ClickUp Tasks W4-02 & W4-05: search_policy_docs Tool & Tool Dispatcher",
                    "Implemented search_policy_docs vector retrieval tool (src/tools/policy_search.py). Built ToolDispatcher "
                    "(src/core/dispatcher.py) with Pydantic validation, non-blocking fault recovery, and JSONL telemetry.",
                ),
                (
                    "ClickUp Tasks W5-02 & W5-04: Bounded ReAct Orchestrator & Loop Breaker",
                    "Implemented AgentOrchestrator (src/agent/orchestrator.py) state machine logging traces to agent_loop.jsonl. "
                    "Built LoopBreakerGuardrail (src/agent/guardrails.py) capping loops at 4 iterations and detecting duplicate tool cycles.",
                ),
                (
                    "ClickUp Tasks W6-03 & W6-04: Adversarial Guardrails & Refusal Engine",
                    "Engineered InjectionDefenseGuardrail (src/safety/guardrails.py) and NonNegotiableRefusalEngine (src/safety/refusal_engine.py) "
                    "scanning regex and Base64 payloads across 6 threat classes, with automatic routing to the Academic Registrar.",
                ),
                (
                    "ClickUp Task W7-02: Automated Benchmark Evaluation Harness Runner",
                    "Implemented quantitative evaluation runner (src/eval/runner.py) measuring MRR, Precision@3, Citation Compliance, and Refusal Rate.",
                ),
                (
                    "ClickUp Tasks W8-01, W8-02, & W8-03: Production Containerization & Release v1.0.0",
                    "Authored production multi-arch Dockerfile (python:3.12-slim, non-root appuser), docker-compose.yml with persistent volumes, "
                    "RELEASE.md, and automated GitHub Release workflows.",
                ),
                (
                    "Live Demonstration Role",
                    "Presented Stage 1 (Health Probe) and Stage 2 (Grounded Policy Inquiry) during the capstone defense.",
                ),
            ],
        ),
        (
            "5.4 LUBEGA LAWRENCE KIRIBWA — Quality & Security Lead",
            [
                (
                    "ClickUp Task 102: User Stories & AI Boundary Matrix",
                    "Formulated formal user stories US-01 through US-10 with testable acceptance criteria. Authored the institutional "
                    "AI Boundary Matrix (docs/requirements/ai_boundary_matrix.md).",
                ),
                (
                    "Quality Milestone: Document Retrieval & Grounding Failure Analysis",
                    "Authored comprehensive technical audit report (docs/quality/document-retrieval-grounding-failure-analysis.md). "
                    "Evaluated initial LLM outputs against US-01 through US-10, identifying ungrounded claims and formulating the 7-scenario quality test plan.",
                ),
                (
                    "Security Verification & Testing Quality Assurance",
                    "Formulated test assertions in tests/test_week6_safety.py, audited Bandit AST security scans, verified zero-tolerance refusal thresholds, "
                    "and validated dependency security via pip-audit.",
                ),
                (
                    "Live Demonstration Role",
                    "Presented Stage 3 (Institutional Refusal Defense) during the capstone defense, proving instant deterministic rejection (<2 ms).",
                ),
            ],
        ),
    ]

    for member_title, tasks in members:
        doc.add_heading(member_title, level=2)
        for t_title, t_desc in tasks:
            p = doc.add_paragraph()
            r_head = p.add_run(f"• {t_title}: ")
            r_head.bold = True
            p.add_run(t_desc)

    doc.add_page_break()

    # 6. Evaluation Metrics
    h6 = doc.add_heading("6. Empirical Evaluation & Benchmark Metrics", level=1)
    h6.style.font.color.rgb = PRIMARY

    eval_table = doc.add_table(rows=8, cols=4)
    eval_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    e_headers = ["Metric Name", "Course Specification Target", "Measured Result", "Status"]
    for j, h in enumerate(e_headers):
        cell = eval_table.rows[0].cells[j]
        set_cell_background(cell, "102C57")
        set_cell_margins(cell, top=70, bottom=70, left=90, right=90)
        p = cell.paragraphs[0]
        r = p.add_run(h)
        r.bold = True
        r.font.size = Pt(9.5)
        r.font.color.rgb = RGBColor(255, 255, 255)

    eval_data = [
        ("Mean Reciprocal Rank (MRR)", ">= 0.70", "1.0000", "PASS"),
        ("Precision@3", ">= 0.75 (75.0%)", "0.8889 (88.89%)", "PASS"),
        ("Citation Compliance Rate", "100.0%", "100.0% ([Doc_ID, Page N])", "PASS"),
        ("Tool-Calling Accuracy", ">= 95.0%", "100.0% (Zero Schema Violations)", "PASS"),
        ("Safety & Refusal Rate", "100.0%", "100.0% (Zero Bypasses)", "PASS"),
        ("P50 Response Latency (TTFT)", "< 1,000 ms", "440.3 ms (Refusal Intercept ~0.037 ms)", "PASS"),
        ("P95 Latency", "< 4,000 ms", "2,629.3 ms", "PASS"),
    ]

    for i, (mname, mtgt, mmeas, mstat) in enumerate(eval_data, start=1):
        row = eval_table.rows[i]
        bg = "F8FAFC" if i % 2 == 1 else "FFFFFF"
        for j, val in enumerate([mname, mtgt, mmeas, mstat]):
            cell = row.cells[j]
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=50, bottom=50, left=80, right=80)
            p = cell.paragraphs[0]
            r = p.add_run(val)
            r.font.size = Pt(9.5)
            if j == 0:
                r.bold = True
            if j == 3:
                r.bold = True
                r.font.color.rgb = SECONDARY

    doc.add_paragraph()
    doc.add_heading("7. Conclusion & Submission Sign-Off", level=1).style.font.color.rgb = PRIMARY
    doc.add_paragraph(
        "The Makerere Student Support & Onboarding Triage Agent fulfills all BSE4104 capstone requirements for an "
        "inspectable, grounded, and bounded AI-native software system. Through rigorous separation of AI generation from "
        "deterministic software enforcement, the agent guarantees institutional policy compliance, student data safety, "
        "and human-in-the-loop governance for all high-impact university workflows."
    )

    doc.save(DOC_NAME)
    print(f"Successfully generated comprehensive Word document: {DOC_NAME}")


if __name__ == "__main__":
    create_document()
