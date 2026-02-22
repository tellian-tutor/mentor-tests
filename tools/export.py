"""Export mentor-tests split-file directories to platform import format (format_version 1).

Usage:
    python tools/export.py tests/ai/fundamentals/              # output to stdout
    python tools/export.py tests/ai/fundamentals/ -o out.json  # output to file
    python tools/export.py --all -o dist/                       # export all tests to dist/

Dependencies: none (stdlib only). Calls tools/validate.py as a subprocess.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

QUESTION_TYPES = ("open_text", "mcq", "chat")
LANGUAGES = ("en", "ru")

RE_QUESTION = re.compile(
    r"^q(?P<seq>\d{2,})\.(?P<type>" + "|".join(QUESTION_TYPES) + r")\.(?P<lang>[a-z]{2})\.json$"
)

# Split-file type -> platform type
TYPE_MAP: dict[str, str] = {
    "mcq": "multiple_choice",
    "open_text": "open_text",
    "chat": "chat",
}

# Fields that go into question_data, per question type
QUESTION_DATA_FIELDS: dict[str, list[str]] = {
    "open_text": ["min_words", "max_length"],
    "multiple_choice": ["options", "correct_index", "correct_indices", "allow_multiple"],
    "chat": ["max_turns", "min_words_per_turn"],
}

# Fields on questions that are i18n (need en+ru merging)
I18N_QUESTION_FIELDS = ("text", "correct_answer", "explanation", "ai_context")

# Fields on meta that are i18n
I18N_META_FIELDS = ("name", "description", "instructions", "ai_instructions", "final_overview_instructions")


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


def load_json(path: Path) -> dict:
    """Load a JSON file, exit on failure."""
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        print(f"ERROR: Cannot read {path}: {exc}", file=sys.stderr)
        sys.exit(1)


def run_validation(target: Path, repo_root: Path) -> bool:
    """Run validate.py on the target. Returns True if validation passed."""
    validate_script = repo_root / "tools" / "validate.py"
    if not validate_script.is_file():
        print("ERROR: tools/validate.py not found", file=sys.stderr)
        sys.exit(2)

    proc = subprocess.run(
        [sys.executable, str(validate_script), str(target)],
        capture_output=True,
        text=True,
    )

    if proc.returncode != 0:
        # Forward validation output
        if proc.stderr:
            print(proc.stderr, file=sys.stderr, end="")
        if proc.stdout:
            print(proc.stdout, file=sys.stderr, end="")
        return False
    return True


def merge_i18n(en_val: str | None, ru_val: str | None) -> dict[str, str]:
    """Combine en and ru values into an i18n object."""
    return {"en": en_val or "", "ru": ru_val or ""}


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
# Export logic
# ---------------------------------------------------------------------------

def export_test(test_dir: Path, repo_root: Path) -> dict:
    """Build the platform import format dict for a single test directory."""

    # --- Meta ---
    meta_en = load_json(test_dir / "meta.en.json")
    meta_ru = load_json(test_dir / "meta.ru.json")

    test_obj: dict = {}
    for field in I18N_META_FIELDS:
        test_obj[field] = merge_i18n(meta_en.get(field), meta_ru.get(field))

    # --- Settings ---
    settings = load_json(test_dir / "settings.json")
    test_obj["settings"] = settings

    # --- Questions ---
    # Discover question files
    question_files: dict[tuple[int, str], dict[str, Path]] = {}
    for fp in sorted(test_dir.glob("q*.json")):
        m = RE_QUESTION.match(fp.name)
        if not m:
            continue
        seq = int(m.group("seq"))
        qtype = m.group("type")
        lang = m.group("lang")
        question_files.setdefault((seq, qtype), {})[lang] = fp

    questions: list[dict] = []
    for (seq, qtype), lang_paths in sorted(question_files.items()):
        en_data = load_json(lang_paths["en"]) if "en" in lang_paths else {}
        ru_data = load_json(lang_paths["ru"]) if "ru" in lang_paths else {}

        platform_type = TYPE_MAP.get(qtype, qtype)

        q: dict = {
            "sequence": seq,
            "type": platform_type,
        }

        # i18n text fields
        for field in I18N_QUESTION_FIELDS:
            q[field] = merge_i18n(en_data.get(field), ru_data.get(field))

        # Non-i18n scalar fields (take from en)
        q["difficulty"] = en_data.get("difficulty", 1)
        q["image_url"] = en_data.get("image_url", "")

        # ai_suggestions — merge by index
        en_sugg = en_data.get("ai_suggestions", [])
        ru_sugg = ru_data.get("ai_suggestions", [])
        merged_suggestions: list[dict] = []
        for i in range(max(len(en_sugg), len(ru_sugg))):
            es = en_sugg[i] if i < len(en_sugg) else {}
            rs = ru_sugg[i] if i < len(ru_sugg) else {}
            merged_suggestions.append({
                "score": es.get("score", rs.get("score", 0.0)),
                "text": merge_i18n(es.get("text"), rs.get("text")),
            })
        q["ai_suggestions"] = merged_suggestions

        # question_data — extract type-specific fields
        qd_fields = QUESTION_DATA_FIELDS.get(platform_type, [])
        question_data: dict = {}
        for field in qd_fields:
            if field == "options":
                # options is translatable — merge by index into i18n objects
                en_opts = en_data.get("options", [])
                ru_opts = ru_data.get("options", [])
                question_data["options"] = [
                    merge_i18n(
                        en_opts[i] if i < len(en_opts) else None,
                        ru_opts[i] if i < len(ru_opts) else None,
                    )
                    for i in range(max(len(en_opts), len(ru_opts)))
                ]
            else:
                val = en_data.get(field)
                if val is not None:
                    question_data[field] = val
        q["question_data"] = question_data

        questions.append(q)

    test_obj["questions"] = questions

    return {
        "format_version": 1,
        "test": test_obj,
    }


def generate_output_name(test_dir: Path, repo_root: Path) -> str:
    """Generate a filename for --all mode from the test directory path.

    tests/ai/fundamentals -> ai__fundamentals.json
    """
    try:
        rel = test_dir.relative_to(repo_root / "tests")
    except ValueError:
        rel = test_dir.relative_to(repo_root)
    return str(rel).replace("/", "__").replace("\\", "__") + ".json"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Export mentor-tests split-file directories to platform import format.",
    )
    parser.add_argument(
        "target",
        nargs="?",
        help="Path to a test directory to export.",
    )
    parser.add_argument(
        "-o", "--output",
        help="Output file path (or directory when using --all). Omit for stdout.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        dest="export_all",
        help="Export all test directories under tests/.",
    )
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Skip running validate.py before export (not recommended).",
    )
    return parser


def write_json(data: dict, output: Path | None) -> None:
    """Write JSON to file or stdout."""
    text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
        print(f"Exported: {output}", file=sys.stderr)
    else:
        sys.stdout.write(text)


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if not args.target and not args.export_all:
        parser.error("Provide a target path or use --all")

    script_dir = Path(__file__).resolve().parent
    repo_root = find_repo_root(script_dir)

    if args.export_all:
        dirs = find_all_test_dirs(repo_root)
        if not dirs:
            print("No test directories found under tests/", file=sys.stderr)
            return 1

        # Determine output directory
        out_dir: Path | None = Path(args.output).resolve() if args.output else None

        errors = 0
        for d in dirs:
            # Validate first
            if not args.skip_validation:
                if not run_validation(d, repo_root):
                    print(f"SKIP: {d.relative_to(repo_root)} (validation failed)", file=sys.stderr)
                    errors += 1
                    continue

            data = export_test(d, repo_root)

            if out_dir:
                out_file = out_dir / generate_output_name(d, repo_root)
                write_json(data, out_file)
            else:
                write_json(data, None)

        return 1 if errors else 0

    else:
        target = Path(args.target).resolve()
        if not target.is_dir():
            print(f"ERROR: Not a directory: {args.target}", file=sys.stderr)
            return 1

        # Validate first
        if not args.skip_validation:
            if not run_validation(target, repo_root):
                print("Export aborted: validation errors found.", file=sys.stderr)
                return 1

        data = export_test(target, repo_root)

        output = Path(args.output).resolve() if args.output else None
        # If output is a directory, generate a filename
        if output and output.is_dir():
            output = output / generate_output_name(target, repo_root)

        write_json(data, output)
        return 0


if __name__ == "__main__":
    sys.exit(main())
