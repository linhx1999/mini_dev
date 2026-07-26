#!/usr/bin/env python3
"""Prepare aligned BIRD JSONL and gold-SQL files from a JSON subset."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REQUIRED_FIELDS = {
    "question_id",
    "db_id",
    "question",
    "evidence",
    "SQL",
    "difficulty",
}
SUPPORTED_DIFFICULTIES = {"simple", "moderate", "challenging"}


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Convert a BIRD JSON subset into position-aligned JSONL and "
            "Mini-Dev evaluator gold-SQL files."
        )
    )
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="source BIRD subset JSON array",
    )
    parser.add_argument(
        "--jsonl-output",
        type=Path,
        help="JSONL destination (default: <input directory>/<input stem>.jsonl)",
    )
    parser.add_argument(
        "--gold-output",
        type=Path,
        help=(
            "gold-SQL destination "
            "(default: <input directory>/<input stem>_gold.sql)"
        ),
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify that both output files already match the input",
    )
    return parser.parse_args()


def load_records(path: Path) -> list[dict[str, Any]]:
    """Load and validate records while preserving their input order."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise SystemExit(f"Cannot read input file {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {path}: {exc}") from exc

    if not isinstance(data, list) or not data:
        raise SystemExit("Input JSON must contain a non-empty array")

    records: list[dict[str, Any]] = []
    seen_question_ids: set[int] = set()
    for index, item in enumerate(data):
        if not isinstance(item, dict):
            raise SystemExit(f"Record {index} must be a JSON object")

        missing_fields = REQUIRED_FIELDS.difference(item)
        if missing_fields:
            missing = ", ".join(sorted(missing_fields))
            raise SystemExit(f"Record {index} is missing required fields: {missing}")

        question_id = item["question_id"]
        if isinstance(question_id, bool) or not isinstance(question_id, int):
            raise SystemExit(
                f"Record {index} has invalid question_id: {question_id!r}"
            )
        if question_id in seen_question_ids:
            raise SystemExit(f"Duplicate question_id: {question_id}")
        seen_question_ids.add(question_id)

        for field in ("db_id", "question", "evidence", "SQL", "difficulty"):
            if not isinstance(item[field], str):
                raise SystemExit(
                    f"Question {question_id} field {field!r} must be a string"
                )

        db_id = item["db_id"]
        sql = item["SQL"]
        difficulty = item["difficulty"]
        if not db_id.strip():
            raise SystemExit(f"Question {question_id} has an empty db_id")
        if not sql.strip():
            raise SystemExit(f"Question {question_id} has empty SQL")
        if any(character in db_id for character in "\t\r\n"):
            raise SystemExit(
                f"Question {question_id} db_id contains a tab or newline"
            )
        if any(character in sql for character in "\t\r\n"):
            raise SystemExit(
                f"Question {question_id} SQL must occupy one physical line"
            )
        if difficulty not in SUPPORTED_DIFFICULTIES:
            raise SystemExit(
                f"Question {question_id} has unsupported difficulty: "
                f"{difficulty!r}"
            )

        records.append(item)

    return records


def serialize_outputs(records: list[dict[str, Any]]) -> tuple[str, str]:
    """Serialize both outputs from the same ordered records."""
    jsonl = "".join(
        json.dumps(record, ensure_ascii=False) + "\n" for record in records
    )
    gold = "".join(f"{record['SQL']}\t{record['db_id']}\n" for record in records)
    return jsonl, gold


def resolve_output_paths(args: argparse.Namespace) -> tuple[Path, Path]:
    """Resolve default destinations beside the actual input file."""
    jsonl_output = args.jsonl_output or args.input.with_suffix(".jsonl")
    gold_output = args.gold_output or args.input.with_name(
        f"{args.input.stem}_gold.sql"
    )

    resolved_paths = {
        args.input.resolve(),
        jsonl_output.resolve(),
        gold_output.resolve(),
    }
    if len(resolved_paths) != 3:
        raise SystemExit("Input, JSONL output, and gold-SQL output must be distinct")
    return jsonl_output, gold_output


def check_output(path: Path, expected: str) -> None:
    """Check that an existing output exactly matches generated content."""
    try:
        actual = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SystemExit(f"Cannot read output file {path}: {exc}") from exc
    if actual != expected:
        raise SystemExit(
            f"Output is stale: {path}\n"
            "Run the script without --check to regenerate both files."
        )


def main() -> None:
    """Generate or verify aligned evaluation inputs."""
    args = parse_args()
    jsonl_output, gold_output = resolve_output_paths(args)
    records = load_records(args.input)
    jsonl, gold = serialize_outputs(records)

    if args.check:
        check_output(jsonl_output, jsonl)
        check_output(gold_output, gold)
        action = "Verified"
    else:
        jsonl_output.parent.mkdir(parents=True, exist_ok=True)
        gold_output.parent.mkdir(parents=True, exist_ok=True)
        jsonl_output.write_text(jsonl, encoding="utf-8")
        gold_output.write_text(gold, encoding="utf-8")
        action = "Wrote"

    question_ids = ",".join(str(record["question_id"]) for record in records)
    print(
        f"{action} {len(records)} aligned records:\n"
        f"  JSONL: {jsonl_output}\n"
        f"  Gold SQL: {gold_output}\n"
        f"  question_ids: {question_ids}"
    )


if __name__ == "__main__":
    main()
