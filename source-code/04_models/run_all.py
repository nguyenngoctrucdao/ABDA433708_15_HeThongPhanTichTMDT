"""
    python run_all.py          # đọc MongoDB (nếu nối được), ghi pkl + collection ml_*
    python run_all.py --csv    # ép đọc từ file CSV, không đụng MongoDB

File này chạy lần lượt các ô code của:
    model1_kmeans.ipynb, model2_random_forest.ipynb, model3_isolation_forest.ipynb
Ba notebook phải nằm cùng thư mục với file này.
"""
import json
import os
import sys
import time
from pathlib import Path

if "--csv" in sys.argv:
    os.environ["ML_FORCE_CSV"] = "1"          # phải đặt TRƯỚC khi import common
os.environ.setdefault("MPLBACKEND", "Agg")    # biểu đồ chỉ lưu ra file, không mở cửa sổ

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from common import MODELS_DIR, load_products, mongo_ok  # noqa: E402

NOTEBOOKS = ["model1_kmeans.ipynb", "model2_random_forest.ipynb", "model3_isolation_forest.ipynb"]


def chay_notebook(ten):
    """Lấy tất cả ô code trong notebook rồi chạy lần lượt từ trên xuống."""
    path = HERE / ten
    if not path.exists():
        raise FileNotFoundError(f"Không thấy {ten} trong {HERE}")
    cells = json.loads(path.read_text(encoding="utf-8"))["cells"]
    code = "\n\n".join("".join(c["source"]) for c in cells if c["cell_type"] == "code")
    exec(compile(code, str(path), "exec"), {"__name__": "__main__", "__file__": str(path)})


if __name__ == "__main__":
    thieu = [n for n in NOTEBOOKS if not (HERE / n).exists()]
    if thieu:
        sys.exit(f"Thiếu notebook trong {HERE}: {thieu}")

    t0 = time.time()
    df = load_products()
    print("\n=== KIỂM TRA DỮ LIỆU ĐẦU VÀO ===")
    print("shape:", df.shape)
    print(df.isna().sum()[df.isna().sum() > 0].to_string() or "không có ô thiếu")
    for ten in NOTEBOOKS:
        print(f"\n{'=' * 70}\n>>> {ten}\n{'=' * 70}")
        chay_notebook(ten)

    print(f"\n=== TÓM TẮT ({time.time() - t0:.0f} giây, Mongo: {'có' if mongo_ok() else 'không'}) ===")
    allm = json.loads((MODELS_DIR / "metrics.json").read_text(encoding="utf-8"))
    for name, d in allm.items():
        print(f"- {name}: n_train={d['n_train']}")
    print("Các file .pkl:", [p.name for p in MODELS_DIR.glob('*.pkl')])