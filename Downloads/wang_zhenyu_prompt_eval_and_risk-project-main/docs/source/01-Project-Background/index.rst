.. _project-background:

Project Background: LLM Prompt Risk Management for the Insurance Industry
==========================================================================

.. list-table::
   :widths: 20 80

   * - **Version**
     - v0.1
   * - **Date**
     - 2026-04-22
   * - **Status**
     - Draft

More project background docs:

.. autotoctree::
    :maxdepth: 1


----

1. Industry Context
------------------------------------------------------------------------------
The insurance industry — spanning commercial property, casualty, personal lines (homeowners, auto), specialty, and workers' compensation — is undergoing a rapid transformation driven by Artificial Intelligence. Large Language Models (LLMs) are being deployed across virtually every business function: underwriting assistants that evaluate risk profiles, claims processing agents that triage First Notice of Loss (FNOL) submissions, customer-facing chatbots that handle policy inquiries, legal review copilots that parse contract language, and internal knowledge assistants that help adjusters navigate complex guidelines.

As a result, a typical large-scale insurer now operates **dozens of AI-powered agent services** across its organization, each configured with internal prompts (System Prompts, Instruction Prompts) that define the agent's behavior, scope, and decision boundaries. These prompts are the invisible "operating code" behind every AI interaction — yet unlike traditional software code, they rarely undergo formal review, version control, or security auditing.

----

2. The Problem: Prompt as an Unmanaged Attack Surface
------------------------------------------------------------------------------
In a multi-line insurance company with numerous business units — commercial insurance, personal auto, homeowners, umbrella liability, marine, and more — each unit tends to independently build and configure its own AI agents. Product managers, operations staff, business analysts, and engineers all contribute to writing and modifying prompts, often without centralized oversight or security awareness.

This creates two categories of structural risk:

2.1 Internal Prompt Authoring Risk
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Prompts authored by internal employees can inadvertently (or intentionally) introduce security vulnerabilities. Common failure modes include:

- **Over-Permissive Authorization** — Vague instructions like "always help the user" that disable the model's ability to refuse inappropriate requests.
- **Hardcoded Sensitive Data** — Embedding proprietary pricing coefficients, underwriting rules, API keys, or internal business logic directly into prompt text, where it can be extracted by adversarial users.
- **Role Confusion** — Loosely defined agent identities that allow users to manipulate the model into adopting an unrestricted persona.
- **Instruction Conflict** — Contradictory directives accumulated from multiple stakeholders over time, leading to unpredictable model behavior at boundary conditions.
- **Logic Ambiguity** — Soft qualifiers ("usually," "try to avoid") that attackers can bypass by constructing plausible exception scenarios.

When multiplied across tens or hundreds of unaudited prompts — a phenomenon known as **Prompt Sprawl** — these risks compound exponentially.

2.2 Prompt Injection Risk (External Data Contamination)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Insurance AI systems routinely process external inputs: customer-submitted claim descriptions, medical reports, legal correspondence, uploaded documents (PDF, images via OCR), third-party database query results, and RAG (Retrieval-Augmented Generation) knowledge base content. Each of these data channels represents a potential vector for **Prompt Injection** — where malicious instructions hidden within ostensibly benign external data hijack the model's behavior.

In the insurance context, a motivated claimant or their attorney could embed adversarial instructions in submitted documents to influence AI-driven claim assessments, risk classifications, or settlement recommendations.

----

3. Why This Matters for Insurance
------------------------------------------------------------------------------
The insurance sector faces unique amplifiers for prompt-related risks:

- **Regulatory Compliance** — Insurance is heavily regulated (NAIC AI guidelines, state insurance regulations, GDPR, HIPAA for health-related claims). AI-assisted decisions must be explainable, auditable, and traceable. A prompt vulnerability that leads to a flawed claim decision creates regulatory exposure.
- **Financial Impact** — Manipulated AI outputs in underwriting or claims can directly translate to monetary loss — whether through fraudulent claim approvals, mispriced policies, or leaked proprietary actuarial models.
- **Reputational Risk** — An AI agent that leaks internal business rules or produces inappropriate responses under a company's brand causes lasting reputational damage.
- **Agentic Escalation** — As insurers move toward agentic AI (agents that can trigger payments, update case statuses, or initiate workflows), the consequences of prompt exploitation escalate from "influencing a recommendation" to "executing unauthorized actions."

