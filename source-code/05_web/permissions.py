from auth import current_user


def require_login():
    user = current_user()

    if not user:
        raise PermissionError("Vui lòng đăng nhập.")

    return user


def require_role(*allowed_roles):
    user = require_login()

    if user["role"] not in allowed_roles:
        raise PermissionError("Bạn không có quyền thực hiện thao tác này.")

    return user


