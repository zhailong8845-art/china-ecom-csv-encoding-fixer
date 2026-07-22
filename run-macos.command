#!/bin/sh
if [ "$#" -ne 1 ]; then
  echo "Drag one CSV file onto run-macos.command."
  read -r _
  exit 2
fi
input=$1
output="${input%.*}-fixed.csv"
script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
python3 "$script_dir/csv_encoding_fixer.py" "$input" "$output" --json
result=$?
if [ "$result" -ne 0 ]; then
  echo "Fix failed. The original file was not changed."
fi
read -r _
exit "$result"
