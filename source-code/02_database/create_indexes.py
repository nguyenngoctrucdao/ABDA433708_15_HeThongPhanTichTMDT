import os
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")
db = MongoClient(os.getenv("MONGO_URI"), serverSelectionTimeoutMS=10000)[os.getenv("MONGO_DB", "ecommerce_db")]
col = db["products_raw"]

# Kiểm tra trùng (source, product_id) trước khi tạo index unique
dups = list(col.aggregate([
    {"$group": {"_id": {"source": "$source", "product_id": "$product_id"}, "n": {"$sum": 1}}},
    {"$match": {"n": {"$gt": 1}}},
    {"$limit": 5},
]))
if dups:
    print("CÓ SẢN PHẨM TRÙNG, ví dụ:", dups)
    print("Không tạo index unique. Báo TV3 xử lý trùng, hoặc tạo index thường.")
    col.create_index([("source", 1), ("product_id", 1)])
else:
    col.create_index([("source", 1), ("product_id", 1)], unique=True)
    print("Đã tạo index unique (source, product_id)")

col.create_index("category_name")
col.create_index("brand")

print("Các index hiện có:")
for name, info in col.index_information().items():
    print(" -", name, info["key"])
