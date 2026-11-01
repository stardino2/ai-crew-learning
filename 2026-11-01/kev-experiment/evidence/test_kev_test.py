"""Unit tests for kev_test.py runner.

Uses synthetic mock fixtures only. No real email data or credentials.
"""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from kev_test import (
    CATEGORIES,
    anonymize_subject,
    calculate_metrics,
    calculate_percentile,
    generate_report_markdown,
    parse_args,
    run_evaluation,
    validate_input,
    validate_probabilities,
)


class TestKevTestValidation(unittest.TestCase):
    def setUp(self):
        self.valid_sample = [
            {
                "id": "item_1",
                "subject": "Synthetic dummy subject 1",
                "expected": "request",
                "rationale": "Dummy reason 1",
                "language": "en",
                "split": "dev",
                "gold_status": "provisional",
            },
            {
                "id": "item_2",
                "subject": "Synthetic dummy subject 2",
                "expected": "notice",
                "rationale": "Dummy reason 2",
                "language": "ko",
                "split": "test",
                "gold_status": "provisional",
            },
        ]

    def test_valid_input_passes(self):
        validate_input(self.valid_sample)

    def test_non_list_fails(self):
        with self.assertRaises(ValueError) as ctx:
            validate_input({"item": "not a list"})
        self.assertIn("JSON array", str(ctx.exception))

    def test_empty_list_fails(self):
        with self.assertRaises(ValueError) as ctx:
            validate_input([])
        self.assertIn("empty", str(ctx.exception))

    def test_item_not_dict_fails(self):
        with self.assertRaises(ValueError) as ctx:
            validate_input(["not a dict"])
        self.assertIn("must be a dict", str(ctx.exception))

    def test_missing_field_fails(self):
        bad = [dict(self.valid_sample[0])]
        del bad[0]["gold_status"]
        with self.assertRaises(ValueError) as ctx:
            validate_input(bad)
        self.assertIn("missing required fields", str(ctx.exception))

    def test_duplicate_id_fails(self):
        bad = [
            dict(self.valid_sample[0]),
            dict(self.valid_sample[1], id="item_1"),
        ]
        with self.assertRaises(ValueError) as ctx:
            validate_input(bad)
        self.assertIn("Duplicate id", str(ctx.exception))

    def test_invalid_category_fails(self):
        bad = [dict(self.valid_sample[0], expected="invalid_category_xyz")]
        with self.assertRaises(ValueError) as ctx:
            validate_input(bad)
        self.assertIn("not in CATEGORIES", str(ctx.exception))

    def test_invalid_split_fails(self):
        bad = [dict(self.valid_sample[0], split="invalid_split")]
        with self.assertRaises(ValueError) as ctx:
            validate_input(bad)
        self.assertIn("must be one of", str(ctx.exception))


class TestProbabilitiesValidation(unittest.TestCase):
    def test_valid_probabilities(self):
        probs = {cat: 0.2 for cat in CATEGORIES.keys()}
        validate_probabilities(probs)

    def test_missing_category_fails(self):
        probs = {"request": 0.5, "schedule": 0.5}
        with self.assertRaises(ValueError) as ctx:
            validate_probabilities(probs)
        self.assertIn("missing category keys", str(ctx.exception))

    def test_non_numeric_fails(self):
        probs = {cat: 0.2 for cat in CATEGORIES.keys()}
        probs["request"] = "not_a_number"
        with self.assertRaises(ValueError) as ctx:
            validate_probabilities(probs)
        self.assertIn("must be numeric", str(ctx.exception))

    def test_non_finite_fails(self):
        probs = {cat: 0.2 for cat in CATEGORIES.keys()}
        probs["request"] = float("inf")
        with self.assertRaises(ValueError) as ctx:
            validate_probabilities(probs)
        self.assertIn("not finite", str(ctx.exception))

    def test_out_of_bounds_fails(self):
        probs = {cat: 0.2 for cat in CATEGORIES.keys()}
        probs["notice"] = 1.05
        with self.assertRaises(ValueError) as ctx:
            validate_probabilities(probs)
        self.assertIn("out of bounds", str(ctx.exception))

        probs["notice"] = -0.01
        with self.assertRaises(ValueError) as ctx:
            validate_probabilities(probs)
        self.assertIn("out of bounds", str(ctx.exception))


