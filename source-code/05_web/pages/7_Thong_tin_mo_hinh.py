
import json
from html import escape
import re
import unicodedata
import streamlit as st
import pandas as pd

from db import get_collection
from permissions import require_login


# =====================================================
# 1. KIỂM TRA ĐĂNG NHẬP
# =====================================================

require_login()


# =====================================================
# 2. CSS GIAO DIỆN
# =====================================================

st.html("""
<style>
/* Nền trang */
[data-testid="stAppViewContainer"] {
    background-color: #f4f7fc;
}

/* Nội dung chính */
[data-testid="stMainBlockContainer"] {
    max-width: 1450px;
    padding-top: 2rem;
    padding-bottom: 3rem;
}

/* Tiêu đề */
h1, h2, h3 {
    color: #172f55;
}

/* Các khung thông tin */
div[data-testid="stVerticalBlockBorderWrapper"] > div {
    border-radius: 16px;
}

/* KPI */
div[data-testid="stMetric"] {
    background: #ffffff;
    border: 1px solid #e1e8f3;
    border-radius: 14px;
    padding: 18px;
    box-shadow: 0 4px 14px rgba(21, 45, 85, 0.05);
}

div[data-testid="stMetricLabel"] p {
    color: #64748b;
    font-weight: 600;
}

div[data-testid="stMetricValue"] {
    color: #1d4ed8;
}

/* Tiêu đề từng mô hình: biểu tượng vector và bố cục đồng nhất */
.ml-model-heading {
    display: flex;
    align-items: flex-start;
    gap: 17px;
    padding: 21px 22px;
    margin-bottom: 24px;
    border: 1px solid #dbe6f5;
    border-radius: 15px;
    background: linear-gradient(110deg, #f8fbff, #eef4fc);
}
.ml-model-icon {
    width: 56px;
    height: 56px;
    min-width: 56px;
    border-radius: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #ffffff;
    background: linear-gradient(135deg, #173b70, #2563b9);
}
.ml-model-heading-content { flex: 1; min-width: 0; }
.ml-model-eyebrow {
    color: #3971af;
    font-size: 11px;
    font-weight: 750;
    letter-spacing: 1px;
    margin-bottom: 5px;
}
.ml-model-title {
    color: #173257;
    font-size: 24px;
    font-weight: 800;
    line-height: 1.3;
}
.ml-model-description {
    color: #536780;
    font-size: 14px;
    line-height: 1.6;
    margin-top: 7px;
}
.ml-model-version {
    border: 1px solid #cbdcf2;
    border-radius: 999px;
    padding: 6px 11px;
    color: #24568e;
    background: #ffffff;
    font-size: 12px;
    font-weight: 650;
    white-space: nowrap;
}
@media (max-width: 700px) {
    .ml-model-heading { flex-wrap: wrap; padding: 16px; gap: 12px; }
    .ml-model-title { font-size: 20px; }
    .ml-model-version { margin-left: 68px; }
}

/* Mục mở rộng */
div[data-testid="stExpander"] {
    background: white;
    border-radius: 12px;
    border: 1px solid #e1e8f3;
}
</style>
""")


# =====================================================
# 3. THÔNG TIN CÁC MÔ HÌNH
# =====================================================

MODEL_INFO = {
    "kmeans": {
        "title": "K-Means Clustering",
        "type": "HỌC KHÔNG GIÁM SÁT",
        "symbol": "clusters",
        "description": (
            "Mô hình học không giám sát dùng để phân nhóm "
            "các sản phẩm có đặc điểm tương đồng."
        ),
    },
    "random_forest_rating": {
        "title": "Random Forest Regressor",
        "type": "HỌC CÓ GIÁM SÁT",
        "symbol": "forest",
        "description": (
            "Mô hình học có giám sát dùng để dự đoán "
            "điểm đánh giá trung bình của sản phẩm."
        ),
    },
    "isolation_forest": {
        "title": "Isolation Forest",
        "type": "PHÁT HIỆN BẤT THƯỜNG",
        "symbol": "anomaly",
        "description": (
            "Mô hình phát hiện bất thường, hỗ trợ nhận diện "
            "những sản phẩm có đặc điểm khác biệt."
        ),
    },
}

