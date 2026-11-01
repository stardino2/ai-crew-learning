#!/usr/bin/env python3
"""Run evaluation for Kev tool-call routing baseline.

Standard library only.
Meets all protocol rules in tasks/routing-protocol.json:
- Strictly isolates model state to json.dumps(item['scenario'])
- Verifies input schema, 100 items, 25-balanced classes, 50/50 lang and split
- Validates 4-class probabilities (finite, 0..1, sum approx 1.0)
- Stores full raw request payloads and responses
- Computes overall/split/language accuracy, macro F1, confusion matrix, p50/p95 latencies
- Clarifies provisional gold labels and out-of-scope model diagnostic nature
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sys
import time
from typing import Any, Dict, List, Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

SCENARIO_REQUIRED_FIELDS = {"user_request", "context", "available_tools", "permissions"}
DATASET_REQUIRED_FIELDS = {
    "id",
    "scenario",
    "expected",
    "rationale",
    "language",
    "split",
    "gold_status",
    "source",
}
VALID_SPLITS = {"dev", "test"}
VALID_LANGUAGES = {"ko", "en"}

CRITERIA_KO = {
    "tool_call": "도구호출 (tool_call)",
    "clarify": "명확화요청 (clarify)",
    "direct_answer": "직접응답 (direct_answer)",
    "refuse": "요청거절 (refuse)",
}


def compute_sha256(path: Path) -> str:
    """Compute SHA256 hex digest of a file."""
    hasher = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def load_protocol(protocol_path: Path) -> Dict[str, Any]:
    """Load and validate the routing protocol JSON."""
    if not protocol_path.exists():
        raise FileNotFoundError(f"Protocol file not found: {protocol_path}")
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    required_keys = {"experiment", "instructions", "criteria", "dataset_constraints"}
    missing = required_keys - set(protocol.keys())
    if missing:
        raise ValueError(f"Protocol missing required keys: {sorted(list(missing))}")
    return protocol


def validate_input(data: Any, protocol: Dict[str, Any]) -> None:
    """Validate full input JSON dataset against schema and protocol constraints."""
    if not isinstance(data, list):
        raise ValueError(f"Input data must be a JSON array (list), got {type(data).__name__}")

    constraints = protocol.get("dataset_constraints", {})
    expected_count = constraints.get("count", 100)
    expected_class_counts = constraints.get("class_counts", 25)
    expected_ko_count = constraints.get("ko_count", 50)
    expected_en_count = constraints.get("en_count", 50)
    expected_dev_count = constraints.get("dev_count", 50)
    expected_test_count = constraints.get("test_count", 50)

    if len(data) != expected_count:
        raise ValueError(f"Dataset count mismatch: expected {expected_count}, got {len(data)}")

    valid_criteria = set(protocol["criteria"].keys())
    seen_ids = set()
    scenario_hashes = set()
    class_counter: Dict[str, int] = {k: 0 for k in valid_criteria}
    lang_counter: Dict[str, int] = {"ko": 0, "en": 0}
    split_counter: Dict[str, int] = {"dev": 0, "test": 0}

    for idx, item in enumerate(data):
        if not isinstance(item, dict):
            raise ValueError(f"Item at index {idx} must be a dict, got {type(item).__name__}")

        missing = DATASET_REQUIRED_FIELDS - set(item.keys())
        if missing:
            raise ValueError(
                f"Item at index {idx} (id={item.get('id')!r}) missing required fields: {sorted(list(missing))}"
            )

        item_id = str(item["id"]).strip()
        if not item_id:
            raise ValueError(f"Item at index {idx} has an empty 'id'")
        if item_id in seen_ids:
            raise ValueError(f"Duplicate id found at index {idx}: {item_id}")
        seen_ids.add(item_id)

        # Validate scenario sub-object
        scenario = item["scenario"]
        if not isinstance(scenario, dict):
            raise ValueError(f"Item {item_id} 'scenario' must be dict, got {type(scenario).__name__}")
        scenario_missing = SCENARIO_REQUIRED_FIELDS - set(scenario.keys())
        if scenario_missing:
            raise ValueError(
                f"Item {item_id} 'scenario' missing fields: {sorted(list(scenario_missing))}"
            )

        if not isinstance(scenario["user_request"], str) or not scenario["user_request"].strip():
            raise ValueError(f"Item {item_id} 'user_request' must be a non-empty string")
        if not isinstance(scenario["context"], str):
            raise ValueError(f"Item {item_id} 'context' must be a string")
        if not isinstance(scenario["available_tools"], list):
            raise ValueError(f"Item {item_id} 'available_tools' must be a list")
        if not isinstance(scenario["permissions"], str):
            raise ValueError(f"Item {item_id} 'permissions' must be a string")

        # Duplicate scenario check
        scen_repr = json.dumps(scenario, sort_keys=True, ensure_ascii=False)
        scen_hash = hashlib.sha256(scen_repr.encode("utf-8")).hexdigest()
        if scen_hash in scenario_hashes:
            raise ValueError(f"Item {item_id} has duplicate scenario content (hash={scen_hash})")
        scenario_hashes.add(scen_hash)

        # Expected category
        expected = item["expected"]
        if expected not in valid_criteria:
            raise ValueError(
                f"Item {item_id} 'expected' category '{expected}' not in criteria: {sorted(list(valid_criteria))}"
            )
        class_counter[expected] += 1

        # Language
        lang = item["language"]
        if lang not in VALID_LANGUAGES:
            raise ValueError(f"Item {item_id} 'language' must be one of {sorted(list(VALID_LANGUAGES))}, got '{lang}'")
        lang_counter[lang] += 1

        # Split
        split = item["split"]
        if split not in VALID_SPLITS:
            raise ValueError(f"Item {item_id} 'split' must be one of {sorted(list(VALID_SPLITS))}, got '{split}'")
        split_counter[split] += 1

        # Rationale, gold_status, source
        if not isinstance(item["rationale"], str) or not item["rationale"].strip():
            raise ValueError(f"Item {item_id} 'rationale' must be a non-empty string")
        if not isinstance(item["gold_status"], str) or not item["gold_status"].strip():
            raise ValueError(f"Item {item_id} 'gold_status' must be a non-empty string")
        if not isinstance(item["source"], str) or not item["source"].strip():
            raise ValueError(f"Item {item_id} 'source' must be a non-empty string")

    # Verify distributions
    for c, cnt in class_counter.items():
        if cnt != expected_class_counts:
            raise ValueError(
                f"Class imbalance for '{c}': expected {expected_class_counts}, got {cnt}"
            )

    if lang_counter["ko"] != expected_ko_count or lang_counter["en"] != expected_en_count:
        raise ValueError(
            f"Language count mismatch: expected ko={expected_ko_count}, en={expected_en_count}; got {lang_counter}"
        )

    if split_counter["dev"] != expected_dev_count or split_counter["test"] != expected_test_count:
        raise ValueError(
            f"Split count mismatch: expected dev={expected_dev_count}, test={expected_test_count}; got {split_counter}"
        )


def build_request_payload(scenario: Dict[str, Any], protocol: Dict[str, Any]) -> Dict[str, Any]:
    """Build Kev API request payload.

    CRITICAL RULE:
    The model state MUST be strictly json.dumps(scenario).
    NO expected labels, rationales, gold_status, source, or split metadata are allowed.
    """
    forbidden_keys = {"expected", "rationale", "gold_status", "source", "split"}
    found_forbidden = forbidden_keys.intersection(scenario.keys())
    if found_forbidden:
        raise ValueError(f"Forbidden keys leaked into scenario object: {sorted(list(found_forbidden))}")

    state_str = json.dumps(scenario, ensure_ascii=False)

    payload = {
        "model": "kev-latest",
        "state": state_str,
        "questions": {
            "route": {
                "type": "choice",
                "instructions": protocol["instructions"],
                "criteria": protocol["criteria"],
            }
        },
    }
    return payload


def validate_probabilities(probabilities: Any, valid_keys: List[str]) -> None:
    """Validate 4-class routing probabilities: finite numbers in [0.0, 1.0], sum approx 1.0."""
    if not isinstance(probabilities, dict):
        raise ValueError(f"probabilities must be dict, got {type(probabilities).__name__}")
    missing_keys = set(valid_keys) - set(probabilities.keys())
    if missing_keys:
        raise ValueError(f"probabilities missing routing keys: {sorted(list(missing_keys))}")

    prob_sum = 0.0
    for k in valid_keys:
        val = probabilities.get(k)
        if not isinstance(val, (int, float)):
            raise ValueError(f"probability for '{k}' must be numeric, got {val!r}")
        if not math.isfinite(val):
            raise ValueError(f"probability for '{k}' is not finite: {val}")
        if not (0.0 <= val <= 1.0):
            raise ValueError(f"probability for '{k}' out of bounds [0.0, 1.0]: {val}")
        prob_sum += float(val)

    if not math.isclose(prob_sum, 1.0, abs_tol=1e-2):
        raise ValueError(f"probabilities sum ({prob_sum:.4f}) deviates significantly from 1.0")


def query_kev_systemone(
    endpoint: str,
    payload: Dict[str, Any],
    timeout: float = 180.0,
) -> Tuple[Dict[str, Any], float]:
    """Execute POST request to Kev systemone endpoint with client-measured round-trip latency."""
    encoded_data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = Request(
        endpoint,
        data=encoded_data,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    start_time = time.perf_counter()
    with urlopen(req, timeout=timeout) as response:
        raw_body = response.read().decode("utf-8")
    elapsed_seconds = round(time.perf_counter() - start_time, 4)
    parsed_response = json.loads(raw_body)
    return parsed_response, elapsed_seconds


def calculate_percentile(values: List[float], p: float) -> float:
    """Calculate percentile p (0-100) using linear interpolation."""
    if not values:
        return 0.0
    sorted_values = sorted(values)
    k = (len(sorted_values) - 1) * (p / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return round(float(sorted_values[int(k)]), 4)
    d0 = sorted_values[int(f)] * (c - k)
    d1 = sorted_values[int(c)] * (k - f)
    return round(float(d0 + d1), 4)


def calculate_metrics(
    results: List[Dict[str, Any]],
    valid_keys: List[str],
    protocol: Dict[str, Any],
    model_metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Calculate accuracy, macro F1, confusion matrix, split/language breakdowns, and latency percentiles."""
    total_count = len(results)
    success_results = [r for r in results if r.get("error") is None]
    failure_results = [r for r in results if r.get("error") is not None]

    success_count = len(success_results)
    failure_count = len(failure_results)
    correct_count = sum(1 for r in results if r.get("correct") is True)

    overall_accuracy = round(correct_count / total_count, 4) if total_count > 0 else 0.0
    success_accuracy = round(correct_count / success_count, 4) if success_count > 0 else 0.0

    # Separate success and failure latencies
    success_latencies = [
        r["elapsed_seconds"]
        for r in success_results
        if r.get("elapsed_seconds") is not None and isinstance(r["elapsed_seconds"], (int, float))
    ]
    failure_latencies = [
        r["elapsed_seconds"]
        for r in failure_results
        if r.get("elapsed_seconds") is not None and isinstance(r["elapsed_seconds"], (int, float))
    ]

    p50_success_latency = calculate_percentile(success_latencies, 50.0)
    p95_success_latency = calculate_percentile(success_latencies, 95.0)
    p50_failure_latency = calculate_percentile(failure_latencies, 50.0) if failure_latencies else None
    p95_failure_latency = calculate_percentile(failure_latencies, 95.0) if failure_latencies else None

    # Category metrics
    category_metrics = {}
    f1_list = []
    for cat in valid_keys:
        tp = sum(1 for r in results if r.get("expected") == cat and r.get("predicted") == cat)
        fp = sum(1 for r in results if r.get("expected") != cat and r.get("predicted") == cat)
        fn = sum(1 for r in results if r.get("expected") == cat and r.get("predicted") != cat)
        support = sum(1 for r in results if r.get("expected") == cat)

        precision = round(tp / (tp + fp), 4) if (tp + fp) > 0 else 0.0
        recall = round(tp / (tp + fn), 4) if (tp + fn) > 0 else 0.0
        f1 = (
            round((2 * precision * recall) / (precision + recall), 4)
            if (precision + recall) > 0
            else 0.0
        )
        f1_list.append(f1)

        category_metrics[cat] = {
            "name_ko": CRITERIA_KO.get(cat, cat),
            "precision": precision,
            "recall": recall,
            "f1_score": f1,
            "support": support,
            "tp": tp,
            "fp": fp,
            "fn": fn,
        }

    macro_f1 = round(sum(f1_list) / len(f1_list), 4) if f1_list else 0.0

    # Confusion matrix: actual x predicted (+ "error")
    confusion_matrix = {act: {pred: 0 for pred in valid_keys + ["error"]} for act in valid_keys}
    for r in results:
        act = r.get("expected")
        if act not in confusion_matrix:
            confusion_matrix[act] = {pred: 0 for pred in valid_keys + ["error"]}
        pred = r.get("predicted")
        if r.get("error") is not None or pred is None:
            confusion_matrix[act]["error"] += 1
        elif pred in confusion_matrix[act]:
            confusion_matrix[act][pred] += 1
        else:
            confusion_matrix[act]["error"] += 1

    # Split breakdown
    splits = sorted(list(set(r.get("split", "unknown") for r in results)))
    split_metrics = {}
    for s in splits:
        s_results = [r for r in results if r.get("split") == s]
        s_total = len(s_results)
        s_success = sum(1 for r in s_results if r.get("error") is None)
        s_failure = sum(1 for r in s_results if r.get("error") is not None)
        s_correct = sum(1 for r in s_results if r.get("correct") is True)
        split_metrics[s] = {
            "total": s_total,
            "success": s_success,
            "failure": s_failure,
            "correct": s_correct,
            "overall_accuracy": round(s_correct / s_total, 4) if s_total > 0 else 0.0,
            "success_accuracy": round(s_correct / s_success, 4) if s_success > 0 else 0.0,
        }

    # Language breakdown
    languages = sorted(list(set(r.get("language", "unknown") for r in results)))
    language_metrics = {}
    for lang in languages:
        l_results = [r for r in results if r.get("language") == lang]
        l_total = len(l_results)
        l_success = sum(1 for r in l_results if r.get("error") is None)
        l_failure = sum(1 for r in l_results if r.get("error") is not None)
        l_correct = sum(1 for r in l_results if r.get("correct") is True)
        language_metrics[lang] = {
            "total": l_total,
            "success": l_success,
            "failure": l_failure,
            "correct": l_correct,
            "overall_accuracy": round(l_correct / l_total, 4) if l_total > 0 else 0.0,
            "success_accuracy": round(l_correct / l_success, 4) if l_success > 0 else 0.0,
        }

    return {
        "metadata": {
            "model": model_metadata.get("name", "kev-latest") if model_metadata else "kev-latest",
            "model_run": model_metadata.get("run", "jaredpalmer/kev-0.8b@v1.0") if model_metadata else "jaredpalmer/kev-0.8b@v1.0",
            "device": model_metadata.get("device", "cpu") if model_metadata else "cpu",
            "evaluation_time_utc": datetime.now(timezone.utc).isoformat(),
            "majority_baseline": 0.25,
            "scope_note": protocol.get(
                "scope_note",
                "Kev-0.8B official model card lists tool-call routing as out of scope; this is a diagnostic synthetic benchmark.",
            ),
            "provisional_gold_note": "합성 데이터셋의 정답은 사전 정의된 잠정(provisional) 기준이며 인간 검수를 거치지 않은 진단용 레이블입니다.",
            "confidence_note": "모델이 출력한 confidence/probability는 보정(calibration)되지 않은 softmax 지표이며 정답 보증(correctness guarantee)이 아닙니다.",
            "latency_measurement_note": "HTTP 왕복 측정 시간(단위: 초), 모델 내부 추론 시간과 구별되며 성공 요청과 실패 요청을 분리 집계함.",
        },
        "overall": {
            "total_count": total_count,
            "success_count": success_count,
            "failure_count": failure_count,
            "correct_count": correct_count,
            "overall_accuracy": overall_accuracy,
            "success_accuracy": success_accuracy,
            "majority_baseline": 0.25,
            "macro_f1": macro_f1,
            "latency_p50_seconds_success": p50_success_latency,
            "latency_p95_seconds_success": p95_success_latency,
            "latency_p50_seconds_failure": p50_failure_latency,
            "latency_p95_seconds_failure": p95_failure_latency,
        },
        "by_split": split_metrics,
        "by_language": language_metrics,
        "by_category": category_metrics,
        "confusion_matrix": confusion_matrix,
    }


