#!/usr/bin/env python3
"""Unit and boundary tests for routing_test.py.

Validates:
1. Model state strict boundary: state contains ONLY scenario, never gold/split/metadata
2. Input validation: 100 items, 25-balanced classes, 50 ko / 50 en, 50 dev / 50 test, duplicate detection
3. Probability validation: 4 classes, finite, [0, 1], sum approx 1.0
4. Percentile and metric calculations (accuracy, macro F1, confusion matrix, latency split)
5. Fail-soft behavior on network or API failures
"""
import copy
import http.server
import json
import math
from pathlib import Path
import threading
import unittest
from typing import Any, Dict, List

import routing_test


def make_dummy_protocol() -> Dict[str, Any]:
    return {
        "experiment": "test-routing",
        "instructions": "Test instructions",
        "criteria": {
            "tool_call": "Use tool",
            "clarify": "Ask info",
            "direct_answer": "Answer directly",
            "refuse": "Refuse request",
        },
        "dataset_constraints": {
            "count": 100,
            "class_counts": 25,
            "ko_count": 50,
            "en_count": 50,
            "dev_count": 50,
            "test_count": 50,
        },
    }


def make_dummy_item(
    idx: int,
    expected: str = "tool_call",
    language: str = "ko",
    split: str = "dev",
) -> Dict[str, Any]:
    return {
        "id": f"route-{idx:03d}",
        "scenario": {
            "user_request": f"Request {idx}",
            "context": f"Context {idx}",
            "available_tools": [f"tool_{idx}"],
            "permissions": f"perm_{idx}",
        },
        "expected": expected,
        "rationale": f"Rationale for {idx}",
        "language": language,
        "split": split,
        "gold_status": "provisional",
        "source": "synthetic-test",
    }


def make_balanced_100_items() -> List[Dict[str, Any]]:
    classes = ["tool_call", "clarify", "direct_answer", "refuse"]
    items = []
    idx = 1
    # 25 per class = 100
    for cls in classes:
        for i in range(25):
            # Alternate ko/en and dev/test to get 50/50 exactly
            lang = "ko" if (idx % 2 == 1) else "en"
            split = "dev" if (idx <= 50) else "test"
            items.append(make_dummy_item(idx, expected=cls, language=lang, split=split))
            idx += 1
    return items


class TestRoutingBoundaryAndSchema(unittest.TestCase):
    def setUp(self):
        self.protocol = make_dummy_protocol()

    def test_build_request_payload_strict_isolation(self):
        """Verify model state strictly contains ONLY scenario and NO metadata leaks."""
        scenario = {
            "user_request": "일정을 추가해줘",
            "context": "내일 오후 3시 회의",
            "available_tools": ["add_calendar_event"],
            "permissions": "calendar:write",
        }
        payload = routing_test.build_request_payload(scenario, self.protocol)

        self.assertEqual(payload["model"], "kev-latest")
        self.assertIn("questions", payload)
        self.assertIn("route", payload["questions"])
        self.assertEqual(payload["questions"]["route"]["criteria"], self.protocol["criteria"])

        # Decode state and verify it contains ONLY scenario keys
        decoded_state = json.loads(payload["state"])
        self.assertEqual(decoded_state, scenario)
        self.assertNotIn("expected", decoded_state)
        self.assertNotIn("rationale", decoded_state)
        self.assertNotIn("gold_status", decoded_state)
        self.assertNotIn("source", decoded_state)
        self.assertNotIn("split", decoded_state)

    def test_build_request_payload_rejects_forbidden_keys_in_scenario(self):
        """Verify ValueError is raised if scenario accidentally contains forbidden gold keys."""
        polluted_scenario = {
            "user_request": "test",
            "context": "test",
            "available_tools": [],
            "permissions": "all",
            "expected": "tool_call",  # LEAK!
        }
        with self.assertRaises(ValueError) as ctx:
            routing_test.build_request_payload(polluted_scenario, self.protocol)
        self.assertIn("Forbidden keys leaked", str(ctx.exception))

    def test_validate_input_balanced_passes(self):
        """Verify that a valid, balanced 100-item dataset passes schema validation."""
        dataset = make_balanced_100_items()
        # Should not raise
        routing_test.validate_input(dataset, self.protocol)

    def test_validate_input_detects_wrong_count(self):
        dataset = make_balanced_100_items()[:99]
        with self.assertRaises(ValueError) as ctx:
            routing_test.validate_input(dataset, self.protocol)
        self.assertIn("Dataset count mismatch", str(ctx.exception))

    def test_validate_input_detects_class_imbalance(self):
        dataset = make_balanced_100_items()
        dataset[0]["expected"] = "clarify"  # was tool_call, now 24 tool_call, 26 clarify
        with self.assertRaises(ValueError) as ctx:
            routing_test.validate_input(dataset, self.protocol)
        self.assertIn("Class imbalance", str(ctx.exception))

    def test_validate_input_detects_duplicate_scenario(self):
        dataset = make_balanced_100_items()
        # Duplicate scenario content
        dataset[1]["scenario"] = copy.deepcopy(dataset[0]["scenario"])
        with self.assertRaises(ValueError) as ctx:
            routing_test.validate_input(dataset, self.protocol)
        self.assertIn("duplicate scenario", str(ctx.exception))

    def test_validate_input_detects_missing_scenario_field(self):
        dataset = make_balanced_100_items()
        del dataset[0]["scenario"]["permissions"]
        with self.assertRaises(ValueError) as ctx:
            routing_test.validate_input(dataset, self.protocol)
        self.assertIn("missing fields", str(ctx.exception))


