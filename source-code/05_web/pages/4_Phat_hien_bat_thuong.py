import streamlit as st
import pandas as pd
import plotly.express as px

from db import get_collection
from permissions import require_login

require_login()

st.title("🚨 Phát hiện sản phẩm bất thường")

records = list(
    get_collection("ml_anomalies").find(
        {}, {"_id": 0}
    )
)

if not records:
    st.info("Chưa có kết quả Isolation Forest từ TV4.")
    st.stop()

df = pd.DataFrame(records)

if "is_anomaly" not in df.columns:
    st.error("Thiếu trường is_anomaly.")
    st.stop()

# Quy ước: True hoặc -1 là bất thường.
def is_outlier(value):
    if isinstance(value, bool):
        return value
    return str(value).lower() in {
        "-1", "true", "1", "anomaly"
    }

df["Bất thường"] = df["is_anomaly"].apply(is_outlier)

total = len(df)
anomalies = int(df["Bất thường"].sum())

c1, c2, c3 = st.columns(3)
c1.metric("Tổng sản phẩm kiểm tra", total)
c2.metric("Sản phẩm bị gắn cờ", anomalies)
c3.metric(
    "Tỷ lệ bị gắn cờ",
    f"{anomalies / total * 100:.2f}%" if total else "N/A"
)

summary = pd.DataFrame({
    "Loại": ["Bình thường", "Bất thường"],
    "Số lượng": [total - anomalies, anomalies]
})

st.plotly_chart(
    px.pie(
        summary,
        names="Loại",
        values="Số lượng",
        title="Phân bố kết quả phát hiện bất thường"
    ),
    use_container_width=True
)

st.subheader("Các sản phẩm cần kiểm tra")

outliers = df[df["Bất thường"]]

if outliers.empty:
    st.success("Không có sản phẩm bị gắn cờ.")
else:
    st.dataframe(
        outliers,
        hide_index=True,
        use_container_width=True
    )

st.caption(
    "Isolation Forest phát hiện những điểm dữ liệu khác biệt. "
    "Sản phẩm bị gắn cờ không nhất thiết là dữ liệu sai."
)

