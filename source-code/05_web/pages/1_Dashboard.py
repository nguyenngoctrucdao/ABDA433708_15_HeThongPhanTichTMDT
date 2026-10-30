import streamlit as st
import pandas as pd
import plotly.express as px

from db import load_products
from permissions import require_login

require_login()

NAVY = "#172F57"
BLUE = "#2563EB"
CYAN = "#20A4D8"
PALETTE = {"tiki": BLUE, "hasaki": CYAN}

st.html("""
<style>
/* Scoped to this page's rendered content; does not modify app.py */
[data-testid="stMainBlockContainer"] {max-width: 1540px; padding-top: 2.0rem; padding-bottom: 3rem;}
[data-testid="stAppViewContainer"] {background-color: #f4f7fc;}
/* Tiêu đề chính đồng bộ với các trang ML */
.dash-header {background:linear-gradient(110deg,#152D55,#2457A6);padding:32px 38px;border-radius:18px;margin-bottom:28px;box-shadow:0 10px 25px rgba(21,45,85,.12);}
.dash-eyebrow {color:#BFDBFE;font-size:13px;font-weight:700;letter-spacing:1.2px;margin-bottom:12px;}
.dash-title {color:#FFFFFF !important;font-size:clamp(26px,2.5vw,34px);font-weight:800;line-height:1.3;margin:0 0 12px 0;}
.dash-subtitle {color:#DBEAFE;font-size:15px;line-height:1.7;margin:0;}
/* Tiêu đề khu vực: nền xanh nhạt + thanh nhấn */
.dash-section, .dash-filter-title {background:#E1ECFF;border-left:5px solid #2563EB;border-radius:8px;padding:14px 18px;color:#12376B;font-size:22px;font-weight:800;line-height:1.4;margin:22px 0 16px;}
/* Tiêu đề biểu đồ: xanh dương + đường gạch chân */
.dash-chart-title {color:#1D4ED8;font-size:17px;font-weight:750;border-bottom:2px solid #BFDBFE;padding:0 0 9px;margin:5px 0 14px;}
@media(max-width:768px){.dash-header{padding:24px}.dash-title{font-size:26px}.dash-section,.dash-filter-title{font-size:19px}}
[data-testid="stMetric"] {background: #fff; border: 1px solid #e3eaf5; border-radius: 16px; padding: 18px 20px; box-shadow: 0 5px 18px rgba(22,47,87,.045); min-height: 118px;}
[data-testid="stMetricLabel"] {color: #66758e; font-weight: 600;}
[data-testid="stMetricValue"] {color: #172F57; font-weight: 780; font-size: clamp(1.35rem, 2vw, 2rem);}
[data-testid="stPlotlyChart"] {background: #fff; border: 1px solid #e3eaf5; border-radius: 16px; padding: 12px; box-shadow: 0 5px 18px rgba(22,47,87,.045);}
[data-testid="stDataFrame"] {border-radius: 12px; overflow: hidden;}
[data-baseweb="select"] > div {border-radius: 10px; border-color: #dbe4f1;}
</style>
""")

st.html("""
<div class="dash-header">
  <div class="dash-eyebrow">E-COMMERCE ANALYTICS / DASHBOARD</div>
  <div class="dash-title">Tổng quan dữ liệu thương mại điện tử</div>
  <div class="dash-subtitle">Theo dõi danh mục, giá bán, đánh giá và mức độ tiêu thụ của sản phẩm trên Tiki &amp; Hasaki.</div>
</div>
""")

with st.spinner("Đang tải dữ liệu Dashboard..."):
    raw_df = load_products()

if raw_df.empty:
    st.warning("Chưa có dữ liệu trong products_cleaned.")
    st.stop()
    
df = raw_df.copy()
required_cols = ["Nguồn dữ liệu", "Tên danh mục", "Tên sản phẩm", "Giá bán", "Điểm đánh giá trung bình", "Số lượt đánh giá", "Số lượng đã bán"]
missing = [col for col in required_cols if col not in df.columns]
if missing:
    st.error("Dữ liệu đang thiếu các cột cần thiết: " + ", ".join(missing))
    st.stop()

numeric_cols = [
    "Giá bán", "Giá gốc", "Số tiền giảm giá", "Tỷ lệ giảm giá",
    "Điểm đánh giá trung bình", "Số lượt đánh giá", "Số lượng đã bán"
]
for col in numeric_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

st.html('<div class="dash-filter-title">Bộ lọc dữ liệu</div>')
filter_a, filter_b = st.columns([1, 2], gap="medium")
with filter_a:
    sources = sorted(df["Nguồn dữ liệu"].dropna().astype(str).unique().tolist())
    source = st.selectbox("Nguồn dữ liệu", ["Tất cả"] + sources)
if source != "Tất cả":
    df = df[df["Nguồn dữ liệu"] == source]

with filter_b:
    categories = sorted(df["Tên danh mục"].dropna().astype(str).unique().tolist())
    selected_categories = st.multiselect(
        "Danh mục sản phẩm", categories,
        placeholder="Chọn danh mục",  # Thay cho Choose options
    )
if selected_categories:
    df = df[df["Tên danh mục"].isin(selected_categories)]

st.caption(f"Đang hiển thị **{len(df):,}** sản phẩm theo bộ lọc đã chọn.")

rated = df.loc[
    (df["Số lượt đánh giá"] > 0) & df["Điểm đánh giá trung bình"].notna(),
    "Điểm đánh giá trung bình"
]
avg_price = df["Giá bán"].mean()
avg_rating = rated.mean()

k1, k2, k3, k4 = st.columns(4, gap="medium")
with k1:
    st.metric("Tổng sản phẩm", f"{len(df):,}")