def generate_report_markdown(summary: Dict[str, Any], results: List[Dict[str, Any]]) -> str:
    """Generate comprehensive Markdown report."""
    meta = summary.get("metadata", {})
    overall = summary.get("overall", {})
    by_split = summary.get("by_split", {})
    by_lang = summary.get("by_language", {})
    by_cat = summary.get("by_category", {})
    cm = summary.get("confusion_matrix", {})

    lines = []
    lines.append("# Kev 도구 라우팅 벤치마크 평가 보고서 (Routing Baseline 20261030)")
    lines.append("")
    lines.append("> [!IMPORTANT]")
    lines.append(f"> **범위 및 진단 안내**: {meta.get('scope_note')}")
    lines.append(f"> **잠정 라벨 한계**: {meta.get('provisional_gold_note')}")
    lines.append(f"> **확신도 주의**: {meta.get('confidence_note')}")
    lines.append("")
    lines.append("## 1. 평가 개요 및 실행 환경")
    lines.append(f"- **실행 모델**: `{meta.get('model', 'kev-latest')}` (`{meta.get('model_run', 'unknown')}`)")
    lines.append(f"- **연산 장치**: `{meta.get('device', 'cpu')}`")
    lines.append(f"- **평가 시각 (UTC)**: `{meta.get('evaluation_time_utc')}`")
    lines.append(f"- **Majority Class Baseline**: `25.0%` (4개 클래스 균등 25건 배분)")
    lines.append(f"- **전체 일치율 (Overall Accuracy)**: **{overall.get('overall_accuracy', 0.0) * 100:.2f}%** ({overall.get('correct_count')}/{overall.get('total_count')})")
    lines.append(f"- **성공 건 일치율 (Success Accuracy)**: **{overall.get('success_accuracy', 0.0) * 100:.2f}%** ({overall.get('correct_count')}/{overall.get('success_count')})")
    lines.append(f"- **Macro F1 Score**: **{overall.get('macro_f1', 0.0):.4f}**")
    lines.append(f"- **성공 요청 레이턴시 (클라이언트 관측 HTTP 왕복)**: p50 = `{overall.get('latency_p50_seconds_success')}s`, p95 = `{overall.get('latency_p95_seconds_success')}s`")
    if overall.get("latency_p50_seconds_failure") is not None:
        lines.append(f"- **실패 요청 레이턴시**: p50 = `{overall.get('latency_p50_seconds_failure')}s`, p95 = `{overall.get('latency_p95_seconds_failure')}s`")
    lines.append("")

    lines.append("## 2. 분할(Split) 및 언어(Language)별 성과")
    lines.append("### Split 성과")
    lines.append("| Split | 총 문항 | 성공 | 실패 | 정답 | 전체 일치율 | 성공 일치율 |")
    lines.append("|---|---|---|---|---|---|---|")
    for s_name, s_data in by_split.items():
        lines.append(
            f"| `{s_name}` | {s_data['total']} | {s_data['success']} | {s_data['failure']} | {s_data['correct']} | {s_data['overall_accuracy']*100:.2f}% | {s_data['success_accuracy']*100:.2f}% |"
        )
    lines.append("")

    lines.append("### Language 성과")
    lines.append("| Language | 총 문항 | 성공 | 실패 | 정답 | 전체 일치율 | 성공 일치율 |")
    lines.append("|---|---|---|---|---|---|---|")
    for l_name, l_data in by_lang.items():
        lines.append(
            f"| `{l_name}` | {l_data['total']} | {l_data['success']} | {l_data['failure']} | {l_data['correct']} | {l_data['overall_accuracy']*100:.2f}% | {l_data['success_accuracy']*100:.2f}% |"
        )
    lines.append("")

    lines.append("## 3. 라우팅 클래스별 상세 성능 지표")
    lines.append("| 클래스 | 한국어 명칭 | Support | Precision | Recall | F1 Score | TP | FP | FN |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for cat_name, cat_data in by_cat.items():
        lines.append(
            f"| `{cat_name}` | {cat_data['name_ko']} | {cat_data['support']} | {cat_data['precision']:.4f} | {cat_data['recall']:.4f} | {cat_data['f1_score']:.4f} | {cat_data['tp']} | {cat_data['fp']} | {cat_data['fn']} |"
        )
    lines.append("")

    lines.append("## 4. 혼동 행렬 (Confusion Matrix)")
    categories = list(by_cat.keys())
    header_cols = ["실제(Actual) \\ 예측(Pred)"] + [f"`{c}`" for c in categories] + ["`error`"]
    lines.append("| " + " | ".join(header_cols) + " |")
    lines.append("|" + "---|"*len(header_cols))
    for act in categories:
        row = [f"`{act}` ({CRITERIA_KO.get(act, act)})"]
        for pred in categories + ["error"]:
            row.append(str(cm.get(act, {}).get(pred, 0)))
        lines.append("| " + " | ".join(row) + " |")
    lines.append("")

    lines.append("## 5. 실행 제약 및 안전성 검증")
    lines.append("- **모델 입력 경계 검증**: API 요청 payload의 `state` 필드에는 순수 `scenario` JSON 객체만 포함되었으며, `expected`, `rationale`, `gold_status`, `source`, `split` 등의 레이블 및 메타데이터는 완전히 차단되었습니다.")
    lines.append("- **개인정보 및 프라이버시**: 합성 데이터셋 시나리오를 사용하였으며 실제 메일함이나 비인가 자원에 접근하지 않았습니다.")
    lines.append("- **단일 패스 실행**: 학습, 파라미터 튜닝, 재실험, 프롬프트 변경 없이 프로토콜 규격 그대로 단 1회 실행되었습니다.")
    lines.append("")

    return "\n".join(lines)


def fetch_model_metadata(models_endpoint: str) -> Dict[str, Any]:
    """Fetch live model metadata from Kev server."""
    req = Request(models_endpoint, method="GET")
    with urlopen(req, timeout=10.0) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    models = data.get("models", [])
    for m in models:
        if m.get("name") == "kev-latest":
            return m
    if models:
        return models[0]
    return {}


def main() -> None:
    parser = argparse.ArgumentParser(description="Run authorized routing benchmark for Kev.")
    parser.add_argument("--data", type=str, default="data/routing_eval.json", help="Path to routing_eval.json")
    parser.add_argument("--protocol", type=str, default="tasks/routing-protocol.json", help="Path to routing-protocol.json")
    parser.add_argument("--output-dir", type=str, default="eval_results/routing-baseline-20261030", help="Output directory")
    parser.add_argument("--endpoint", type=str, default="http://127.0.0.1:8009/v1/systemone", help="Kev systemone API endpoint")
    parser.add_argument("--models-endpoint", type=str, default="http://127.0.0.1:8009/v1/models", help="Kev models API endpoint")
    parser.add_argument("--timeout", type=float, default=180.0, help="Per-request timeout in seconds")
    parser.add_argument("--validate-only", action="store_true", help="Only validate dataset and protocol schema, do not execute API")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent
    data_path = (project_root / args.data).resolve()
    protocol_path = (project_root / args.protocol).resolve()
    output_dir = (project_root / args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"[INIT] Loading protocol from {protocol_path}", flush=True)
    protocol = load_protocol(protocol_path)
    valid_keys = sorted(list(protocol["criteria"].keys()))

    if not data_path.exists():
        print(f"[WAIT] Dataset file does not exist yet: {data_path}", flush=True)
        sys.exit(2)

    print(f"[INIT] Loading dataset from {data_path}", flush=True)
    dataset = json.loads(data_path.read_text(encoding="utf-8"))

    print("[VALIDATE] Checking input schema, counts, balance, and constraints...", flush=True)
    validate_input(dataset, protocol)
    print(f"[VALIDATE] Dataset OK: {len(dataset)} items, balanced 4 classes, 50 ko / 50 en, 50 dev / 50 test.", flush=True)

    if args.validate_only:
        print("[VALIDATE] --validate-only specified. Exiting successfully.")
        return

    # Check server availability and fetch model metadata
    print(f"[INIT] Probing Kev model metadata at {args.models_endpoint}...", flush=True)
    try:
        model_meta = fetch_model_metadata(args.models_endpoint)
        print(f"[INIT] Connected to Kev server: model={model_meta.get('name')}, run={model_meta.get('run')}, device={model_meta.get('device')}", flush=True)
    except Exception as e:
        print(f"[ERROR] Failed to query models endpoint: {e}", file=sys.stderr)
        sys.exit(1)

    # Freeze hashes in run-manifest.json BEFORE execution
    manifest_path = output_dir / "run-manifest.json"
    manifest_data = {
        "run_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "timestamp_start_utc": datetime.now(timezone.utc).isoformat(),
        "experiment": protocol.get("experiment", "routing-baseline-20261030"),
        "model_run": model_meta.get("run", "jaredpalmer/kev-0.8b@v1.0"),
        "api_model_alias": model_meta.get("name", "kev-latest"),
        "device": model_meta.get("device", "cpu"),
        "backend": model_meta.get("backend", "torch"),
        "dtype": model_meta.get("dtype", "float32"),
        "temperature": model_meta.get("temperature", 2.3510958125672174),
        "data_path": str(data_path),
        "data_sha256": compute_sha256(data_path),
        "protocol_path": str(protocol_path),
        "protocol_sha256": compute_sha256(protocol_path),
        "code_path": str(Path(__file__).resolve()),
        "code_sha256": compute_sha256(Path(__file__).resolve()),
        "status": "executing",
        "scope_note": protocol.get("scope_note", ""),
        "majority_class_baseline": 0.25,
        "instructions": protocol["instructions"],
        "criteria": protocol["criteria"],
    }
    manifest_path.write_text(json.dumps(manifest_data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[MANIFEST] Pre-execution run-manifest frozen at {manifest_path}", flush=True)

    raw_calls_path = output_dir / "raw_calls.jsonl"
    results_path = output_dir / "results.json"
    summary_path = output_dir / "summary.json"
    report_path = output_dir / "report.md"

    # Open raw_calls.jsonl for streaming append
    raw_calls_file = raw_calls_path.open("w", encoding="utf-8")

    results: List[Dict[str, Any]] = []
    print(f"[EXEC] Beginning 100-item routing evaluation against {args.endpoint}...", flush=True)

    for idx, item in enumerate(dataset, start=1):
        item_id = item["id"]
        scenario = item["scenario"]
        expected = item["expected"]

        # Build payload strictly without gold labels
        payload = build_request_payload(scenario, protocol)

        predicted_choice: Optional[str] = None
        probabilities: Optional[Dict[str, float]] = None
        confidence: Optional[float] = None
        latency_ms: Optional[float] = None
        elapsed_seconds: Optional[float] = None
        error_msg: Optional[str] = None
        raw_response: Optional[Dict[str, Any]] = None

        try:
            raw_response, elapsed_seconds = query_kev_systemone(args.endpoint, payload, timeout=args.timeout)
            answers = raw_response.get("answers", {})
            route_answer = answers.get("route")
            if not route_answer:
                raise ValueError(f"Missing 'route' key in answers: {list(answers.keys())}")

            predicted_choice = route_answer.get("choice")
            if predicted_choice not in valid_keys:
                raise ValueError(f"Predicted choice '{predicted_choice}' not in valid criteria {valid_keys}")

            probabilities = route_answer.get("probabilities")
            validate_probabilities(probabilities, valid_keys)

            confidence = route_answer.get("confidence")
            latency_ms = raw_response.get("latency_ms")

        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            if elapsed_seconds is None:
                elapsed_seconds = 0.0

        is_correct = (predicted_choice == expected) if error_msg is None else False
        mark = "O" if is_correct else ("E" if error_msg else "X")

        # Record raw interaction
        raw_record = {
            "index": idx,
            "id": item_id,
            "request_payload": payload,
            "raw_response": raw_response,
            "elapsed_seconds": elapsed_seconds,
            "error": error_msg,
        }
        raw_calls_file.write(json.dumps(raw_record, ensure_ascii=False) + "\n")
        raw_calls_file.flush()

        item_result = {
            "id": item_id,
            "scenario": scenario,
            "expected": expected,
            "rationale": item["rationale"],
            "language": item["language"],
            "split": item["split"],
            "gold_status": item["gold_status"],
            "source": item["source"],
            "predicted": predicted_choice,
            "probabilities": probabilities,
            "confidence": confidence,
            "correct": is_correct,
            "elapsed_seconds": elapsed_seconds,
            "latency_ms": latency_ms,
            "error": error_msg,
        }
        results.append(item_result)

        exp_ko = CRITERIA_KO.get(expected, expected)
        pred_ko = CRITERIA_KO.get(predicted_choice, str(predicted_choice))
        conf_str = f"{confidence:.4f}" if confidence is not None else "N/A"
        err_str = f" | 오류: {error_msg}" if error_msg else ""
        print(
            f"[{idx:03d}/100] [{mark}] ID: {item_id} | 예상: {exp_ko} | 결과: {pred_ko} | 확신도: {conf_str} | 소요: {elapsed_seconds}s{err_str}",
            flush=True,
        )

    raw_calls_file.close()

    print("[SUMMARY] Calculating comprehensive evaluation metrics...", flush=True)
    summary = calculate_metrics(results, valid_keys, protocol, model_metadata=model_meta)

    # Save results and summary
    results_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    # Generate Markdown report
    report_md = generate_report_markdown(summary, results)
    report_path.write_text(report_md, encoding="utf-8")

    # Finalize manifest
    manifest_data["status"] = "completed"
    manifest_data["timestamp_end_utc"] = datetime.now(timezone.utc).isoformat()
    manifest_data["total_count"] = summary["overall"]["total_count"]
    manifest_data["success_count"] = summary["overall"]["success_count"]
    manifest_data["failure_count"] = summary["overall"]["failure_count"]
    manifest_data["correct_count"] = summary["overall"]["correct_count"]
    manifest_data["overall_accuracy"] = summary["overall"]["overall_accuracy"]
    manifest_data["success_accuracy"] = summary["overall"]["success_accuracy"]
    manifest_data["macro_f1"] = summary["overall"]["macro_f1"]
    manifest_path.write_text(json.dumps(manifest_data, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n" + "=" * 60)
    print(f"평가 완료 요약:")
    print(f"- 전체 문항: {summary['overall']['total_count']}")
    print(f"- 성공: {summary['overall']['success_count']}, 실패: {summary['overall']['failure_count']}")
    print(f"- 일치 건수: {summary['overall']['correct_count']}")
    print(f"- 전체 일치율 (Overall Accuracy): {summary['overall']['overall_accuracy']*100:.2f}% (Majority Baseline: 25.0%)")
    print(f"- Macro F1 Score: {summary['overall']['macro_f1']:.4f}")
    print(f"- 결과 저장: {output_dir}")
    print("=" * 60 + "\n", flush=True)


if __name__ == "__main__":
    main()