MODEL_ICONS = {
    "clusters": '<circle cx="7" cy="7" r="3"/><circle cx="18" cy="7" r="3"/><circle cx="12" cy="18" r="3"/><path d="M9.5 9.5l1.5 5M15.5 9.5l-2 5"/>',
    "forest": '<path d="M4 20h16M7 17V9M12 17V5M17 17V11"/><path d="M4 12l3-3 3 3M9 8l3-3 3 3M14 14l3-3 3 3"/>',
    "anomaly": '<circle cx="11" cy="11" r="7"/><path d="m16.5 16.5 4 4M11 7v5M11 15h.01"/>',
}


def render_model_heading(model_info, version):
    """Chỉ tạo tiêu đề giao diện; không thay đổi kết quả mô hình."""
    title = escape(str(model_info.get("title", "Mô hình")))
    model_type = escape(str(model_info.get("type", "MACHINE LEARNING")))
    description = escape(str(model_info.get("description", "")))
    version_text = escape(str(version))
    svg_paths = MODEL_ICONS.get(model_info.get("symbol"), MODEL_ICONS["clusters"])
    st.html(f"""
    <div class="ml-model-heading">
      <div class="ml-model-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
             stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"
             width="28" height="28" aria-hidden="true">{svg_paths}</svg>
      </div>
      <div class="ml-model-heading-content">
        <div class="ml-model-eyebrow">{model_type}</div>
        <div class="ml-model-title">{title}</div>
        <div class="ml-model-description">{description}</div>
      </div>
      <div class="ml-model-version">Phiên bản {version_text}</div>
    </div>
    """)


# =====================================================
# 4. GIẢI THÍCH CÁC CHỈ SỐ
# =====================================================

METRIC_INFO = {
    "MAE": {
        "name": "Mean Absolute Error",
        "vi": "Sai số tuyệt đối trung bình",
        "meaning": (
            "Đo mức chênh lệch tuyệt đối trung bình giữa "
            "giá trị dự đoán và giá trị thực tế. "
            "Càng thấp càng tốt."
        ),
    },
    "RMSE": {
        "name": "Root Mean Squared Error",
        "vi": "Căn bậc hai của sai số bình phương trung bình",
        "meaning": (
            "Đánh giá độ lớn sai số dự đoán, đồng thời "
            "phạt mạnh hơn các sai số lớn. "
            "Càng thấp càng tốt."
        ),
    },
    "R2": {
        "name": "R-squared",
        "vi": "Hệ số xác định R²",
        "meaning": (
            "Phản ánh mức độ mô hình giải thích sự biến thiên "
            "của biến mục tiêu. Giá trị cao hơn thường tốt hơn; "
            "R² cũng có thể âm."
        ),
    },
    "silhouette": {
        "name": "Silhouette Score",
        "vi": "Hệ số đánh giá chất lượng phân cụm",
        "meaning": (
            "Đo mức độ gắn kết trong cùng cụm và "
            "phân tách giữa các cụm. "
            "Giá trị gần 1 thường thể hiện phân cụm tốt."
        ),
    },
    "inertia": {
        "name": "Inertia",
        "vi": "Tổng bình phương khoảng cách đến tâm cụm",
        "meaning": (
            "Đo độ phân tán của các điểm dữ liệu quanh "
            "tâm cụm. Cần xem xét cùng số cụm và "
            "các chỉ số khác khi đánh giá."
        ),
    },
    "pca_explained_variance": {
        "name": "PCA Explained Variance",
        "vi": "Tỷ lệ phương sai được giải thích bởi PCA",
        "meaning": (
            "Cho biết các thành phần chính giữ lại "
            "bao nhiêu thông tin biến thiên của dữ liệu."
        ),
    },
}