class TestMetricsAndZeroDivision(unittest.TestCase):
    def test_zero_division_safety(self):
        # Empty results
        summary = calculate_metrics([])
        self.assertEqual(summary["overall"]["total_count"], 0)
        self.assertEqual(summary["overall"]["overall_accuracy"], 0.0)
        self.assertEqual(summary["overall"]["success_accuracy"], 0.0)
        for cat_info in summary["by_category"].values():
            self.assertEqual(cat_info["precision"], 0.0)
            self.assertEqual(cat_info["recall"], 0.0)
            self.assertEqual(cat_info["f1_score"], 0.0)

    def test_metrics_accuracy_and_f1(self):
        results = [
            # 1. request TP
            {
                "id": "1",
                "expected": "request",
                "predicted": "request",
                "correct": True,
                "error": None,
                "split": "dev",
                "language": "en",
                "elapsed_seconds": 0.1,
            },
            # 2. request FN (predicted schedule)
            {
                "id": "2",
                "expected": "request",
                "predicted": "schedule",
                "correct": False,
                "error": None,
                "split": "dev",
                "language": "en",
                "elapsed_seconds": 0.2,
            },
            # 3. schedule TP
            {
                "id": "3",
                "expected": "schedule",
                "predicted": "schedule",
                "correct": True,
                "error": None,
                "split": "test",
                "language": "ko",
                "elapsed_seconds": 0.3,
            },
            # 4. Failed request
            {
                "id": "4",
                "expected": "notice",
                "predicted": None,
                "correct": False,
                "error": "URLError: connection refused",
                "split": "test",
                "language": "ko",
                "elapsed_seconds": 0.4,
            },
        ]
        summary = calculate_metrics(results)
        overall = summary["overall"]
        self.assertEqual(overall["total_count"], 4)
        self.assertEqual(overall["success_count"], 3)
        self.assertEqual(overall["failure_count"], 1)
        self.assertEqual(overall["correct_count"], 2)
        # overall_acc = 2/4 = 0.5
        self.assertEqual(overall["overall_accuracy"], 0.5)
        # success_acc = 2/3 = 0.6667
        self.assertEqual(overall["success_accuracy"], 0.6667)

        # Category request:
        # TP = 1 (id 1)
        # FP = 0
        # FN = 1 (id 2)
        # Precision = 1 / 1 = 1.0, Recall = 1 / 2 = 0.5, F1 = 2*1*0.5/(1.5) = 0.6667
        req_metrics = summary["by_category"]["request"]
        self.assertEqual(req_metrics["precision"], 1.0)
        self.assertEqual(req_metrics["recall"], 0.5)
        self.assertEqual(req_metrics["f1_score"], 0.6667)
        self.assertEqual(req_metrics["support"], 2)

        # Notice has support 1 (id 4), but failed -> TP=0, FP=0, FN=1
        notice_metrics = summary["by_category"]["notice"]
        self.assertEqual(notice_metrics["tp"], 0)
        self.assertEqual(notice_metrics["fn"], 1)
        self.assertEqual(notice_metrics["precision"], 0.0)
        self.assertEqual(notice_metrics["recall"], 0.0)

        # Check confusion matrix error column
        cm = summary["confusion_matrix"]
        self.assertEqual(cm["notice"]["error"], 1)
        self.assertEqual(cm["request"]["request"], 1)
        self.assertEqual(cm["request"]["schedule"], 1)

    def test_percentile_calculation(self):
        values = [0.1, 0.2, 0.3, 0.4, 0.5]
        p50 = calculate_percentile(values, 50.0)
        p95 = calculate_percentile(values, 95.0)
        self.assertEqual(p50, 0.3)
        self.assertAlmostEqual(p95, 0.48, places=2)
        self.assertEqual(calculate_percentile([], 50.0), 0.0)


