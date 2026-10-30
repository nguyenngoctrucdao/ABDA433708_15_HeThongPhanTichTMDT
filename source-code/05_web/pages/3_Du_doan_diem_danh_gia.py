
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from db import get_collection
from permissions import require_login


# =====================================================
# 1. KIỂM TRA ĐĂNG NHẬP
# =====================================================

require_login()

NAVY = "#152D55"
BLUE = "#2563EB"
CYAN = "#0891B2"
TEXT = "#334155"
GRID = "#E8EEF6"


# =====================================================
# 2. CSS GIAO DIỆN
# =====================================================

st.html("""
<style>
[data-testid="stAppViewContainer"] {
    background: #F4F7FC;
}

[data-testid="stMainBlockContainer"] {
    max-width: 1500px;
    padding-top: 2rem;
    padding-bottom: 3rem;
}

h1, h2, h3 {
    color: #152D55;
}

div[data-testid="stMetric"] {
    background: white;
    border: 1px solid #E2E8F0;
    border-radius: 16px;
    padding: 20px;
    box-shadow: 0 5px 18px rgba(21,45,85,0.05);
}

div[data-testid="stMetricLabel"] p {
    color: #64748B;
    font-weight: 600;
}

div[data-testid="stMetricValue"] {
    color: #152D55;
    font-weight: 750;
}

div[data-testid="stPlotlyChart"] {
    background: white;
    border: 1px solid #E2E8F0;
    border-radius: 16px;
    padding: 12px;
    box-shadow: 0 5px 18px rgba(21,45,85,0.05);
}

div[data-baseweb="select"] > div {
    border-radius: 12px;
    border-color: #DCE5F2;
}

div[data-testid="stExpander"] {
    background: white;
    border-radius: 12px;
    border: 1px solid #E2E8F0;
}

/* Tiêu đề các khu vực phân tích */
.pred-section-title {
    color: #12376B;
    background: linear-gradient(90deg, #DFEBFF 0%, #F1F6FF 100%);
    border-left: 5px solid #2563EB;
    border-radius: 8px;
    padding: 13px 18px;
    margin: 24px 0 16px;
    font-size: 23px;
    font-weight: 800;
    line-height: 1.4;
}
/* Tiêu đề phía trên từng biểu đồ */
.pred-chart-title {
    color: #1D4ED8;
    font-size: 19px;
    font-weight: 750;
    padding: 6px 0 10px;
    margin: 5px 0 14px;
    border-bottom: 2px solid #BFDBFE;
}
</style>
""")


# =====================================================
# 3. HEADER
# =====================================================

st.html("""
<div style="
    background: linear-gradient(110deg, #152D55, #2457A6);
    padding: 32px 38px;
    border-radius: 18px;
    margin-bottom: 25px;
    box-shadow: 0 10px 25px rgba(21,45,85,0.12);
">
    <div style="
        color: #BFDBFE;
        font-size: 13px;
        font-weight: 700;
        letter-spacing: 1px;
        margin-bottom: 12px;
    ">
        E-COMMERCE ANALYTICS / MACHINE LEARNING
    </div>

    <div style="
        color: white;
        font-size: 32px;
        font-weight: 800;
        line-height: 1.3;
        margin-bottom: 12px;
    ">
        Dự đoán điểm đánh giá sản phẩm
    </div>

    <div style="
        color: #DBEAFE;
        font-size: 15px;
        line-height: 1.7;
    ">
        Phân tích kết quả dự đoán bằng Random Forest
        và đánh giá mức độ sai lệch giữa
        điểm thực tế và điểm dự đoán.
    </div>
</div>
""")


# =====================================================
# 4. ĐỌC DỮ LIỆU MONGODB
# =====================================================

@st.cache_data(
    ttl=300,
    show_spinner="Đang tải..."
)
def load_predictions():
    records = list(
        get_collection("ml_rating_predictions").find(
            {},
            {"_id": 0}
        )
    )
    return pd.DataFrame(records)


try:
    df = load_predictions()

except Exception:
    st.error(
        "Không thể đọc dữ liệu từ collection "
        "ml_rating_predictions."
    )
    st.stop()


if df.empty:
    st.warning(
        "Collection ml_rating_predictions "
        "chưa có kết quả dự đoán."
    )
    st.stop()


# =====================================================
# 5. CHUẨN HÓA DỮ LIỆU
# =====================================================

df = df.copy()

required = {
    "rating_thuc",
    "rating_du_doan"
}

if not required.issubset(df.columns):
    st.error(
        "Dữ liệu thiếu cột rating_thuc "
        "hoặc rating_du_doan."
    )
    st.stop()


for col in required:
    df[col] = pd.to_numeric(
        df[col],
        errors="coerce"
    )

valid = df.dropna(
    subset=list(required)
).copy()

if valid.empty:
    st.warning(
        "Không có bản ghi dự đoán hợp lệ."
    )
    st.stop()


valid["Sai số"] = (
    valid["rating_du_doan"]
    - valid["rating_thuc"]
)