----

4. What This Project Does
------------------------------------------------------------------------------
``prompt_risk`` is a Python-based software framework designed to systematically detect, assess, and mitigate prompt-level security risks in enterprise LLM deployments. Rather than relying solely on governance documents and manual review processes, this project provides **programmatic tooling** that integrates into the software development and deployment lifecycle.

Core Capabilities
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
1. **Automated Prompt Scanning** — Static analysis of prompt text to detect known risk patterns:

   - Secrets detection (API keys, credentials, connection strings, proprietary coefficients)
   - Over-permissive language pattern matching (e.g., "never refuse," "always comply," "no restrictions")
   - Role confusion signal detection (weak identity boundaries, user-overridable role definitions)
   - Instruction conflict identification via semantic analysis

2. **Risk Quantification** — A structured scoring framework (Exploitability, Impact, Detectability) that produces a **Prompt Risk Matrix**, enabling teams to prioritize which prompts require immediate remediation.

3. **LLM-as-Judge Evaluation** — Leveraging LLMs themselves to perform deeper semantic analysis of prompts — identifying subtle logic ambiguities, implicit permission escalations, and conflict patterns that rule-based scanning cannot catch.

4. **Lifecycle Integration** — Designed to plug into CI/CD pipelines, prompt registries, and pre-deployment gates, making prompt security a continuous and automated part of the development workflow rather than a one-time audit.

Technology Stack
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
- **Python** — Core implementation language, supporting Python 3.10+
- **LLM Integration** — Uses large language models for semantic-level prompt analysis (LLM-as-Judge pattern)
- **Rule Engine** — Regex and pattern-based scanning for deterministic risk detection
- **Extensible Architecture** — Designed as an installable Python package (``pip install prompt-risk``) for easy integration into existing toolchains

----

5. How It Fits Together
------------------------------------------------------------------------------
The overall approach follows a three-layer defense model:

.. code-block:: text

   Layer 1: Prevention (Authoring Guidelines + Automated Scanning at Write Time)
       ↓
   Layer 2: Detection (Pre-Deployment Security Review + Adversarial Testing)
       ↓
   Layer 3: Monitoring (In-Production Continuous Prompt Health Tracking)

This project — ``prompt_risk`` — provides the **software backbone** for Layers 1 and 2: automated scanning rules, risk scoring algorithms, and LLM-powered analysis that transform prompt security from a manual, ad-hoc process into a scalable, repeatable, and auditable engineering practice.

----

6. Target Audience
------------------------------------------------------------------------------
- **AI/ML Engineers** building and deploying LLM-powered agents in insurance workflows
- **Security Teams** responsible for AI risk assessment and compliance
- **Platform Teams** managing prompt registries and LLMOps infrastructure
- **Business Stakeholders** (product managers, operations) who author or approve production prompts

----

7. References
------------------------------------------------------------------------------
- `OWASP Top 10 for LLM Applications (2025) <https://genai.owasp.org/llm-top-10/>`_ — LLM06: Excessive Agency, LLM07: System Prompt Leakage
- `NIST AI Risk Management Framework (AI RMF) <https://www.nist.gov/itl/ai-risk-management-framework>`_ — GenAI Profile
- `ISO/IEC 42001 — AI Management System Standard <https://www.iso.org/standard/81230.html>`_
- `NAIC Model Bulletin on AI in Insurance <https://content.naic.org/sites/default/files/cmte-h-big-data-artificial-intelligence-wg-ai-model-bulletin.pdf.pdf>`_
- `AWS Prescriptive Guidance on LLM Lifecycle Management <https://docs.aws.amazon.com/pdfs/prescriptive-guidance/latest/gen-ai-lifecycle-operational-excellence/gen-ai-lifecycle-operational-excellence.pdf>`_

----

*Document maintained as part of the* ``prompt_risk`` *project — Last updated: 2026-04-22*
