import json
import os
import sys
import time
from pathlib import Path

# Ensure backend on path
BASE_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = BASE_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.config import Settings
from app.pipeline.layout import ClassicalLayoutAnalyzer
from app.pipeline.ocr import TesseractOCR, _configure_tesseract
from app.pipeline.pipeline import DocumentPipeline
from app.pipeline.table import normalize_vietnamese_number

_configure_tesseract()

DATASET_DIR = BASE_DIR / "dataset"
TEST_SET_DIR = DATASET_DIR / "test_set"
GROUND_TRUTH_DIR = DATASET_DIR / "ground_truth"
EVAL_DIR = BASE_DIR / "eval"
RESULTS_JSON_PATH = EVAL_DIR / "eval_results.json"


# ==============================================================================
# PURE PYTHON METRICS
# ==============================================================================
def levenshtein(s1: list | str, s2: list | str) -> int:
    if len(s1) < len(s2):
        return levenshtein(s2, s1)
    if len(s2) == 0:
        return len(s1)

    previous_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        current_row = [i + 1] + [0] * len(s2)
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row[j + 1] = min(insertions, deletions, substitutions)
        previous_row = current_row
    return previous_row[-1]


def compute_cer(ref: str, hyp: str) -> float:
    ref_chars = list(ref.strip())
    hyp_chars = list(hyp.strip())
    if not ref_chars:
        return 0.0 if not hyp_chars else 100.0
    dist = levenshtein(ref_chars, hyp_chars)
    return round(min(100.0, (dist / len(ref_chars)) * 100.0), 2)


def compute_wer(ref: str, hyp: str) -> float:
    ref_words = ref.strip().split()
    hyp_words = hyp.strip().split()
    if not ref_words:
        return 0.0 if not hyp_words else 100.0
    dist = levenshtein(ref_words, hyp_words)
    return round(min(100.0, (dist / len(ref_words)) * 100.0), 2)


def compute_numerical_precision(exact_numbers: list[str], hyp_text: str) -> float:
    if not exact_numbers:
        return 100.0
    norm_hyp = normalize_vietnamese_number(hyp_text)
    matched = 0
    for num in exact_numbers:
        norm_num = normalize_vietnamese_number(num)
        clean_num = norm_num.strip(".,;:()")
        raw_num = clean_num.replace("%", "").strip()
        if (
            norm_num in norm_hyp
            or clean_num in norm_hyp
            or raw_num in norm_hyp
            or num in hyp_text
        ):
            matched += 1
    return round((matched / len(exact_numbers)) * 100.0, 2)


def compute_reading_order_accuracy(expected_texts: list[str], blocks: list) -> float:
    if len(expected_texts) <= 1:
        return 100.0

    block_texts = [(b.order, b.text.lower()) for b in blocks if b.text]
    if not block_texts:
        return 0.0

    matched_orders: list[int | None] = []
    for exp in expected_texts:
        exp_words = set(exp.lower().split())
        best_order = None
        best_overlap = 0.0
        for order, b_text in block_texts:
            b_words = set(b_text.split())
            overlap = len(exp_words & b_words) / max(1, len(exp_words))
            if overlap > best_overlap and overlap >= 0.15:
                best_overlap = overlap
                best_order = order
        matched_orders.append(best_order)

    correct_pairs = 0
    total_pairs = 0
    for i in range(len(matched_orders)):
        for j in range(i + 1, len(matched_orders)):
            oi = matched_orders[i]
            oj = matched_orders[j]
            if oi is not None and oj is not None and oi != oj:
                total_pairs += 1
                if oi < oj:
                    correct_pairs += 1

    if total_pairs == 0:
        return 100.0
    return round((correct_pairs / total_pairs) * 100.0, 2)


