
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from db import get_collection
from permissions import require_login


# =====================================================
# 1. KIỂM TRA ĐĂNG NHẬP
# =====================================================

require_login()


# =====================================================
# 2. CẤU HÌNH MÀU SẮC
# =====================================================

NAVY = "#152D55"
BLUE = "#2563EB"
TEXT = "#334155"
GRID = "#E8EEF6"

CLUSTER_COLORS = [
    "#2563EB",
    "#0891B2",
    "#7C3AED",
    "#0D9488",
    "#F59E0B",
    "#E11D48",
    "#64748B",
    "#84CC16"
]


# =====================================================
# 3. CSS GIAO DIỆN
# =====================================================

st.html("""
<style>
/* Nền nội dung */
[data-testid="stAppViewContainer"] {
    background: #F4F7FC;
}

/* Khung chính */
[data-testid="stMainBlockContainer"] {
    max-width: 1500px;
    padding-top: 2rem;
    padding-bottom: 3rem;
}

/* Tiêu đề */
h1, h2, h3 {
    color: #152D55;
}

/* KPI */
div[data-testid="stMetric"] {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 16px;
    padding: 20px;
    box-shadow: 0 5px 18px rgba(21, 45, 85, 0.05);
}

div[data-testid="stMetricLabel"] p {
    color: #64748B;
    font-size: 14px;
    font-weight: 600;
}

div[data-testid="stMetricValue"] {
    color: #152D55;
    font-weight: 750;
}

/* Bộ lọc */
div[data-baseweb="select"] > div {
    border-radius: 12px;
    border-color: #DCE5F2;
}

/* Khung biểu đồ */
div[data-testid="stPlotlyChart"] {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 16px;
    padding: 12px;
    box-shadow: 0 5px 18px rgba(21, 45, 85, 0.05);
}

/* Bảng dữ liệu */
div[data-testid="stDataFrame"] {
    border-radius: 12px;
    overflow: hidden;
}

/* Mục mở rộng */
div[data-testid="stExpander"] {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
}
</style>
""")


# =====================================================
# 4. HEADER
# =====================================================

# Dùng st.html để tránh lỗi hiện nguyên thẻ HTML
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
        Phân cụm sản phẩm bằng K-Means
    </div>

    <div style="
        color: #DBEAFE;
        font-size: 15px;
        line-height: 1.7;
    ">
        Phân tích các nhóm sản phẩm có đặc điểm tương đồng
        thông qua thuật toán K-Means và trực quan hóa PCA.
    </div>
