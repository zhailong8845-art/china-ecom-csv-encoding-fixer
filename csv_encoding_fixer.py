#!/usr/bin/env python3
"""Normalize Chinese e-commerce CSV exports for Excel and data tools."""

from __future__ import annotations

import argparse
import csv
import io
import json
from dataclasses import asdict, dataclass
from pathlib import Path

ENCODINGS = ("utf-8-sig", "utf-8", "gb18030")
DELIMITERS = (",", "\t", ";", "|")


@dataclass(frozen=True)
class Result:
    input: str
    output: str
    source_encoding: str
    source_delimiter: str
    output_encoding: str
    rows: int
    columns: int


def decode_csv(data: bytes) -> tuple[str, str]:
    for encoding in ENCODINGS:
        try:
            return data.decode(encoding), encoding
        except UnicodeDecodeError:
            continue
    raise ValueError("input is not valid UTF-8, UTF-8 BOM, or GB18030 text")


def detect_delimiter(text: str) -> str:
    sample = "\n".join(text.splitlines()[:20])
    try:
        return csv.Sniffer().sniff(sample, delimiters="".join(DELIMITERS)).delimiter
    except csv.Error as exc:
        header = text.splitlines()[0] if text.splitlines() else ""
        counts = {delimiter: header.count(delimiter) for delimiter in DELIMITERS}
        delimiter = max(counts, key=counts.get)
        if counts[delimiter] > 0:
            return delimiter
        raise ValueError("could not detect comma, tab, semicolon, or pipe delimiter") from exc


def normalize(input_path: Path, output_path: Path, output_encoding: str = "utf-8-sig") -> Result:
    if input_path.resolve() == output_path.resolve():
        raise ValueError("input and output paths must be different")
    text, source_encoding = decode_csv(input_path.read_bytes())
    delimiter = detect_delimiter(text)
    rows = list(csv.reader(io.StringIO(text, newline=""), delimiter=delimiter))
    if not rows:
        raise ValueError("input CSV is empty")
    width = len(rows[0])
    if width < 2:
        raise ValueError("input must contain at least two columns")
    for number, row in enumerate(rows, 1):
        if len(row) != width:
            raise ValueError(f"row {number} has {len(row)} columns; expected {width}")
    buffer = io.StringIO(newline="")
    csv.writer(buffer, lineterminator="\n").writerows(rows)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(buffer.getvalue().encode(output_encoding))
    return Result(str(input_path), str(output_path), source_encoding, delimiter, output_encoding, len(rows), width)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fix Chinese e-commerce CSV encoding and delimiters")
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--output-encoding", choices=("utf-8-sig", "gb18030"), default="utf-8-sig")
    parser.add_argument("--json", action="store_true", help="print an audit result as JSON")
    args = parser.parse_args(argv)
    try:
        result = normalize(args.input, args.output, args.output_encoding)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    if args.json:
        print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
    else:
        print(f"Fixed {result.rows} rows x {result.columns} columns: {result.output}")
        print(f"Detected {result.source_encoding}, delimiter {result.source_delimiter!r}; wrote {result.output_encoding}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
