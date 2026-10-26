import streamlit as st
import pandas as pd

from db import get_collection
from permissions import require_login

require_login()

st.title("🤖 Thông tin và đánh giá mô hình")

records = list(
    get_collection("ml_model_metrics").find(
        {}, {"_id": 0}
    )
)

if not records:
    st.info("TV4 chưa lưu chỉ số đánh giá mô hình.")
    st.stop()

df = pd.DataFrame(records)

st.subheader("Bảng chỉ số đánh giá")
st.dataframe(
    df,
    hide_index=True,
    use_container_width=True
)

st.subheader("Ý nghĩa các chỉ số")

st.markdown("""
**K-Means**
- Silhouette Score: đánh giá mức độ phân tách giữa các cụm.
- Inertia: tổng bình phương khoảng cách đến tâm cụm.

**Random Forest Regressor**
- MAE: sai số tuyệt đối trung bình.
- RMSE: căn bậc hai sai số bình phương trung bình.
- R²: mức độ giải thích biến thiên của biến mục tiêu.

**Isolation Forest**
- Anomaly Score: điểm đánh giá mức độ khác biệt.
- Số lượng và tỷ lệ bị gắn cờ: thống kê sản phẩm cần kiểm tra.
""")
