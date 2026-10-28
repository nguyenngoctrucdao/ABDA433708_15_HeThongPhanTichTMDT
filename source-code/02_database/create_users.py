import os, getpass
from datetime import datetime, timezone
from pathlib import Path
import bcrypt
from dotenv import load_dotenv
from pymongo import MongoClient

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")
db = MongoClient(os.getenv("MONGO_URI"), serverSelectionTimeoutMS=10000)[os.getenv("MONGO_DB", "ecommerce_db")]
users = db["users"]
users.create_index("username", unique=True)

# (username, họ tên, quyền)
ACCOUNTS = [
    ("admin", "Quản trị viên", "admin"),
    ("viewer", "Người xem", "viewer"),
]

for username, name, role in ACCOUNTS:
    pw = getpass.getpass(f"Nhập mật khẩu cho '{username}': ")   # không gõ mật khẩu vào code
    pw_hash = bcrypt.hashpw(pw.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    users.update_one(
        {"username": username},
        {"$set": {"name": name, "password_hash": pw_hash, "role": role,
                  "created_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True,
    )
    print("Đã tạo/cập nhật:", username, "-", role)

print("Tổng số tài khoản:", users.count_documents({}))