with k2:
    st.metric("Số danh mục", f"{df['Tên danh mục'].nunique():,}")
with k3:
    st.metric("Giá bán trung bình", f"{avg_price:,.0f} ₫" if pd.notna(avg_price) else "N/A")
with k4:
    st.metric("Điểm đánh giá TB", f"{avg_rating:.2f}/5" if pd.notna(avg_rating) else "N/A")


def style_chart(fig, height=350, horizontal=False):
    fig.update_layout(
        template="plotly_white", height=height,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Arial", color="#43526a", size=12),
        margin=dict(l=12, r=12, t=25, b=22),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        hoverlabel=dict(bgcolor="#ffffff"),
    )
    if horizontal:
        fig.update_xaxes(gridcolor="#edf1f7", zeroline=False)
        fig.update_yaxes(showgrid=False)
    else:
        fig.update_xaxes(showgrid=False)
        fig.update_yaxes(gridcolor="#edf1f7", zeroline=False)
    return fig


def section(title, caption=None):
    st.html(f'<div class="dash-section">{title}</div>')
    if caption:
        st.caption(caption)


section("01  |  Cơ cấu sản phẩm", "Số lượng sản phẩm theo nguồn và theo danh mục trong dữ liệu đã thu thập.")
left_chart, right_chart = st.columns(2, gap="medium")
with left_chart:
    st.html('<div class="dash-chart-title">Phân bố sản phẩm theo nguồn</div>')
    source_counts = df["Nguồn dữ liệu"].value_counts().rename_axis("Nguồn").reset_index(name="Số sản phẩm")
    if not source_counts.empty:
        fig = px.bar(source_counts, x="Nguồn", y="Số sản phẩm", text="Số sản phẩm", color="Nguồn", color_discrete_map=PALETTE)
        fig.update_traces(textposition="outside", cliponaxis=False, marker_line_width=0)
        fig.update_layout(showlegend=False)
        st.plotly_chart(style_chart(fig), use_container_width=True)
    else:
        st.info("Không có dữ liệu nguồn để hiển thị.")

with right_chart:
    st.html('<div class="dash-chart-title">Top 10 danh mục nhiều sản phẩm</div>')
    top_categories = df["Tên danh mục"].value_counts().head(10).rename_axis("Danh mục").reset_index(name="Số sản phẩm")
    if not top_categories.empty:
        top_categories = top_categories.sort_values("Số sản phẩm")
        fig = px.bar(top_categories, x="Số sản phẩm", y="Danh mục", orientation="h", text="Số sản phẩm")
        fig.update_traces(marker_color=BLUE, textposition="outside", cliponaxis=False)
        fig.update_layout(yaxis_title=None, xaxis_title=None)
        st.plotly_chart(style_chart(fig, height=350, horizontal=True), use_container_width=True)
    else:
        st.info("Không có dữ liệu danh mục để hiển thị.")

section("02  |  Giá bán và đánh giá", "Phân bố giá bán và điểm đánh giá của sản phẩm có lượt đánh giá thực tế.")
price_col, rating_col = st.columns(2, gap="medium")
with price_col:
    st.html('<div class="dash-chart-title">Phân bố giá bán theo nguồn</div>')
    price_df = df.dropna(subset=["Giá bán"])
    if not price_df.empty:
        fig = px.box(price_df, x="Nguồn dữ liệu", y="Giá bán", color="Nguồn dữ liệu", points=False, color_discrete_map=PALETTE)
        fig.update_layout(showlegend=False, xaxis_title=None, yaxis_title="Giá bán (VNĐ)")
        st.plotly_chart(style_chart(fig), use_container_width=True)
    else:
        st.info("Không có dữ liệu giá bán hợp lệ.")
with rating_col:
    st.html('<div class="dash-chart-title">Phân bố điểm đánh giá</div>')
    rating_df = df[(df["Số lượt đánh giá"] > 0) & df["Điểm đánh giá trung bình"].notna()]
    if not rating_df.empty:
        fig = px.histogram(rating_df, x="Điểm đánh giá trung bình", nbins=20, color="Nguồn dữ liệu", barmode="group", color_discrete_map=PALETTE)
        fig.update_layout(xaxis_title="Điểm đánh giá", yaxis_title="Số sản phẩm")
        st.plotly_chart(style_chart(fig), use_container_width=True)
    else:
        st.info("Không có sản phẩm có lượt đánh giá để hiển thị.")

section("03  |  Sản phẩm bán chạy", "Chỉ xếp hạng những sản phẩm có số lượng đã bán được ghi nhận; dữ liệu trống không được thay bằng 0.")
sold_df = df.dropna(subset=["Số lượng đã bán"])
if not sold_df.empty:
    top_sold = sold_df.nlargest(10, "Số lượng đã bán")
    st.dataframe(
        top_sold[["Tên sản phẩm", "Nguồn dữ liệu", "Giá bán", "Số lượng đã bán"]],
        hide_index=True, use_container_width=True,
        column_config={
            "Tên sản phẩm": st.column_config.TextColumn("Tên sản phẩm", width="large"),
            "Nguồn dữ liệu": st.column_config.TextColumn("Nguồn"),
            "Giá bán": st.column_config.NumberColumn("Giá bán (VNĐ)", format="%,.0f"),
            "Số lượng đã bán": st.column_config.NumberColumn("Đã bán", format="%,.0f"),
        }
    )
else:
    st.info("Không có số lượng đã bán hợp lệ.")

with st.expander("Xem dữ liệu chi tiết", expanded=False):
    st.caption("Dữ liệu được lấy từ collection products_cleaned, áp dụng các bộ lọc phía trên.")
    st.dataframe(df, hide_index=True, use_container_width=True)
