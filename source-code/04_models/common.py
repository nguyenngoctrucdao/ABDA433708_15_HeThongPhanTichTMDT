"""
common.py - Các hàm dùng chung cho cả 3 mô hình.

Việc file này làm:
  1. Đọc cấu hình từ file .env (MONGO_URI, DB_NAME).
  2. Đọc dữ liệu sản phẩm từ MongoDB (hoặc từ file CSV nếu chưa nối được Mongo).
  3. Đổi tên cột tiếng Việt có dấu sang tên không dấu cho dễ viết code.
  4. Chuẩn bị dữ liệu cho mô hình (xử lý rating = 0, giá gốc thiếu).
  5. Ghi kết quả mô hình vào MongoDB (collection ml_*) và luôn lưu thêm 1 bản CSV.
"""
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

try:
    from dotenv import load_dotenv
except ImportError:          # chưa cài python-dotenv thì bỏ qua, dùng biến môi trường hệ thống
    load_dotenv = None

# ----------------------------------------------------------------------------
# 1. Đường dẫn và cấu hình
# ----------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[2]
if load_dotenv:
    load_dotenv(ROOT / ".env")

MONGO_URI = os.getenv("MONGO_URI")                                   # lấy từ .env
DB_NAME = os.getenv("DB_NAME") or os.getenv("MONGO_DB") or "ecommerce_db"
SRC_COLL = "products_cleaned"                                        # collection nguồn (chỉ đọc)
CSV_FILE = ROOT / "dataset" / "cleaned" / "products_cleaned.csv"     # bản CSV dự phòng
FORCE_CSV = os.getenv("ML_FORCE_CSV") == "1"                         # run_all.py --csv sẽ bật

