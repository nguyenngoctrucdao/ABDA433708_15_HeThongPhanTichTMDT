import bcrypt
import streamlit as st

from db import get_collection


def login(username, password):
    username = username.strip()

    if not username or not password:
        return False, "Vui lòng nhập đầy đủ thông tin."

    user = get_collection("users").find_one(
        {"username": username}
    )

    if not user:
        return False, "Tên đăng nhập hoặc mật khẩu không đúng."

    stored_hash = user.get("password_hash")

    if not stored_hash:
        return False, "Tài khoản chưa được cấu hình mật khẩu."

    try:
        valid = bcrypt.checkpw(
            password.encode("utf-8"),
            stored_hash.encode("utf-8")
        )
    except (ValueError, TypeError):
        return False, "Thông tin xác thực không hợp lệ."

    if not valid:
        return False, "Tên đăng nhập hoặc mật khẩu không đúng."

    if user.get("role") not in {"admin", "viewer", "analyst"}:
        return False, "Tài khoản chưa được cấp quyền hợp lệ."

    st.session_state["user"] = {
        "username": user["username"],
        "name": user.get("name", user["username"]),
        "role": user["role"],
    }

    return True, "Đăng nhập thành công."


def logout():
    st.session_state.pop("user", None)


def current_user():
    return st.session_state.get("user")
