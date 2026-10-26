import streamlit as st
import pandas as pd
import plotly.express as px

from db import get_collection
from permissions import require_login

require_login()

st.title("🧩 Phân cụm sản phẩm bằng K-Means")

records = list(
    get_collection("ml_kmeans_results").find(
        {}, {"_id": 0}
    )
)

if not records:
    st.info("Chưa có kết quả K-Means từ TV4.")
    st.stop()

df = pd.DataFrame(records)

st.metric("Số sản phẩm đã phân cụm", len(df))

if "cluster" in df.columns:
    cluster_counts = (
        df["cluster"]
        .value_counts()
        .reset_index()
    )
    cluster_counts.columns = ["Cụm", "Số sản phẩm"]

    st.plotly_chart(
        px.bar(
            cluster_counts,
            x="Cụm",
            y="Số sản phẩm",
            text="Số sản phẩm"
        ),
        use_container_width=True
    )

if {"pc1", "pc2", "cluster"}.issubset(df.columns):
    chart_df = df.copy()
    chart_df["cluster"] = chart_df["cluster"].astype(str)

    st.plotly_chart(
        px.scatter(
            chart_df,
            x="pc1",
            y="pc2",
            color="cluster",
            title="Trực quan hóa phân cụm PCA"
        ),
        use_container_width=True
    )

st.subheader("Đặc điểm các cụm")

profiles = list(
    get_collection("ml_cluster_profile").find(
        {}, {"_id": 0}
    )
)

if profiles:
    st.dataframe(
        pd.DataFrame(profiles),
        hide_index=True,
        use_container_width=True
    )
else:
    st.info("Chưa có bảng mô tả đặc điểm các cụm.")

st.subheader("Kết quả chi tiết")
st.dataframe(df, hide_index=True, use_container_width=True)


