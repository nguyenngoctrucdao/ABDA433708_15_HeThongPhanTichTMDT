"""
app.py - điểm vào của web "E-Commerce Analytics" (Streamlit).

Chạy:  streamlit run app.py
Yêu cầu: Streamlit >= 1.46 (dùng st.navigation(position="hidden") và st.container(key=...)).

Bố cục:
  - Chưa đăng nhập: trang đăng nhập dạng "một thẻ hai cột" (panel xanh bên trái, form bên phải).
  - Đã đăng nhập : menu bên trái + các trang trong thư mục pages/.
"""
import base64
import inspect
from html import escape

import streamlit as st

from auth import login, logout, current_user


# =====================================================
# 1. CẤU HÌNH TRANG
# =====================================================

st.set_page_config(
    page_title="E-Commerce Analytics",
    page_icon=":material/dashboard:",
    layout="wide",
    initial_sidebar_state="expanded" if current_user() else "collapsed",
)
if not current_user():
    st.html("""
    <style>
    [data-testid="stSidebar"],
    [data-testid="stSidebarCollapsedControl"],
    [data-testid="collapsedControl"] {
        display: none !important;
    }
    </style>
    """)
# =====================================================
# 2. HÌNH ẢNH (SVG nhúng sẵn, không cần file ngoài)
# =====================================================

def svg_uri(svg: str) -> str:
    """Đổi chuỗi SVG thành data-URI để dùng trong <img> hoặc CSS url()."""
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode("utf-8")).decode("ascii")


def build_chart_svg() -> str:
    """Biểu đồ cột + đường ở cuối panel bên trái."""
    heights = [46, 69, 53, 96, 74, 115, 87, 104, 121]
    bar_w, step, x0, total_h = 28, 46, 14, 150
    width = x0 * 2 + step * (len(heights) - 1) + bar_w

    bars, points = [], []
    for i, h in enumerate(heights):
        x = x0 + i * step
        y = total_h - 6 - h
        fill = "url(#b1)" if i % 2 == 0 else "url(#b2)"
        bars.append(f'<rect x="{x}" y="{y}" width="{bar_w}" height="{h}" rx="4" fill="{fill}"/>')
        points.append(f"{x + bar_w // 2},{y - 12}")

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {total_h}">'
        '<defs>'
        '<linearGradient id="b1" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#3f78e0"/><stop offset="1" stop-color="#2f5fc4"/></linearGradient>'
        '<linearGradient id="b2" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#3bb7ea"/><stop offset="1" stop-color="#2f93cf"/></linearGradient>'
        '</defs>'
        + "".join(bars)
        + f'<polyline points="{" ".join(points)}" fill="none" stroke="#b9f6e3" '
          'stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>'
        '</svg>'
    )


LOGO_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" fill="none" '
    'stroke="#7cc4fa" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M5 28V18M12 28V12M19 28V20M26 28V8"/>'
    '<path d="M4 13l7-6 6 5 11-9"/></svg>'
)

USER_ICON_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" '
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>'
)

LOCK_ICON_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" '
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
    '<rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>'
)


# =====================================================
# 3. CSS TRANG ĐĂNG NHẬP
# =====================================================
# Chỉ được nạp khi chưa đăng nhập, nên không ảnh hưởng các trang khác.
# Muốn đổi chiều cao thẻ: sửa --card-h.