# =====================================================
# 5. CÁC HÀM XỬ LÝ DỮ LIỆU
# =====================================================

def parse_json(value):
    """Chuyển JSON dạng chuỗi thành dict/list nếu có."""
    if isinstance(value, (dict, list)):
        return value

    if isinstance(value, str):
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value

    return value


def normalize_metric_key(key):
    """Chuẩn hóa tên chỉ số để tra cứu."""
    key = str(key).strip()

    aliases = {
        "r²": "R2",
        "r2": "R2",
        "r_squared": "R2",
        "mae": "MAE",
        "rmse": "RMSE",
        "silhouette_score": "silhouette",
        "silhouette": "silhouette",
        "inertia": "inertia",
    }

    return aliases.get(key.lower(), key)


def flatten_metrics(data, prefix=""):
    """
    Chuyển metrics dạng JSON lồng nhau thành
    danh sách các chỉ số số học.
    """
    results = []

    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, dict):
                results.extend(
                    flatten_metrics(value, prefix)
                )
            elif isinstance(value, (int, float)) and not isinstance(value, bool):
                results.append((str(key), value))
            elif isinstance(value, list):
                # Giữ các danh sách kỹ thuật ở mục chi tiết
                continue

    return results


def format_number(value):
    """Định dạng giá trị chỉ số."""
    if pd.isna(value):
        return "N/A"

    return f"{float(value):,.4f}"


METRIC_DISPLAY_NAMES = {
    "mae_cai_thien_so_voi_co_so_pct": "Mức cải thiện MAE so với mô hình cơ sở (%)",
    "cv5_mae_rf": "MAE trung bình qua 5 lần kiểm định chéo",
    "cv5_mae_baseline": "MAE mô hình cơ sở qua 5 lần kiểm định chéo",
    "n_test": "Số sản phẩm trong tập kiểm tra",
    "num__Số lượng đã bán": "Mức độ quan trọng – Số lượng đã bán",
    "num__Giá bán": "Mức độ quan trọng – Giá bán",
    "num__Giá gốc": "Mức độ quan trọng – Giá gốc",
    "num__Số lượt đánh giá": "Mức độ quan trọng – Số lượt đánh giá",
    "num__Tỷ lệ giảm giá": "Mức độ quan trọng – Tỷ lệ giảm giá",
    
    "gia_ban_le_0": "Số sản phẩm có giá bán ≤ 0",
    "gia_ban_gt_gia_goc": "Số sản phẩm có giá bán lớn hơn giá gốc",
    "ty_le_giam_gia_ngoai_0_100": "Số sản phẩm có tỷ lệ giảm giá ngoài 0–100%",
    "gia_goc_thieu": "Số sản phẩm thiếu giá gốc",
    "so_tien_giam_gia_thieu": "Số sản phẩm thiếu số tiền giảm giá",
    "so_dong_thieu_gia_goc_khong_xet": "Số dòng thiếu giá gốc không được xét",
    "hasaki": "Số sản phẩm Hasaki",
    "tiki": "Số sản phẩm Tiki",
    "jaccard_khi_them_so_luong_da_ban": "Độ tương đồng Jaccard khi bổ sung số lượng đã bán",
    "ty_le_trung_voi_iqr": "Tỷ lệ trùng kết quả với phương pháp IQR",
}

