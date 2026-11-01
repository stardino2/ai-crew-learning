#!/usr/bin/env python3
"""Run evaluation for Kev email subject classification.

Reuses classify, CATEGORIES, CATEGORY_KO from mail_demo.py without modifications.
Standard library only.
"""
import argparse
import json
import math
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from mail_demo import CATEGORIES, CATEGORY_KO, classify

REQUIRED_FIELDS = {"id", "subject", "expected", "rationale", "language", "split", "gold_status"}
VALID_SPLITS = {"dev", "test"}


def anonymize_subject(subject: str) -> str:
    """Anonymize subject to avoid logging private user data."""
    if not subject:
        return "[EMPTY]"
    return f"[REDACTED len={len(subject)}]"


def validate_input(data: Any) -> None:
    """Validate full input JSON dataset before executing any model requests."""
    if not isinstance(data, list):
        raise ValueError(f"Input data must be a JSON array (list), got {type(data).__name__}")
    if len(data) == 0:
        raise ValueError("Input data array is empty.")

    seen_ids = set()
    for idx, item in enumerate(data):
        if not isinstance(item, dict):
            raise ValueError(f"Item at index {idx} must be a dict, got {type(item).__name__}")

        missing = REQUIRED_FIELDS - set(item.keys())
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

        if not isinstance(item["subject"], str):
            raise ValueError(f"Item {item_id} 'subject' must be str")

        if item["expected"] not in CATEGORIES:
            raise ValueError(
                f"Item {item_id} 'expected' category '{item['expected']}' is not in CATEGORIES: {sorted(list(CATEGORIES.keys()))}"
            )

        if item["split"] not in VALID_SPLITS:
            raise ValueError(
                f"Item {item_id} 'split' must be one of {sorted(list(VALID_SPLITS))}, got '{item['split']}'"
            )

        if not isinstance(item["language"], str) or not item["language"].strip():
            raise ValueError(f"Item {item_id} 'language' must be a non-empty string")

        if not isinstance(item["rationale"], str):
            raise ValueError(f"Item {item_id} 'rationale' must be str")

        if not isinstance(item["gold_status"], str) or not item["gold_status"].strip():
            raise ValueError(f"Item {item_id} 'gold_status' must be a non-empty string")


def validate_probabilities(probabilities: Any) -> None:
    """Validate 5-category probabilities to be finite numbers in [0.0, 1.0]."""
    if not isinstance(probabilities, dict):
        raise ValueError(f"probabilities must be dict, got {type(probabilities).__name__}")
    missing_keys = set(CATEGORIES.keys()) - set(probabilities.keys())
    if missing_keys:
        raise ValueError(f"probabilities missing category keys: {sorted(list(missing_keys))}")
    for cat in CATEGORIES.keys():
        val = probabilities.get(cat)
        if not isinstance(val, (int, float)):
            raise ValueError(f"probability for '{cat}' must be numeric, got {val!r}")
        if not math.isfinite(val):
            raise ValueError(f"probability for '{cat}' is not finite: {val}")
        if not (0.0 <= val <= 1.0):
            raise ValueError(f"probability for '{cat}' out of bounds [0.0, 1.0]: {val}")


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