class TestFaultToleranceAndReportPrivacy(unittest.TestCase):
    def test_run_evaluation_continues_on_failure_and_anonymizes_report(self):
        test_data = [
            {
                "id": "dummy_01",
                "subject": "SUPER_SECRET_PII_12345",
                "expected": "request",
                "rationale": "dummy rationale",
                "language": "ko",
                "split": "dev",
                "gold_status": "provisional",
            },
            {
                "id": "dummy_02",
                "subject": "CONFIDENTIAL_FINANCIAL_INFO",
                "expected": "notice",
                "rationale": "dummy rationale",
                "language": "en",
                "split": "test",
                "gold_status": "provisional",
            },
        ]

        def mock_classify(subject):
            if "SECRET" in subject:
                # First one succeeds
                return {
                    "choice": "request",
                    "probabilities": {cat: 0.2 for cat in CATEGORIES.keys()},
                }
            # Second one raises an exception
            raise ConnectionResetError("Server crashed during request")

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            input_file = tmp_path / "eval_input.json"
            out_dir = tmp_path / "results_out"

            input_file.write_text(json.dumps(test_data), encoding="utf-8")

            # Run evaluation with mock
            summary = run_evaluation(
                input_path=input_file,
                output_dir=out_dir,
                split_filter="all",
                classify_fn=mock_classify,
            )

            # Check files exist
            self.assertTrue((out_dir / "results.json").exists())
            self.assertTrue((out_dir / "summary.json").exists())
            self.assertTrue((out_dir / "report.md").exists())

            # Check results.json content
            saved_results = json.loads((out_dir / "results.json").read_text(encoding="utf-8"))
            self.assertEqual(len(saved_results), 2)
            self.assertTrue(saved_results[0]["correct"])
            self.assertIsNone(saved_results[0]["error"])
            self.assertFalse(saved_results[1]["correct"])
            self.assertIn("ConnectionResetError", saved_results[1]["error"])

            # Check report.md privacy: RAW SUBJECT MUST NOT APPEAR
            report_text = (out_dir / "report.md").read_text(encoding="utf-8")
            self.assertNotIn("SUPER_SECRET_PII_12345", report_text)
            self.assertNotIn("CONFIDENTIAL_FINANCIAL_INFO", report_text)
            self.assertIn("[REDACTED len=", report_text)
            self.assertIn("provisional", report_text)
            self.assertIn("unknown", report_text)

    def test_split_filtering(self):
        test_data = [
            {
                "id": "dev_01",
                "subject": "Dev email subject",
                "expected": "request",
                "rationale": "r",
                "language": "en",
                "split": "dev",
                "gold_status": "provisional",
            },
            {
                "id": "test_01",
                "subject": "Test email subject",
                "expected": "notice",
                "rationale": "r",
                "language": "ko",
                "split": "test",
                "gold_status": "provisional",
            },
        ]

        def mock_classify(subject):
            return {
                "choice": "request",
                "probabilities": {cat: 0.2 for cat in CATEGORIES.keys()},
            }

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            input_file = tmp_path / "eval_input.json"
            out_dir = tmp_path / "results_out"

            input_file.write_text(json.dumps(test_data), encoding="utf-8")

            # Run with split=dev
            run_evaluation(
                input_path=input_file,
                output_dir=out_dir,
                split_filter="dev",
                classify_fn=mock_classify,
            )

            saved_results = json.loads((out_dir / "results.json").read_text(encoding="utf-8"))
            self.assertEqual(len(saved_results), 1)
            self.assertEqual(saved_results[0]["id"], "dev_01")


class TestCLIArgParsing(unittest.TestCase):
    def test_default_args(self):
        args = parse_args([])
        self.assertEqual(args.input, Path("data/gmail_eval.json"))
        self.assertEqual(args.output_dir, Path("eval_results"))
        self.assertEqual(args.split, "all")

    def test_custom_args(self):
        args = parse_args(["--input", "custom.json", "--output-dir", "custom_out", "--split", "dev"])
        self.assertEqual(args.input, Path("custom.json"))
        self.assertEqual(args.output_dir, Path("custom_out"))
        self.assertEqual(args.split, "dev")


if __name__ == "__main__":
    unittest.main()
