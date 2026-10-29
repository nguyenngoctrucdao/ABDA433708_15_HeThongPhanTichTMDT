"""
predict.py - Hàm dự đoán cho web (Streamlit/Flask...). Web chỉ cần: from predict import ...

  assign_cluster(df)  -> thêm cột cluster, cluster_label
  predict_rating(df)  -> mảng điểm đánh giá dự đoán (1..5)
  score_anomaly(df)   -> thêm cột anomaly_score, is_anomaly

DataFrame đầu vào dùng tên cột KHÔNG DẤU
Cột nào thiếu giá gốc / giảm giá sẽ được tự điền giống lúc huấn luyện.
"""
from functools import lru_cache

import joblib
import numpy as np
import pandas as pd

from common import MODELS_DIR, TEN_KHONG_DAU, prepare_ml_data, them_cot_co_dau


@lru_cache(maxsize=None)
def _load(name):
    path = MODELS_DIR / f"{name}.pkl"
    if not path.exists():
        raise FileNotFoundError(f"Chưa có {path}. Hãy chạy: python run_all.py")
    return joblib.load(path)


def _need(df, cols):
    """Kiểm tra DataFrame đầu vào có đủ cột. Web dùng tên KHÔNG DẤU (gia_ban...), nên đổi tên có dấu về không dấu."""
    cols = [TEN_KHONG_DAU.get(c, c) for c in cols]
    thieu = [c for c in cols if c not in df.columns]
    if thieu:
        raise ValueError(f"DataFrame thiếu cột: {thieu}")


def assign_cluster(df: pd.DataFrame) -> pd.DataFrame:
    """Cần các cột: gia_ban, gia_goc, so_tien_giam_gia, ty_le_giam_gia, diem_danh_gia_trung_binh
    (0 hoặc để trống = chưa có đánh giá), so_luot_danh_gia, so_luong_da_ban."""
    a = _load("kmeans")
    _need(df, a["features"])
    d = them_cot_co_dau(prepare_ml_data(df))
    out = df.copy()
    out["cluster"] = a["model"].predict(d[a["features"]])
    out["cluster_label"] = out["cluster"].map(a["labels"])
    return out


def predict_rating(df: pd.DataFrame) -> np.ndarray:
    """Cần các cột: nguon, ten_danh_muc, gia_ban, gia_goc, ty_le_giam_gia, so_luot_danh_gia, so_luong_da_ban."""
    a = _load("rf_rating")
    _need(df, a["features"])
    d = them_cot_co_dau(prepare_ml_data(df))
    return np.clip(a["model"].predict(d[a["features"]]), 1, 5)


def score_anomaly(df: pd.DataFrame) -> pd.DataFrame:
    """Cần các cột: nguon, gia_ban, gia_goc, so_tien_giam_gia, ty_le_giam_gia.
    Sàn chưa từng huấn luyện (nguon lạ) -> is_anomaly = False, score = NaN."""
    a = _load("iforest")
    _need(df, ["nguon"] + a["features"])
    d = them_cot_co_dau(prepare_ml_data(df))
    out = df.copy()
    out["anomaly_score"] = np.nan
    out["is_anomaly"] = False
    for src, m in a["models"].items():
        idx = (out["nguon"] == src).to_numpy()
        if idx.any():
            X = d.loc[idx, a["features"]]
            out.loc[idx, "anomaly_score"] = (-m.score_samples(X)).round(4)
            out.loc[idx, "is_anomaly"] = m.predict(X) == -1
    return out
