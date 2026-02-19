"""Validate mentor-tests split-file test directories against JSON schemas.

Usage:
    python tools/validate.py tests/ai/fundamentals/              # validate one test
    python tools/validate.py --all                                 # validate all tests under tests/
    python tools/validate.py tests/ai/fundamentals/q01.mcq.en.json  # validate single file

Dependencies: jsonschema (see tools/requirements.txt)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    from jsonschema import Draft7Validator, ValidationError
except ImportError:
    print(
        "ERROR: jsonschema is required. Install with:\n"
        "  pip install -r tools/requirements.txt",
        file=sys.stderr,
    )
    sys.exit(2)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

QUESTION_TYPES = ("open_text", "mcq", "chat")
LANGUAGES = ("en", "ru")

# Regex patterns for recognized file names inside a test directory
RE_META = re.compile(r"^meta\.(?P<lang>[a-z]{2})\.json$")
RE_SETTINGS = re.compile(r"^settings\.json$")
RE_QUESTION = re.compile(
    r"^q(?P<seq>\d{2,})\.(?P<type>" + "|".join(QUESTION_TYPES) + r")\.(?P<lang>[a-z]{2})\.json$"
)

# Schema file name lookup
SCHEMA_MAP: dict[str, str] = {
    "meta": "meta.schema.json",
    "settings": "settings.schema.json",
    "open_text": "question.open_text.schema.json",
    "mcq": "question.mcq.schema.json",
    "chat": "question.chat.schema.json",
}

# Language-independent fields that must match between .en and .ru files, by question type
LANG_INDEPENDENT_FIELDS: dict[str, list[str]] = {
    "open_text": ["difficulty", "min_words", "max_length"],
    "mcq": ["difficulty", "correct_index", "correct_indices", "allow_multiple"],
    "chat": ["difficulty", "max_turns", "min_words_per_turn"],
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def find_repo_root(start: Path) -> Path:
    """Walk up from *start* until we find a directory containing ``schemas/``."""
    current = start.resolve()
    for parent in [current, *current.parents]:
        if (parent / "schemas").is_dir():
            return parent
    print("ERROR: Cannot find repo root (directory containing schemas/)", file=sys.stderr)
    sys.exit(2)


def load_json(path: Path) -> dict | list | None:
    """Load a JSON file, returning None and printing an error on failure."""
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        return exc  # caller will record an error


def load_schema(repo_root: Path, schema_name: str) -> dict:
    """Load and return a JSON Schema dict from the schemas/ directory."""
    path = repo_root / "schemas" / schema_name
    with open(path, encoding="utf-8") as f:
        return json.load(f)


class ValidationResult:
    """Accumulates errors and warnings."""

    def __init__(self) -> None:
        self.errors: list[tuple[str, str]] = []   # (file, message)
        self.warnings: list[tuple[str, str]] = []  # (file, message)

    def error(self, file: str, msg: str) -> None:
        self.errors.append((file, msg))

    def warn(self, file: str, msg: str) -> None:
        self.warnings.append((file, msg))

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0

    def print_report(self) -> None:
        """Print errors/warnings to stderr, summary to stdout."""
        # Group by file
        if self.errors:
            files_seen: set[str] = set()
            for file, msg in self.errors:
                if file not in files_seen:
                    files_seen.add(file)
                    print(f"\n  {file}:", file=sys.stderr)
                print(f"    ERROR: {msg}", file=sys.stderr)

        if self.warnings:
            files_seen_w: set[str] = set()
            for file, msg in self.warnings:
                if file not in files_seen_w:
                    files_seen_w.add(file)
                    print(f"\n  {file}:", file=sys.stderr)
                print(f"    WARNING: {msg}", file=sys.stderr)

        # Summary to stdout
        ne = len(self.errors)
        nw = len(self.warnings)
        if ne == 0 and nw == 0:
            print("OK")
        elif ne == 0:
            print(f"OK ({nw} warning{'s' if nw != 1 else ''})")
        else:
            print(f"{ne} error{'s' if ne != 1 else ''}, {nw} warning{'s' if nw != 1 else ''}")


# ---------------------------------------------------------------------------
# Per-file schema validation
# ---------------------------------------------------------------------------

def detect_file_type(filename: str) -> tuple[str, str | None, int | None] | None:
    """Detect file type from filename.

    Returns (kind, lang, seq) where:
      kind  = "meta" | "settings" | "open_text" | "mcq" | "chat"
      lang  = "en" | "ru" | None (for settings)
      seq   = question sequence number | None (for meta/settings)
    Returns None if the filename doesn't match any known pattern.
    """
    m = RE_META.match(filename)
    if m:
        return ("meta", m.group("lang"), None)

    if RE_SETTINGS.match(filename):
        return ("settings", None, None)

    m = RE_QUESTION.match(filename)
    if m:
        return (m.group("type"), m.group("lang"), int(m.group("seq")))

    return None


def validate_file(
    file_path: Path,
    repo_root: Path,
    result: ValidationResult,
) -> dict | None:
    """Validate a single JSON file against its schema.

    Returns the parsed JSON data on success, or None on failure.
    """
    fname = file_path.name
    rel = str(file_path.relative_to(repo_root)) if file_path.is_relative_to(repo_root) else fname

    info = detect_file_type(fname)
    if info is None:
        result.warn(rel, f"Unrecognized file name pattern: {fname}")
        return None

    kind, _lang, _seq = info
    schema_name = SCHEMA_MAP.get(kind)
    if schema_name is None:
        result.error(rel, f"No schema mapping for kind '{kind}'")
        return None

    data = load_json(file_path)
    if isinstance(data, Exception):
        result.error(rel, f"Cannot read JSON: {data}")
        return None

    schema = load_schema(repo_root, schema_name)
    validator = Draft7Validator(schema)
    errors_found = False
    for err in sorted(validator.iter_errors(data), key=lambda e: list(e.path)):
        path_str = ".".join(str(p) for p in err.absolute_path) if err.absolute_path else "(root)"
        result.error(rel, f"Schema: {path_str} — {err.message}")
        errors_found = True

    return data if not errors_found else data  # return data even with errors for cross-checks


# ---------------------------------------------------------------------------
# Cross-file business rules
# ---------------------------------------------------------------------------

def validate_directory(test_dir: Path, repo_root: Path, result: ValidationResult) -> None:
    """Validate all files in a test directory and apply cross-file rules."""
    rel_dir = str(test_dir.relative_to(repo_root)) if test_dir.is_relative_to(repo_root) else str(test_dir)

    # Inventory files
    json_files = sorted(test_dir.glob("*.json"))
    if not json_files:
        result.error(rel_dir, "No JSON files found in test directory")
        return

    # Categorize files
    meta_files: dict[str, Path] = {}       # lang -> path
    settings_file: Path | None = None
    question_files: dict[tuple[int, str], dict[str, Path]] = {}  # (seq, type) -> {lang: path}
    loaded: dict[Path, dict | None] = {}

    for fp in json_files:
        info = detect_file_type(fp.name)
        if info is None:
            result.warn(rel_dir, f"Skipping unrecognized file: {fp.name}")
            continue

        kind, lang, seq = info

        # Validate each file against schema
        data = validate_file(fp, repo_root, result)
        loaded[fp] = data

        if kind == "meta":
            meta_files[lang] = fp
        elif kind == "settings":
            settings_file = fp
        else:
            key = (seq, kind)
            question_files.setdefault(key, {})[lang] = fp

    # --- Required files ---
    for lang in LANGUAGES:
        if lang not in meta_files:
            result.error(rel_dir, f"Missing meta.{lang}.json")

    if settings_file is None:
        result.error(rel_dir, "Missing settings.json")

    # --- Question pair checks ---
    for (seq, qtype), lang_paths in sorted(question_files.items()):
        q_label = f"q{seq:02d}.{qtype}"

        # Both languages must exist
        for lang in LANGUAGES:
            if lang not in lang_paths:
                result.error(rel_dir, f"Missing {q_label}.{lang}.json (unpaired question)")

        # Cross-language consistency checks
        if "en" in lang_paths and "ru" in lang_paths:
            en_data = loaded.get(lang_paths["en"])
            ru_data = loaded.get(lang_paths["ru"])

            if isinstance(en_data, dict) and isinstance(ru_data, dict):
                _check_lang_independent_fields(en_data, ru_data, qtype, q_label, rel_dir, result)
                _check_mcq_correctness(en_data, qtype, f"{q_label}.en", rel_dir, result)
                _check_mcq_correctness(ru_data, qtype, f"{q_label}.ru", rel_dir, result)
                _check_mcq_options_length(en_data, ru_data, qtype, q_label, rel_dir, result)
                _check_ai_suggestions(en_data, ru_data, q_label, rel_dir, result)
        elif "en" in lang_paths:
            en_data = loaded.get(lang_paths["en"])
            if isinstance(en_data, dict):
                _check_mcq_correctness(en_data, qtype, f"{q_label}.en", rel_dir, result)

    # --- Sequence gaps ---
    if question_files:
        sequences = sorted({seq for seq, _ in question_files.keys()})
        expected = list(range(1, max(sequences) + 1))
        missing = set(expected) - set(sequences)
        if missing:
            result.warn(rel_dir, f"Question sequence gap: missing q{', q'.join(f'{s:02d}' for s in sorted(missing))}")
        if 0 in sequences:
            result.warn(rel_dir, "Question sequences should start from 1, found q00")
        if sequences and sequences[0] != 1 and 0 not in sequences:
            result.warn(rel_dir, f"Question sequences should start from 1, first is q{sequences[0]:02d}")


def _check_lang_independent_fields(
    en_data: dict,
    ru_data: dict,
    qtype: str,
    q_label: str,
    rel_dir: str,
    result: ValidationResult,
) -> None:
    """Ensure language-independent fields match between en and ru files."""
    fields = LANG_INDEPENDENT_FIELDS.get(qtype, ["difficulty"])
    for field in fields:
        en_val = en_data.get(field)
        ru_val = ru_data.get(field)
        # Only compare if both are present (schema validation handles required fields)
        if en_val is not None and ru_val is not None and en_val != ru_val:
            result.error(
                rel_dir,
                f"{q_label}: '{field}' mismatch between en ({en_val}) and ru ({ru_val})",
            )


def _check_mcq_correctness(
    data: dict,
    qtype: str,
    q_label: str,
    rel_dir: str,
    result: ValidationResult,
) -> None:
    """Check MCQ correct_index/correct_indices bounds and consistency."""
    if qtype != "mcq":
        return

    options = data.get("options", [])
    n_opts = len(options)
    allow_multiple = data.get("allow_multiple")

    if allow_multiple is False:
        ci = data.get("correct_index")
        if ci is not None and ci >= n_opts:
            result.error(
                rel_dir,
                f"{q_label}: correct_index ({ci}) >= number of options ({n_opts})",
            )
        if ci is None and "correct_index" not in data:
            result.error(
                rel_dir,
                f"{q_label}: allow_multiple is false but correct_index is missing",
            )
    elif allow_multiple is True:
        cis = data.get("correct_indices")
        if cis is not None:
            for idx in cis:
                if idx >= n_opts:
                    result.error(
                        rel_dir,
                        f"{q_label}: correct_indices contains {idx} >= number of options ({n_opts})",
                    )
        if cis is None and "correct_indices" not in data:
            result.error(
                rel_dir,
                f"{q_label}: allow_multiple is true but correct_indices is missing",
            )


def _check_mcq_options_length(
    en_data: dict,
    ru_data: dict,
    qtype: str,
    q_label: str,
    rel_dir: str,
    result: ValidationResult,
) -> None:
    """Check that MCQ options arrays have the same length across languages."""
    if qtype != "mcq":
        return

    en_opts = en_data.get("options", [])
    ru_opts = ru_data.get("options", [])
    if len(en_opts) != len(ru_opts):
        result.error(
            rel_dir,
            f"{q_label}: options length mismatch — en has {len(en_opts)}, ru has {len(ru_opts)}",
        )


def _check_ai_suggestions(
    en_data: dict,
    ru_data: dict,
    q_label: str,
    rel_dir: str,
    result: ValidationResult,
) -> None:
    """Check ai_suggestions scores are in range and match between languages."""
    en_sugg = en_data.get("ai_suggestions", [])
    ru_sugg = ru_data.get("ai_suggestions", [])

    # Check score range (schema should handle this, but belt-and-suspenders)
    for i, s in enumerate(en_sugg):
        score = s.get("score")
        if score is not None and not (0.0 <= score <= 1.0):
            result.error(rel_dir, f"{q_label}.en: ai_suggestions[{i}].score ({score}) not in [0.0, 1.0]")

    for i, s in enumerate(ru_sugg):
        score = s.get("score")
        if score is not None and not (0.0 <= score <= 1.0):
            result.error(rel_dir, f"{q_label}.ru: ai_suggestions[{i}].score ({score}) not in [0.0, 1.0]")

    # Check count and scores match
    if en_sugg and ru_sugg:
        if len(en_sugg) != len(ru_sugg):
            result.error(
                rel_dir,
                f"{q_label}: ai_suggestions count mismatch — en has {len(en_sugg)}, ru has {len(ru_sugg)}",
            )
        else:
            for i, (es, rs) in enumerate(zip(en_sugg, ru_sugg)):
                if es.get("score") != rs.get("score"):
                    result.error(
                        rel_dir,
                        f"{q_label}: ai_suggestions[{i}].score mismatch — en={es.get('score')}, ru={rs.get('score')}",
                    )


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------

def find_all_test_dirs(repo_root: Path) -> list[Path]:
    """Find all test directories (those containing settings.json) under tests/."""
    tests_root = repo_root / "tests"
    if not tests_root.is_dir():
        return []

    dirs: list[Path] = []
    for settings in sorted(tests_root.rglob("settings.json")):
        dirs.append(settings.parent)
    return dirs


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate mentor-tests split-file test directories against JSON schemas.",
    )
    parser.add_argument(
        "target",
        nargs="?",
        help="Path to a test directory or a single JSON file to validate.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        dest="validate_all",
        help="Validate all test directories under tests/.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if not args.target and not args.validate_all:
        parser.error("Provide a target path or use --all")

    script_dir = Path(__file__).resolve().parent
    repo_root = find_repo_root(script_dir)
    result = ValidationResult()

    if args.validate_all:
        dirs = find_all_test_dirs(repo_root)
        if not dirs:
            print("No test directories found under tests/", file=sys.stderr)
            return 1
        for d in dirs:
            validate_directory(d, repo_root, result)
    else:
        target = Path(args.target).resolve()
        if target.is_file():
            validate_file(target, repo_root, result)
        elif target.is_dir():
            validate_directory(target, repo_root, result)
        else:
            print(f"ERROR: Target not found: {args.target}", file=sys.stderr)
            return 1

    result.print_report()
    return 0 if result.ok else 1


if __name__ == "__main__":
    sys.exit(main())
