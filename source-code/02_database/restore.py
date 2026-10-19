import os, sys, json
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")
db = MongoClient(os.getenv("MONGO_URI"), serverSelectionTimeoutMS=10000)[os.getenv("DB_NAME", "ecommerce_db")]

# Dùng: python restore.py [tên_thư_mục_backup]; không truyền thì lấy bản mới nhất
backups = sorted(p for p in (ROOT / "backup").iterdir() if p.is_dir())
folder = (ROOT / "backup" / sys.argv[1]) if len(sys.argv) > 1 else backups[-1]
print("Phục hồi từ:", folder)

if input("Thao tác sẽ GHI ĐÈ dữ liệu hiện tại. Gõ 'yes' để tiếp tục: ") != "yes":
    sys.exit("Đã hủy.")

for file in folder.glob("*.json"):
    name = file.stem
    docs = json.loads(file.read_text(encoding="utf-8"))
    db[name].delete_many({})
    if docs:
        db[name].insert_many(docs)
    print(f"{name}: đã phục hồi {len(docs)} bản ghi")