</div>
""")


# =====================================================
# 5. ĐỌC DỮ LIỆU MONGODB
# =====================================================

@st.cache_data(ttl=300)
def load_kmeans_results():
    records = list(
        get_collection("ml_kmeans_results").find(
            {},
            {"_id": 0}
        )
    )
    return pd.DataFrame(records)


@st.cache_data(ttl=300)
def load_cluster_profiles():
    records = list(
        get_collection("ml_cluster_profile").find(
            {},
            {"_id": 0}
        )
    )
    return pd.DataFrame(records)


try:
    df = load_kmeans_results()
    profiles_df = load_cluster_profiles()

except Exception:
    st.error(
        "Không thể đọc dữ liệu phân cụm từ MongoDB. "
        "Vui lòng kiểm tra kết nối."
    )
    st.stop()


if df.empty:
    st.warning(
        "Collection ml_kmeans_results chưa có dữ liệu."
    )
    st.stop()


if "cluster" not in df.columns:
    st.error(
        "Dữ liệu thiếu cột 'cluster'. "
        "Vui lòng kiểm tra kết quả từ TV4."
    )
    st.stop()


# =====================================================
# 6. CHUẨN HÓA DỮ LIỆU HIỂN THỊ
# =====================================================

df = df.copy()

df["cluster"] = pd.to_numeric(
    df["cluster"],
    errors="coerce"
)

df = df.dropna(
    subset=["cluster"]
).copy()

if df.empty:
    st.warning("Không có mã cụm hợp lệ để hiển thị.")
    st.stop()

df["cluster"] = df["cluster"].astype(int)

df["Tên cụm"] = df["cluster"].apply(
    lambda x: f"Cụm {x}"
)

if "cluster_label" in df.columns:
    df["Nhãn mô tả"] = df["cluster_label"].fillna(
        "Chưa có mô tả"
    )

for col in ["pc1", "pc2"]:
    if col in df.columns:
        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )


# =====================================================
# 7. BỘ LỌC
# =====================================================

st.subheader("Bộ lọc phân tích")

all_clusters = sorted(
    df["cluster"].unique().tolist()
)

filter_col1, filter_col2 = st.columns(
    [1, 2],
    gap="medium"
)

with filter_col1:
    selected_clusters = st.multiselect(
        "Chọn cụm sản phẩm",
        options=all_clusters,
        default=all_clusters,
        format_func=lambda x: f"Cụm {x}",
        placeholder="Chọn cụm"
    )

with filter_col2:
    search_keyword = st.text_input(
        "Tìm mã sản phẩm",
        placeholder="Nhập mã sản phẩm để tìm kiếm..."
    )


filtered_df = df[
    df["cluster"].isin(selected_clusters)
].copy()

if search_keyword.strip():
    id_col = (
        "ma_san_pham"
        if "ma_san_pham" in filtered_df.columns
        else "Mã sản phẩm"
        if "Mã sản phẩm" in filtered_df.columns
        else None
    )

    if id_col:
        filtered_df = filtered_df[
            filtered_df[id_col]
            .astype(str)
            .str.contains(
                search_keyword.strip(),
                case=False,
                regex=False,
                na=False
            )
        ]

if filtered_df.empty:
    st.info(
        "Không có sản phẩm phù hợp với bộ lọc hiện tại."
    )
    st.stop()


# =====================================================
# 8. THẺ KPI
# =====================================================

total_products = len(filtered_df)
total_clusters = filtered_df["cluster"].nunique()

largest_cluster = (
    filtered_df["cluster"]
    .value_counts()
    .idxmax()
)

largest_count = (
    filtered_df["cluster"]
    .value_counts()
    .max()
)

k1, k2, k3, k4 = st.columns(4)

with k1:
    st.metric(
        "Sản phẩm phân cụm",
        f"{total_products:,}"
    )

with k2:
    st.metric(
        "Số cụm đang hiển thị",
        total_clusters
    )

with k3:
    st.metric(
        "Cụm lớn nhất",
        f"Cụm {largest_cluster}"
    )

with k4:
    st.metric(
        "Sản phẩm trong cụm lớn nhất",
        f"{largest_count:,}"
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
            b=25
        ),
        legend=dict(
            title="Cụm sản phẩm",
            orientation="h",
            y=-0.2
        )
    )

    fig.update_xaxes(
        showgrid=False,
        zeroline=False
    )

    fig.update_yaxes(
        gridcolor=GRID,
        zeroline=False
    )

    return fig


color_map = {
    f"Cụm {cluster}": CLUSTER_COLORS[
        i % len(CLUSTER_COLORS)
    ]
    for i, cluster in enumerate(all_clusters)
}


# =====================================================
# 10. BIỂU ĐỒ PHÂN BỐ CỤM
# =====================================================

st.write("")
st.subheader("Trực quan hóa kết quả phân cụm")

chart_col1, chart_col2 = st.columns(
    2,
    gap="large"
)

with chart_col1:

    st.markdown("#### Phân bố sản phẩm theo cụm")

    cluster_counts = (
        filtered_df["Tên cụm"]
        .value_counts()
        .reset_index()
    )

    cluster_counts.columns = [
        "Cụm",
        "Số sản phẩm"
    ]

    cluster_counts["Cụm số"] = (
        cluster_counts["Cụm"]
        .str.extract(r"(\d+)")
        .astype(int)
    )

    cluster_counts = cluster_counts.sort_values(
        "Cụm số"
    )

    fig_bar = px.bar(
        cluster_counts,
        x="Cụm",
        y="Số sản phẩm",
        color="Cụm",
        text="Số sản phẩm",
        color_discrete_map=color_map
    )

    fig_bar.update_traces(
        textposition="outside",
        marker_line_width=0
    )

    fig_bar.update_layout(
        showlegend=False
    )

    style_figure(fig_bar)

    st.plotly_chart(
        fig_bar,
        use_container_width=True
    )


# =====================================================
# 11. BIỂU ĐỒ PCA
# =====================================================

with chart_col2:

    st.markdown("#### Trực quan hóa phân cụm PCA")

    if {"pc1", "pc2"}.issubset(
        filtered_df.columns
    ):

        pca_df = filtered_df.dropna(
            subset=["pc1", "pc2"]
        ).copy()

        if not pca_df.empty:

            hover_cols = [
                col
                for col in [
                    "nguon",
                    "ma_san_pham",
                    "cluster_label"
                ]
                if col in pca_df.columns
            ]

            fig_pca = px.scatter(
                pca_df,
                x="pc1",
                y="pc2",
                color="Tên cụm",
                color_discrete_map=color_map,
                hover_data=hover_cols,
                opacity=0.65,
                labels={
                    "pc1": "Thành phần chính 1",
                    "pc2": "Thành phần chính 2",
                    "Tên cụm": "Cụm"
                }
            )

            fig_pca.update_traces(
                marker=dict(size=7)
            )

            style_figure(fig_pca)

            st.plotly_chart(
                fig_pca,
                use_container_width=True
            )

        else:
            st.info(
                "Chưa có tọa độ PCA hợp lệ."
            )

    else:
        st.info(
            "Dữ liệu chưa có hai cột pc1 và pc2."
        )


# =====================================================
# 12. TỶ TRỌNG CÁC CỤM
# =====================================================

st.subheader("Tỷ trọng sản phẩm theo cụm")

share_df = (
    filtered_df["Tên cụm"]
    .value_counts()
    .reset_index()
)

share_df.columns = [
    "Cụm",
    "Số sản phẩm"
]

fig_donut = px.pie(
    share_df,
    names="Cụm",
    values="Số sản phẩm",
    hole=0.58,
    color="Cụm",
    color_discrete_map=color_map
)

fig_donut.update_traces(
    textinfo="percent+label",
    textposition="outside"
)

style_figure(fig_donut, height=370)

st.plotly_chart(
    fig_donut,
    use_container_width=True
)


# =====================================================
# 13. ĐẶC ĐIỂM CÁC CỤM
# =====================================================

st.subheader("Đặc điểm các cụm sản phẩm")

st.caption(
    "Bảng mô tả đặc điểm các cụm được đọc từ "
    "collection ml_cluster_profile."
)

if not profiles_df.empty:

    profile_view = profiles_df.copy()

    if "cluster" in profile_view.columns:

        profile_view["cluster"] = pd.to_numeric(
            profile_view["cluster"],
            errors="coerce"
        )

        profile_view = profile_view[
            profile_view["cluster"].isin(
                selected_clusters
            )
        ]

    st.dataframe(
        profile_view,
        hide_index=True,
        use_container_width=True
    )

else:
    st.info(
        "Chưa có bảng mô tả đặc điểm các cụm."
    )


# =====================================================
# 14. KẾT QUẢ CHI TIẾT
# =====================================================

st.subheader("Danh sách sản phẩm đã phân cụm")

st.caption(
    f"Đang hiển thị {len(filtered_df):,} sản phẩm "
    "theo bộ lọc đã chọn."
)

preferred_cols = [
    "nguon",
    "ma_san_pham",
    "cluster",
    "cluster_label",
    "pc1",
    "pc2"
]

display_cols = [
    col
    for col in preferred_cols
    if col in filtered_df.columns
]

if display_cols:

    detail_df = filtered_df[
        display_cols
    ].copy()

else:
    detail_df = filtered_df.copy()


rename_map = {
    "nguon": "Nguồn dữ liệu",
    "ma_san_pham": "Mã sản phẩm",
    "cluster": "Mã cụm",
    "cluster_label": "Tên cụm",
    "pc1": "PCA 1",
    "pc2": "PCA 2"
}

detail_df = detail_df.rename(
    columns=rename_map
)

st.dataframe(
    detail_df,
    hide_index=True,
    use_container_width=True,
    height=380
)


# =====================================================
# 15. TẢI DỮ LIỆU
# =====================================================

csv_data = detail_df.to_csv(
    index=False
).encode("utf-8-sig")

st.download_button(
    label="Tải kết quả phân cụm (CSV)",
    data=csv_data,
    file_name="ket_qua_phan_cum_kmeans.csv",
    mime="text/csv",
    use_container_width=False
)


# =====================================================
# 16. GIẢI THÍCH THUẬT TOÁN
# =====================================================

with st.expander(
    "Tìm hiểu về thuật toán K-Means và PCA"
):

    st.markdown("""
    **K-Means Clustering**

    K-Means là thuật toán học không giám sát,
    dùng để phân chia các sản phẩm thành những
    nhóm có đặc điểm tương đồng.

    **Cluster (Cụm)**

    Là nhóm sản phẩm được thuật toán xác định
    dựa trên các đặc trưng đầu vào.

    **PCA (Principal Component Analysis)**

    Là phương pháp giảm chiều dữ liệu, giúp
    trực quan hóa các sản phẩm trên mặt phẳng
    hai chiều thông qua PC1 và PC2.

    **Lưu ý khi diễn giải**

    Vị trí của các điểm trên biểu đồ PCA thể hiện
    cấu trúc dữ liệu sau khi giảm chiều. Hai trục
    PC1 và PC2 không trực tiếp đại diện cho
    giá bán hoặc số lượng bán.
    """)


st.info(
    "Kết quả được đọc từ MongoDB và chỉ dùng "
    "để trực quan hóa, không huấn luyện lại mô hình."
)
