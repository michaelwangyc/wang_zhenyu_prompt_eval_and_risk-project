.. _use-case-catalog:

Use Case Catalog: AI Applications with Prompt Exposure in Insurance
==============================================================================

.. list-table::
   :widths: 20 80

   * - **Version**
     - v0.2 Draft
   * - **Date**
     - 2026-04-22
   * - **Purpose**
     - Define six representative AI application patterns deployed within an insurance enterprise, each involving distinct prompt architectures and risk profiles. This document serves as an index — each use case will be expanded into a dedicated document with full prompt specifications and risk analysis.

----

Overview
------------------------------------------------------------------------------
A large-scale insurance company operates AI-powered applications across its value chain — from policy quoting and underwriting to claims handling, legal review, and customer engagement. These applications vary significantly in their **architecture** (single-turn vs. multi-step orchestration, retrieval-augmented vs. tool-augmented), **autonomy level** (human-in-the-loop vs. fully autonomous), and **exposure surface** (internal-only vs. customer-facing, static data vs. live external data).

To systematically analyze prompt-level risks, we define six use cases that collectively cover the spectrum of LLM integration patterns found in insurance operations. Each use case is grounded in a specific business function and describes:

- **Business context** — What the application does and who uses it
- **Architecture pattern** — How the LLM is orchestrated (single call, chained calls, RAG, agent loop, etc.)
- **Prompt inventory** — Which prompts exist in the system, where they act, and what risks they carry
- **Data flow** — What data enters the LLM context and from which sources

The six use cases are ordered by increasing architectural complexity:

.. list-table::
   :header-rows: 1
   :widths: 5 25 25 25 20

   * - #
     - Use Case
     - Architecture Pattern
     - Business Function
     - User Type
   * - 1
     - Multi-Step Claim Intake Processing
     - LLM Orchestration (chained pipeline)
     - Claims — FNOL Processing
     - Internal adjuster
   * - 2
     - Underwriting Knowledge Assistant
     - RAG over internal knowledge base
     - Underwriting
     - Internal underwriter
   * - 3
     - Commercial Client Risk Profiling Agent
     - Web-fetch research agent
     - Commercial Underwriting — Pre-Bind Risk Assessment
     - Internal underwriter
   * - 4
     - Litigation Support Agent
     - Autonomous agent with basic tools
     - Claims — Litigated Claims
     - Internal claims attorney
   * - 5
     - Claims Automation Agent
     - Advanced autonomous agent with privileged tools
     - Claims Operations
     - System (automated)
   * - 6
     - Policyholder Self-Service AI
     - Customer-facing conversational agent
     - Customer Service
     - External policyholder

----

Use Case 1: Multi-Step Claim Intake Processing
------------------------------------------------------------------------------

**Pattern:** LLM Orchestration — Chained Multi-Step Pipeline

Business Context
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
When a policyholder reports a loss (First Notice of Loss — FNOL), the incoming information arrives in unstructured form: a phone transcript, a web form narrative, uploaded photos, and supporting documents. Before a human adjuster can begin working the claim, this raw input must be transformed into a structured claim record — categorized by line of business, assessed for severity, checked for coverage applicability, and routed to the appropriate handling team.

This application automates the FNOL intake pipeline. It is used by **internal claims staff** who review and approve the structured output before it enters the claims management system.

Architecture
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The application is a **deterministic multi-step LLM pipeline** — a fixed sequence of LLM calls where the output of each step feeds into the next. There is no autonomous decision-making; the orchestration logic is hardcoded in application code. Each step calls the LLM with a different prompt tailored to a specific subtask.

