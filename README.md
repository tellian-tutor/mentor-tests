# mentor-tests

Content workspace for authoring tests in the **split file format**. Each test is a directory of small, focused JSON files rather than one monolithic bilingual blob. This makes tests human-readable, git-friendly, and easy to review.

## Repository Structure

```
tests/
  {domain}/{group}/           # one directory per test
    meta.en.json              # test metadata (English)
    meta.ru.json              # test metadata (Russian)
    settings.json             # language-independent settings
    q01.mcq.en.json           # question 1, MCQ type, English
    q01.mcq.ru.json           # question 1, MCQ type, Russian
    q02.open_text.en.json     # question 2, open-text type, English
    q02.open_text.ru.json
    ...
  _templates/                 # starter templates for new tests
docs/
  format.md                   # split format v1 specification
  workflow.md                 # authoring and export workflow
tools/
  validate.py                 # validate test directory structure and content
  export.py                   # export split files to platform JSON
```

## Quick Start

### Create a new test

1. Copy the templates directory into the appropriate domain/group path:
   ```bash
   cp -r tests/_templates/ tests/ai/fundamentals/
   ```
2. Fill in the metadata files (`meta.en.json`, `meta.ru.json`).
3. Edit `settings.json` for time limits, scoring, randomization, etc.
4. Rename and edit question files using the naming convention `q{NN}.{type}.{lang}.json`.
5. Add Russian translations as `q{NN}.{type}.ru.json` alongside each English file.

### Validate

```bash
python tools/validate.py tests/ai/fundamentals/
```

Checks file naming, required fields, language parity, and schema conformance.

### Export for platform import

```bash
python tools/export.py tests/ai/fundamentals/
```

Outputs platform-compatible JSON (format_version: 1) to stdout. Pipe to a file or paste into the platform import UI.

## File Naming Conventions

- **Questions:** `q{NN}.{type}.{lang}.json` where NN is zero-padded (01, 02, ...), type is `mcq`, `open_text`, or `chat`, and lang is `en` or `ru`.
- **Metadata:** `meta.{lang}.json` -- one per language.
- **Settings:** `settings.json` -- single file, language-independent.
- All field names use `snake_case`. No camelCase.

## Question Types

| Type | File suffix | Key fields |
|------|------------|------------|
| Multiple choice | `.mcq.` | `text`, `options`, `correct_index` / `correct_indices`, `allow_multiple` |
| Open text | `.open_text.` | `text`, `min_words`, `max_length`, `correct_answer` |
| Chat | `.chat.` | `text`, `max_turns`, `min_words_per_turn`, `correct_answer` |

All types share: `difficulty` (1--5), optional `explanation`, `image_url`, `ai_context`, `ai_suggestions`.

## Contributing

1. Branch from `main` with a descriptive name.
2. Add or edit tests in the split format.
3. Validate before committing.
4. Create a PR for review.
5. Merge after approval.

## Documentation

- [docs/format.md](docs/format.md) -- full split format v1 specification
- [docs/workflow.md](docs/workflow.md) -- authoring and export workflow
