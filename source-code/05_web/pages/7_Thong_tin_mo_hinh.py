
import json
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
        "icon": "🔷",
        "description": (
            "Mô hình học không giám sát dùng để phân nhóm "
            "các sản phẩm có đặc điểm tương đồng."
        ),
    },
    "random_forest_rating": {
        "title": "Random Forest Regressor",
        "icon": "🌳",
        "description": (
            "Mô hình học có giám sát dùng để dự đoán "
            "điểm đánh giá trung bình của sản phẩm."
        ),
    },
    "isolation_forest": {
        "title": "Isolation Forest",
        "icon": "🔍",
        "description": (
            "Mô hình phát hiện bất thường, hỗ trợ nhận diện "
            "những sản phẩm có đặc điểm khác biệt."
        ),
    },
}


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
                    label=(
                        "R²" if normalized == "R2"
                        else normalized
                    ),
                    value=format_number(value),
                    help=(
                        f"{info.get('name', key)} — "
                        f"{info.get('vi', '')}\n\n"
                        f"{info.get('meaning', '')}"
                    ) if info else None
                )

                if info:
                    st.caption(info["vi"])


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
            "icon": "📈",
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

        st.markdown(
            f"### {model_info['icon']} "
            f"{model_info['title']}"
        )

        st.caption(
            f"Phiên bản: {version}"
        )

        st.write(
            model_info["description"]
        )

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