valid["Sai số tuyệt đối"] = (
    valid["Sai số"].abs()
)

valid["Sai số bình phương"] = (
    valid["Sai số"] ** 2
)

valid["Đánh giá sai số"] = pd.cut(
    valid["Sai số tuyệt đối"],
    bins=[-0.001, 0.2, 0.5, float("inf")],
    labels=[
        "Sai số thấp",
        "Sai số trung bình",
        "Sai số cao"
    ]
)


# =====================================================
# 6. BỘ LỌC
# =====================================================

st.html('<div class="pred-section-title">Bộ lọc kết quả dự đoán</div>')

filter1, filter2 = st.columns(2)

with filter1:
    if "nguon" in valid.columns:

        sources = sorted(
            valid["nguon"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

        selected_source = st.selectbox(
            "Nguồn dữ liệu",
            ["Tất cả"] + sources
        )

    else:
        selected_source = "Tất cả"


with filter2:
    selected_error = st.selectbox(
        "Mức độ sai số",
        [
            "Tất cả",
            "Sai số thấp",
            "Sai số trung bình",
            "Sai số cao"
        ]
    )


filtered = valid.copy()

if (
    selected_source != "Tất cả"
    and "nguon" in filtered.columns
):
    filtered = filtered[
        filtered["nguon"] == selected_source
    ]


if selected_error != "Tất cả":
    filtered = filtered[
        filtered["Đánh giá sai số"].astype(str)
        == selected_error
    ]


if filtered.empty:
    st.info(
        "Không có dữ liệu phù hợp với bộ lọc."
    )
    st.stop()


# =====================================================
# 7. TÍNH CHỈ SỐ
# =====================================================

mae = filtered["Sai số tuyệt đối"].mean()

rmse = np.sqrt(
    filtered["Sai số bình phương"].mean()
)

y_true = filtered["rating_thuc"].to_numpy()
y_pred = filtered["rating_du_doan"].to_numpy()

ss_res = np.sum(
    (y_true - y_pred) ** 2
)

ss_tot = np.sum(
    (y_true - np.mean(y_true)) ** 2
)

r2 = (
    1 - ss_res / ss_tot
    if len(y_true) >= 2 and ss_tot > 0
    else np.nan
)


# =====================================================
# 8. THẺ KPI
# =====================================================

st.write("")

k1, k2, k3, k4 = st.columns(4)

with k1:
    st.metric(
        "Số bản ghi dự đoán",
        f"{len(filtered):,}"
    )

with k2:
    st.metric(
        "MAE",
        f"{mae:.4f}",
        help=(
            "Mean Absolute Error - "
            "Sai số tuyệt đối trung bình. "
            "Càng thấp càng tốt."
        )
    )

with k3:
    st.metric(
        "RMSE",
        f"{rmse:.4f}",
        help=(
            "Root Mean Squared Error - "
            "Căn bậc hai của sai số "
            "bình phương trung bình."
        )
    )

with k4:
    st.metric(
        "R²",
        f"{r2:.4f}" if pd.notna(r2) else "N/A",
        help=(
            "R-squared - Hệ số xác định. "
            "Đánh giá mức độ mô hình giải thích "
            "biến thiên của điểm đánh giá."
        )
    )


st.caption(
    "Các chỉ số trên được tính từ những bản ghi "
    "đang hiển thị sau khi lọc, không mặc định "
    "là kết quả đánh giá trên tập kiểm tra."
)


# =====================================================
# 9. CẤU HÌNH BIỂU ĐỒ
# =====================================================

def style_figure(fig, height=410):

    fig.update_layout(
        template="plotly_white",
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(
            family="Arial",
            color=TEXT,
            size=12
        ),
        margin=dict(
            l=25,
            r=25,
            t=30,
            b=30
        )
    )

    fig.update_xaxes(
        gridcolor=GRID,
        zeroline=False
    )

    fig.update_yaxes(
        gridcolor=GRID,
        zeroline=False
    )

    return fig


# =====================================================
# 10. BIỂU ĐỒ THỰC TẾ VÀ DỰ ĐOÁN
# =====================================================

st.write("")
st.html('<div class="pred-section-title">Phân tích kết quả dự đoán</div>')

chart1, chart2 = st.columns(
    2,
    gap="large"
)

with chart1:

    st.html('<div class="pred-chart-title">Điểm thực tế và điểm dự đoán</div>')

    hover_cols = [
        col
        for col in [
            "nguon",
            "ma_san_pham"
        ]
        if col in filtered.columns
    ]

    fig_scatter = px.scatter(
        filtered,
        x="rating_thuc",
        y="rating_du_doan",
        color="Đánh giá sai số",
        hover_data=hover_cols,
        color_discrete_map={
            "Sai số thấp": "#0891B2",
            "Sai số trung bình": "#F59E0B",
            "Sai số cao": "#E11D48"
        },
        opacity=0.65,
        labels={
            "rating_thuc": "Điểm thực tế",
            "rating_du_doan": "Điểm dự đoán",
            "Đánh giá sai số": "Mức sai số"
        }
    )

    # Đường dự đoán lý tưởng y = x
    axis_min = min(
        filtered["rating_thuc"].min(),
        filtered["rating_du_doan"].min()
    )

    axis_max = max(
        filtered["rating_thuc"].max(),
        filtered["rating_du_doan"].max()
    )

    fig_scatter.add_trace(
        go.Scatter(
            x=[axis_min, axis_max],
            y=[axis_min, axis_max],
            mode="lines",
            name="Dự đoán lý tưởng",
            line=dict(
                color="#10B981",
                dash="dash",
                width=2
            )
        )
    )

    style_figure(fig_scatter)

    st.plotly_chart(
        fig_scatter,
        use_container_width=True
    )


# =====================================================
# 11. BIỂU ĐỒ PHÂN BỐ SAI SỐ
# =====================================================

with chart2:

    st.html('<div class="pred-chart-title">Phân bố sai số dự đoán</div>')

    fig_hist = px.histogram(
        filtered,
        x="Sai số",
        nbins=30,
        color_discrete_sequence=[BLUE],
        labels={
            "Sai số": "Sai số (Dự đoán - Thực tế)"
        }
    )

    fig_hist.add_vline(
        x=0,
        line_dash="dash",
        line_color="#10B981",
        annotation_text="Sai số = 0"
    )

    style_figure(fig_hist)

    st.plotly_chart(
        fig_hist,
        use_container_width=True
    )


# =====================================================
# 12. SO SÁNH ĐIỂM TRUNG BÌNH
# =====================================================

st.html('<div class="pred-section-title">So sánh điểm đánh giá trung bình</div>')

avg_compare = pd.DataFrame({
    "Loại điểm": [
        "Điểm thực tế",
        "Điểm dự đoán"
    ],
    "Điểm trung bình": [
        filtered["rating_thuc"].mean(),
        filtered["rating_du_doan"].mean()
    ]
})

fig_compare = px.bar(
    avg_compare,
    x="Loại điểm",
    y="Điểm trung bình",
    color="Loại điểm",
    text="Điểm trung bình",
    color_discrete_map={
        "Điểm thực tế": NAVY,
        "Điểm dự đoán": BLUE
    }
)

fig_compare.update_traces(
    texttemplate="%{text:.2f}",
    textposition="outside"
)

fig_compare.update_layout(
    showlegend=False
)

fig_compare.update_yaxes(
    range=[0, 5]
)

style_figure(fig_compare, height=350)

st.plotly_chart(
    fig_compare,
    use_container_width=True
)


# =====================================================
# 13. BẢNG KẾT QUẢ DỰ ĐOÁN
# =====================================================

st.html('<div class="pred-section-title">Bảng kết quả dự đoán</div>')

st.caption(
    f"Đang hiển thị {len(filtered):,} bản ghi."
)

preferred_cols = [
    "nguon",
    "ma_san_pham",
    "rating_thuc",
    "rating_du_doan",
    "Sai số",
    "Sai số tuyệt đối",
    "Đánh giá sai số"
]

display_cols = [
    col
    for col in preferred_cols
    if col in filtered.columns
]

display_df = filtered[
    display_cols
].copy()

display_df = display_df.rename(
    columns={
        "nguon": "Nguồn dữ liệu",
        "ma_san_pham": "Mã sản phẩm",
        "rating_thuc": "Điểm thực tế",
        "rating_du_doan": "Điểm dự đoán"
    }
)

st.dataframe(
    display_df,
    hide_index=True,
    use_container_width=True,
    height=400
)


# =====================================================
# 14. XUẤT FILE CSV
# =====================================================

csv_data = display_df.to_csv(
    index=False
).encode("utf-8-sig")

st.download_button(
    "Tải kết quả dự đoán (CSV)",
    data=csv_data,
    file_name="ket_qua_du_doan_diem_danh_gia.csv",
    mime="text/csv"
)


# =====================================================
# 15. GIẢI THÍCH CÁC CHỈ SỐ
# =====================================================

with st.expander(
    "Giải thích thuật toán và các chỉ số đánh giá"
):

    st.markdown("""
    **Random Forest Regressor**

    Là thuật toán học có giám sát sử dụng
    nhiều cây quyết định để dự đoán
    giá trị liên tục.

    Trong hệ thống này, biến mục tiêu là
    điểm đánh giá trung bình của sản phẩm.

    **MAE (Mean Absolute Error)**

    Sai số tuyệt đối trung bình giữa
    điểm dự đoán và điểm thực tế.

    **RMSE (Root Mean Squared Error)**

    Căn bậc hai của sai số bình phương trung bình,
    nhạy hơn với những sai số lớn.

    **R² (R-squared)**

    Hệ số xác định, phản ánh mức độ mô hình
    giải thích sự biến thiên của biến mục tiêu.
    R² có thể mang giá trị âm.

    **Đường dự đoán lý tưởng**

    Là đường y = x trên biểu đồ phân tán.
    Điểm dữ liệu càng gần đường này thì
    dự đoán càng gần giá trị thực tế.
    """)