def calculate_metrics(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate evaluation metrics, split/language breakdowns, confusion matrix, and latency."""
    total_count = len(results)
    success_results = [r for r in results if r.get("error") is None]
    failure_results = [r for r in results if r.get("error") is not None]

    success_count = len(success_results)
    failure_count = len(failure_results)
    correct_count = sum(1 for r in results if r.get("correct") is True)

    overall_accuracy = round(correct_count / total_count, 4) if total_count > 0 else 0.0
    success_accuracy = round(correct_count / success_count, 4) if success_count > 0 else 0.0

    elapsed_times = [
        r["elapsed_seconds"]
        for r in results
        if r.get("elapsed_seconds") is not None and isinstance(r["elapsed_seconds"], (int, float))
    ]
    p50_latency = calculate_percentile(elapsed_times, 50.0)
    p95_latency = calculate_percentile(elapsed_times, 95.0)

    cat_keys = sorted(list(CATEGORIES.keys()))
    category_metrics = {}
    for cat in cat_keys:
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

        category_metrics[cat] = {
            "name_ko": CATEGORY_KO.get(cat, cat),
            "precision": precision,
            "recall": recall,
            "f1_score": f1,
            "support": support,
            "tp": tp,
            "fp": fp,
            "fn": fn,
        }

    confusion_matrix = {act: {pred: 0 for pred in cat_keys + ["error"]} for act in cat_keys}
    for r in results:
        act = r.get("expected")
        if act not in confusion_matrix:
            confusion_matrix[act] = {pred: 0 for pred in cat_keys + ["error"]}
        pred = r.get("predicted")
        if r.get("error") is not None or pred is None:
            confusion_matrix[act]["error"] += 1
        elif pred in confusion_matrix[act]:
            confusion_matrix[act][pred] += 1
        else:
            confusion_matrix[act]["error"] += 1

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
            "model": "unknown",
            "device": "unknown",
            "evaluation_time_utc": datetime.now(timezone.utc).isoformat(),
            "provisional_gold_note": "미검수 정답은 provisional 결과이며 실사용 정확도 확정 불가",
            "latency_measurement_note": "실제 클라이언트 HTTP 왕복 측정 시간(단위: 초), 모델 내부 추론 시간과 구별됨",
        },
        "overall": {
            "total_count": total_count,
            "success_count": success_count,
            "failure_count": failure_count,
            "correct_count": correct_count,
            "overall_accuracy": overall_accuracy,
            "success_accuracy": success_accuracy,
            "latency_p50_seconds": p50_latency,
            "latency_p95_seconds": p95_latency,
        },
        "by_split": split_metrics,
        "by_language": language_metrics,
        "by_category": category_metrics,
        "confusion_matrix": confusion_matrix,
    }


def generate_report_markdown(summary: Dict[str, Any], results: List[Dict[str, Any]]) -> str:
    """Generate Markdown report. Subject is never printed in raw format."""
    meta = summary.get("metadata", {})
    overall = summary.get("overall", {})
    by_split = summary.get("by_split", {})
    by_lang = summary.get("by_language", {})
    by_cat = summary.get("by_category", {})
    cm = summary.get("confusion_matrix", {})

    lines = []
    lines.append("# Kev 메일 제목 분류 평가 보고서 (Baseline)")
    lines.append("")
    lines.append("> [!WARNING]")
    lines.append(f"> **안내**: {meta.get('provisional_gold_note', '미검수 정답은 provisional 결과이며 실사용 정확도 확정 불가')}")
    lines.append("> 개인정보 보호를 위해 원문 메일 제목은 보고서에 출력되지 않으며 익명화 표기됩니다.")
    lines.append("")
    lines.append("## 1. 실행 환경 및 메타데이터")
    lines.append(f"- **평가 일시(UTC)**: {meta.get('evaluation_time_utc', 'unknown')}")
    lines.append(f"- **모델명**: {meta.get('model', 'unknown')}")
    lines.append(f"- **실행 장치**: {meta.get('device', 'unknown')}")
    lines.append(f"- **지연시간 측정 방식**: {meta.get('latency_measurement_note', 'unknown')}")
    lines.append("")
    lines.append("## 2. 전체 요약 지표")
    lines.append("| 지표 | 값 |")
    lines.append("| --- | --- |")
    lines.append(f"| 총 평가 메일 수 | {overall.get('total_count', 0)}건 |")
    lines.append(f"| 성공 요청 수 | {overall.get('success_count', 0)}건 |")
    lines.append(f"| 실패 요청 수 | {overall.get('failure_count', 0)}건 |")
    lines.append(f"| 정답 건수 | {overall.get('correct_count', 0)}건 |")
    overall_acc_pct = round(overall.get('overall_accuracy', 0.0) * 100, 2)
    success_acc_pct = round(overall.get('success_accuracy', 0.0) * 100, 2)
    lines.append(f"| 전체 정답률 (실패 포함) | {overall.get('overall_accuracy', 0.0):.4f} ({overall_acc_pct}%) |")
    lines.append(f"| 성공건 정답률 | {overall.get('success_accuracy', 0.0):.4f} ({success_acc_pct}%) |")
    lines.append(f"| 요청 지연시간 p50 | {overall.get('latency_p50_seconds', 0.0):.4f}초 |")
    lines.append(f"| 요청 지연시간 p95 | {overall.get('latency_p95_seconds', 0.0):.4f}초 |")
    lines.append("")

    lines.append("## 3. Split별 지표")
    lines.append("| Split | Total | Success | Failure | Correct | Overall Accuracy | Success Accuracy |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- |")
    for s, data in by_split.items():
        lines.append(
            f"| {s} | {data.get('total')} | {data.get('success')} | {data.get('failure')} | "
            f"{data.get('correct')} | {data.get('overall_accuracy', 0.0):.4f} | {data.get('success_accuracy', 0.0):.4f} |"
        )
    lines.append("")

    lines.append("## 4. 언어별 지표")
    lines.append("| Language | Total | Success | Failure | Correct | Overall Accuracy | Success Accuracy |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- |")
    for lang, data in by_lang.items():
        lines.append(
            f"| {lang} | {data.get('total')} | {data.get('success')} | {data.get('failure')} | "
            f"{data.get('correct')} | {data.get('overall_accuracy', 0.0):.4f} | {data.get('success_accuracy', 0.0):.4f} |"
        )
    lines.append("")

    lines.append("## 5. 분류 카테고리별 성능")
    lines.append("| 카테고리 | 한글명 | Precision | Recall | F1-Score | Support | TP | FP | FN |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for cat, data in by_cat.items():
        lines.append(
            f"| {cat} | {data.get('name_ko')} | {data.get('precision', 0.0):.4f} | "
            f"{data.get('recall', 0.0):.4f} | {data.get('f1_score', 0.0):.4f} | "
            f"{data.get('support')} | {data.get('tp')} | {data.get('fp')} | {data.get('fn')} |"
        )
    lines.append("")

    lines.append("## 6. 혼동행렬 (Confusion Matrix)")
    cat_keys = sorted(list(CATEGORIES.keys()))
    header = "| 실제(Actual) \\ 예측(Predicted) | " + " | ".join(cat_keys + ["error"]) + " |"
    lines.append(header)
    lines.append("| " + " | ".join(["---"] * (len(cat_keys) + 2)) + " |")
    for act in cat_keys:
        row_counts = [str(cm.get(act, {}).get(pred, 0)) for pred in cat_keys + ["error"]]
        lines.append(f"| **{act}** ({CATEGORY_KO.get(act, act)}) | " + " | ".join(row_counts) + " |")
    lines.append("")

    lines.append("## 7. 오분류 및 오류 목록")
    misclassified_or_errors = [r for r in results if (not r.get("correct")) or r.get("error")]
    if not misclassified_or_errors:
        lines.append("오분류 또는 오류가 발생한 항목이 없습니다.")
    else:
        lines.append("| ID | Split | 언어 | 정답(Expected) | 예측(Predicted) | 익명화 제목 | 소요시간(초) | 오류 내용 |")
        lines.append("| --- | --- | --- | --- | --- | --- | --- | --- |")
        for r in misclassified_or_errors:
            item_id = r.get("id", "-")
            split = r.get("split", "-")
            lang = r.get("language", "-")
            exp = r.get("expected", "-")
            pred = r.get("predicted", "-")
            anon_title = anonymize_subject(r.get("subject", ""))
            elapsed = f"{r.get('elapsed_seconds', 0.0):.2f}" if r.get("elapsed_seconds") is not None else "-"
            err = (r.get("error") or "-").replace("\n", " ")
            lines.append(f"| {item_id} | {split} | {lang} | {exp} | {pred} | {anon_title} | {elapsed} | {err} |")
    lines.append("")

    return "\n".join(lines)


def run_evaluation(
    input_path: Path,
    output_dir: Path,
    split_filter: str = "all",
    classify_fn=classify,
) -> Dict[str, Any]:
    """Execute evaluation with fault tolerance and incremental saving."""
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    raw_data = json.loads(input_path.read_text(encoding="utf-8"))
    validate_input(raw_data)

    if split_filter != "all":
        items = [item for item in raw_data if item.get("split") == split_filter]
    else:
        items = list(raw_data)

    if not items:
        raise ValueError(f"No items match split filter: '{split_filter}'")

    output_dir.mkdir(parents=True, exist_ok=True)
    results_path = output_dir / "results.json"
    summary_path = output_dir / "summary.json"
    report_path = output_dir / "report.md"

    results: List[Dict[str, Any]] = []
    total = len(items)

    print(f"=== Kev 테스트 실행 시작 (대상: {total}건, split: {split_filter}) ===", flush=True)

    for idx, item in enumerate(items, start=1):
        item_id = item.get("id", str(idx))
        subject = item.get("subject", "")
        expected = item.get("expected")

        start_time = time.perf_counter()
        predicted: Optional[str] = None
        probabilities: Optional[Dict[str, float]] = None
        correct = False
        error_msg: Optional[str] = None

        try:
            answer = classify_fn(subject)
            validate_probabilities(answer.get("probabilities"))
            predicted = answer.get("choice")
            if predicted not in CATEGORIES:
                raise ValueError(f"Returned category '{predicted}' is not in CATEGORIES")
            probabilities = answer.get("probabilities")
            correct = (predicted == expected)
        except Exception as exc:
            error_msg = f"{type(exc).__name__}: {str(exc)}"

        elapsed = round(time.perf_counter() - start_time, 4)

        result_entry = {
            **item,
            "predicted": predicted,
            "probabilities": probabilities,
            "correct": correct,
            "elapsed_seconds": elapsed,
            "error": error_msg,
        }
        results.append(result_entry)

        # Incremental save to preserve results on failure or interruption
        results_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

        # Console log with anonymized subject / status
        mark = "O" if correct else "X"
        exp_ko = CATEGORY_KO.get(expected, expected)
        pred_ko = CATEGORY_KO.get(predicted, predicted) if predicted else (f"ERR:{error_msg}" if error_msg else "NONE")
        print(f"[{idx}/{total}] ID: {item_id} | [{mark}] 예상: {exp_ko} | 결과: {pred_ko} | {elapsed:.2f}s", flush=True)

    summary = calculate_metrics(results)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    report_md = generate_report_markdown(summary, results)
    report_path.write_text(report_md, encoding="utf-8")

    overall = summary.get("overall", {})
    print("\n=== 테스트 완료 ===", flush=True)
    print(f"총 {overall.get('total_count')}건 중 성공 {overall.get('success_count')}건, 실패 {overall.get('failure_count')}건", flush=True)
    print(f"정답 수: {overall.get('correct_count')}건", flush=True)
    print(f"전체 정답률(요청실패 포함): {overall.get('overall_accuracy', 0.0):.4f}", flush=True)
    print(f"성공건 정답률: {overall.get('success_accuracy', 0.0):.4f}", flush=True)
    print(f"지연시간 p50: {overall.get('latency_p50_seconds', 0.0):.4f}s | p95: {overall.get('latency_p95_seconds', 0.0):.4f}s", flush=True)
    print(f"결과 저장 완료: {output_dir}", flush=True)

    return summary


def parse_args(args=None):
    parser = argparse.ArgumentParser(
        description="Run evaluation benchmark for Kev email subject classification."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/gmail_eval.json"),
        help="Path to evaluation input JSON file (default: data/gmail_eval.json)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("eval_results"),
        help="Directory to save results.json, summary.json, report.md (default: eval_results)",
    )
    parser.add_argument(
        "--split",
        choices=["all", "dev", "test"],
        default="all",
        help="Evaluation split to run: 'all', 'dev', or 'test' (default: all)",
    )
    return parser.parse_args(args)


def main():
    args = parse_args()
    try:
        run_evaluation(
            input_path=args.input,
            output_dir=args.output_dir,
            split_filter=args.split,
        )
    except Exception as e:
        sys.stderr.write(f"Error during evaluation: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
