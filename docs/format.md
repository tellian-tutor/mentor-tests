# Split Format v1 Specification

## Overview

The split format stores each test as a directory of small, single-purpose JSON files. Design goals:

- **Human-readable** -- each file is short and focused on one concern.
- **Git-friendly** -- changes to one question or one language produce minimal diffs.
- **Per-language files** -- translators work on isolated files without touching shared logic.
- **Flat question data** -- type-specific fields live at the top level since the question type is encoded in the filename.
- **Minimal by default** -- only non-empty and non-default fields need to be present.

All field names use `snake_case`. No camelCase anywhere.

## Directory Layout

```
tests/{domain}/{group}/
    meta.en.json
    meta.ru.json
    settings.json
    q01.mcq.en.json
    q01.mcq.ru.json
    q02.open_text.en.json
    q02.open_text.ru.json
    q03.chat.en.json
    q03.chat.ru.json
    ...
```

## File Types

### meta.{lang}.json

Test-level metadata, one file per language.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | yes | Test title |
| `description` | string | yes | Short description shown to students |
| `instructions` | string | yes | Instructions displayed before the test starts |
| `ai_instructions` | string | yes | System prompt / instructions for AI evaluation |
| `final_overview_instructions` | string | no | Instructions for the final overview stage (if enabled) |

### settings.json

Language-independent test configuration. A single file shared across all languages.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `time_limit_minutes` | integer or null | null | Time limit in minutes; null means no limit |
| `randomize_order` | boolean | false | Randomize question order for each attempt |
| `max_score` | integer | -- | Maximum possible score |
| `mode` | string | -- | Test mode identifier |
| `passing_score` | number | -- | Score required to pass |
| `passing_mode` | string | -- | How passing is determined |
| `include_previous_context` | boolean | -- | Include previous answers as context for AI |
| `context_depth` | integer | -- | Number of previous answers to include |
| `show_ai_recommendation` | boolean | -- | Show AI recommendation to student |
| `enable_final_overview` | boolean | -- | Enable the final overview stage |
| `final_overview_replace_score` | boolean | -- | Whether final overview score replaces the test score |
| `final_overview_student_visible` | boolean | -- | Whether final overview is visible to students |
| `final_overview_teacher_visible` | boolean | -- | Whether final overview is visible to teachers |
| `show_correct_answers` | boolean | -- | Show correct answers after submission |
| `show_explanations` | boolean | -- | Show explanations after submission |
| `feedback_mode` | string | -- | When and how feedback is shown |
| `research` | object | -- | Research/experiment settings (see below) |

**research object:**

| Field | Type | Description |
|-------|------|-------------|
| `pre_commitment_enabled` | boolean | Enable pre-commitment prompts |
| `pre_commitment_frequency` | string | How often pre-commitment is shown |
| `ai_suggestions_enabled` | boolean | Enable AI suggestion display |
| `ai_suggestion_frequency` | string | How often AI suggestions appear |
| `ai_suggestion_types` | array of strings | Which suggestion types to show |

Only include fields that differ from defaults. A minimal `settings.json` might contain just `time_limit_minutes` and `randomize_order`.

### q{NN}.{type}.{lang}.json -- Question Files

Question filename pattern: `q{NN}.{type}.{lang}.json`

- **NN** -- zero-padded sequence number (01, 02, ..., 99).
- **type** -- one of `mcq`, `open_text`, `chat`.
- **lang** -- `en` or `ru`.

The question type is encoded in the filename, so `question_data` fields are flattened to the top level.

---

#### MCQ Questions (`.mcq.`)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | string | yes | Question text |
| `difficulty` | integer (1--5) | yes | Difficulty level |
| `options` | array of strings | yes | Answer options |
| `correct_index` | integer | yes (single) | Index of the correct option (0-based); used when `allow_multiple` is false |
| `correct_indices` | array of integers | yes (multi) | Indices of correct options (0-based); used when `allow_multiple` is true |
| `allow_multiple` | boolean | yes | Whether multiple options can be selected |
| `correct_answer` | string | yes | Text explanation of the correct answer for AI evaluation |
| `explanation` | string | no | Explanation shown to the student after answering |
| `image_url` | string | no | URL of an associated image |
| `ai_context` | string | no | Additional context for AI evaluation |
| `ai_suggestions` | array | no | Pre-authored AI suggestion objects (`{score, text}`) |

**Language parity rule:** `difficulty`, `correct_index`, `correct_indices`, `allow_multiple`, and the order/count of `options` must be identical between the `.en.json` and `.ru.json` files for the same question. Only the text content differs.

---

#### Open Text Questions (`.open_text.`)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | string | yes | Question text |
| `difficulty` | integer (1--5) | yes | Difficulty level |
| `min_words` | integer | yes | Minimum word count for the answer |
| `max_length` | integer | yes | Maximum character length for the answer |
| `correct_answer` | string | yes | Reference answer for AI evaluation |
| `explanation` | string | no | Explanation shown after answering |
| `image_url` | string | no | URL of an associated image |
| `ai_context` | string | no | Additional context for AI evaluation |
| `ai_suggestions` | array | no | Pre-authored AI suggestion objects (`{score, text}`) |

---

#### Chat Questions (`.chat.`)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | string | yes | Initial prompt / question text |
| `difficulty` | integer (1--5) | yes | Difficulty level |
| `max_turns` | integer | yes | Maximum number of conversation turns |
| `min_words_per_turn` | integer | yes | Minimum words required per student turn |
| `correct_answer` | string | yes | Reference answer / evaluation criteria for AI |
| `ai_context` | string | no | Additional context for AI evaluation |
| `ai_suggestions` | array | no | Pre-authored AI suggestion objects |

---

## Language Parity

Every question must have both `.en.json` and `.ru.json` files. Language-independent fields must have identical values across both files:

- `difficulty`
- `correct_index` / `correct_indices`
- `allow_multiple`
- Number and order of `options` (for MCQ)
- `min_words`, `max_length` (for open_text)
- `max_turns`, `min_words_per_turn` (for chat)

The validation tool checks this automatically.

## Platform Export Format

The export tool (`tools/export.py`) merges split files into the platform's native JSON format:

- `format_version`: 1
- All translatable strings become i18n objects: `{"en": "...", "ru": "..."}`
- Questions are nested under `questions` array with `question_type` and `question_data` fields
- Settings are merged at the top level
- Metadata fields become i18n objects

Example of an i18n field after export:

```json
{
  "name": {"en": "AI Fundamentals", "ru": "Основы ИИ"},
  "description": {"en": "...", "ru": "..."}
}
```

The import UI in the platform (Test management -> Import) accepts this format directly.
