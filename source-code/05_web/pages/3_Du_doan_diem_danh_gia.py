import streamlit as st
import pandas as pd
import plotly.express as px

from db import get_collection
from permissions import require_login

require_login()

st.title("🔮 Dự đoán điểm đánh giá sản phẩm")

records = list(
    get_collection("ml_rating_predictions").find(
        {}, {"_id": 0}
    )
)

if not records:
    st.info("Chưa có kết quả dự đoán từ TV4.")
    st.stop()

df = pd.DataFrame(records)

st.metric("Số bản ghi dự đoán", len(df))

required = {"rating_thuc", "rating_du_doan"}

if required.issubset(df.columns):
    df["rating_thuc"] = pd.to_numeric(
        df["rating_thuc"], errors="coerce"
    )
    df["rating_du_doan"] = pd.to_numeric(
        df["rating_du_doan"], errors="coerce"
    )

    valid = df.dropna(subset=list(required)).copy()

    if not valid.empty:
        valid["Sai số tuyệt đối"] = (
            valid["rating_thuc"]
            - valid["rating_du_doan"]
        ).abs()

        st.metric(
            "MAE trên các bản ghi hiển thị",
            f"{valid['Sai số tuyệt đối'].mean():.3f}"
        )

        st.plotly_chart(
            px.scatter(
                valid,
                x="rating_thuc",
                y="rating_du_doan",
                title="Điểm thực tế và điểm dự đoán",
                labels={
                    "rating_thuc": "Điểm thực tế",
                    "rating_du_doan": "Điểm dự đoán"
                }
            ),
            use_container_width=True
        )

        st.caption(
            "MAE trên đây được tính từ các bản ghi lưu trong "
            "MongoDB, không mặc định là MAE của tập kiểm tra."
        )

st.subheader("Bảng kết quả dự đoán")
st.dataframe(df, hide_index=True, use_container_width=True)