class TestProbabilityValidation(unittest.TestCase):
    def setUp(self):
        self.keys = ["tool_call", "clarify", "direct_answer", "refuse"]

    def test_valid_probabilities(self):
        probs = {"tool_call": 0.70, "clarify": 0.10, "direct_answer": 0.15, "refuse": 0.05}
        # Should not raise
        routing_test.validate_probabilities(probs, self.keys)

    def test_missing_key_fails(self):
        probs = {"tool_call": 0.80, "clarify": 0.10, "direct_answer": 0.10}
        with self.assertRaises(ValueError) as ctx:
            routing_test.validate_probabilities(probs, self.keys)
        self.assertIn("missing routing keys", str(ctx.exception))

    def test_out_of_bounds_fails(self):
        probs = {"tool_call": 1.20, "clarify": 0.0, "direct_answer": 0.0, "refuse": -0.2}
        with self.assertRaises(ValueError) as ctx:
            routing_test.validate_probabilities(probs, self.keys)
        self.assertIn("out of bounds", str(ctx.exception))

    def test_non_finite_fails(self):
        probs = {"tool_call": float("nan"), "clarify": 0.5, "direct_answer": 0.25, "refuse": 0.25}
        with self.assertRaises(ValueError) as ctx:
            routing_test.validate_probabilities(probs, self.keys)
        self.assertIn("not finite", str(ctx.exception))

    def test_sum_deviation_fails(self):
        probs = {"tool_call": 0.5, "clarify": 0.1, "direct_answer": 0.1, "refuse": 0.1}  # sum = 0.8
        with self.assertRaises(ValueError) as ctx:
            routing_test.validate_probabilities(probs, self.keys)
        self.assertIn("deviates significantly", str(ctx.exception))


class TestMetricsCalculation(unittest.TestCase):
    def setUp(self):
        self.keys = ["tool_call", "clarify", "direct_answer", "refuse"]
        self.protocol = make_dummy_protocol()

    def test_calculate_metrics_perfect_score(self):
        results = []
        for i in range(100):
            cat = self.keys[i % 4]
            results.append({
                "id": f"route-{i+1:03d}",
                "expected": cat,
                "predicted": cat,
                "correct": True,
                "error": None,
                "split": "dev" if i < 50 else "test",
                "language": "ko" if i % 2 == 0 else "en",
                "elapsed_seconds": 0.10,
            })
        summary = routing_test.calculate_metrics(results, self.keys, self.protocol)
        self.assertEqual(summary["overall"]["total_count"], 100)
        self.assertEqual(summary["overall"]["success_count"], 100)
        self.assertEqual(summary["overall"]["failure_count"], 0)
        self.assertEqual(summary["overall"]["overall_accuracy"], 1.0)
        self.assertEqual(summary["overall"]["macro_f1"], 1.0)
        self.assertEqual(summary["overall"]["majority_baseline"], 0.25)

    def test_calculate_metrics_with_errors_and_latency_separation(self):
        results = [
            {"id": "r1", "expected": "tool_call", "predicted": "tool_call", "correct": True, "error": None, "split": "dev", "language": "ko", "elapsed_seconds": 0.20},
            {"id": "r2", "expected": "clarify", "predicted": "direct_answer", "correct": False, "error": None, "split": "dev", "language": "en", "elapsed_seconds": 0.40},
            {"id": "r3", "expected": "refuse", "predicted": None, "correct": False, "error": "HTTP 500", "split": "test", "language": "ko", "elapsed_seconds": 1.50},
        ]
        summary = routing_test.calculate_metrics(results, self.keys, self.protocol)
        self.assertEqual(summary["overall"]["total_count"], 3)
        self.assertEqual(summary["overall"]["success_count"], 2)
        self.assertEqual(summary["overall"]["failure_count"], 1)
        self.assertEqual(summary["overall"]["correct_count"], 1)
        self.assertEqual(summary["overall"]["latency_p50_seconds_success"], 0.30)
        self.assertEqual(summary["overall"]["latency_p50_seconds_failure"], 1.50)
        self.assertEqual(summary["confusion_matrix"]["refuse"]["error"], 1)


class MockKevServerHandler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers["Content-Length"])
        body = self.rfile.read(content_length).decode("utf-8")
        req_json = json.loads(body)

        # Check path
        if self.path == "/v1/systemone":
            # Return valid response
            resp = {
                "model": "kev-latest",
                "answers": {
                    "route": {
                        "type": "choice",
                        "choice": "tool_call",
                        "confidence": 0.85,
                        "probabilities": {
                            "tool_call": 0.85,
                            "clarify": 0.05,
                            "direct_answer": 0.05,
                            "refuse": 0.05,
                        },
                    }
                },
                "latency_ms": 25.4,
            }
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(resp).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Suppress logging
        pass


class TestMockKevSystemOneIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = http.server.HTTPServer(("127.0.0.1", 0), MockKevServerHandler)
        cls.port = cls.server.server_port
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def test_query_kev_systemone(self):
        protocol = make_dummy_protocol()
        scenario = {
            "user_request": "조회해줘",
            "context": "내용",
            "available_tools": ["search"],
            "permissions": "read",
        }
        payload = routing_test.build_request_payload(scenario, protocol)
        endpoint = f"http://127.0.0.1:{self.port}/v1/systemone"

        resp, elapsed = routing_test.query_kev_systemone(endpoint, payload, timeout=5.0)
        self.assertIn("answers", resp)
        self.assertIn("route", resp["answers"])
        self.assertEqual(resp["answers"]["route"]["choice"], "tool_call")
        self.assertGreater(elapsed, 0.0)


if __name__ == "__main__":
    unittest.main()
