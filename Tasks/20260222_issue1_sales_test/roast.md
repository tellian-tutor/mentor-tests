# Roast Findings: Sales Demo Test

## Validation
`tools/validate.py` — **OK** (schema + business rules pass)

## Findings

### CRITICAL (1)

**C1: ai_suggestions violate impersonal rule**
All 8 ai_suggestions in q01 (EN+RU) used "you/your", coaching tone, and prescriptive advice. They should be short, impersonal, descriptive pre-answer hints.
- **Status:** FIXED in IMPROVE phase

### MAJOR (2)

**D6: Description too long for demo card**
~350 words with embedded URLs. Shortened to 2-3 punchy sentences. URLs moved to ai_instructions.
- **Status:** FIXED

**F4: ai_suggestions data exists but `research.ai_suggestions_enabled` not set**
Added `research.ai_suggestions_enabled: true` and `ai_suggestion_frequency: 1` to settings.json.
- **Status:** FIXED

### MINOR (4)

**D7: ai_instructions don't mention 3-min constraint**
Added timing note to ai_instructions in both languages.
- **Status:** FIXED

**D8: Q2 CFO role unnatural for sales onboarding topic**
Changed CFO to VP of Sales in both EN and RU.
- **Status:** FIXED

**E4: MEDDIC vs MEDDPICC URL mismatch**
Test covers MEDDIC but URL points to MEDDPICC page. Acceptable — same source.
- **Status:** Not fixed (acceptable)

**F5: show_ai_recommendation not explicitly set**
Defaults to true. Left as default.
- **Status:** Not fixed (acceptable)

### POSITIVE (10)
- Format/schema clean, all snake_case, correct naming
- Language parity perfect across all pairs
- Description compelling with research citations
- Three distinct sales skills covered
- MCQ distractors plausible (map to named archetypes)
- Explanations teach, not just state answers
- Russian uses natural B2B jargon (пайплайн, стейкхолдеры)
- All three methodologies accurately depicted
- Timing works for 3 minutes
- Final overview well-designed with three-dimensional assessment
