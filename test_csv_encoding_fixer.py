import csv
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from csv_encoding_fixer import decode_csv, detect_delimiter, normalize, normalize_directory


class EncodingFixerTest(unittest.TestCase):
    def test_decodes_gb18030(self):
        text, encoding = decode_csv("订单号,商品名称\n1,测试商品\n".encode("gb18030"))
        self.assertEqual(encoding, "gb18030")
        self.assertIn("测试商品", text)

    def test_distinguishes_utf8_with_and_without_bom(self):
        plain_text, plain_encoding = decode_csv("订单号,金额\n".encode("utf-8"))
        bom_text, bom_encoding = decode_csv("订单号,金额\n".encode("utf-8-sig"))
        self.assertEqual((plain_text, plain_encoding), ("订单号,金额\n", "utf-8"))
        self.assertEqual((bom_text, bom_encoding), ("订单号,金额\n", "utf-8-sig"))

    def test_detects_tab_delimiter(self):
        self.assertEqual(detect_delimiter("订单号\t金额\n1\t12.50\n"), "\t")

    def test_normalizes_to_excel_utf8_bom(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "taobao.csv"
            target = Path(directory) / "fixed.csv"
            source.write_bytes("订单号;商品名称;金额\n1001;测试商品;39.00\n".encode("gb18030"))
            result = normalize(source, target)
            self.assertEqual((result.rows, result.columns), (2, 3))
            self.assertEqual(result.source_delimiter, ";")
            self.assertTrue(target.read_bytes().startswith(b"\xef\xbb\xbf"))
            with target.open(encoding="utf-8-sig", newline="") as handle:
                self.assertEqual(list(csv.reader(handle))[1], ["1001", "测试商品", "39.00"])

    def test_preserves_quoted_commas_and_newlines(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.csv"
            target = Path(directory) / "fixed.csv"
            source.write_text('订单号,备注\n1,"红色,大码\n次日达"\n', encoding="utf-8")
            normalize(source, target)
            with target.open(encoding="utf-8-sig", newline="") as handle:
                self.assertEqual(list(csv.reader(handle))[1][1], "红色,大码\n次日达")

    def test_rejects_ragged_rows_without_partial_output(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "broken.csv"
            target = Path(directory) / "fixed.csv"
            source.write_text("订单号,金额\n1\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "row 2"):
                normalize(source, target)
            self.assertFalse(target.exists())

    def test_rejects_same_input_and_output(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "orders.csv"
            source.write_text("订单号,金额\n1,5\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "different"):
                normalize(source, source)

    def test_rejects_existing_output_without_force(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "orders.csv"
            target = Path(directory) / "fixed.csv"
            source.write_text("订单号,金额\n1,5\n", encoding="utf-8")
            target.write_text("keep me", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "output already exists"):
                normalize(source, target)
            self.assertEqual(target.read_text(encoding="utf-8"), "keep me")
            normalize(source, target, overwrite=True)
            self.assertTrue(target.read_bytes().startswith(b"\xef\xbb\xbf"))

    def test_drag_drop_launchers_are_fail_closed(self):
        root = Path(__file__).parent
        windows = (root / "run-windows.bat").read_text(encoding="utf-8")
        macos = (root / "run-macos.command").read_text(encoding="utf-8")
        self.assertIn("%~dpn1-fixed.csv", windows)
        self.assertIn("${input%.*}-fixed.csv", macos)
        self.assertNotIn("--force", windows)
        self.assertNotIn("--force", macos)

    def test_github_action_entry_writes_audit_and_outputs(self):
        root = Path(__file__).parent
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            source = workspace / "exports"
            source.mkdir()
            (source / "orders.csv").write_bytes("订单号;金额\n1;5\n".encode("gb18030"))
            github_output = workspace / "github-output.txt"
            environment = os.environ | {
                "GITHUB_WORKSPACE": str(workspace),
                "GITHUB_OUTPUT": str(github_output),
                "CSV_GUARD_INPUT": "exports",
                "CSV_GUARD_OUTPUT": "fixed",
                "CSV_GUARD_BATCH": "true",
                "CSV_GUARD_REPORT": "audit.json",
            }
            process = subprocess.run(
                [sys.executable, str(root / "action_entry.py")], env=environment, text=True, capture_output=True
            )
            self.assertEqual(process.returncode, 0, process.stderr)
            audit = json.loads((workspace / "audit.json").read_text(encoding="utf-8"))
            self.assertEqual((audit["processed"], audit["failed"]), (1, 0))
            self.assertIn("processed=1", github_output.read_text(encoding="utf-8"))

    def test_github_action_entry_fails_closed_with_report(self):
        root = Path(__file__).parent
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            source = workspace / "exports"
            source.mkdir()
            (source / "broken.csv").write_text("订单号,金额\n1\n", encoding="utf-8")
            environment = os.environ | {
                "GITHUB_WORKSPACE": str(workspace),
                "CSV_GUARD_INPUT": "exports",
                "CSV_GUARD_OUTPUT": "fixed",
                "CSV_GUARD_BATCH": "true",
                "CSV_GUARD_REPORT": "audit.json",
            }
            process = subprocess.run(
                [sys.executable, str(root / "action_entry.py")], env=environment, text=True, capture_output=True
            )
            self.assertEqual(process.returncode, 2)
            audit = json.loads((workspace / "audit.json").read_text(encoding="utf-8"))
            self.assertEqual((audit["processed"], audit["failed"]), (0, 1))
            self.assertIn("row 2", audit["errors"][0]["error"])

    def test_github_action_rejects_workspace_escape(self):
        root = Path(__file__).parent
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            environment = os.environ | {
                "GITHUB_WORKSPACE": str(workspace),
                "CSV_GUARD_INPUT": "../outside.csv",
                "CSV_GUARD_REPORT": "audit.json",
            }
            process = subprocess.run(
                [sys.executable, str(root / "action_entry.py")], env=environment, text=True, capture_output=True
            )
            self.assertNotEqual(process.returncode, 0)
            self.assertIn("must stay inside GITHUB_WORKSPACE", process.stderr)

    def test_batch_normalizes_multiple_encodings(self):
        with tempfile.TemporaryDirectory() as directory:
            source_dir = Path(directory) / "exports"
            output_dir = Path(directory) / "fixed"
            source_dir.mkdir()
            (source_dir / "taobao.csv").write_bytes("订单号;金额\n1;5\n".encode("gb18030"))
            (source_dir / "jd.CSV").write_text("订单号\t金额\n2\t8\n", encoding="utf-8")
            results, errors = normalize_directory(source_dir, output_dir)
            self.assertEqual(len(results), 2)
            self.assertEqual(errors, [])
            self.assertTrue((output_dir / "taobao.csv").read_bytes().startswith(b"\xef\xbb\xbf"))
            self.assertTrue((output_dir / "jd.CSV").exists())

    def test_batch_reports_bad_file_and_keeps_good_result(self):
        with tempfile.TemporaryDirectory() as directory:
            source_dir = Path(directory) / "exports"
            output_dir = Path(directory) / "fixed"
            source_dir.mkdir()
            (source_dir / "good.csv").write_text("订单号,金额\n1,5\n", encoding="utf-8")
            (source_dir / "bad.csv").write_text("订单号,金额\n1\n", encoding="utf-8")
            results, errors = normalize_directory(source_dir, output_dir)
            self.assertEqual(len(results), 1)
            self.assertEqual(len(errors), 1)
            self.assertIn("row 2", errors[0]["error"])
            self.assertTrue((output_dir / "good.csv").exists())
            self.assertFalse((output_dir / "bad.csv").exists())

    def test_batch_rejects_more_than_one_hundred_files(self):
        with tempfile.TemporaryDirectory() as directory:
            source_dir = Path(directory) / "exports"
            output_dir = Path(directory) / "fixed"
            source_dir.mkdir()
            for number in range(101):
                (source_dir / f"{number}.csv").write_text("订单号,金额\n1,5\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "maximum is 100"):
                normalize_directory(source_dir, output_dir)


if __name__ == "__main__":
    unittest.main()
