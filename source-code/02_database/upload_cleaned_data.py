import os
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv
from pymongo import MongoClient

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

client = MongoClient(
    os.getenv("MONGO_URI"),
    serverSelectionTimeoutMS=10000
)

db = client[os.getenv("MONGO_DB", "ecommerce_db")]
col = db["products_cleaned"]

# File CSV đã làm sạch
CLEAN_FILE = ROOT / "dataset" / "cleaned" / "products_cleaned.csv"

# Đọc dữ liệu
df = pd.read_csv(CLEAN_FILE, dtype={"Mã sản phẩm": str})
n_csv = len(df)

# Đếm dòng trùng theo nguồn dữ liệu và mã sản phẩm
n_trung = df.duplicated(
    subset=["Nguồn dữ liệu", "Mã sản phẩm"]
).sum()

print(f"Số dòng trùng (Nguồn dữ liệu, Mã sản phẩm): {n_trung}")

# NaN -> None để MongoDB lưu thành null
df = df.astype(object).where(df.notna(), None)

# Xóa dữ liệu cũ trong collection rồi nạp lại
col.delete_many({})
col.insert_many(df.to_dict("records"))

# Kiểm tra số bản ghi sau khi upload
n_db = col.count_documents({})

print(
    f"products_cleaned: CSV {n_csv} dòng, MongoDB {n_db} bản ghi,",
    "KHỚP" if n_csv == n_db else "KHÔNG KHỚP"
)

print("Tổng products_cleaned:", col.count_documents({}))

client.close()