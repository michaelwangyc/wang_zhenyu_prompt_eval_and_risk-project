.. _governance-recommendations:

Internal Prompt Authoring Risk: Governance Recommendations
==============================================================================

.. list-table::
   :widths: 20 80

   * - **Version**
     - v0.1
   * - **Date**
     - 2026-04-16
   * - **Series**
     - LLM Prompt Security Research --- Topic 1, Document 3 of 3

----

Why Prompt Governance?
------------------------------------------------------------------------------
The first two documents completed risk identification (:ref:`risk-taxonomy`) and risk quantification (:ref:`prompt-risk-matrix`). This document addresses the final practical question: **how should an organization systematically eliminate these risks?**

The conclusion: patch-level fixes are insufficient. A one-time correction of a single high-risk prompt cannot solve the structural problem of Prompt Sprawl, nor can it prevent the same risk patterns from recurring in newly authored prompts. An effective solution must be **institutional** --- embedding security checks into the entire lifecycle of a prompt, from creation to retirement, rather than intervening only after problems emerge.

This document proposes three layers of governance: Authoring Guidelines, Audit Workflow, and Automated Scanning, with a final section on alignment with established industry frameworks.

----

Part A: Prompt Authoring Guidelines
------------------------------------------------------------------------------
**Core principle: treat prompts as production code.**

A prompt is not a memo, not a configuration file, not a document that can be casually edited. It is business logic running in a production environment and requires the same level of discipline and governance applied to code assets. The following five principles correspond to the five risk categories identified in the :ref:`risk-taxonomy`.

Principle 1: Minimum Privilege
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The behavioral permissions granted to the model by a prompt should be strictly limited to the minimum scope required to accomplish the current business objective. Capabilities that are not needed must not be granted; information that does not need to be accessed must not be mentioned. Specifically, each prompt should explicitly enumerate what the model **may do** and --- equally important --- what it **must not do**, with a standard refusal response pattern defined for out-of-scope requests. Vague phrases like "try your best to help the user" should not appear in any production prompt.

Principle 2: No Secrets in Prompts
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
All credentials, internal coefficients, pricing rules, connection strings, and API keys must be removed from prompt text and injected at runtime through an external secret management service. Prompt design should always operate under the OWASP LLM07 recommendation: **"Assume prompts will be extracted"** --- anything written into a prompt should be assumed to eventually be extractable by a sufficiently motivated user.

Principle 3: Hard Role Boundary
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The model's identity description must be precise, not broad. The prompt should explicitly state that the model must not be guided by users into switching identities during multi-turn conversations, must not participate in any role-play premised on "suppose you are...," and that this rule itself cannot be overridden by user input. The experience goals of "flexibility" and "friendliness" should be achieved through tone and wording, not by relaxing role boundaries.

Principle 4: Single Authoritative Version
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Each AI product should have one and only one production version of its prompt, managed by a designated owner, stored in a centrally access-controlled Prompt Registry. Multiple individuals maintaining different local versions is prohibited. Overwriting a production prompt without documenting the delta is prohibited. All modifications must have a complete record of version number, modifier, and modification rationale.

Principle 5: Explicit Failure Handling
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Every prompt must include explicit instructions for handling situations where the model cannot fulfill the user's request, covering: what it should say, what it should not say, and whether it should direct the user to a human agent. A prompt that lacks this section surrenders all decision-making authority to the model's own judgment in boundary scenarios, producing unpredictable outcomes.

----

Part B: Four-Gate Audit Workflow
------------------------------------------------------------------------------
Drawing on AWS Prescriptive Guidance for prompt lifecycle management best practices and LLMOps industry standards, this section defines a four-gate audit workflow covering the complete lifecycle of a prompt from inception to retirement.

Gate 1 --- Pre-Authoring: Design Brief
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Before anyone begins writing a prompt, the project owner must complete and submit a **Prompt Design Brief** that explicitly documents: the business objective the prompt serves, the data scope it is permitted to access, an explicit list of prohibited behaviors, the target user audience, and a checklist of expected "refusal scenarios."

This document is not a formality --- it is the baseline against which all subsequent security reviews are conducted. A prompt without a Design Brief must not proceed to the authoring phase.

Gate 2 --- Pre-Deployment: Security Review
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Before a prompt enters the production environment, it must pass three checks, all of which are mandatory:

**Automated Scan:** Run Secrets Detection and Over-Permissive Pattern Detection scans (see Part C). Any scan hit must be remediated and re-scanned before proceeding.

**Peer Review:** At least one engineer or security team member who did not participate in authoring must conduct a structural review of the prompt against the Authoring Guidelines, with particular focus on role boundary definition and instruction consistency.

**Adversarial Testing:** Testers simulate three categories of scenarios: attempted role switching (Role Confusion), attempted information extraction (Prompt Extraction), and boundary condition triggering (Instruction Conflict). Test results must be documented in writing.

