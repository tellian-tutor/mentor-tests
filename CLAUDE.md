# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Purpose

**`mentor-tests`** is the content workspace for authoring bilingual (EN/RU) educational tests in the **split file format**. Each test is a directory of small, focused JSON files — human-readable, git-friendly, and easy to review.

**Organization structure:**

| Repository | Purpose |
|------------|---------|
| `general` | Source of truth: product vision, architecture, ADRs, epics, context-bundler |
| `infra` | Deployment infrastructure: Terraform, Ansible, Docker Compose, Caddy |
| `svc-core` | Django monolith: API, auth, business logic, database |
| `svc-frontend` | React SPA: presentation layer |
| `svc-ai-processor` | FastAPI sidecar: LLM evaluation service |
| `e2e-tests` | End-to-end user flow tests |
| **`mentor-tests` (this repo)** | Test content: split-format JSON files, validation and export tools |

**Local paths:**

| Repository | Local Path |
|------------|-----------|
| `svc-core` | `/home/levko/svc-core/` |

**Tracking:** GitHub Projects v2 at org level (`tellian-tutor`).

---

## Commands

### Install dependencies

```bash
pip install -r tools/requirements.txt
```

### Validate a single test

```bash
python tools/validate.py tests/{domain}/{group}/
```

### Validate all tests

```bash
python tools/validate.py --all
```

### Export a single test to platform JSON

```bash
python tools/export.py tests/{domain}/{group}/
# or save to file:
python tools/export.py tests/{domain}/{group}/ -o output.json
```

### Export all tests

```bash
python tools/export.py --all -o dist/
```

Export calls validate internally (skip with `--skip-validation`).

---

## Architecture

### Split File Format (v1)

Each test is a directory under `tests/{domain}/{group}/` containing:

```
meta.en.json / meta.ru.json   — bilingual metadata (name, description, instructions, ai_instructions)
settings.json                  — language-independent config (time limit, scoring, research flags)
q{NN}.{type}.{lang}.json      — individual questions (NN = 01-99, type = mcq|open_text|chat, lang = en|ru)
```

Templates for new tests live in `tests/_templates/`.

### Question Types

- **MCQ** (`.mcq.`) — multiple choice with `options`, `correct_index`/`correct_indices`, `allow_multiple`
- **Open Text** (`.open_text.`) — free text with `min_words`, `max_length`, `correct_answer`
- **Chat** (`.chat.`) — multi-turn conversation with `max_turns`, `min_words_per_turn`, `correct_answer`

### ai_suggestions (IMPORTANT)

`ai_suggestions` are **pre-answer hints shown to the student BEFORE they answer**. They slightly help the student calibrate the quality of their response by showing what different score levels look like. They are **NOT** post-answer evaluation rubrics or coaching feedback.

**Correct style** (brief, describes what the answer level looks like):
```json
{"score": 1.0, "text": "Clearly defines the concept and gives two valid examples with rationale."}
{"score": 0.3, "text": "Mentions the concept but gives only one example or mixes up terms."}
```

**WRONG style** (addressed to student as feedback, too long, coaching tone):
```json
{"score": 1.0, "text": "Excellent — your answer demonstrates deep understanding. You correctly identified..."}
```

Keep ai_suggestions text **short** (1-2 sentences), **descriptive** (not prescriptive), and **impersonal** (no "you/your").

### Validation Pipeline (two tiers)

1. **JSON Schema** (`schemas/*.schema.json`) — per-file structural validation via `jsonschema` (Draft7)
2. **Business rules** (`tools/validate.py`) — cross-file invariants:
   - Language parity: every question needs both `.en.json` and `.ru.json`
   - Language-independent fields (`difficulty`, `correct_index`, `allow_multiple`, option count, `min_words`, `max_turns`, `ai_suggestions[*].score`) must match between language files
   - Consecutive question numbering (q01, q02, ... no gaps)
   - At least one question per test

### Export Pipeline

`tools/export.py` merges split files into platform-native JSON (`format_version: 1`):
- Translatable strings → i18n objects: `{"en": "...", "ru": "..."}`
- Question fields nested under `questions[].question_data`
- Runs validation before export (unless `--skip-validation`)

### Key Reference Files