LOGIN_CSS = """
<style>
:root { --card-h: 650px; }

/* ---------- Nền trang & ẩn thanh công cụ ---------- */
.stApp { background: #f4f7fc; }
header[data-testid="stHeader"] { background: transparent; }
[data-testid="stToolbar"], [data-testid="stDecoration"], #MainMenu, footer { display: none !important; }
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"], [data-testid="collapsedControl"] {
    display: none !important;
}
.block-container, [data-testid="stMainBlockContainer"] {
    max-width: 1500px;
    padding-top: 4vh;
    padding-bottom: 2rem;
}

/* ---------- Thẻ chính (bo góc, chứa 2 cột) ---------- */
.st-key-login_card {
    background: #ffffff;
    border: 1px solid #e6ebf3;
    border-radius: 24px;
    overflow: hidden;
    box-shadow: 0 18px 45px rgba(20, 45, 90, 0.10);
    max-width: 1400px;
    width: 96%;
    margin: 0 auto;
    padding: 0;
    gap: 0;
}
.st-key-login_card [data-testid="stHorizontalBlock"] { gap: 0 !important; }

/* ---------- Panel bên trái ---------- */
.st-key-login_left { padding: 55px 65px; }
.login-hero {
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    box-sizing: border-box;
    min-height: var(--card-h);
    padding: 50px 50px 25px 50px;
    background: #152d55;
    color: #ffffff;
}
.hero-brand {
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 24px;
    font-weight: 700;
    color: #ffffff;
}
.hero-brand img { width: 34px; height: 34px; }
.hero-title {
    font-size: 36px;
    line-height: 1.3;
    font-weight: 800;
    color: #ffffff;
    margin: 28px 0 14px 0;
}
.hero-description {
    font-size: 17px;
    line-height: 1.7;
    color: #c9d8f0;
    margin-bottom: 22px;
}
.hero-tags { display: flex; flex-wrap: wrap; gap: 10px; }
.hero-tag {
    display: inline-block;
    padding: 6px 13px;
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.12);
    font-size: 15px;
    font-weight: 700;
    color: #ffffff;
}
.hero-chart { display: block; width: 100%; height: auto; margin-top: 18px; }

/* ---------- Panel bên phải ---------- */
.st-key-login_right {
    padding: 38px 46px;
    min-height: var(--card-h);
    justify-content: center;
    gap: 0.8rem;
    box-sizing: border-box;
}
.login-heading { font-size: 36px; font-weight: 800; color: #142c50; line-height: 1.2; }
.login-subtitle { font-size: 17px; color: #64748b; margin: 4px 0 8px 0; }

/* Bỏ khung mặc định của st.form */
.st-key-login_card [data-testid="stForm"] {
    border: none !important;
    padding: 0 !important;
    background: transparent !important;
}

/* Nhãn ô nhập */
.st-key-login_card [data-testid="stWidgetLabel"] p {
    font-size: 15px;
    font-weight: 600;
    color: #475569;
}

/* Ô nhập */
.st-key-login_card [data-baseweb="input"],
.st-key-login_card [data-baseweb="base-input"] {
    border-radius: 12px !important;
    background: #ffffff !important;
}
.st-key-login_card [data-baseweb="input"] {
    border: 1px solid #dbe3ef !important;
    min-height: 52px;
}
.st-key-login_card [data-baseweb="input"]:focus-within {
    border-color: #2563eb !important;
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.14);
}
.st-key-login_card input {
    height: 50px;
    padding-left: 46px !important;
    font-size: 15px;
    color: #1e293b;
    background-repeat: no-repeat !important;
    background-position: 15px center !important;
    background-size: 20px 20px !important;
}
.st-key-login_card input::placeholder { color: #94a3b8; opacity: 1; }
.st-key-login_user input { background-image: url("__USER_ICON__") !important; }
.st-key-login_pass input { background-image: url("__LOCK_ICON__") !important; }

/* Ẩn dòng "Press Enter to submit form" */
.st-key-login_card [data-testid="InputInstructions"] { display: none; }

/* Nút đăng nhập */
.st-key-login_card [data-testid="stFormSubmitButton"] button {
    height: 48px;
    border: none;
    border-radius: 12px;
    background: #2563eb;
    box-shadow: 0 8px 18px rgba(37, 99, 235, 0.22);
    transition: background 0.2s ease;
}
.st-key-login_card [data-testid="stFormSubmitButton"] button:hover { background: #1d4ed8; }
.st-key-login_card [data-testid="stFormSubmitButton"] button p {
    font-size: 17px;
    font-weight: 700;
    color: #ffffff;
}

.login-footer {
    text-align: center;
    font-size: 11.5px;
    color: #94a3b8;
    margin-top: 6px;
}

/* ---------- Màn hình nhỏ ---------- */
@media (max-width: 640px) {
    .block-container, [data-testid="stMainBlockContainer"] { padding-top: 1rem; }
    .login-hero { min-height: auto; padding: 26px 22px 14px 22px; }
    .hero-title { font-size: 23px; }
    .st-key-login_right { min-height: auto; padding: 26px 22px; }
}
</style>
"""