MODELS_DIR = ROOT / "models"            # file .pkl và metrics.json
OUTPUT_DIR = ROOT / "output"            # bản CSV kết quả
FIG_DIR = OUTPUT_DIR / "figures"        # biểu đồ .png
for _d in (MODELS_DIR, OUTPUT_DIR, FIG_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# Đổi tên cột: tên tiếng Việt có dấu (trong CSV / MongoDB) -> tên không dấu
ALIASES = {
    "Nguồn dữ liệu": "nguon", "source": "nguon",
    "Mã sản phẩm": "ma_san_pham", "product_id": "ma_san_pham",
    "Tên sản phẩm": "ten_san_pham", "name": "ten_san_pham",
    "Thương hiệu": "thuong_hieu", "brand": "thuong_hieu",
    "Giá bán": "gia_ban", "price": "gia_ban",
    "Giá gốc": "gia_goc", "original_price": "gia_goc",
    "Số tiền giảm giá": "so_tien_giam_gia", "discount": "so_tien_giam_gia",
    "discount_amount": "so_tien_giam_gia",
    "Tỷ lệ giảm giá": "ty_le_giam_gia", "discount_rate": "ty_le_giam_gia",
    "Điểm đánh giá trung bình": "diem_danh_gia_trung_binh",
    "rating_average": "diem_danh_gia_trung_binh",
    "Số lượt đánh giá": "so_luot_danh_gia", "review_count": "so_luot_danh_gia",
    "Số lượng đã bán": "so_luong_da_ban", "quantity_sold": "so_luong_da_ban",
    "Tên danh mục": "ten_danh_muc", "category_name": "ten_danh_muc",
}
NUMERIC_COLS = ["gia_ban", "gia_goc", "so_tien_giam_gia", "ty_le_giam_gia",
                "diem_danh_gia_trung_binh", "so_luot_danh_gia", "so_luong_da_ban"]
REQUIRED = ["nguon", "ma_san_pham", "ten_danh_muc"] + NUMERIC_COLS

# Tên CÓ DẤU của các cột dùng làm đặc trưng (giống tên cột trong collection products_cleaned)
TEN_CO_DAU = {
    "gia_ban": "Giá bán", "gia_goc": "Giá gốc", "so_tien_giam_gia": "Số tiền giảm giá",
    "ty_le_giam_gia": "Tỷ lệ giảm giá", "diem_danh_gia_trung_binh": "Điểm đánh giá trung bình",
    "so_luot_danh_gia": "Số lượt đánh giá", "so_luong_da_ban": "Số lượng đã bán",
    "nguon": "Nguồn dữ liệu", "ten_danh_muc": "Tên danh mục",
}
TEN_KHONG_DAU = {v: k for k, v in TEN_CO_DAU.items()}


# ----------------------------------------------------------------------------
# 2. Kết nối MongoDB
# ----------------------------------------------------------------------------
_mongo_state = None   # nhớ kết quả kiểm tra để không ping nhiều lần


def _client():
    from pymongo import MongoClient          # import ở đây để chạy CSV được dù chưa cài pymongo
    return MongoClient(MONGO_URI, serverSelectionTimeoutMS=8000)


def mongo_ok():
    """True nếu nối được MongoDB. Nếu không, in lý do và trả False."""
    global _mongo_state
    if _mongo_state is not None:
        return _mongo_state
    if FORCE_CSV:
        print("[Mongo] Chế độ --csv: bỏ qua MongoDB.")
        _mongo_state = False
    elif not MONGO_URI:
        print("[Mongo] Chưa có MONGO_URI trong .env -> dùng file CSV.")
        _mongo_state = False
    else:
        try:
            with _client() as c:
                c.admin.command("ping")
            _mongo_state = True
            print(f"[Mongo] Kết nối thành công, database = {DB_NAME}")
        except Exception as e:                # noqa: BLE001
            print(f"[Mongo] KHÔNG kết nối được ({type(e).__name__}): {str(e)[:150]}")
            print("[Mongo] -> tạm dùng file CSV. Kiểm tra .env, mạng, IP Whitelist trên Atlas.")
            _mongo_state = False
    return _mongo_state


# ----------------------------------------------------------------------------
# 3. Đọc dữ liệu
# ----------------------------------------------------------------------------
def load_products(from_mongo=None):
    """Đọc products_cleaned -> DataFrame với tên cột không dấu.

    from_mongo=None : tự chọn (Mongo nếu nối được, không thì CSV)
    from_mongo=True / False : ép dùng Mongo / CSV
    """
    use_mongo = mongo_ok() if from_mongo is None else from_mongo
    if use_mongo:
        with _client() as c:
            df = pd.DataFrame(list(c[DB_NAME][SRC_COLL].find({}, {"_id": 0})))
        print(f"[Dữ liệu] Đọc từ MongoDB {DB_NAME}.{SRC_COLL}: {len(df)} dòng")
        if CSV_FILE.exists():                 # đối chiếu số dòng với CSV
            n_csv = len(pd.read_csv(CSV_FILE, encoding="utf-8-sig", usecols=[0]))
            if n_csv != len(df):
                print(f"[CẢNH BÁO] MongoDB {len(df)} dòng nhưng CSV {n_csv} dòng "
                      "-> báo người phụ trách MongoDB.")
    else:
        if not CSV_FILE.exists():
            raise FileNotFoundError(f"Không thấy file CSV: {CSV_FILE}")
        df = pd.read_csv(CSV_FILE, encoding="utf-8-sig")
        print(f"[Dữ liệu] Đọc từ CSV {CSV_FILE.name}: {len(df)} dòng")

    df = df.rename(columns=ALIASES)
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise ValueError(f"Thiếu cột: {missing}. Cột hiện có: {df.columns.tolist()}")

    # Trong Mongo mã sản phẩm là chuỗi, trong CSV là số -> ép về chuỗi cho thống nhất
    df["ma_san_pham"] = df["ma_san_pham"].astype(str)
    for c in NUMERIC_COLS:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def prepare_ml_data(df):
    """Chuẩn bị dữ liệu trước khi đưa vào mô hình (dùng cả khi huấn luyện lẫn khi dự đoán).

    1) Điểm đánh giá = 0 nghĩa là CHƯA có đánh giá, không phải điểm thật -> đổi thành NaN.
    2) Giá gốc thiếu (Hasaki: sản phẩm không giảm giá) -> gia_goc = gia_ban, giảm giá = 0.
       Không điền trung vị vì có thể làm giá gốc nhỏ hơn giá bán.
    """
    d = df.copy()
    if "diem_danh_gia_trung_binh" in d.columns:
        d.loc[d["diem_danh_gia_trung_binh"] <= 0, "diem_danh_gia_trung_binh"] = np.nan
    if {"gia_goc", "gia_ban"} <= set(d.columns):
        d["gia_goc"] = d["gia_goc"].fillna(d["gia_ban"])
        if "so_tien_giam_gia" in d.columns:
            d["so_tien_giam_gia"] = d["so_tien_giam_gia"].fillna(d["gia_goc"] - d["gia_ban"])
        if "ty_le_giam_gia" in d.columns:
            tinh = ((d["gia_goc"] - d["gia_ban"]) / d["gia_goc"].replace(0, np.nan) * 100).round()
            d["ty_le_giam_gia"] = d["ty_le_giam_gia"].fillna(tinh)
    return d


def them_cot_co_dau(df):
    """Thêm các cột CÓ DẤU (bản sao) bên cạnh cột không dấu.
    Mô hình dùng tên có dấu (Giá bán, Giá gốc...); cột không dấu (nguon, ma_san_pham...) vẫn giữ để làm khóa nối.
    Gọi hàm này SAU prepare_ml_data (vì prepare_ml_data xử lý các cột không dấu)."""
    d = df.copy()
    for k, v in TEN_CO_DAU.items():
        if k in d.columns:
            d[v] = d[k]
    return d


# ----------------------------------------------------------------------------
# 4. Ghi kết quả
# ----------------------------------------------------------------------------
def _py(v):
    """Đổi kiểu numpy/NaN sang kiểu Python để MongoDB lưu được."""
    if v is None:
        return None
    if isinstance(v, np.bool_):
        return bool(v)
    if isinstance(v, np.integer):
        return int(v)
    if isinstance(v, (np.floating, float)):
        return None if np.isnan(v) else float(v)
    if isinstance(v, pd.Timestamp):
        return v.to_pydatetime()
    return v


def save_results(coll, df, version="v1"):
    """Ghi DataFrame vào collection `coll` (xóa dữ liệu cũ rồi ghi lại -> chạy lại không bị trùng).
    Luôn lưu thêm output/<coll>.csv để làm báo cáo. Chỉ ghi vào collection ml_*, KHÔNG ghi vào products_cleaned."""
    assert coll.startswith("ml_"), "Chỉ được ghi vào collection ml_*"
    df.to_csv(OUTPUT_DIR / f"{coll}.csv", index=False, encoding="utf-8-sig")
    if not mongo_ok():
        print(f"[Lưu] {coll}: {len(df)} dòng -> output/{coll}.csv (chưa ghi Mongo)")
        return False
    now = datetime.now(timezone.utc)
    docs = [{**{k: _py(v) for k, v in row.items()}, "model_version": version, "created_at": now}
            for row in df.to_dict("records")]
    with _client() as c:
        col = c[DB_NAME][coll]
        col.delete_many({})
        if docs:
            col.insert_many(docs)
        n_db = col.count_documents({})
    print(f"[Lưu] {coll}: DataFrame {len(df)} dòng, MongoDB {n_db} document,",
          "KHỚP" if n_db == len(df) else "KHÔNG KHỚP")
    return True


def save_metrics(model_name, metrics, params, n_train, version="v1"):
    """Ghi 1 dòng vào ml_model_metrics (mỗi mô hình 1 document) và models/metrics.json."""
    doc = {"model_name": model_name, "model_version": version, "metrics": metrics,
           "params": params, "n_train": int(n_train),
           "trained_at": datetime.now(timezone.utc)}
    path = MODELS_DIR / "metrics.json"
    allm = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    allm[model_name] = json.loads(json.dumps(doc, default=lambda o: _py(o) if not isinstance(o, datetime) else o.isoformat()))
    path.write_text(json.dumps(allm, ensure_ascii=False, indent=2), encoding="utf-8")
    if mongo_ok():
        with _client() as c:
            c[DB_NAME]["ml_model_metrics"].replace_one({"model_name": model_name}, doc, upsert=True)
        print(f"[Lưu] ml_model_metrics: đã ghi {model_name}")
    else:
        print(f"[Lưu] metrics {model_name} -> models/metrics.json (chưa ghi Mongo)")


def savefig(plt, name):
    """Lưu biểu đồ ra output/figures/<name>.png"""
    path = FIG_DIR / f"{name}.png"
    plt.tight_layout()
    plt.savefig(path, dpi=130)
    print(f"[Biểu đồ] {path.relative_to(ROOT)}")
