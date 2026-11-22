"""Sinh bộ ảnh + đáp án kiểm thử VQA từ các biểu đồ trong dataset/ của nhóm.

    cd backend
    python -m vqa_eval.make_truth            # ghi vqa_eval/images/ và vqa_eval/truth.json

Mỗi biểu đồ chart_0X sinh 4 ảnh (rõ nét, mờ, độ phân giải thấp, bị xoá nhãn trục) và thêm 1 câu hỏi
không thể trả lời trên ảnh rõ nét. Ảnh xấu được đánh dấu "expect_warning": true để đo khả năng
bắt cảnh báo; ảnh rõ là false để đo cảnh báo thừa.

Lưu ý: đây là biểu đồ sinh bằng matplotlib. Hãy bổ sung vài ảnh chụp/ảnh thật vào truth.json
trước khi kết luận về độ chính xác.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
GT_DIR = ROOT / "dataset" / "ground_truth"
SRC_DIR = ROOT / "dataset" / "test_set"
OUT = Path(__file__).resolve().parent
IMG_DIR = OUT / "images"

NUM_RE = re.compile(r"\d+(?:[.,]\d+)*")

# Kiểu biểu đồ: mặc định là cột đứng. Khi thêm biểu đồ mới hãy khai báo ở đây nếu là thanh ngang ("barh") hoặc đường ("line").
CHART_KIND = {"chart_03": "line", "chart_04": "barh"}
SECOND_ITEM_QUESTION = {
    "bar": "Cột thứ hai từ trái sang có giá trị bao nhiêu?",
    "line": "Điểm thứ hai từ trái sang có giá trị bao nhiêu?",
    "barh": "Thanh thứ hai tính từ dưới lên có giá trị bao nhiêu?",  # matplotlib vẽ mục đầu tiên ở dưới cùng
}


def parse_vn_number(text: str) -> float:
    """'1.250,5' -> 1250.5; '98,5%' -> 98.5; '1.200' -> 1200 (dấu chấm là phân cách hàng nghìn)."""
    t = NUM_RE.search(text).group(0)
    if re.fullmatch(r"\d{1,3}(\.\d{3})+(,\d+)?", t):
        t = t.replace(".", "")
    return float(t.replace(",", "."))


def numbers_in(text: str) -> set[float]:
    out: set[float] = set()
    for tok in NUM_RE.findall(text):
        for cand in {tok, tok.replace(".", "").replace(",", "."), tok.replace(",", ".")}:
            try:
                out.add(float(cand))
            except ValueError:
                pass
    return out


def make_variants(src: Path, kind: str = "bar") -> dict[str, Image.Image]:
    img = Image.open(src).convert("RGB")
    w, h = img.size
    blur = img.filter(ImageFilter.GaussianBlur(2.5))
    low = img.resize((w // 4, h // 4), Image.BILINEAR).resize((w, h), Image.BILINEAR)
    no_axis = img.copy()
    d = ImageDraw.Draw(no_axis)
    d.rectangle([0, int(h * 0.90), w, h], fill="white")        # nhãn trục hoành và tên trục
    # thanh ngang: nhãn hạng mục nằm bên trái và dài hơn nhiều so với số chia của cột đứng
    d.rectangle([0, 0, int(w * (0.26 if kind == "barh" else 0.055)), h], fill="white")
    return {"ro": img, "mo": blur, "phan_giai_thap": low, "thieu_nhan_truc": no_axis}


def main() -> None:
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    truth: list[dict] = []
    for gt_path in sorted(GT_DIR.glob("chart_*.png.json")):
        gt = json.loads(gt_path.read_text(encoding="utf-8"))
        cid = gt["file_id"].removesuffix(".png")
        facts = gt["key_facts"]
        points = facts["data_points"]
        labels = list(points)
        values = {k: parse_vn_number(v) for k, v in points.items()}
        grounded = set()  # số nào xuất hiện trong ảnh thì nhắc tới đều không phải "bịa"
        for text in [facts["chart_title"], facts["unit"], *labels, *points.values()]:
            grounded |= numbers_in(text)
        top = max(values, key=values.get)

        kind = CHART_KIND.get(cid, "bar")
        second_q = SECOND_ITEM_QUESTION[kind]
        for variant, image in make_variants(SRC_DIR / gt["file_id"], kind).items():
            fname = f"{cid}_{variant}.png"
            image.save(IMG_DIR / fname)
            bad = variant != "ro"
            second = labels[1]
            truth.append({
                "id": f"{cid}_{variant}", "file": fname, "category": variant,
                "question": second_q if variant == "thieu_nhan_truc" else f"Giá trị của {second} là bao nhiêu?",
                "answerable": True, "expected_numbers": [values[second]],
                "allowed_numbers": sorted(grounded), "expect_warning": bad,
            })

        # câu hỏi không có trong ảnh, hỏi trên ảnh rõ nét
        truth.append({
            "id": f"{cid}_khong_co", "file": f"{cid}_ro.png", "category": "khong_tra_loi_duoc",
            "question": "Giá trị dự báo của năm 2030 là bao nhiêu?", "answerable": False,
        })
        # câu hỏi so sánh trên ảnh rõ nét
        truth.append({
            "id": f"{cid}_cao_nhat", "file": f"{cid}_ro.png", "category": "ro_so_sanh",
            "question": "Mục nào có giá trị cao nhất và giá trị đó là bao nhiêu?",
            "answerable": True, "expected_numbers": [values[top]],
            "allowed_numbers": sorted(grounded), "expect_warning": False,
        })

    (OUT / "truth.json").write_text(json.dumps(truth, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Đã ghi {len(truth)} mục vào vqa_eval/truth.json và {len(list(IMG_DIR.glob('*.png')))} ảnh vào vqa_eval/images/")


if __name__ == "__main__":
    main()