- `docs/format.md` — full split format v1 specification
- `docs/workflow.md` — authoring and export workflow
- `schemas/rules.md` — business rules and cross-file invariants (language parity details, settings defaults)

---

## Conventions

- **All JSON field names:** `snake_case` — no camelCase anywhere
- **File naming:** `q{NN}.{type}.{lang}.json` (NN = zero-padded, type = `mcq`|`open_text`|`chat`, lang = `en`|`ru`)
- **Indentation:** 2 spaces for JSON/YAML/MD, 4 spaces for Python (see `.editorconfig`)
- **Line endings:** LF, UTF-8, final newline, trim trailing whitespace
- **Python tools:** type hints (`from __future__ import annotations`), `pathlib.Path`, stdlib-only where possible

---

## Orchestrator Pattern (MANDATORY)

**The main agent acts ONLY as an orchestrator.** ALL substantive work MUST be delegated to specialized subagents via the Task tool.

| Orchestrator CAN | Orchestrator MUST Delegate |
|-------------------|---------------------------|
| Read files for context | ALL code/config writing |
| Explore codebase | ALL architecture design |
| Create task breakdown | ALL detailed planning |
| Review subagent outputs | ALL code review |
| Communicate with user | ALL technical decisions |
| Trivial edits (<15 min) | ALL research tasks |

> **Note:** The columns above are independent lists, not paired rows.

### Orchestrator Rules

**Rule 1 — Task plan before delegating:**
Before spawning subagents, orchestrator SHOULD create a task plan using TaskCreate. For Medium+ tasks (>2h), TaskCreate is **MANDATORY**. For Small tasks (15 min–2h), TaskCreate is recommended when there are multiple steps or dependencies but not required.

**Rule 2 — Parallel subagent spawning:**
When multiple subagent tasks have no data dependency, orchestrator MUST spawn them in parallel (multiple Task tool calls in a single message).

**Rule 3 — Graduated enforcement:**

| Task Size | Self-Work | Delegation | TaskCreate |
|-----------|-----------|------------|------------|
| Trivial (<15 min) | Orchestrator MAY do directly | Optional | Not required |
| Small (15 min–2h) | Orchestrator MUST delegate | Required via subagents | Recommended |
| Medium+ (>2h) | Zero self-work | ALL work through subagents | **MANDATORY** |

---

## CREATE → ROAST → IMPROVE Pattern (MANDATORY)

**Every non-trivial artifact MUST follow this cycle.**

```
CREATE (subagent) → ROAST (separate subagent) → IMPROVE (subagent)
                           │
                           ▼
              If CRITICAL/MAJOR issues found:
                    ROAST again after IMPROVE
```

### ROAST Phase: Key Questions

1. Does this align with the process/issue requirements?
2. Are language-independent fields consistent across EN/RU?
3. Will this work for agent-driven execution?
4. Is this the simplest version that works?
5. Are schemas and business rules followed?

---

## Mandatory Agent Rules

1. **Never push directly to `main`.** Always create a feature branch and PR.
2. **Create the feature branch immediately** when starting work on an issue (`issue-NNN-description`), before any code changes.
3. **Never merge your own PR.** The human reviews and merges.
4. **Always reference the issue number** in branch names (`issue-NNN-description`) and commit messages.
5. **MANDATORY: Update GitHub Projects v2 status at every work transition.** Status lives on the project board (not labels, not issue open/closed state). Every new issue MUST be added to the project board immediately after creation. Status MUST be updated at each transition:
   - **Starting work** → set status to `In progress`
   - **PR created / submitted for review** → set status to `In review`
   - **Issue closed (work complete)** → set status to `Done`
   - **Blocked** → keep current status, add `blocked` label, comment with blocker
   - **New issue / not yet started** → set status to `Backlog` (or `Ready` if actionable)
6. **Decompose large tasks** (size > M or > 8 hours) into subtasks as sub-issues before implementing.

---

## Work Tracking

**Primary:** GitHub Issues + Projects v2. All tasks tracked as GitHub issues.
**Secondary:** Tasks/ folders for local execution artifacts.

- Tasks/ folders include issue number: `Tasks/YYYYMMDD_issueNNN_name/`
- Final results posted as GitHub issue comments
- Issue statuses MUST be updated at every transition on the **Projects v2 board**

---

## Task Workspace Protocol (MANDATORY)

