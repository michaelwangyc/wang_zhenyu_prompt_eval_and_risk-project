# Judges — Prompt Risk Evaluation

LLM-as-judge prompts that evaluate production prompts for specific security and quality risks. Each judge receives a target prompt (system prompt + optional user prompt template) and returns a structured JSON assessment with per-criterion findings, severity ratings, and actionable recommendations.

## Directory layout

- [prompts/](prompts/) — One subdirectory per judge:
  - [j1-over-permissive/](prompts/j1-over-permissive/) — Evaluates whether a prompt contains over-permissive authorization patterns (unbounded scope, unconditional compliance, missing refusal capability)
    - [versions/01/](prompts/j1-over-permissive/versions/01/) — Judge version 01
      - `system-prompt.jinja` — System prompt defining the judge's role, five evaluation criteria (refusal capability, scope boundaries, unconditional compliance, failure handling, anti-injection guardrails), scoring guide, and JSON output format
      - `user-prompt.jinja` — User prompt template with `{{ data.target_system_prompt }}` and optional `{{ data.target_user_prompt_template }}` placeholders for the prompt under review
      - `metadata.toml` — Version description and date
