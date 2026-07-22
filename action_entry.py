#!/usr/bin/env python3
"""GitHub Action entrypoint for CSV Encoding Guard."""

from __future__ import annotations

import json
import os
from dataclasses import asdict
from pathlib import Path

from csv_encoding_fixer import normalize, normalize_directory


def enabled(name: str) -> bool:
    value = os.getenv(name, "false").strip().lower()
    if value not in {"true", "false"}:
        raise ValueError(f"{name} must be true or false")
    return value == "true"


def write_outputs(report: Path, processed: int, failed: int) -> None:
    github_output = os.getenv("GITHUB_OUTPUT")
    if not github_output:
        return
    with Path(github_output).open("a", encoding="utf-8") as handle:
        handle.write(f"report={report}\nprocessed={processed}\nfailed={failed}\n")


def workspace_path(workspace: Path, value: str, name: str) -> Path:
    path = (workspace / value).resolve()
    if path != workspace and workspace not in path.parents:
        raise ValueError(f"{name} must stay inside GITHUB_WORKSPACE")
    return path


def main() -> int:
    workspace = Path(os.getenv("GITHUB_WORKSPACE", ".")).resolve()
    source = workspace_path(workspace, os.getenv("CSV_GUARD_INPUT", "."), "input")
    target = workspace_path(workspace, os.getenv("CSV_GUARD_OUTPUT", "fixed-csv"), "output")
    report = workspace_path(workspace, os.getenv("CSV_GUARD_REPORT", "csv-encoding-audit.json"), "report")
    encoding = os.getenv("CSV_GUARD_OUTPUT_ENCODING", "utf-8-sig")
    try:
        batch = enabled("CSV_GUARD_BATCH")
        force = enabled("CSV_GUARD_FORCE")
        if encoding not in {"utf-8-sig", "gb18030"}:
            raise ValueError("CSV_GUARD_OUTPUT_ENCODING must be utf-8-sig or gb18030")
        if batch:
            results, errors = normalize_directory(source, target, encoding, force)
        else:
            result = normalize(source, target, encoding, force)
            results, errors = [result], []
    except (OSError, ValueError) as exc:
        results, errors = [], [{"input": str(source), "error": str(exc)}]
    payload = {
        "input": str(source),
        "output": str(target),
        "processed": len(results),
        "failed": len(errors),
        "results": [asdict(item) for item in results],
        "errors": errors,
    }
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_outputs(report, len(results), len(errors))
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