**All task work products go in `Tasks/` folder. Artifacts MUST be saved incrementally as work progresses — not retroactively at the end.**

```
Tasks/
├── YYYYMMDD_issueNNN_task_name/
│   ├── plan.md              # REQUIRED: Save BEFORE starting work
│   ├── research.md          # Save IMMEDIATELY after research phase completes
│   ├── roast.md             # REQUIRED: Save IMMEDIATELY after roast phase completes
│   └── result.md            # REQUIRED: Final summary
```

**Rules:**
1. Create `Tasks/` folder and `plan.md` BEFORE spawning any subagents.
2. After each phase (research, create, roast, improve, test-pass), save the output to the corresponding file IMMEDIATELY — do not defer.
3. Subagent outputs are ephemeral (lost after context compression). The `Tasks/` folder is the persistent record. If it's not saved there, it doesn't exist.
4. These artifacts serve as intermediate checkpoints: if work is interrupted, they allow resuming without repeating completed phases.

---

## Project Board Operations (MANDATORY)

**Project:** "tutor project" (#2), org-level at `tellian-tutor`
**Project ID:** `PVT_kwDOD1L3xM4BPMsh`

**Status field ID:** `PVTSSF_lADOD1L3xM4BPMshzg9rWhg`

| Status | Option ID |
|--------|-----------|
| Backlog | `b7d4ffe0` |
| Ready | `14e819db` |
| In progress | `b90d1054` |
| In review | `8fb212d7` |
| Done | `67fddecd` |

**Other fields:**

| Field | Field ID | Options |
|-------|----------|---------|
| Priority | `PVTSSF_lADOD1L3xM4BPMshzg9rWqo` | P0=`6c75236f`, P1=`78af5464`, P2=`5884464a`, P3=`562a1922` |
| Size | `PVTSSF_lADOD1L3xM4BPMshzg9rWqs` | XS=`25742954`, S=`011d9452`, M=`4c74bd78`, L=`afc608f5`, XL=`84b2ed83` |
| Service | `PVTSSF_lADOD1L3xM4BPMshzg9tdiU` | general=`ce49a106`, svc-core=`a26ab787`, svc-frontend=`a7b5a6af`, svc-ai-processor=`c2fc778b`, e2e-tests=`e3cd96f9`, cross-repo=`ae08100a` |

**Step 1: Add issue to the project board (immediately after creation):**
```bash
gh project item-add 2 --owner tellian-tutor --url https://github.com/tellian-tutor/{repo}/issues/{number}
```

**Step 2: Get the item ID and set status:**
```bash
ITEM_ID=$(gh project item-list 2 --owner tellian-tutor --format json | jq -r '.items[] | select(.content.url == "https://github.com/tellian-tutor/{repo}/issues/{number}") | .id')

# Set status (replace option ID as needed)
gh project item-edit --id $ITEM_ID --field-id PVTSSF_lADOD1L3xM4BPMshzg9rWhg --project-id PVT_kwDOD1L3xM4BPMsh --single-select-option-id b7d4ffe0
```

**Rules:**
1. Every `gh issue create` MUST be followed by `gh project item-add`.
2. Every issue close MUST be accompanied by setting status to `Done`.
3. Labels are supplementary — Projects v2 Status field is the source of truth.

---

## Anti-Patterns (NEVER DO THESE)

| Anti-Pattern | Correct Approach |
|--------------|------------------|
| Edit split JSON without validating | Always run `validate.py` before committing |
| Create questions in only one language | Every question needs both `.en.json` and `.ru.json` |
| Skip ROAST phase | Every artifact gets roasted by a separate subagent |
| Create issues without adding to project board | Always run `gh project item-add 2 ...` immediately |
| Push directly to `main` | Feature branches + PR, never push to main |
| Leave issue status stale | Update status at every transition |
| Run independent subagents sequentially | Spawn independent subagents in parallel |
| Skip task plan on Medium+ tasks | Create task plan (TaskCreate) before spawning subagents |
| Use camelCase in JSON fields | All field names use snake_case |
| Leave gaps in question numbering | Questions must be consecutive: q01, q02, q03... |
| Save Tasks/ artifacts only at the end | Save each artifact IMMEDIATELY after its phase completes |
| Write ai_suggestions as coaching feedback | ai_suggestions are pre-answer hints: short, impersonal, descriptive |
