#!/usr/bin/env python3
"""Đánh giá Factual Correctness của module VQA biểu đồ và quét ngưỡng tin cậy.

Chạy:  python eval_vqa.py --truth truth.json --adapter adapter.py --images images/ [--threshold 0.70] [--out report.json]

adapter.py cần định nghĩa  ask(image_path: str, question: str) -> dict  với các khoá:
    answer           (bắt buộc) câu mà người dùng sẽ NGHE (sau khi áp dụng fallback)
    confidence       (bắt buộc) 0..1, điểm cuối cùng dùng để so ngưỡng
    abstained        (tuỳ chọn) True nếu hệ thống đã từ chối/fallback; mặc định = confidence < --threshold
    raw_answer       (tuỳ chọn) câu của mô hình TRƯỚC fallback, dùng để quét ngưỡng; mặc định = answer
    model_answerable (tuỳ chọn) False nếu mô hình tự báo không trả lời được; mặc định True
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import re
import sys
import unicodedata
from pathlib import Path

NUM_RE = re.compile(r"\d+(?:[.,]\d+)*")


def _cands(tok: str) -> set[float]:
    out: set[float] = set()
    try:
        if "." in tok and "," in tok:
            last = max(tok.rfind("."), tok.rfind(","))
            out.add(float(re.sub(r"[.,]", "", tok[:last]) + "." + tok[last + 1:]))
        elif "." in tok or "," in tok:
            sep = "." if "." in tok else ","
            parts = tok.split(sep)
            if len(parts) == 2:
                out.add(float(parts[0] + "." + parts[1]))
            if all(len(p) == 3 for p in parts[1:]):
                out.add(float("".join(parts)))
        else:
            out.add(float(tok))
    except ValueError:
        pass
    return out


def numbers_in(text: str) -> list[set[float]]:
    return [c for c in (_cands(t) for t in NUM_RE.findall(text or "")) if c]


def _match(cands: set[float], target: float, tol: float) -> bool:
    return any(math.isclose(c, target, rel_tol=tol, abs_tol=1e-9) for c in cands)


def norm(s: str) -> str:
    return unicodedata.normalize("NFC", s or "").casefold()


def judge(item: dict, text: str) -> str:
    """Chấm nội dung một câu trả lời: correct | wrong | hallucinated (bỏ qua chuyện từ chối)."""
    tol = float(item.get("tolerance", 0.0))
    found = numbers_in(text)
    expected = item.get("expected_numbers", [])
    allowed = list(expected) + list(item.get("allowed_numbers", []))
    missing = [e for e in expected if not any(_match(c, e, tol) for c in found)]
    ok_phrases = all(norm(p) in norm(text) for p in item.get("expected_phrases", []))
    if missing or not ok_phrases:
        return "wrong"  # thiếu số đúng (kể cả khi thay bằng số khác)
    extra = [c for c in found if not any(_match(c, a, tol) for a in allowed)]
    return "hallucinated" if extra else "correct"  # đủ số đúng nhưng nêu thêm số không có căn cứ


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(c - h, 0.0), min(c + h, 1.0))


def evaluate(truth: list[dict], results: dict[str, dict], threshold: float) -> dict:
    rows = []
    for it in truth:
        r = results[it["id"]]
        conf = float(r["confidence"])
        abstained = r.get("abstained", conf < threshold)
        answerable = it.get("answerable", True)
        if abstained:
            verdict = "abstain_ok" if not answerable else "abstain_missed"
        elif not answerable:
            verdict = "leak"  # lẽ ra phải từ chối nhưng vẫn trả lời
        else:
            verdict = judge(it, r["answer"])
        rows.append({"id": it["id"], "category": it.get("category", "khác"), "answerable": answerable,
                     "confidence": conf, "verdict": verdict, "answer": r["answer"]})

    good = {"correct", "abstain_ok"}
    n = len(rows)
    k = sum(r["verdict"] in good for r in rows)
    cats: dict[str, dict] = {}
    for r in rows:
        c = cats.setdefault(r["category"], {"n": 0, "good": 0})
        c["n"] += 1
        c["good"] += r["verdict"] in good
    pos = [it for it in truth if it.get("expect_warning") is True]    # ảnh mờ / thiếu nhãn trục: PHẢI bị cảnh báo
    neg = [it for it in truth if it.get("expect_warning") is False]   # ảnh rõ: KHÔNG nên bị cảnh báo
    below = lambda it, t: float(results[it["id"]]["confidence"]) < t
    summary = {
        "warning_recall": (sum(below(it, threshold) for it in pos) / len(pos)) if pos else None,
        "false_alarm_rate": (sum(below(it, threshold) for it in neg) / len(neg)) if neg else None,
        "n": n,
        "factual_correctness": k / n if n else 0.0,
        "ci95": wilson(k, n),
        "hallucination_rate": sum(r["verdict"] in {"hallucinated", "leak"} for r in rows) / n if n else 0.0,
        "abstain_missed": sum(r["verdict"] == "abstain_missed" for r in rows),
        "by_category": {c: {**v, "rate": v["good"] / v["n"]} for c, v in cats.items()},
    }

    # Quét ngưỡng: chấm nội dung thô của mô hình, rồi xem mỗi ngưỡng sẽ trả lời bao nhiêu và sai bao nhiêu
    sweep = []
    for t in [round(0.40 + 0.05 * i, 2) for i in range(11)]:
        answered = unsafe = good_ans = 0
        for it in truth:
            r = results[it["id"]]
            if float(r["confidence"]) < t:
                continue
            if not it.get("answerable", True):
                if r.get("model_answerable", True):
                    answered += 1; unsafe += 1
                continue
            answered += 1
            v = judge(it, r.get("raw_answer", r["answer"]))
            good_ans += v == "correct"
            unsafe += v != "correct"
        sweep.append({"threshold": t, "coverage": answered / n if n else 0.0, "answered": answered,
                      "unsafe": unsafe, "selective_accuracy": good_ans / answered if answered else None,
                      "warning_recall": (sum(below(it, t) for it in pos) / len(pos)) if pos else None,
                      "false_alarm_rate": (sum(below(it, t) for it in neg) / len(neg)) if neg else None})
    safe = [s for s in sweep if s["unsafe"] == 0 and s["answered"] > 0]
    summary["recommended_threshold"] = min(safe, key=lambda s: s["threshold"])["threshold"] if safe else None
    return {"summary": summary, "rows": rows, "sweep": sweep}


def report(truth: list[dict], results: dict[str, dict], threshold: float, target: float, out: str) -> int:
    rep = evaluate(truth, results, threshold)
    s = rep["summary"]
    lo, hi = s["ci95"]
    print(f"\nFactual Correctness: {s['factual_correctness']:.1%} ({s['n']} ảnh, KTC 95%: {lo:.0%} - {hi:.0%}) "
          f"| mục tiêu {target:.0%}: {'ĐẠT' if s['factual_correctness'] > target else 'CHƯA ĐẠT'}")
    print(f"Tỷ lệ nêu số bịa / trả lời khi lẽ ra phải từ chối: {s['hallucination_rate']:.1%}"
          f" | từ chối nhầm câu trả lời được: {s['abstain_missed']}")
    if s["warning_recall"] is not None or s["false_alarm_rate"] is not None:
        wr, fa = s["warning_recall"], s["false_alarm_rate"]
        print(f"Cảnh báo tại T_conf = {threshold:.2f}: bắt được ảnh xấu {'-' if wr is None else format(wr, '.0%')}"
              f" | báo thừa trên ảnh rõ {'-' if fa is None else format(fa, '.0%')}")
    print("\nTheo nhóm ảnh:")
    for c, v in sorted(s["by_category"].items()):
        print(f"  {c:<22} {v['good']}/{v['n']}  {v['rate']:.0%}")
    print("\nQuét ngưỡng (độ phủ = tỷ lệ ảnh được trả lời; 'không an toàn' = trả lời sai hoặc bịa):")
    print("  ngưỡng  độ phủ  đã trả lời  không an toàn  chính xác khi trả lời  bắt ảnh xấu  báo thừa")
    for r in rep["sweep"]:
        acc = "-" if r["selective_accuracy"] is None else f"{r['selective_accuracy']:.0%}"
        mark = "  <-- hiện tại" if abs(r["threshold"] - threshold) < 1e-9 else ""
        wr = "-" if r["warning_recall"] is None else f"{r['warning_recall']:.0%}"
        fa = "-" if r["false_alarm_rate"] is None else f"{r['false_alarm_rate']:.0%}"
        print(f"  {r['threshold']:.2f}    {r['coverage']:>5.0%}  {r['answered']:>10}  {r['unsafe']:>13}  {acc:>20}  {wr:>11}  {fa:>7}{mark}")
    rec = s["recommended_threshold"]
    print(f"\nNgưỡng thấp nhất không có câu trả lời không an toàn: {rec if rec is not None else 'không có ngưỡng nào'}")
    if s["n"] < 50:
        print("Lưu ý: mẫu nhỏ, khoảng tin cậy rộng. Dùng kết quả để định hướng chỉnh, không coi là kết luận cuối.")
    Path(out).write_text(json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


def load_adapter(path: str):
    spec = importlib.util.spec_from_file_location("adapter", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod.ask


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--truth", required=True)
    ap.add_argument("--adapter", required=True)
    ap.add_argument("--images", required=True)
    ap.add_argument("--threshold", type=float, default=0.70)
    ap.add_argument("--target", type=float, default=0.90)
    ap.add_argument("--out", default="report.json")
    a = ap.parse_args(argv)

    truth = json.loads(Path(a.truth).read_text(encoding="utf-8"))
    ask = load_adapter(a.adapter)
    results = {}
    for it in truth:
        results[it["id"]] = ask(str(Path(a.images) / it["file"]), it["question"])
        print(f"  {it['id']:<12} conf={results[it['id']]['confidence']:.2f}", file=sys.stderr)

    return report(truth, results, a.threshold, a.target, a.out)


if __name__ == "__main__":
    raise SystemExit(main())
