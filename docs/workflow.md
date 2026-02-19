# Test Authoring Workflow

This document describes the manual workflow for creating, validating, exporting, and importing tests.

## 1. Author or Edit Test Files

Create a new test directory under the appropriate domain and group:

```bash
mkdir -p tests/{domain}/{group}
cp tests/_templates/meta.en.json tests/{domain}/{group}/
cp tests/_templates/settings.json tests/{domain}/{group}/
```

Copy and rename question templates as needed:

```bash
cp tests/_templates/q01.mcq.en.json tests/{domain}/{group}/q01.mcq.en.json
cp tests/_templates/q01.mcq.en.json tests/{domain}/{group}/q01.mcq.ru.json
```

Edit each file with the actual content. Every question needs both `.en.json` and `.ru.json` variants. Language-independent fields (difficulty, correct_index, etc.) must match between the two language files.

See [format.md](format.md) for the full field reference.

## 2. Validate

Run the validation tool against the test directory:

```bash
python tools/validate.py tests/{domain}/{group}/
```

The validator checks:
- File naming conventions (`q{NN}.{type}.{lang}.json`)
- Required fields are present and non-empty
- Language parity (both `.en.json` and `.ru.json` exist for each question, language-independent fields match)
- Field types and value ranges (e.g., difficulty is 1--5)
- Settings schema conformance

Fix any reported issues before proceeding.

## 3. Export

Generate platform-compatible JSON from the split files:

```bash
python tools/export.py tests/{domain}/{group}/
```

This outputs JSON to stdout in the platform's native format (`format_version: 1`). To save to a file:

```bash
python tools/export.py tests/{domain}/{group}/ > output.json
```

Review the exported JSON to confirm it looks correct.

## 4. Import into Platform

1. Open the platform web UI.
2. Navigate to **Test management**.
3. Click **Import**.
4. Paste or upload the exported JSON.
5. Review the imported test in the UI to verify questions, translations, and settings.

## 5. Handle Images

If any questions use `image_url`:

1. Upload the image to the platform's storage or a public hosting service.
2. Set the `image_url` field in the question file to the resulting URL.
3. Do this **before** exporting and importing, so the URLs are included in the platform JSON.

## 6. Commit and Review

1. Create a branch from `main`:
   ```bash
   git checkout -b add-{domain}-{group}-test
   ```
2. Add the test files:
   ```bash
   git add tests/{domain}/{group}/
   ```
3. Commit with a descriptive message:
   ```bash
   git commit -m "Add {domain}/{group} test"
   ```
4. Push and create a pull request.
5. Get a review from a team member.
6. Merge to `main` after approval.

This ensures all test content is version-controlled, reviewed, and traceable.
