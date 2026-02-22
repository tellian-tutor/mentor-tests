# Plan: Issue #1 — Create Sales Demo Test

**Issue:** https://github.com/tellian-tutor/mentor-tests/issues/1
**Branch:** `issue-1-create-sales-test`
**Status:** Complete

## Goal

Create a short (3-4 questions, ~3 minutes) sales demo test that:
- Hooks potential customers who train sales teams
- Creates wow and FOMO effect
- Showcases AI evaluation on open-text questions
- Covers different sales actions from industry-recognized methodologies

## Task Breakdown

| # | Task | Status |
|---|------|--------|
| 1 | Research sales training programs | Done |
| 2 | Create test files (EN + RU) | Done |
| 3 | ROAST the test | Done |
| 4 | IMPROVE based on roast | Done |
| 5 | Test-pass by subagent | Done |

## Design Decisions

- **Methodologies chosen:** SPIN Selling, Challenger Sale, MEDDIC — the three most universally recognized, covering discovery → insight → qualification
- **Question structure:** Q1 open_text (SPIN), Q2 MCQ (Challenger), Q3 MCQ (MEDDIC)
- **3 questions, not 4** — tighter pacing for demo, covers three distinct skills
- **Cumulative evaluation** via `enable_final_overview: true` with three-dimensional assessment
- **ai_suggestions enabled** — pre-answer hints for Q1 to demonstrate research feature
