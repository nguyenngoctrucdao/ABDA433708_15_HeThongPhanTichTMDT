import streamlit as st
import pandas as pd
import plotly.express as px

from db import load_products
from permissions import require_login

require_login()

st.title("📊 Dashboard thương mại điện tử")

df = load_products()

if df.empty:
    st.warning("Chưa có dữ liệu trong products_cleaned.")
    st.stop()

numeric_cols = [
    "Giá bán", "Giá gốc", "Số tiền giảm giá",
    "Tỷ lệ giảm giá", "Điểm đánh giá trung bình",
    "Số lượt đánh giá", "Số lượng đã bán"
]

for col in numeric_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

source = st.selectbox(
    "Nguồn dữ liệu",
    ["Tất cả"] + sorted(
        df["Nguồn dữ liệu"].dropna().unique().tolist()
    )
)

if source != "Tất cả":
    df = df[df["Nguồn dữ liệu"] == source]

categories = sorted(
    df["Tên danh mục"].dropna().unique().tolist()
)

selected_categories = st.multiselect(
    "Lọc danh mục",
    categories
)

if selected_categories:
    df = df[df["Tên danh mục"].isin(selected_categories)]

c1, c2, c3, c4 = st.columns(4)

c1.metric("Tổng sản phẩm", f"{len(df):,}")
c2.metric("Số danh mục", df["Tên danh mục"].nunique())

avg_price = df["Giá bán"].mean()
c3.metric(
    "Giá bán trung bình",
    f"{avg_price:,.0f} VNĐ" if pd.notna(avg_price) else "N/A"
)

rated = df.loc[
    df["Số lượt đánh giá"] > 0,
    "Điểm đánh giá trung bình"
]
avg_rating = rated.mean()

c4.metric(
    "Điểm đánh giá TB",
    f"{avg_rating:.2f}/5" if pd.notna(avg_rating) else "N/A"
)

st.subheader("Phân bố sản phẩm theo nguồn")
source_counts = (
    df["Nguồn dữ liệu"]
    .value_counts()
    .reset_index()
)
source_counts.columns = ["Nguồn", "Số sản phẩm"]

st.plotly_chart(
    px.bar(
        source_counts,
        x="Nguồn",
        y="Số sản phẩm",
        text="Số sản phẩm"
    ),
    use_container_width=True
)

st.subheader("Top 10 danh mục nhiều sản phẩm")

top_categories = (
    df["Tên danh mục"]
    .value_counts()
    .head(10)
    .reset_index()
)
top_categories.columns = ["Danh mục", "Số sản phẩm"]

st.plotly_chart(
    px.bar(
        top_categories,
        x="Số sản phẩm",
        y="Danh mục",
        orientation="h"
    ),
    use_container_width=True
)

st.subheader("Phân bố giá bán")

price_df = df.dropna(subset=["Giá bán"])

if not price_df.empty:
    st.plotly_chart(
        px.box(
            price_df,
            x="Nguồn dữ liệu",
            y="Giá bán",
            points=False
        ),
        use_container_width=True
    )

st.subheader("Phân bố điểm đánh giá")

rating_df = df[
    (df["Số lượt đánh giá"] > 0)
    & df["Điểm đánh giá trung bình"].notna()
]

if not rating_df.empty:
    st.plotly_chart(
        px.histogram(
            rating_df,
            x="Điểm đánh giá trung bình",
            nbins=20,
            color="Nguồn dữ liệu"
        ),
        use_container_width=True
    )

st.subheader("Top 10 sản phẩm bán chạy")

sold_df = df.dropna(subset=["Số lượng đã bán"])

if not sold_df.empty:
    top_sold = sold_df.nlargest(
        10, "Số lượng đã bán"
    )

    st.dataframe(
        top_sold[
            [
                "Tên sản phẩm",
                "Nguồn dữ liệu",
                "Giá bán",
                "Số lượng đã bán"
            ]
        ],
        hide_index=True,
        use_container_width=True
    )

st.subheader("Dữ liệu chi tiết")
st.dataframe(df, hide_index=True, use_container_width=True)

