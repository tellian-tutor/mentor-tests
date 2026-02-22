# Roast: Customer Support Test

## CRITICAL (3)
- C1: Time mismatch — settings says 6 min, meta says 5 min
- C2: ai_suggestions use coaching/prescriptive tone ("your", "use", "avoid") — must be impersonal descriptive
- C3: Same 4-line reference block duplicated 8 times across files

## MAJOR (7)
- M1: Placeholder URLs "(company-specific SOP link)" in student-facing description
- M2: ISO standard links are paywalled — useless as references
- M3: Q3 min_words: 12 too low for 2-4 sentence reply (→25+)
- M4: Q1 min_words: 6 too low for 1-3 sentence reply (→10+)
- M5: Q2 MCQ has no ai_suggestions (Q1/Q3 have 4 each)
- M6: Q2 explanation too terse — doesn't teach why wrong answers are wrong
- M7: context_depth "all" redundant with 3 questions

## MINOR (8)
- m1: No demo_answers file
- m2: Description mixes marketing copy with bibliography
- m3: final_overview_instructions could be stronger
- m4: Russian naturalness issues ("операционны", awkward phrasing)
- m5: Redundant disabled settings (ai_suggestion_frequency: 0, types: [])
- m6: pre_commitment_frequency: 1 while disabled
- m7: Q2 EN phrasing "You have the customer in the chat" awkward
- m8: README.md not reviewed

## POSITIVE (8)
- Clean validation, strong scenario flow, good MCQ distractors
- Agent capabilities list in Q3 is excellent design
- Rich ai_context, sensible difficulty progression
