# Plan: Issue #2 — Review and Improve Customer Support Test

**Issue:** https://github.com/tellian-tutor/mentor-tests/issues/2
**Branch:** `issue-2-improve-support-test`
**Source:** Platform-format JSON attached to issue

## Initial Issues Spotted

1. `final_overview_instructions` at top level is empty `{}` — the real content is inside `settings.final_overview_instructions` (non-standard placement)
2. `https://YOUR-KB/...` placeholder URLs — need real references or removal
3. Q3 has `type: "open_text"` but `question_data` contains `max_turns` and `min_words_per_turn` — looks like it should be `chat` type
4. Q2 `ai_context` is empty `{}`
5. `question_count: null` in settings — not a standard field
6. References duplicated verbatim in description, correct_answer, explanation for every question — very repetitive
7. `feedback_mode: "score"` — should probably be `"detailed"` for a demo test
8. ai_suggestions look properly formatted (pre-answer hints, impersonal)

## Tasks

| # | Task | Status |
|---|------|--------|
| 1 | Split JSON into split format + fix structural issues | Pending |
| 2 | ROAST content and format | Pending |
| 3 | IMPROVE based on roast | Pending |