LOGIN_CSS = (
    LOGIN_CSS
    .replace("__USER_ICON__", svg_uri(USER_ICON_SVG))
    .replace("__LOCK_ICON__", svg_uri(LOCK_ICON_SVG))
)

# Nạp CSS đăng nhập trước khi tạo điều hướng hoặc nội dung trang.
# Tránh việc CSS giao diện sau đăng nhập còn tồn tại khi Streamlit rerun.
if not current_user():
    st.html(LOGIN_CSS)


# =====================================================
# GIAO DIỆN SAU ĐĂNG NHẬP - CHỈ ÁP DỤNG KHI ĐÃ ĐĂNG NHẬP
# =====================================================
HOME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded');
.stApp { background: #f5f7fc; }
header[data-testid="stHeader"] { background: #f5f7fc; }
[data-testid="stMainBlockContainer"] { max-width: 1500px; padding-top: 2.5rem; padding-bottom: 3rem; }
[data-testid="stSidebar"] { background: #152d55; }
[data-testid="stSidebar"] * { color: #e9f1ff; }
[data-testid="stSidebar"] [data-testid="stSidebarNav"] a { border-radius: 10px; margin: 3px 10px; padding: 10px 12px; transition: background .15s; }
[data-testid="stSidebar"] [data-testid="stSidebarNav"] a:hover { background: rgba(255,255,255,.11); }
[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-current="page"] { background: #2563eb; }
[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-current="page"] * { color: #fff; }
[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,.17); }
[data-testid="stSidebar"] button { border-radius: 10px; border: 1px solid rgba(255,255,255,.24); background: rgba(255,255,255,.08); }
[data-testid="stSidebar"] button:hover { background: #2563eb; border-color: #2563eb; }
.home-welcome { border-radius: 22px; background: linear-gradient(112deg,#152d55 0%,#194a89 73%,#2563eb 100%); padding: 37px 42px; color: #fff; box-shadow: 0 14px 30px rgba(21,45,85,.12); margin-bottom: 30px; }
.home-eyebrow { font-size: 12px; letter-spacing: 2px; color: #a8d7ff; font-weight: 700; margin-bottom: 13px; }
.home-welcome-title { font-size: 34px; font-weight: 800; color: white; margin-bottom: 12px; }
.home-welcome-desc { font-size: 15px; line-height: 1.8; color: #dbeafe; max-width: 780px; }
.home-welcome-pill { display: inline-block; margin-top: 19px; padding: 7px 13px; background: rgba(255,255,255,.13); border: 1px solid rgba(255,255,255,.18); border-radius: 30px; font-size: 12px; color: #c7f9e9; }
.home-section-title { font-size: 23px; font-weight: 800; color: #152d55; margin-bottom: 5px; }
.home-section-desc { color: #64748b; font-size: 14px; margin-bottom: 18px; }
div[class*="st-key-feature_"] { background: white; border: 1px solid #e4eaf4; border-radius: 18px; padding: 22px 22px 16px; min-height: 246px; box-shadow: 0 4px 16px rgba(21,45,85,.035); margin-bottom: 12px; transition: box-shadow .2s, transform .2s; }
div[class*="st-key-feature_"]:hover { box-shadow: 0 12px 25px rgba(21,45,85,.10); transform: translateY(-2px); }
.feature-icon { display: flex; align-items: center; justify-content: center; width: 45px; height: 45px; border-radius: 13px; background: #eaf2ff; color: #2563eb; margin-bottom: 15px; }
.material-symbols-rounded { font-family: 'Material Symbols Rounded'; font-size: 26px; font-weight: normal; font-style: normal; line-height: 1; }
.feature-title { color: #152d55; font-size: 17px; font-weight: 750; margin-bottom: 8px; }
.feature-description { color: #64748b; font-size: 13px; line-height: 1.65; min-height: 43px; }
.feature-tag { display: inline-block; background: #eef4ff; color: #3264aa; font-size: 11px; font-weight: 650; border-radius: 30px; padding: 5px 10px; margin-top: 11px; }
div[class*="st-key-feature_"] [data-testid="stPageLink"] a { color: #2563eb; font-weight: 650; font-size: 13px; }
.home-footnote { text-align: center; color: #94a3b8; font-size: 12px; padding-top: 20px; }
@media(max-width: 900px) { .home-welcome { padding: 28px 24px; } .home-welcome-title { font-size: 27px; } }
</style>
"""


# =====================================================
# 4. HÀM TIỆN ÍCH
# =====================================================

def compact_html(html: str) -> str:
    """Bỏ thụt đầu dòng và dòng trống để Markdown không hiểu nhầm HTML là code."""
    lines = (line.strip() for line in html.splitlines())
    return "\n".join(line for line in lines if line)


def render_html(html: str) -> None:
    st.markdown(compact_html(html), unsafe_allow_html=True)


def stretch(func) -> dict:
    """Nút rộng hết khung, chạy được cả Streamlit cũ (use_container_width) lẫn mới (width='stretch')."""
    try:
        if "width" in inspect.signature(func).parameters:
            return {"width": "stretch"}
    except (TypeError, ValueError):
        pass
    return {"use_container_width": True}


def hero_html() -> str:
    return f"""
    <div class="login-hero">
        <div>
            <div class="hero-brand">
                <img src="{svg_uri(LOGO_SVG)}" alt="">
                <span>E-Commerce Analytics</span>
            </div>
            <div class="hero-title">Hệ thống phân tích dữ liệu thương mại điện tử</div>
            <div class="hero-description">
                Nền tảng phân tích sản phẩm từ Tiki và Hasaki, tích hợp trực quan hóa dữ liệu
                và Machine Learning.
            </div>
            <div class="hero-tags">
                <span class="hero-tag">MongoDB</span>
                <span class="hero-tag">Machine Learning</span>
                <span class="hero-tag">Dashboard</span>
            </div>
        </div>
        <img class="hero-chart" src="{svg_uri(build_chart_svg())}" alt="">
    </div>
    """


HEADING_HTML = """
<div class="login-heading">Chào mừng trở lại!</div>
<div class="login-subtitle">Đăng nhập để truy cập hệ thống</div>
"""

FOOTER_HTML = """
<div class="login-footer">Hệ thống phân tích thương mại điện tử • 2026</div>
"""


# =====================================================
# 5. TRANG CHỦ / ĐĂNG NHẬP
# =====================================================

def trang_chu():
    user = current_user()

    # ---------- CHƯA ĐĂNG NHẬP ----------
    if not user:
        # CSS đăng nhập đã được nạp trước phần điều hướng.

        with st.container(key="login_card"):
            left, right = st.columns([1.1, 1], gap="small", vertical_alignment="center")

            # Cột trái: giới thiệu hệ thống
            with left:
                with st.container(key="login_left"):
                    render_html(hero_html())

            # Cột phải: form đăng nhập
            with right:
                with st.container(key="login_right"):
                    render_html(HEADING_HTML)

                    with st.form("login_form"):
                        username = st.text_input(
                            "Tên đăng nhập",
                            placeholder="Nhập tên đăng nhập",
                            key="login_user",
                        )
                        password = st.text_input(
                            "Mật khẩu",
                            type="password",
                            placeholder="Nhập mật khẩu",
                            key="login_pass",
                        )
                        submitted = st.form_submit_button(
                            "Đăng nhập →",
                            type="primary",
                            **stretch(st.form_submit_button),
                        )

                    if submitted:
                        if not username.strip():
                            st.warning("Vui lòng nhập tên đăng nhập.")
                        elif not password:
                            st.warning("Vui lòng nhập mật khẩu.")
                        else:
                            try:
                                success, message = login(username.strip(), password)
                            except Exception as exc:
                                st.error(
                                    "Không thể xác thực lúc này. "
                                    "Vui lòng kiểm tra kết nối MongoDB."
                                )
                                with st.expander("Chi tiết kỹ thuật"):
                                    st.code(f"{type(exc).__name__}: {exc}")
                            else:
                                if success:
                                    st.rerun()
                                else:
                                    st.error(message)

                    render_html(FOOTER_HTML)
        return

    # ---------- ĐÃ ĐĂNG NHẬP: TRANG CHỦ MỚI ----------

    st.html(f"""
    <div class="home-welcome">
      <div class="home-eyebrow">E-COMMERCE ANALYTICS / OVERVIEW</div>
      <div class="home-welcome-title">Tổng quan hệ thống</div>
      <div class="home-welcome-desc">
        Chào mừng bạn đến với nền tảng phân tích dữ liệu thương mại điện tử!
        Khám phá dữ liệu sản phẩm Tiki &amp; Hasaki, trực quan hóa kết quả và ứng dụng Machine Learning trên cùng một hệ thống.
      </div>
      <div class="home-welcome-pill">● Hệ thống sẵn sàng</div>
    </div>
    """)

    st.html('<div class="home-section-title">Khám phá chức năng</div><div class="home-section-desc">Chọn một công cụ để bắt đầu phân tích dữ liệu.</div>')

    features = [
        ("pages/1_Dashboard.py", "dashboard", "Dashboard", "Trực quan hóa số liệu, giá bán và đánh giá sản phẩm.", "Biểu đồ & KPI"),
        ("pages/2_Phan_cum.py", "hub", "Phân cụm sản phẩm", "Khám phá các nhóm sản phẩm bằng mô hình K-Means.", "K-Means"),
        ("pages/3_Du_doan_diem_danh_gia.py", "query_stats", "Dự đoán đánh giá", "Phân tích kết quả dự đoán điểm đánh giá sản phẩm.", "Random Forest"),
        ("pages/4_Phat_hien_bat_thuong.py", "monitoring", "Phát hiện bất thường", "Nhận diện các sản phẩm có đặc điểm khác biệt.", "Isolation Forest"),
        ("pages/5_Quan_ly_du_lieu.py", "database", "Quản lý dữ liệu", "Xem và quản lý thông tin sản phẩm theo quyền truy cập.", "MongoDB"),
        ("pages/6_Bao_cao.py", "description", "Báo cáo", "Tổng hợp và xuất kết quả phân tích phục vụ báo cáo.", "Xuất dữ liệu"),
        ("pages/7_Thong_tin_mo_hinh.py", "model_training", "Thông tin mô hình", "Theo dõi các chỉ số và thông tin của mô hình ML.", "Model metrics"),
    ]

    for i in range(0, len(features), 3):
        cols = st.columns(3, gap="medium")
        for col, (path, ico, title, description, tag) in zip(cols, features[i:i+3]):
            with col:
                with st.container(key=f"feature_{i}_{ico}"):
                    st.html(f"""<div class="feature-icon"><span class="material-symbols-rounded">{ico}</span></div>
                    <div class="feature-title">{title}</div>
                    <div class="feature-description">{description}</div>
                    <div class="feature-tag">{tag}</div>""")
                    st.page_link(path, label="Mở chức năng", icon=":material/arrow_forward:", use_container_width=True)

    st.html("""
    <div class="home-footnote">
        E-Commerce Analytics · Tiki &amp; Hasaki · Big Data Project
    </div>

    <div style="
        text-align: right;
        font-size: 11px;
        color: #94a3b8;
        text-decoration: underline;
        margin-top: 5px;
        padding-right: 5px;
    ">
        Developer by: Team 15-Big Data
    </div>
    """)

# =====================================================
# 6. ĐIỀU HƯỚNG
# =====================================================

user = current_user()

if user:
    pages = [
        st.Page(trang_chu, title="Trang chủ", icon=":material/home:", default=True),
        st.Page("pages/1_Dashboard.py", title="Dashboard", icon=":material/dashboard:"),
        st.Page("pages/2_Phan_cum.py", title="Phân cụm", icon=":material/hub:"),
        st.Page("pages/3_Du_doan_diem_danh_gia.py", title="Dự đoán điểm đánh giá", icon=":material/query_stats:"),
        st.Page("pages/4_Phat_hien_bat_thuong.py", title="Phát hiện bất thường", icon=":material/monitoring:"),
        st.Page("pages/5_Quan_ly_du_lieu.py", title="Quản lý dữ liệu", icon=":material/database:"),
        st.Page("pages/6_Bao_cao.py", title="Báo cáo", icon=":material/description:"),
        st.Page("pages/7_Thong_tin_mo_hinh.py", title="Thông tin mô hình", icon=":material/model_training:"),
    ]
else:
    pages = [st.Page(trang_chu, title="Đăng nhập", icon=":material/lock:", default=True)]
# Áp dụng giao diện trước khi khởi tạo điều hướng
if user:
    st.html(HOME_CSS)

# Ẩn menu mặc định để chủ động đặt tài khoản phía trên Trang chủ.
nav = st.navigation(pages, position="hidden")


# =====================================================
# 7. SIDEBAR SAU KHI ĐĂNG NHẬP
# =====================================================

if user:
    # Ưu tiên username; nếu hệ thống chỉ lưu name thì dùng name.
    username = escape(str(user.get("username") or user.get("name") or "admin"))
    role_key = str(user.get("role", "")).lower()
    role_label = "Quản trị viên" if role_key == "admin" else "Người dùng"

    with st.sidebar:
        st.html("""
        <style>
        .sidebar-account {
            display:flex; align-items:center; gap:12px;
            padding:14px 12px; margin:10px 0 16px;
            background:rgba(255,255,255,.075);
            border:1px solid rgba(191,219,254,.18);
            border-radius:14px;
        }
        .sidebar-avatar {
            width:46px; height:46px; flex-shrink:0; border-radius:50%;
            background:linear-gradient(135deg,#2563eb,#38bdf8);
            display:flex; align-items:center; justify-content:center;
        }
        .sidebar-account-name {font-size:16px;font-weight:800;color:#fff;}
        .sidebar-account-role {font-size:12px;color:#bfdbfe;margin-top:3px;}
        [data-testid="stSidebar"] [data-testid="stPageLink"] a {
            border-radius:10px; padding:9px 12px; margin:2px 0;
        }
        [data-testid="stSidebar"] [data-testid="stPageLink"] a:hover {
            background:rgba(255,255,255,.12);
        }
        </style>
        """)
        st.markdown("### ◈ E-Commerce Analytics")
        st.caption("DATA INTELLIGENCE PLATFORM")
        st.divider()
        st.html(f"""
        <div class="sidebar-account">
          <div class="sidebar-avatar">
            <span class="material-symbols-rounded"
                style="font-size:30px; color:#FFFFFF;">
                person
            </span>
          </div>
          <div>
            <div class="sidebar-account-name">{username}</div>
            <div class="sidebar-account-role">{role_label}</div>
          </div>
        </div>
        """)

        # Menu đặt sau avatar; st.navigation vẫn quản lý định tuyến.
        for page in pages:
            st.page_link(page, label=page.title, icon=page.icon, use_container_width=True)

        st.divider()
        if st.button("Đăng xuất", icon=":material/logout:", **stretch(st.button)):
            logout()
            st.rerun()


# =====================================================
# 8. CHẠY TRANG
# =====================================================

nav.run()