- **Step 1: Information Extraction** — Prompt A parses raw FNOL narrative into structured fields
- **Step 2: Line of Business Classification** — Prompt B determines LoB (auto, property, GL, workers' comp, etc.) based on extracted fields
- **Step 3: Severity & Priority Triage** — Prompt C assigns severity level and handling priority
- **Step 4: Coverage Applicability Check** — Prompt D cross-references claim details against policy coverage rules
- **Step 5: Summary & Routing** — Prompt E generates a claim summary and recommends the handling unit
- **Output** — Structured Claim Record sent to human review

Each step's output feeds directly into the next step's input, forming a linear chain.

Prompt Inventory
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 15 20 20 45

   * - Prompt
     - Role in Workflow
     - Input Sources
     - Primary Risk
   * - **Prompt A — Extraction Prompt**
     - Parses raw FNOL narrative into structured fields (date of loss, location, parties involved, damage description, injury indicators)
     - Customer-submitted text, phone transcripts
     - **Prompt injection** — customer-submitted content is the primary injection surface; malicious instructions embedded in FNOL text could manipulate extracted fields, poisoning all downstream steps
   * - **Prompt B — Classification Prompt**
     - Determines line of business (auto, property, general liability, workers' comp, etc.) based on extracted fields
     - Output of Prompt A
     - **Chain propagation** — if Prompt A's output is compromised by injection, the corrupted fields flow here unchecked, potentially forcing misclassification
   * - **Prompt C — Triage Prompt**
     - Assigns severity level (1–5) and handling priority based on damage indicators, injury presence, and estimated exposure
     - Output of Prompts A + B
     - **Chain propagation** — severity manipulation via upstream corruption; an attacker who controls extraction output can engineer a lower severity score to reduce scrutiny
   * - **Prompt D — Coverage Check Prompt**
     - Cross-references extracted claim details against policy coverage rules to flag potential coverage issues
     - Output of Prompt A + policy summary data from internal systems
     - **Hardcoded sensitive data** — if policy coverage rules or internal decision thresholds are embedded directly in the prompt, they become extractable; also inherits injection risk from Prompt A's output
   * - **Prompt E — Routing Prompt**
     - Generates a human-readable claim summary and recommends the appropriate handling unit and adjuster skill level
     - Output of all previous steps
     - **Accumulated chain risk** — this prompt consumes all upstream outputs, meaning any injection or corruption from Steps 1–4 culminates here and shapes the final recommendation seen by human reviewers

Key Characteristics
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- **Fixed orchestration** — No LLM autonomy; the pipeline sequence is determined by application code.
- **Prompt chaining risk** — Errors or injections in early steps propagate and amplify through downstream prompts.
- **External data ingestion** — Prompt A directly processes customer-submitted content, making it the primary injection surface.
- **Internal reference data** — Prompt D incorporates policy data from internal systems, introducing hardcoded-data risk if policy rules are embedded in the prompt.

----

Use Case 2: Underwriting Knowledge Assistant
------------------------------------------------------------------------------

**Pattern:** Retrieval-Augmented Generation (RAG) over Internal Knowledge Base

Business Context
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Insurance underwriting requires deep expertise across product lines — commercial property, general liability, professional liability, marine, cyber, and more. Underwriters must constantly reference internal guidelines, appetite documents, rate filings, reinsurance treaties, and regulatory bulletins. Historically, this knowledge is scattered across SharePoint sites, PDF manuals, and tribal expertise.

This application provides underwriters with a **conversational knowledge assistant** that answers questions by retrieving relevant content from an internal knowledge base and synthesizing a response. It is used by **internal underwriters** during the quoting and risk evaluation process.

Architecture
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The application follows the standard **RAG pattern**:

- **Step 1: Query Processing** — Prompt F rewrites the underwriter's question into an optimized retrieval query
- **Step 2: Vector Store Retrieval** — No LLM involved; embedding similarity search retrieves top-k document chunks from the internal knowledge base
- **Step 3: Response Generation** — Prompt G synthesizes an answer from the retrieved passages and the original question
- **Output** — Answer with source citations delivered to the underwriter

Prompt Inventory
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 15 20 20 45

   * - Prompt
     - Role in Workflow
     - Input Sources
     - Primary Risk
   * - **Prompt F — Query Rewrite Prompt**
     - Transforms the underwriter's natural language question into an optimized retrieval query (keyword expansion, disambiguation)
     - User question (internal employee)
     - **Low direct risk** — input is from a trusted internal user; however, a poorly designed rewrite prompt could inadvertently broaden retrieval scope, pulling in irrelevant or sensitive documents
   * - **Prompt G — RAG System Prompt**
     - Defines the assistant's identity, behavior constraints, citation requirements, and instructions for synthesizing an answer from retrieved passages
     - Static system prompt + dynamically retrieved document chunks + user question
     - **Indirect prompt injection via knowledge base** — if any indexed document contains adversarial content (planted or accidentally ingested), it enters the LLM context through retrieval and can override system instructions; also risks **sensitive data leakage** if the prompt fails to restrict verbatim quoting of proprietary underwriting guidelines, pricing logic, or reinsurance terms

Key Characteristics
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- **Knowledge base as attack surface** — If any indexed document contains adversarial content (whether planted or accidentally ingested), it enters the LLM context via retrieval, creating an **indirect prompt injection** vector.
- **Sensitive internal content** — Retrieved passages may contain proprietary underwriting guidelines, pricing logic, risk appetite thresholds, or reinsurance terms. The RAG System Prompt must enforce boundaries on what the model can quote verbatim vs. summarize.
- **Single-turn interaction** — Each question is independent; no multi-turn planning or tool use.
- **Source attribution** — The prompt must instruct the model to cite specific source documents, adding complexity around hallucination control.

----

Use Case 3: Commercial Client Risk Profiling Agent
------------------------------------------------------------------------------

**Pattern:** Web-Fetch Research Agent with External Data Gathering

Business Context
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
When underwriting a new commercial insurance policy — whether for a manufacturing plant, a restaurant chain, a construction contractor, or a technology company — underwriters need to assess the prospective client's risk profile beyond what the application form provides. This includes the company's financial health, litigation history, regulatory violations, safety records, news coverage, customer complaints, and industry-specific risk factors.

Traditionally, underwriters manually search public databases, news sites, court records, and regulatory filings. This application automates that process: given a prospective commercial client's identity, the agent autonomously searches the open web to gather publicly available information and produces a **structured risk assessment report**. It is used by **internal underwriters** during the pre-bind evaluation of commercial accounts.

Architecture
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The agent operates in a **research loop** tailored to risk assessment:

- **Step 1: Research Planning** — Prompt H analyzes the client profile (company name, industry, location, requested coverage) and generates a targeted search plan covering relevant risk dimensions (financial, legal, regulatory, operational, reputational)
- **Step 2: Web Search & Fetch** — The agent executes web searches and fetches relevant pages (news articles, court records, regulatory filings, review sites, financial reports)
- **Step 3: Content Analysis** — Prompt I extracts risk-relevant facts and signals from each fetched page
- **Step 4: Sufficiency Check** — Prompt J evaluates whether enough information has been gathered across all risk dimensions, or if additional targeted searches are needed; if more data is needed, the loop returns to Step 2
- **Step 5: Risk Report Synthesis** — Prompt K compiles findings into a structured risk profiling report with risk indicators, confidence levels, and source citations
- **Output** — Structured Risk Assessment Report sent to underwriter review

Prompt Inventory
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 15 20 20 45

   * - Prompt
     - Role in Workflow
     - Input Sources
     - Primary Risk
   * - **Prompt H — Research Planner Prompt**
     - Decomposes the client profile into specific search queries across risk dimensions (financial stability, litigation history, OSHA violations, environmental compliance, news sentiment, etc.)
     - Client profile from underwriting submission (internal)
     - **Over-permissive search scope** — if the prompt does not strictly bound which types of information are relevant, the agent may search for and surface information that is legally impermissible to use in underwriting decisions (e.g., protected class information, certain types of consumer data)
   * - **Prompt I — Content Analysis Prompt**
     - Extracts risk-relevant facts, red flags, and data points from a fetched web page and assesses their relevance and reliability
     - Raw web page content (external, untrusted)
     - **Indirect prompt injection** — adversarial content on public web pages (invisible text, SEO-manipulated content, competitor disinformation) directly enters the LLM context and could manipulate the risk assessment; a company under investigation could plant favorable content designed to be picked up by AI crawlers
   * - **Prompt J — Sufficiency Evaluation Prompt**
     - Determines whether findings adequately cover all required risk dimensions or if additional searches are needed
     - Aggregated findings from previous iterations
     - **Research steering** — if an early-stage injection biases the accumulated findings, this prompt may conclude that "enough positive information" has been gathered and terminate the loop prematurely, producing an incomplete risk picture
   * - **Prompt K — Risk Report Synthesis Prompt**
     - Compiles all gathered findings into a structured risk profiling report with risk level indicators, confidence scores, and source attribution
     - All accumulated analysis results
     - **Biased synthesis** — the prompt must reconcile potentially contradictory signals from multiple external sources; injection-influenced intermediate findings could skew the final risk rating, directly affecting underwriting decisions and pricing

Key Characteristics
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- **Uncontrolled external content** — The agent fetches arbitrary web pages, making every fetched page a potential **indirect prompt injection** vector. A company seeking favorable insurance terms could manipulate its public web presence to influence the AI's risk assessment.
- **Iterative autonomy** — The agent decides how many searches to conduct and when to stop, introducing a feedback loop where early-stage injection could steer subsequent search behavior.
- **No privileged tool access** — The agent can search and read, but cannot modify any internal system. Impact is limited to **information integrity** — producing a biased risk assessment that leads to mispriced policies or undetected risk concentrations.
- **Regulatory sensitivity** — Underwriting decisions are subject to state insurance regulations. If the agent surfaces or relies on legally impermissible information (even from public sources), it creates compliance exposure.

----

Use Case 4: Litigation Support Agent
------------------------------------------------------------------------------

**Pattern:** Autonomous Agent with Basic Tool Access

Business Context
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Insurance and litigation are inseparable. When liability claims are disputed, injury claims escalate, or coverage disagreements arise, claims move into litigation — and insurers become direct participants. An insurer's claims legal team manages thousands of litigated cases simultaneously, each involving large volumes of documents: pleadings, depositions, medical records, expert reports, settlement demands, and years of correspondence. Efficient case analysis directly impacts litigation outcomes and reserve accuracy, making it a core insurance function.

This application is a **litigation support agent** that helps internal claims attorneys analyze litigated claim files. Given a legal question or task — such as "summarize the liability exposure in this case" or "identify all medical treatment gaps in the claimant's records" — it autonomously plans an approach, reads relevant documents from the case file, and produces structured analysis. It has access to a small set of **read-only tools** for navigating the document repository. It is used by **internal claims legal staff**.

Architecture
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The agent follows an **autonomous plan-and-execute loop** with access to basic read-only tools. Unlike Use Case 3 (which fetches external web content), this agent works exclusively with internal case documents accessed through controlled tool interfaces.

- **Step 1: Task Planning** — Prompt L analyzes the attorney's question and creates a step-by-step investigation plan (which documents to review, what to look for)
- **Step 2: Execution Loop** — Prompt M governs each iteration: selects a tool, interprets results, decides the next step

  - Available tools: ``search_case_files``, ``read_document``, ``list_case_documents``, ``get_document_metadata``
  - Loop continues until the agent determines the task is complete or requires escalation

- **Step 3: Response Synthesis** — Prompt N compiles findings into a structured legal analysis with citations and risk assessment
- **Output** — Structured Legal Analysis sent to attorney review

Prompt Inventory
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 15 20 20 45

   * - Prompt
     - Role in Workflow
     - Input Sources
     - Primary Risk
   * - **Prompt L — Litigation Planner Prompt**
     - Analyzes the attorney's question and creates a step-by-step plan for which documents to review and what to look for
     - Attorney question (internal)
     - **Planning manipulation via document content** — while the initial input is trusted (internal attorney), the plan itself may be influenced by document titles or metadata that contain adversarial content from external parties (e.g., opposing counsel's strategically named filings)
   * - **Prompt M — Agent Reasoning Prompt**
     - Core agent loop prompt that governs tool selection, result interpretation, and next-step reasoning. Defines available tools, their usage rules, and the agent's behavioral constraints
     - Attorney question + plan + tool results (internal documents containing external-origin content)
     - **Indirect injection via case documents** — litigated claim files contain documents from opposing counsel, claimants, medical providers, and experts — all external parties. Adversarial instructions embedded in these documents (e.g., a demand letter with hidden text) enter the LLM context when the agent reads them, potentially steering the agent to overlook unfavorable evidence or over-weight favorable arguments
   * - **Prompt N — Legal Analysis Synthesis Prompt**
     - Compiles findings from multiple document reviews into a structured legal analysis with citations and risk assessment
     - Accumulated tool results and intermediate reasoning
     - **Biased output** — if the agent's investigation was steered by document-borne injection, the synthesis will reflect that bias, potentially leading to inaccurate liability assessments or flawed settlement recommendations with direct financial consequences

Key Characteristics
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- **Read-only tool access** — The agent can search and read documents but cannot modify, delete, or transmit anything. This limits the blast radius of any prompt-related failure to **information output quality**.
- **Internal repository, external-origin content** — The document repository is internal and managed, but many documents within it originate from external parties (opposing counsel pleadings, claimant statements, third-party medical records). This creates a subtle but real injection surface.
- **Autonomous planning** — The agent decides its own investigation path, meaning a compromised reasoning step could lead it to ignore critical documents or over-weight favorable ones.
- **High-stakes output** — Legal analysis directly informs litigation strategy, reserve adequacy, and settlement authority decisions. Inaccurate or manipulated output carries significant financial and legal consequences.

----

Use Case 5: Claims Automation Agent
------------------------------------------------------------------------------

**Pattern:** Advanced Autonomous Agent with Privileged Tool Access

Business Context
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
For high-volume, lower-complexity claims (e.g., auto glass replacement, minor property damage, straightforward medical payments), insurers seek to automate end-to-end processing — from intake through investigation to resolution — with minimal human intervention. This reduces cycle time, improves customer experience, and frees adjusters to focus on complex claims.

This application is an **advanced claims automation agent** that can autonomously investigate a claim and take actions in enterprise systems. Unlike Use Case 4 (read-only tools), this agent has **write access to production systems** and can trigger real-world business outcomes. It operates as a **system-level automated process** with human oversight at defined checkpoints.

Architecture
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The agent operates with a **rich tool set** that includes both read and write capabilities across multiple enterprise systems. It follows an autonomous plan-execute-verify loop with escalation logic.

- **Step 1: Claim Assessment & Planning** — Prompt O (the master system prompt) defines the agent's identity, authority boundaries, escalation rules, and compliance constraints. The agent reviews the incoming claim and formulates an investigation plan.
- **Step 2: Execution Loop** — Prompt P governs each iteration: selects a tool, interprets results, decides the next action or escalation.

  - Read tools: ``query_policy_database``, ``query_claims_history``, ``retrieve_claimant_profile``, ``search_fraud_indicators``
  - Read/write tools: ``request_vendor_estimate`` (external vendor API)
  - Write tools: ``update_claim_status``, ``set_reserve_amount``, ``schedule_inspection``, ``issue_payment``, ``escalate_to_adjuster``, ``send_claimant_notification``, ``log_investigation_notes``
  - Loop continues until the agent reaches a resolution or escalation decision.

- **Step 3: Resolution & Documentation** — Prompt Q generates the final claim resolution documentation, including decision rationale, payment justification, and compliance attestation.
- **Output** — Claim resolved or escalated, with full audit log.

Prompt Inventory
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 15 20 20 45

   * - Prompt
     - Role in Workflow
     - Input Sources
     - Primary Risk
   * - **Prompt O — Claims Agent System Prompt**
     - Master system prompt defining the agent's identity, authority boundaries, escalation rules, compliance constraints, and the complete tool inventory with usage policies
     - Static configuration
     - **Over-permissive authorization / instruction conflict** — this is the most complex system prompt in the catalog; if authority boundaries are vaguely defined or if escalation rules conflict with efficiency directives, the agent may authorize actions (e.g., payments, status changes) beyond intended limits
   * - **Prompt P — Agent Reasoning Prompt**
     - Governs each iteration of the agent loop: which tool to call next, how to interpret results, when to escalate vs. proceed autonomously, and how to handle ambiguous or conflicting data
     - Claim data + tool results (mix of internal systems and external vendor responses)
     - **Indirect injection via external data + privileged action abuse** — vendor estimate responses and claimant-submitted materials enter the agent's context and could carry adversarial content; unlike UC3/UC4 where injection only affects information quality, here it could trigger unauthorized write actions (e.g., a manipulated vendor response that causes the agent to issue an inflated payment)
   * - **Prompt Q — Resolution Prompt**
     - Generates the final claim resolution documentation, including decision rationale, payment justification, and compliance attestation
     - All accumulated investigation data and reasoning
     - **Compliance risk** — if upstream reasoning was influenced by injection or the system prompt has authorization gaps, this prompt will generate documentation that rationalizes a flawed decision, creating a misleading audit trail that could fail regulatory scrutiny

Key Characteristics (Contrast with Use Case 4)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 20 40 40

   * - Dimension
     - Use Case 4 (Litigation Support)
     - Use Case 5 (Claims Automation)
   * - **Tool access**
     - 4 read-only tools on a single system
     - 11+ tools across multiple systems, including write operations
   * - **System scope**
     - Single document repository
     - Policy DB, claims system, fraud detection, vendor APIs, payment system, notification service
   * - **Action consequences**
     - Output is advisory — attorney decides
     - Agent can issue payments, update records, and notify claimants directly
   * - **Autonomy level**
     - Plans and researches; human synthesizes conclusions
     - Plans, investigates, decides, and executes with checkpoint-based human oversight
   * - **Failure blast radius**
     - Flawed analysis (fixable)
     - Unauthorized payment, incorrect reserve, missed fraud, regulatory violation
   * - **External data exposure**
     - Opposing counsel documents (within case file)
     - Vendor API responses, claimant-submitted materials, fraud database results

- **Privileged write access** — The agent can trigger irreversible business actions (payments, status changes, notifications). Prompt vulnerabilities here have **direct financial and operational consequences**.
- **Multi-system integration** — Data flows from and actions execute against multiple enterprise systems, each with its own trust boundary. The prompt must correctly enforce which tools are appropriate for which situations.
- **External data injection surface** — Vendor estimate responses and claimant-submitted materials enter the agent's context and could carry adversarial content designed to influence claim outcomes.
- **Compliance-critical decisions** — Every action must be explainable and auditable. The Resolution Prompt must produce documentation that satisfies regulatory scrutiny.

----

Use Case 6: Policyholder Self-Service AI
------------------------------------------------------------------------------

**Pattern:** Customer-Facing Conversational Agent

Business Context
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Policyholders interact with their insurer for a wide range of needs: checking policy details, filing claims, requesting certificates of insurance, understanding coverage, updating personal information, and asking billing questions. Traditionally these interactions flow through call centers, web portals, or local agents.

This application is a **customer-facing AI agent** embedded in the insurer's website, mobile app, and messaging channels. It is the first point of contact for **external policyholders** — the general public — and must handle a vast range of intents while maintaining strict brand, compliance, and security standards.

Architecture
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The agent operates as a **multi-turn conversational system** with access to customer-specific data via authenticated API calls. It combines intent classification, data retrieval, and response generation in a controlled dialogue flow.

- **Step 1: Intent Classification & Safety Screening** — Prompt R classifies the customer's message and performs initial safety checks
- **Step 2: Context Retrieval** — No LLM involved; API calls to the policy management system retrieve customer-specific data (policy details, claim status, billing info) based on the authenticated session
- **Step 3: Response Generation** — Prompt S generates a response using the customer's data, conversation history, and the classified intent
- **Step 4: Output Safety Filter** — Prompt T reviews the generated response before delivery
- **Output** — Filtered response delivered to the policyholder

Prompt Inventory
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 15 20 20 45

   * - Prompt
     - Role in Workflow
     - Input Sources
     - Primary Risk
   * - **Prompt R — Intent Router Prompt**
     - Classifies the customer's message into a predefined intent category and performs initial safety screening (detecting prompt injection attempts, abusive content, or out-of-scope requests)
     - Customer message (external, untrusted)
     - **Direct prompt injection bypass** — this is the first line of defense; if the injection detection logic in this prompt can be bypassed (e.g., via encoding tricks, multilingual obfuscation, or multi-turn gradual escalation), all downstream processing operates on unsanitized input
   * - **Prompt S — Conversational Agent System Prompt**
     - Master system prompt defining the agent's persona, tone, compliance boundaries (what it can/cannot disclose), escalation triggers (when to route to a human agent), and response formatting rules
     - Static system prompt + customer-specific data from APIs + conversation history + customer message
     - **Role confusion / over-permissive authorization** — the most complex prompt in this application; must balance helpfulness with strict compliance boundaries; vague persona definitions or overly accommodating instructions could allow attackers to manipulate the agent into disclosing internal system details, quoting policy terms out of context, or providing advice that constitutes unauthorized practice of law or insurance
   * - **Prompt T — Output Guard Prompt**
     - Reviews the generated response before delivery to check for: accidental disclosure of internal system details, non-compliant language, hallucinated policy information, and prompt leakage
     - Generated response + original customer message
     - **Guard bypass / false sense of security** — the output guard is itself a prompt that can be influenced; if the adversarial content is crafted to appear benign at the output-review stage (e.g., leaking information through subtle phrasing rather than explicit statements), the guard may pass it through; also introduces its own prompt leakage risk

Key Characteristics
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- **Untrusted user input** — Every message comes from an external user with unknown intent. This is the **highest direct prompt injection exposure** of all six use cases.
- **Brand and compliance stakes** — Every response is delivered under the company's brand. Inappropriate, inaccurate, or manipulated responses directly impact customer trust and regulatory standing.
- **Multi-turn conversation** — Extended dialogue creates opportunities for **gradual context manipulation** — an attacker can slowly steer the conversation across multiple turns to bypass safety boundaries.
- **Output filtering layer** — The inclusion of a dedicated Output Guard Prompt (Prompt T) adds a defense layer but also introduces its own prompt — which itself must be secured against bypass.
- **No write actions** — The agent can retrieve customer data but cannot modify policies, process payments, or update records. Actions requiring changes are escalated to human agents or authenticated self-service portals.
- **Highest volume** — This is the most frequently invoked application, meaning even low-probability prompt failures will occur at scale.

----

Cross-Use-Case Comparison
------------------------------------------------------------------------------

.. list-table::
   :header-rows: 1
   :widths: 16 14 14 14 14 14 14

   * - Dimension
     - UC1 Pipeline
     - UC2 RAG
     - UC3 Web Research
     - UC4 Basic Agent
     - UC5 Advanced Agent
     - UC6 Customer-Facing
   * - **Autonomy**
     - None (fixed pipeline)
     - None (single-turn)
     - Moderate (search loop)
     - Moderate (plan + read)
     - High (plan + read/write)
     - Low (classification + response)
   * - **External data exposure**
     - Customer FNOL text
     - None (internal KB)
     - Web pages (fully untrusted)
     - External-origin docs in internal repo
     - Vendor APIs + claimant docs
     - Customer messages (untrusted)
   * - **Write access to systems**
     - No
     - No
     - No
     - No
     - Yes (payments, records, notifications)
     - No
   * - **User type**
     - Internal
     - Internal
     - Internal
     - Internal
     - System (automated)
     - External (public)
   * - **Prompt count**
     - 5
     - 2
     - 4
     - 3
     - 3
     - 3
   * - **Primary risk vector**
     - Injection via FNOL content; chain propagation
     - KB poisoning; sensitive data in retrieved context
     - Web content injection; research steering; regulatory compliance
     - Document-borne injection; planning manipulation
     - Privileged action abuse; multi-system injection
     - Direct prompt injection; brand/compliance violation

----

Next Steps
------------------------------------------------------------------------------
Each use case will be expanded into a dedicated document covering:

1. Detailed prompt specifications (purpose, structure, constraints)
2. Threat model (specific attack scenarios for each prompt)
3. Risk assessment using the Prompt Risk Matrix framework
4. Recommended mitigations mapped to the Governance framework

----

*Document maintained as part of the* ``prompt_risk`` *project — Last updated: 2026-04-22*