def get_metric_display_name(key):
    """Chỉ đổi nhãn hiển thị; không sửa tên trường MongoDB."""
    raw_key = str(key).strip()
    normalized = normalize_metric_key(raw_key)

    # Giữ nguyên các ánh xạ đã có trong phiên bản gốc.
    if raw_key in METRIC_DISPLAY_NAMES:
        return METRIC_DISPLAY_NAMES[raw_key]

    if normalized in METRIC_INFO:
        return METRIC_INFO[normalized]["vi"]

    # Chuẩn hóa để nhận diện cả dấu tiếng Việt, khoảng trắng, dấu _ và ký hiệu.
    def clean_name(value):
        value = str(value).lower().strip()
        value = unicodedata.normalize("NFD", value)
        value = "".join(c for c in value if unicodedata.category(c) != "Mn")
        value = value.replace("đ", "d")
        value = value.replace("≤", " le ").replace("<=", " le ")
        value = value.replace(">=", " ge ").replace(">", " gt ")
        value = re.sub(r"[^a-z0-9]+", "_", value)
        return value.strip("_")

    key_clean = clean_name(raw_key)

    # So khớp các tên đã định nghĩa, dù tên gốc khác dấu hoặc dấu cách.
    for original, display in METRIC_DISPLAY_NAMES.items():
        if clean_name(original) == key_clean:
            return display

    # Một số tên MongoDB dùng ký hiệu hoặc cách viết khác.
    extra_names = {
        "gia_ban_le_0": "Số sản phẩm có giá bán ≤ 0",
        "gia_ban_gt_gia_goc": "Số sản phẩm có giá bán lớn hơn giá gốc",
        "ty_le_giam_gia_ngoai_0_100": "Số sản phẩm có tỷ lệ giảm giá ngoài 0–100%",
        "gia_goc_thieu": "Số sản phẩm thiếu giá gốc",
        "so_tien_giam_gia_thieu": "Số sản phẩm thiếu số tiền giảm giá",
        "so_dong_thieu_gia_goc_khong_xet": "Số dòng thiếu giá gốc không được xét",
        "jaccard_khi_them_so_luong_da_ban": "Độ tương đồng Jaccard khi bổ sung số lượng đã bán",
        "ty_le_trung_voi_iqr": "Tỷ lệ trùng kết quả với phương pháp IQR",
    }
    if key_clean in extra_names:
        return extra_names[key_clean]

    if raw_key.startswith("num__"):
        return "Mức độ quan trọng – " + raw_key.removeprefix("num__")

    return raw_key.replace("_", " ")

def show_metrics(metrics):
    """Hiển thị chỉ số dưới dạng các KPI."""
    metric_list = flatten_metrics(metrics)

    if not metric_list:
        st.info(
            "Chưa có chỉ số dạng số để hiển thị. "
            "Xem dữ liệu kỹ thuật bên dưới."
        )
        return

    for start in range(0, len(metric_list), 3):
        cols = st.columns(3)

        for col, (key, value) in zip(
            cols,
            metric_list[start:start + 3]
        ):
            normalized = normalize_metric_key(key)
            info = METRIC_INFO.get(normalized, {})

            with col:
                st.metric(
                    label=get_metric_display_name(key),
                    value=format_number(value),
                    help=(
                        f"{info.get('name', key)} — "
                        f"{info.get('vi', '')}\n\n"
                        f"{info.get('meaning', '')}"
                    ) if info else None
                )

def show_json_data(title, value):
    """Hiển thị JSON có định dạng dễ đọc."""
    st.markdown(f"**{title}**")

    if isinstance(value, (dict, list)):
        st.json(value, expanded=False)
    elif value is None:
        st.caption("Chưa có dữ liệu.")
    else:
        st.code(str(value), language="text")


# =====================================================
# 6. ĐỌC DỮ LIỆU MONGODB
# =====================================================

try:
    records = list(
        get_collection("ml_model_metrics").find(
            {},
            {"_id": 0}
        )
    )

except Exception:
    st.error(
        "Không thể đọc dữ liệu từ collection "
        "ml_model_metrics. Vui lòng kiểm tra MongoDB."
    )
    st.stop()


# =====================================================
# 7. HEADER
# =====================================================


# =====================================================
# 7. HEADER - ĐÃ SỬA LỖI HTML
# =====================================================

