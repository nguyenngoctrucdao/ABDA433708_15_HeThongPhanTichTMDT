import streamlit as st

from auth import login, logout, current_user

st.set_page_config(
    page_title="E-commerce Analytics",
    page_icon="📊",
    layout="wide"
)

user = current_user()

if not user:
    st.title("Hệ thống phân tích thương mại điện tử")
    st.write("Đăng nhập để tiếp tục.")

    with st.form("login_form"):
        username = st.text_input("Tên đăng nhập")
        password = st.text_input(
            "Mật khẩu",
            type="password"
        )
        submitted = st.form_submit_button("Đăng nhập")

    if submitted:
        try:
            success, message = login(username, password)

            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)

        except Exception:
            st.error("Không thể xác thực lúc này. Vui lòng thử lại.")

    st.stop()


def trang_chu():
    st.title("Tổng quan hệ thống")
    st.write("Chọn một trang ở thanh điều hướng bên trái.")


pages = [
    st.Page(trang_chu, title="Trang chủ", icon="🏠", default=True),
    st.Page("pages/1_Dashboard.py", title="Dashboard", icon="📊"),
    st.Page("pages/2_Phan_cum.py", title="Phân cụm", icon="🧩"),
    st.Page("pages/3_Du_doan_diem_danh_gia.py", title="Dự đoán điểm đánh giá", icon="🔮"),
    st.Page("pages/4_Phat_hien_bat_thuong.py", title="Phát hiện bất thường", icon="🚨"),
    st.Page("pages/5_Quan_ly_du_lieu.py", title="Quản lý dữ liệu", icon="🗂️"),
    st.Page("pages/6_Bao_cao.py", title="Báo cáo", icon="📄"),
    st.Page("pages/7_Thong_tin_mo_hinh.py", title="Thông tin mô hình", icon="🤖"),
]

nav = st.navigation(pages)

st.sidebar.write(f"Xin chào, {user['name']}")
st.sidebar.write(f"Quyền: {user['role']}")

if st.sidebar.button("Đăng xuất"):
    logout()
    st.rerun()

nav.run()