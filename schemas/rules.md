# Test Content Rules

Business rules and cross-file invariants for the mentor-tests repository.
JSON Schema files enforce per-file structure; this document covers rules that
span multiple files or cannot be expressed in JSON Schema alone.

---

## 1. File Structure Rules

- Every test directory MUST contain both `meta.en.json` and `meta.ru.json`.
- Every test directory MUST contain `settings.json`.
- Questions MUST exist in matching language pairs:
  `q01.mcq.en.json` + `q01.mcq.ru.json`.
  A question file in one language without its counterpart is invalid.
- Question sequence numbers MUST be consecutive integers starting from `01`
  (i.e. `q01`, `q02`, `q03`, ...). Gaps are not allowed.
- A test directory with zero questions is invalid.

---

## 2. Cross-File Invariants

Language-independent fields MUST have identical values between the `.en.json`
and `.ru.json` files of the same question. The AI evaluator and backend rely
on these values being consistent across languages.

### MCQ questions (`q{NN}.mcq.{lang}.json`)

| Field | Must match across languages |
|-------|---------------------------|
| `difficulty` | Yes |
| `correct_index` | Yes |
| `correct_indices` | Yes |
| `allow_multiple` | Yes |
| `options` array length | Yes (content differs by language) |
| `ai_suggestions[*].score` | Yes (text differs by language) |

### Open-text questions (`q{NN}.open_text.{lang}.json`)

| Field | Must match across languages |
|-------|---------------------------|
| `difficulty` | Yes |
| `min_words` | Yes |
| `max_length` | Yes |
| `ai_suggestions[*].score` | Yes (text differs by language) |

### Chat questions (`q{NN}.chat.{lang}.json`)

| Field | Must match across languages |
|-------|---------------------------|
| `difficulty` | Yes |
| `max_turns` | Yes |
| `min_words_per_turn` | Yes |
| `ai_suggestions[*].score` | Yes (text differs by language) |

### settings.json

`settings.json` is shared across all languages within a test directory.
There is exactly one `settings.json` per test, never per-language variants.

---

## 3. MCQ-Specific Rules

- `correct_index` MUST be less than `len(options)`.
- When `allow_multiple` is `true`, every value in `correct_indices` MUST be
  less than `len(options)`.
- When `allow_multiple` is `false`, use `correct_index` (single correct answer).
- When `allow_multiple` is `true`, use `correct_indices` (multiple correct answers).
- The `correct_answer` text field is always present regardless of `allow_multiple`
  and is used by the AI evaluator as a human-readable reference.

---

## 4. ai_suggestions Rules

- Each suggestion's `score` MUST be in the range `[0.0, 1.0]`.
- Suggestions SHOULD be sorted in descending order by `score`.
- For open-text questions, at least 2 suggestions are recommended (not required
  by schema, but expected by the frontend when `research.ai_suggestions_enabled`
  is `true`).
- The `score` values in `ai_suggestions` are language-independent and MUST match
  between `.en.json` and `.ru.json` files. The `text` values differ by language.

---

## 5. Settings Field Inventory

All fields in `settings.json` are optional. When absent, the backend or frontend
applies the default listed below.

| Field | Type | Default | Backend reads | Frontend reads | Notes |
|-------|------|---------|:---:|:---:|-------|
| `time_limit_minutes` | integer \| null | `null` | yes | yes | Timer duration in minutes. `null` = no limit. |
| `randomize_order` | boolean | `false` | yes | -- | Shuffle question order on each attempt. |
| `max_score` | number | `10` | yes | -- | Maximum achievable score for the test. |
| `mode` | string | `"training"` | yes | yes | `"training"` or `"control"`. |
| `passing_score` | number \| null | `null` | yes | -- | Fraction 0--1 of `max_score` required to pass. `null` = no threshold. |
| `passing_mode` | string | `"any"` | yes | -- | `"any"` = best attempt counts; `"control"` = only control attempts count. |
| `include_previous_context` | boolean | `false` | yes | -- | Include prior Q&A pairs in AI evaluation context. |
| `context_depth` | string \| integer | `"all"` | yes | -- | `"all"` or a non-negative integer. |
| `show_ai_recommendation` | boolean | `true` | -- | yes | Display AI score recommendation to the student. |
| `enable_final_overview` | boolean | `false` | yes | yes | Enable AI-generated final overview after completion. |
| `final_overview_replace_score` | boolean | `false` | yes | -- | Replace per-question aggregate score with overview score. |
| `final_overview_student_visible` | boolean | `true` | -- | yes | Student can see the final overview. |
| `final_overview_teacher_visible` | boolean | `true` | -- | yes | Teacher can see the final overview. |
| `show_correct_answers` | boolean | -- | -- | yes | Show correct answers after submission. Frontend only. |
| `show_explanations` | boolean | -- | -- | yes | Show explanations after submission. Frontend only. |
| `feedback_mode` | string | -- | -- | yes | `"score"`, `"detailed"`, or `"none"`. Frontend only. |
| `research.pre_commitment_enabled` | boolean | `false` | yes | -- | Enable the pre-commitment prompt. |
| `research.pre_commitment_frequency` | integer | `0` | yes | -- | Show pre-commitment every N questions (0 = disabled). |
| `research.ai_suggestions_enabled` | boolean | `false` | yes | -- | Enable AI-authored answer suggestions. |
| `research.ai_suggestion_frequency` | integer | `0` | yes | -- | Show AI suggestions every N questions (0 = disabled). |
| `research.ai_suggestion_types` | array | `[]` | yes | -- | Types of AI suggestions to offer. |

---

## 6. Naming Convention

- All JSON field names use **snake_case**. No camelCase anywhere in the repository.
- `tools/export.py` handles any platform-specific naming transformations at
  export time; source files always use snake_case.
- File naming pattern: `q{NN}.{type}.{lang}.json` where:
  - `{NN}` is a zero-padded two-digit sequence number (`01`, `02`, ...).
  - `{type}` is one of: `open_text`, `mcq`, `chat`.
  - `{lang}` is a two-letter language code: `en`, `ru`.
