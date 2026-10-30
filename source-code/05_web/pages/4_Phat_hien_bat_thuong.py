
import streamlit as st
import pandas as pd
import plotly.express as px

from db import get_collection
from permissions import require_login


# =====================================================
# 1. KIỂM TRA ĐĂNG NHẬP
# =====================================================

require_login()

NAVY = "#152D55"
BLUE = "#2563EB"
CYAN = "#0891B2"
ORANGE = "#F59E0B"
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
    background: #FFFFFF;
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
    background: #FFFFFF;
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
    background: #FFFFFF;
    border-radius: 12px;
    border: 1px solid #E2E8F0;
}

/* Tiêu đề các phần chính: nền xanh nhạt, viền nhấn xanh */
.anomaly-section-title {
    background: #E1ECFF;
    border-left: 5px solid #2563EB;
    border-radius: 8px;
    padding: 13px 18px;
    margin: 24px 0 16px;
    color: #12376B;
    font-size: 23px;
    font-weight: 800;
    line-height: 1.4;
    box-shadow: 0 2px 8px rgba(37,99,235,0.07);
}
/* Tiêu đề biểu đồ: xanh dương đậm và gạch chân */
.anomaly-chart-title {
    color: #1D4ED8;
    font-size: 19px;
    font-weight: 750;
    border-bottom: 2px solid #BFDBFE;
    padding-bottom: 9px;
    margin: 12px 0 18px;
}
</style>
""")


# =====================================================
# 3. HEADER
# =====================================================

# Dùng st.html để tránh lỗi hiện nguyên HTML
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
        Phát hiện sản phẩm bất thường
    </div>

    <div style="
        color: #DBEAFE;
        font-size: 15px;
        line-height: 1.7;
    ">
        Phân tích các sản phẩm có đặc điểm khác biệt
        bằng thuật toán Isolation Forest,
        hỗ trợ phát hiện những trường hợp cần kiểm tra.
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
def load_anomalies():
    records = list(
        get_collection("ml_anomalies").find(
            {},
            {"_id": 0}
        )
    )
    return pd.DataFrame(records)


try:
    df = load_anomalies()

except Exception:
    st.error(
        "Không thể đọc dữ liệu từ collection ml_anomalies. "
        "Vui lòng kiểm tra kết nối MongoDB."
    )
    st.stop()


if df.empty:
    st.warning(
        "Collection ml_anomalies chưa có kết quả."
    )
    st.stop()


if "is_anomaly" not in df.columns:
    st.error(
        "Dữ liệu thiếu trường is_anomaly."
    )
    st.stop()


# =====================================================
# 5. CHUẨN HÓA DỮ LIỆU
# =====================================================

df = df.copy()


def is_outlier(value):
    """
    Quy ước:
    True, -1, 1, 'true', 'anomaly'
    được xem là bất thường.
    """
    if isinstance(value, bool):
        return value

    if pd.isna(value):
        return False

    return str(value).strip().lower() in {
        "-1",
        "1",
        "true",
        "anomaly"
    }


df["Bất thường"] = df["is_anomaly"].apply(
    is_outlier
)

df["Trạng thái"] = df["Bất thường"].map({
    True: "Cần kiểm tra",
    False: "Bình thường"
})

if "anomaly_score" in df.columns:
    df["anomaly_score"] = pd.to_numeric(
        df["anomaly_score"],
        errors="coerce"
    )


# =====================================================
# 6. BỘ LỌC
# =====================================================

st.html('<div class="anomaly-section-title">Bộ lọc kết quả phân tích</div>')

f1, f2, f3 = st.columns(
    [1, 1, 1.4],
    gap="medium"
)

with f1:
    selected_status = st.selectbox(
        "Trạng thái sản phẩm",
        [
            "Tất cả",
            "Cần kiểm tra",
            "Bình thường"
        ]
    )

with f2:
    if "nguon" in df.columns:
        sources = sorted(
            df["nguon"]
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

with f3:
    search_keyword = st.text_input(
        "Tìm mã sản phẩm",
        placeholder="Nhập mã sản phẩm..."
    )


filtered = df.copy()

if selected_status != "Tất cả":
    filtered = filtered[
        filtered["Trạng thái"] == selected_status
    ]

if (
    selected_source != "Tất cả"
    and "nguon" in filtered.columns
):
    filtered = filtered[
        filtered["nguon"] == selected_source
    ]

if search_keyword.strip():
    id_col = (
        "ma_san_pham"
        if "ma_san_pham" in filtered.columns
        else "Mã sản phẩm"
        if "Mã sản phẩm" in filtered.columns
        else None
    )

    if id_col:
        filtered = filtered[
            filtered[id_col]
            .astype(str)
            .str.contains(
                search_keyword.strip(),
                case=False,
                regex=False,
                na=False
            )
        ]


if filtered.empty:
    st.info(
        "Không có sản phẩm phù hợp với bộ lọc."
    )
    st.stop()


# =====================================================
# 7. THẺ KPI
# =====================================================

total = len(filtered)
anomalies = int(
    filtered["Bất thường"].sum()
)
normal = total - anomalies

rate = (
    anomalies / total * 100
    if total > 0
    else 0
)

k1, k2, k3, k4 = st.columns(4)

with k1:
    st.metric(
        "Sản phẩm đã kiểm tra",
        f"{total:,}"
    )

with k2:
    st.metric(
        "Sản phẩm cần kiểm tra",
        f"{anomalies:,}"
    )

with k3:
    st.metric(
        "Sản phẩm bình thường",
        f"{normal:,}"
    )

with k4:
    st.metric(
        "Tỷ lệ bị gắn cờ",
        f"{rate:.2f}%"
    )

st.caption(
    "Các KPI phản ánh tập dữ liệu sau khi lọc. "
    "Tỷ lệ bị gắn cờ không phải tỷ lệ dữ liệu sai."
)


# =====================================================
# 8. CẤU HÌNH BIỂU ĐỒ
# =====================================================

def style_figure(fig, height=400):
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
            t=35,
            b=25
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
# 9. BIỂU ĐỒ PHÂN BỐ TRẠNG THÁI
# =====================================================

st.write("")
st.html('<div class="anomaly-section-title">Trực quan hóa kết quả phát hiện</div>')

c1, c2 = st.columns(
    2,
    gap="large"
)

with c1:
    st.html('<div class="anomaly-chart-title">Phân bố trạng thái sản phẩm</div>')

    summary = pd.DataFrame({
        "Trạng thái": [
            "Bình thường",
            "Cần kiểm tra"
        ],
        "Số sản phẩm": [
            normal,
            anomalies
        ]
    })

    fig_pie = px.pie(
        summary,
        names="Trạng thái",
        values="Số sản phẩm",
        hole=0.58,
        color="Trạng thái",
        color_discrete_map={
            "Bình thường": BLUE,
            "Cần kiểm tra": ORANGE
        }
    )

    fig_pie.update_traces(
        textinfo="percent+label",
        textposition="outside"
    )

    style_figure(fig_pie)

    st.plotly_chart(
        fig_pie,
        use_container_width=True
    )


# =====================================================
# 10. PHÂN BỐ ĐIỂM BẤT THƯỜNG
# =====================================================

with c2:
    st.html('<div class="anomaly-chart-title">Phân bố điểm bất thường</div>')

    if "anomaly_score" in filtered.columns:

        score_df = filtered.dropna(
            subset=["anomaly_score"]
        )

        if not score_df.empty:

            fig_hist = px.histogram(
                score_df,
                x="anomaly_score",
                color="Trạng thái",
                nbins=35,
                color_discrete_map={
                    "Bình thường": BLUE,
                    "Cần kiểm tra": ORANGE
                },
                labels={
                    "anomaly_score": "Điểm bất thường"
                },
                barmode="overlay",
                opacity=0.75
            )

            style_figure(fig_hist)

            st.plotly_chart(
                fig_hist,
                use_container_width=True
            )

        else:
            st.info(
                "Chưa có điểm bất thường hợp lệ."
            )

    else:
        st.info(
            "Dữ liệu chưa có trường anomaly_score."
        )


# =====================================================
# 11. THỐNG KÊ THEO NGUỒN
# =====================================================

if "nguon" in filtered.columns:

    st.html('<div class="anomaly-section-title">Kết quả phát hiện theo nguồn dữ liệu</div>')

    source_summary = (
        filtered.groupby(
            ["nguon", "Trạng thái"]
        )
        .size()
        .reset_index(name="Số sản phẩm")
    )

    fig_source = px.bar(
        source_summary,
        x="nguon",
        y="Số sản phẩm",
        color="Trạng thái",
        barmode="group",
        text="Số sản phẩm",
        color_discrete_map={
            "Bình thường": BLUE,
            "Cần kiểm tra": ORANGE
        },
        labels={
            "nguon": "Nguồn dữ liệu"
        }
    )

    fig_source.update_traces(
        textposition="outside"
    )

    style_figure(fig_source, height=370)

    st.plotly_chart(
        fig_source,
        use_container_width=True
    )


# =====================================================
# 12. DANH SÁCH SẢN PHẨM CẦN KIỂM TRA
# =====================================================

st.html('<div class="anomaly-section-title">Danh sách sản phẩm cần kiểm tra</div>')

outliers = filtered[
    filtered["Bất thường"]
].copy()

if outliers.empty:
    st.info(
        "Không có sản phẩm bị gắn cờ "
        "trong bộ lọc hiện tại."
    )

else:
    if "anomaly_score" in outliers.columns:
        # Điểm lớn hơn tương ứng mức khác biệt cao hơn
        # theo quy ước score đã dùng ở TV4.
        outliers = outliers.sort_values(
            "anomaly_score",
            ascending=False,
            na_position="last"
        )

    preferred_cols = [
        "nguon",
        "ma_san_pham",
        "anomaly_score",
        "ly_do",
        "Trạng thái"
    ]

    display_cols = [
        col
        for col in preferred_cols
        if col in outliers.columns
    ]

    outlier_view = outliers[
        display_cols
    ].copy()

    outlier_view = outlier_view.rename(
        columns={
            "nguon": "Nguồn dữ liệu",
            "ma_san_pham": "Mã sản phẩm",
            "anomaly_score": "Điểm bất thường",
            "ly_do": "Lý do gắn cờ"
        }
    )

    st.dataframe(
        outlier_view,
        hide_index=True,
        use_container_width=True,
        height=400
    )

    csv_data = outlier_view.to_csv(
        index=False
    ).encode("utf-8-sig")

    st.download_button(
        "Tải danh sách cần kiểm tra (CSV)",
        data=csv_data,
        file_name="san_pham_can_kiem_tra.csv",
        mime="text/csv"
    )


# =====================================================
# 13. BẢNG KẾT QUẢ ĐẦY ĐỦ
# =====================================================

with st.expander(
    "Xem toàn bộ kết quả phát hiện"
):

    st.dataframe(
        filtered,
        hide_index=True,
        use_container_width=True,
        height=400
    )


# =====================================================
# 14. GIẢI THÍCH THUẬT TOÁN
# =====================================================

with st.expander(
    "Tìm hiểu về Isolation Forest"
):

    st.markdown("""
    **Isolation Forest là gì?**

    Isolation Forest là thuật toán phát hiện
    bất thường bằng cách xác định những
    điểm dữ liệu dễ bị cô lập trong tập dữ liệu.

    **Anomaly Score**

    Là điểm dùng để phản ánh mức độ khác biệt
    của một bản ghi theo quy ước của mô hình.

    Trong kết quả TV4, điểm lớn hơn được hiểu
    là mức độ bất thường cao hơn nếu sử dụng
    công thức `-score_samples()`.

    **is_anomaly**

    Trường đánh dấu kết quả phát hiện:
    - `True`: sản phẩm bị gắn cờ.
    - `False`: sản phẩm không bị gắn cờ.

    **Lưu ý quan trọng**

    Một sản phẩm bị gắn cờ không nhất thiết
    là sản phẩm có dữ liệu sai. Đó có thể
    là sản phẩm có giá, mức giảm giá hoặc
    các đặc điểm khác biệt so với phần lớn
    sản phẩm trong tập dữ liệu.
    """)