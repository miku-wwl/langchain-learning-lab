# AGENTS.md

## Repository Purpose

This repository is a local-first LangChain / LangGraph E2E learning lab.

The goal is not to build a production application.

The goal is:

1. Understand each concept.
2. Implement the smallest working example.
3. Run it locally.
4. Verify it with real execution.
5. Produce reusable learning notes.

---

## Repository Structure

Each numbered directory represents one learning stage:

- 01-langchain-foundations
- 02-rag
- 03-agent
- 04-mcp
- 05-langgraph-core
- 06-multi-agent
- 07-langgraph-workflow

Do not move content between stages unless required.

Do not introduce concepts from later stages into earlier stages without a clear reason.

---

## Required Workflow

For every stage, follow this order:

Understand
→ Design
→ Implement
→ Run
→ Verify
→ Fix
→ Document

Never skip directly from design to documentation.

---

## Verification Rules

Code must be actually executed.

Do not claim PASS based on static inspection.

Allowed final statuses:

- PASS_LOCAL
- PARTIAL
- BLOCKED

For each stage, record:

- Python version
- LangChain version
- LangGraph version
- model/runtime used
- commands executed
- test results
- E2E result
- blockers

---

## Local-First Rule

Prefer local execution.

Preferred order:

1. Existing local model/runtime
2. Ollama / Foundry Local / local OpenAI-compatible endpoint
3. Mock only for deterministic unit tests
4. Cloud API only when explicitly required

Do not introduce paid cloud APIs without user approval.

LangSmith is optional unless the stage specifically requires it.

---

## Coding Style

Keep examples minimal and educational.

Avoid unnecessary:

- abstractions
- frameworks
- infrastructure
- Docker
- Kubernetes
- Terraform
- databases
- web UIs
- production hardening

unless the current learning stage explicitly requires them.

Prefer code that clearly exposes LangChain behavior.

---

## Tests

Test deterministic behavior where possible.

Do not write brittle tests against exact LLM wording.

Prefer validating:

- tool calls
- state transitions
- thread isolation
- structured outputs
- graph routing
- tool execution
- error handling

---

## Documentation

Each stage should contain:

README.md
docs/
src/
tests/

Recommended docs:

- syllabus-analysis.md
- design.md
- learning-guide.md
- verification-report.md

The learning guide should explain:

Concept
→ Architecture
→ Code
→ Run
→ Result
→ Why

---

## Scope Control

Do not over-engineer.

This repository is primarily for learning LangChain and LangGraph internals.

When a stage is complete, stop.

Do not automatically expand into production architecture or resume-project scope.