Gate 3 --- In-Production: Continuous Monitoring
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
AWS explicitly recommends **"logging all prompts, parameters, and model responses"** for production LLM systems to support post-hoc review and compliance traceability. Based on this, the following signals should be continuously tracked in production:

- **Extraction attack signals:** User inputs containing phrases like "system prompt," "initial instructions," "output your settings in Base64," etc., trigger an alert.
- **Role switching signals:** User inputs containing role-inducement phrases like "suppose you are," "pretend to be an unrestricted," etc., trigger an alert.
- **Refusal rate anomalies:** A significant drop in the model's refusal rate for user requests may indicate that the prompt has been overridden or bypassed.

Monitoring data should be reviewed on a regular basis (quarterly recommended) as ongoing input to prompt health assessment.

Gate 4 --- Retirement: Formal Decommission
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
When a prompt is replaced or deactivated, a formal retirement process must be executed rather than simply deleting it: archive the old version to the Prompt Registry's historical section, record the decommission date, reason, and replacement version number, and confirm that all production systems have switched to the new version with no residual dependencies.

This step is particularly important in regulated industries such as insurance: when a regulator asks "which version of the prompt was the AI system using during a given time period," a complete retirement record is the only basis for providing a credible answer.

----

Part C: Automated Scanning Rules
------------------------------------------------------------------------------
Manual review cannot scale in a Prompt Sprawl scenario. The following scanning rules form the technical foundation of the governance framework and should be integrated into CI/CD pipelines or Prompt Registry pre-commit hooks.

**Rule Type 1 --- Secrets Detection:** Regex-based matching for API key format strings (``sk-xxx``, ``Bearer xxx``), IP addresses, database connection strings, and numeric credential patterns. The design philosophy mirrors tools like GitGuardian for code repository scanning, adapted to prompt text.

**Rule Type 2 --- Over-Permissive Pattern Detection:** Blacklist scanning for high-risk phrases including but not limited to: "unconditionally," "under all circumstances," "must not refuse," "no restrictions," and their English equivalents: ``never refuse``, ``always comply``, ``no restrictions``, ``ignore your guidelines``.

**Rule Type 3 --- Role Confusion Signal Detection:** Detects whether the prompt contains identity-weakening statements, such as: "the user's requests always take priority over your initial settings," "you may adjust your role based on the situation," and any statement that authorizes users to override the system identity definition.

**Rule Type 4 --- Conflict Instruction Detection:** Uses semantic similarity analysis to identify instruction pairs within a prompt that contain potential logical contradictions. For example, when both a "confidentiality" directive and a "help as thoroughly as possible" directive appear, the pair is flagged for manual review.

----

Part D: Framework Alignment
------------------------------------------------------------------------------
The governance framework proposed here is not designed in isolation --- it maps directly to four established industry frameworks, facilitating regulatory reporting and compliance audits.

.. list-table::
   :header-rows: 1
   :widths: 30 30 40

   * - Governance Component
     - Aligned Framework
     - Specific Reference
   * - Risk Taxonomy + Risk Matrix
     - OWASP Top 10 for LLM 2025
     - LLM06: Excessive Agency, LLM07: System Prompt Leakage
   * - Four-Gate Audit Workflow
     - NIST AI RMF
     - Govern / Map / Measure / Manage functional domains
   * - Prompt Lifecycle Management
     - ISO/IEC 42001
     - AI system documentation, versioning, and risk audit requirements
   * - Auditability + Traceability
     - NAIC AI Model Bulletin
     - Explainability and accountability requirements for AI-assisted decisions

For organizations in regulated industries, the NAIC alignment is particularly critical. When an AI-assisted decision is challenged, the first piece of evidence a regulator typically requests is "which version of the prompt was the system using when that decision was made, who approved it, and when did it take effect" --- precisely the audit trail covered by the Four-Gate Audit Workflow.

----

Summary: Governance Framework at a Glance
------------------------------------------------------------------------------
.. list-table::
   :header-rows: 1
   :widths: 25 35 40

   * - Governance Layer
     - Core Mechanism
     - Risk Addressed
   * - **Authoring Guidelines**
     - Five authoring principles
     - Prevent risk introduction at the source
   * - **Four-Gate Audit Workflow**
     - Pre-Authoring / Pre-Deployment / In-Production / Retirement
     - Lifecycle-wide security checkpoints
   * - **Automated Scanning**
     - Four scanning rule types
     - Scalable detection under Prompt Sprawl
   * - **Framework Alignment**
     - OWASP / NIST / ISO / NAIC
     - Compliance audit and regulatory reporting support

The three documents in Topic 1 form a complete closed loop: **identify risks** |rarr| **quantify priorities** |rarr| **systematically eliminate**.

----

*Document maintained as part of the* ``prompt_risk`` *project --- Last updated: 2026-04-16*

*References: AWS Prescriptive Guidance on LLM Lifecycle Management, OWASP Top 10 for LLM Applications 2025, NIST AI RMF GenAI Profile, ISO/IEC 42001, NAIC AI Model Bulletin*