st.html("""
<style>
.model-header {
    background: linear-gradient(
        110deg,
        #152d55,
        #2457a6
    );
    padding: 32px 38px;
    border-radius: 18px;
    margin-bottom: 28px;
    box-shadow: 0 10px 25px rgba(21, 45, 85, 0.12);
}

.model-header-label {
    font-size: 13px;
    letter-spacing: 1.2px;
    color: #bfdbfe;
    font-weight: 700;
    margin-bottom: 12px;
}

.model-header-title {
    color: #ffffff !important;
    font-size: 34px;
    font-weight: 800;
    line-height: 1.3;
    margin: 0 0 12px 0;
}

.model-header-description {
    color: #dbeafe;
    font-size: 15px;
    line-height: 1.7;
    margin: 0;
}

@media (max-width: 768px) {
    .model-header {
        padding: 24px;
    }

    .model-header-title {
        font-size: 26px;
    }
}
</style>

<div class="model-header">
    <div class="model-header-label">
        E-COMMERCE ANALYTICS / MACHINE LEARNING
    </div>

    <h1 class="model-header-title">
        Thông tin và đánh giá mô hình
    </h1>

    <p class="model-header-description">
        Tổng hợp kết quả đánh giá các mô hình
        Machine Learning trên dữ liệu Tiki và Hasaki.
    </p>
</div>
""")


if not records:
    st.warning(
        "Collection ml_model_metrics chưa có dữ liệu."
    )
    st.stop()


# =====================================================
# 8. THỐNG KÊ TỔNG QUAN
# =====================================================

unique_models = {
    str(row.get("model_name", ""))
    for row in records
}

c1, c2 = st.columns(2)

with c1:
    st.metric(
        "Số mô hình",
        len(unique_models)
    )

with c2:
    st.metric(
        "Số bản ghi đánh giá",
        len(records)
    )

st.write("")


# =====================================================
# 9. THÔNG TIN TỪNG MÔ HÌNH
# =====================================================

st.subheader("Kết quả đánh giá từng mô hình")

# Sắp xếp theo thứ tự mong muốn
model_order = {
    "kmeans": 0,
    "random_forest_rating": 1,
    "isolation_forest": 2,
}

records.sort(
    key=lambda row: model_order.get(
        row.get("model_name", ""),
        99
    )
)

for row in records:

    model_name = str(
        row.get("model_name", "unknown")
    )

    version = str(
        row.get("model_version", "N/A")
    )

    model_info = MODEL_INFO.get(
        model_name,
        {
            "title": model_name,
            "symbol": "clusters",
            "type": "MACHINE LEARNING",
            "description": "Thông tin đánh giá mô hình.",
        }
    )

    metrics = parse_json(
        row.get("metrics", {})
    )

    params = parse_json(
        row.get("params", {})
    )

    with st.container(border=True):

        render_model_heading(model_info, version)

        st.markdown("#### Các chỉ số đánh giá")

        show_metrics(metrics)

        with st.expander(
            "Xem thông số kỹ thuật và dữ liệu chi tiết"
        ):

            show_json_data(
                "Chỉ số đánh giá (Metrics)",
                metrics
            )

            show_json_data(
                "Tham số mô hình (Parameters)",
                params
            )

    st.write("")


# =====================================================
# 10. GIẢI THÍCH CÁC CHỈ SỐ
# =====================================================

st.subheader("Giải thích thuật ngữ đánh giá")

st.caption(
    "Các chỉ số dưới đây giúp diễn giải kết quả "
    "của mô hình Machine Learning."
)

for key, info in METRIC_INFO.items():

    display_name = "R²" if key == "R2" else key

    with st.expander(
        f"{display_name} — {info['name']}"
    ):

        st.markdown(
            f"**Tên tiếng Việt:** {info['vi']}"
        )

        st.write(
            info["meaning"]
        )


# =====================================================
# 11. GHI CHÚ
# =====================================================

st.info(
    "Các chỉ số được đọc trực tiếp từ collection "
    "ml_model_metrics trong MongoDB. "
    "Trang này chỉ hiển thị và giải thích kết quả, "
    "không huấn luyện lại mô hình."
)