# ==============================================================================
# EVALUATION RUNNER
# ==============================================================================
def main():
    print("=== BẮT ĐẦU GIAI ĐOẠN 3: ĐÁNH GIÁ ĐỊNH LƯỢNG PIPELINE OCR ===")
    EVAL_DIR.mkdir(parents=True, exist_ok=True)

    pipeline = DocumentPipeline(ClassicalLayoutAnalyzer(), TesseractOCR("vie"), Settings())

    gt_files = sorted(list(GROUND_TRUTH_DIR.glob("*.json")))
    if not gt_files:
        print("Lỗi: Không tìm thấy file ground truth trong dataset/ground_truth/!")
        sys.exit(1)

    print(f"-> Tìm thấy {len(gt_files)} file ground-truth để đánh giá.\n")

    results_by_file = []
    categories: dict[str, list[dict]] = {
        "slide": [],
        "two_column": [],
        "table": [],
        "chart": [],
    }

    for gt_path in gt_files:
        with open(gt_path, "r", encoding="utf-8") as f:
            gt_data = json.load(f)

        file_id = gt_data["file_id"]
        img_path = TEST_SET_DIR / file_id
        if not img_path.exists():
            print(f"Cảnh báo: Không tìm thấy ảnh {img_path}")
            continue

        doc_type = gt_data.get("document_type", "unknown")
        expected_texts = gt_data.get("expected_reading_order_texts", [])
        exact_numbers = gt_data.get("exact_numbers", [])
        ref_full_text = " ".join(expected_texts)

        with open(img_path, "rb") as f:
            img_bytes = f.read()

        start_time = time.perf_counter()
        doc_result, _ = pipeline.process(img_bytes, file_id, f"eval-{file_id}")
        latency = round(time.perf_counter() - start_time, 3)

        page_blocks = doc_result.pages[0].blocks if doc_result.pages else []
        hyp_full_text = " ".join(b.text for b in page_blocks if b.text)

        cer = compute_cer(ref_full_text, hyp_full_text)
        wer = compute_wer(ref_full_text, hyp_full_text)
        num_prec = compute_numerical_precision(exact_numbers, hyp_full_text)
        order_acc = compute_reading_order_accuracy(expected_texts, page_blocks)

        record = {
            "file_id": file_id,
            "document_type": doc_type,
            "cer_percent": cer,
            "wer_percent": wer,
            "numerical_precision_percent": num_prec,
            "reading_order_accuracy_percent": order_acc,
            "latency_seconds": latency,
            "block_count": len(page_blocks),
            "exact_numbers_count": len(exact_numbers),
        }
        results_by_file.append(record)
        if doc_type in categories:
            categories[doc_type].append(record)

        print(
            f"[{file_id:18s}] Type: {doc_type:10s} | CER: {cer:5.2f}% | WER: {wer:5.2f}% | "
            f"NumPrec: {num_prec:5.2f}% | OrderAcc: {order_acc:5.2f}% | Latency: {latency:.2f}s"
        )

    # Compute category & overall averages
    summary_by_type = {}
    for cat, items in categories.items():
        if items:
            summary_by_type[cat] = {
                "count": len(items),
                "avg_cer": round(sum(x["cer_percent"] for x in items) / len(items), 2),
                "avg_wer": round(sum(x["wer_percent"] for x in items) / len(items), 2),
                "avg_num_prec": round(sum(x["numerical_precision_percent"] for x in items) / len(items), 2),
                "avg_order_acc": round(sum(x["reading_order_accuracy_percent"] for x in items) / len(items), 2),
                "avg_latency": round(sum(x["latency_seconds"] for x in items) / len(items), 3),
            }

    total_count = len(results_by_file)
    overall_avg = {
        "count": total_count,
        "avg_cer": round(sum(x["cer_percent"] for x in results_by_file) / total_count, 2) if total_count else 0.0,
        "avg_wer": round(sum(x["wer_percent"] for x in results_by_file) / total_count, 2) if total_count else 0.0,
        "avg_num_prec": round(sum(x["numerical_precision_percent"] for x in results_by_file) / total_count, 2) if total_count else 0.0,
        "avg_order_acc": round(sum(x["reading_order_accuracy_percent"] for x in results_by_file) / total_count, 2) if total_count else 0.0,
        "avg_latency": round(sum(x["latency_seconds"] for x in results_by_file) / total_count, 3) if total_count else 0.0,
    }

    # Save to JSON
    output_payload = {
        "overall_summary": overall_avg,
        "category_summary": summary_by_type,
        "details_by_file": results_by_file,
    }
    with open(RESULTS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(output_payload, f, ensure_ascii=False, indent=2)

    # Print Markdown Summary Table
    print("\n" + "=" * 95)
    print("### BẢNG KẾT QUẢ ĐÁNH GIÁ ĐỊNH LƯỢNG PIPELINE OCR TIẾNG VIỆT (EYEASSISTWEB)")
    print("=" * 95)
    print("| Loại tài liệu             | Số lượng | CER (%) | WER (%) | Numerical Prec (%) | Reading Order Acc (%) | Latency (s/trang) |")
    print("|:--------------------------|:--------:|:-------:|:-------:|:------------------:|:---------------------:|:-----------------:|")

    type_names = {
        "slide": "Slide bài giảng UET",
        "two_column": "Bài báo 2 cột",
        "table": "Bảng biểu / Hóa đơn",
        "chart": "Biểu đồ cột / đường",
    }
    for cat, name in type_names.items():
        s = summary_by_type.get(cat, {})
        if s:
            print(
                f"| {name:<25s} | {s['count']:^8d} | {s['avg_cer']:^7.2f} | {s['avg_wer']:^7.2f} | "
                f"{s['avg_num_prec']:^18.2f} | {s['avg_order_acc']:^21.2f} | {s['avg_latency']:^17.2f} |"
            )

    print("|" + "-" * 27 + "|" + "-" * 10 + "|" + "-" * 9 + "|" + "-" * 9 + "|" + "-" * 20 + "|" + "-" * 23 + "|" + "-" * 19 + "|")
    print(
        f"| {'TRUNG BÌNH TOÀN BỘ':<25s} | {overall_avg['count']:^8d} | {overall_avg['avg_cer']:^7.2f} | {overall_avg['avg_wer']:^7.2f} | "
        f"{overall_avg['avg_num_prec']:^18.2f} | {overall_avg['avg_order_acc']:^21.2f} | {overall_avg['avg_latency']:^17.2f} |"
    )
    print("=" * 95)

    # Top Error Files
    print("\n### DANH SÁCH CÁC FILE CÓ SAI SỐ CAO NHẤT (TOP ERROR FILES):")
    top_errors = sorted(results_by_file, key=lambda x: (x["cer_percent"] + x["wer_percent"]), reverse=True)[:5]
    for rank, err in enumerate(top_errors, 1):
        print(
            f"{rank}. {err['file_id']:18s} ({err['document_type']:10s}) - CER: {err['cer_percent']:5.2f}% | "
            f"WER: {err['wer_percent']:5.2f}% | NumPrec: {err['numerical_precision_percent']:5.2f}% | "
            f"OrderAcc: {err['reading_order_accuracy_percent']:5.2f}% | Latency: {err['latency_seconds']:.2f}s"
        )
    print(f"\n-> Kết quả đánh giá chi tiết đã được lưu tại: {RESULTS_JSON_PATH}")


if __name__ == "__main__":
    main()
