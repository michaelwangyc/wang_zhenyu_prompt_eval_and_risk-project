.. _prompt-risk-matrix:

Internal Prompt Authoring Risk: Prompt Risk Matrix
==============================================================================

.. list-table::
   :widths: 20 80

   * - **Version**
     - v0.1
   * - **Date**
     - 2026-04-16
   * - **Series**
     - LLM Prompt Security Research --- Topic 1, Document 2 of 3

----

Overview
------------------------------------------------------------------------------
The previous document (:ref:`risk-taxonomy`) identified five categories of security risk in internally authored prompts. This document tackles the practical question: **when we discover a risk in a production prompt, which one should we fix first?**

The assessment uses a three-dimensional scoring framework, each dimension scored 1--5:

**Exploitability** --- How easy it is for an attacker to trigger the risk. Higher scores mean that even ordinary users without specialized knowledge can trigger it.

**Impact** --- The business, compliance, and reputational damage caused when the risk is successfully exploited. Higher scores indicate more severe consequences.

**Detectability** --- The probability that the risk will be caught by routine security processes without a dedicated audit. **Note that the scoring direction is inverted relative to the other two dimensions: lower Detectability scores mean harder to detect, which means higher actual danger.**

Overall risk level = f(Exploitability, Impact, 1/Detectability), classified into four tiers: Critical / High / Medium / Low.

----

Scoring Rationale
------------------------------------------------------------------------------
Before presenting the matrix, two scoring decisions deserve explanation.

**Why is Hardcoded Sensitive Data scored 4 for Exploitability?**

Intuitively, "extracting a System Prompt" sounds like it requires advanced technical skill. The reality is the opposite. Security researchers at Keysight's ATI Research Centre demonstrated in 2025 that an attacker need only ask the model to "repeat its initial settings" using Leetspeak (substituting letters for numbers/symbols), Morse code, Pig Latin, or ROT13 encoding to bypass keyword-based filters and extract hidden System Prompt contents with very high success rates. This technique requires no technical background --- any user who knows the trick can perform it. OWASP consequently classified this under **LLM07: System Prompt Leakage** in its 2025 edition, with the explicit recommendation: **"Assume prompts will be extracted."**

**Why is Instruction Conflict scored 1 for Detectability?**

Instruction conflicts only trigger under specific boundary conditions and almost never surface during routine functional testing. No tool proactively alerts that "two of your directives will contradict each other in a certain edge case" --- this requires deliberately designed Adversarial Testing to expose, and most organizations have never conducted such testing against their prompts.

----

Prompt Risk Matrix
------------------------------------------------------------------------------
.. list-table::
   :header-rows: 1
   :widths: 30 15 15 15 25

   * - Risk Category
     - Exploitability
     - Impact
     - Detectability
     - Overall Level
   * - **Over-Permissive Authorization**
     - 5
     - 4
     - 2
     - Critical
   * - **Hardcoded Sensitive Data**
     - 4
     - 5
     - 4
     - Critical
   * - **Role Confusion**
     - 4
     - 3
     - 2
     - High
   * - **Instruction Conflict**
     - 3
     - 3
     - 1
     - High
   * - **Logic Ambiguity**
     - 3
     - 2
     - 2
     - Medium
   * - **Prompt Sprawl (System-level)**
     - 4
     - 5
     - 1
     - Critical

----

Key Findings
------------------------------------------------------------------------------
**Two Critical risks require immediate action.**

Over-Permissive Authorization scores a maximum 5 on Exploitability because it requires no attack technique whatsoever --- ordinary users can trigger it during normal usage, and system logs will record nothing anomalous. Hardcoded Sensitive Data scores a maximum 5 on Impact because what leaks is not merely data but the entire business logic system (pricing models, underwriting criteria, risk coefficients), and the extraction techniques are publicly documented.

**Prompt Sprawl is a system-level Critical risk.**

Its Detectability is scored 1 because no existing tool proactively scans for "how many unreviewed prompts are running in production across the organization." Sprawl is not a vulnerability category in itself --- it is an **amplifier** for all other vulnerabilities: each additional unreviewed prompt adds one more unit of risk exposure.

**Instruction Conflict is the most deeply hidden risk.**

Detectability is only 1, yet both Exploitability and Impact are non-trivial. It is the hardest of the five risks to discover through conventional means, and also the most common --- because virtually every enterprise prompt that has been edited by multiple stakeholders contains some degree of directive contradiction.

----

Prioritization Guidance
------------------------------------------------------------------------------
Based on the scoring above, the recommended order for prompt review and remediation is:

**Immediate:** Scan all production prompts to remove Hardcoded Sensitive Data. Identify and rewrite prompts containing unconditional authorization statements (Over-Permissive patterns).

**Short-term:** Conduct Instruction Conflict audits on all prompts that have been edited by multiple stakeholders. Add explicit role boundary statements to prompts with vague identity definitions.

**Ongoing:** Establish a centralized Prompt Registry to address Prompt Sprawl at the structural level. Incorporate Logic Ambiguity checks into Prompt Authoring Guidelines.

----

**Next document:** :ref:`governance-recommendations` presents specific governance recommendations, including Prompt Authoring Guidelines, a Four-Gate Audit Workflow, and automated scanning rule design.

----

*Document maintained as part of the* ``prompt_risk`` *project --- Last updated: 2026-04-16*

*References: OWASP Top 10 for LLM Applications 2025 (LLM06, LLM07), Keysight ATI Research Centre 2025, NIST AI RMF*
