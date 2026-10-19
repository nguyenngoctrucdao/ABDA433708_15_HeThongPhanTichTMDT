import os
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv
from pymongo import MongoClient

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

client = MongoClient(os.getenv("MONGO_URI"), serverSelectionTimeoutMS=10000)
db = client[os.getenv("DB_NAME", "ecommerce_db")]
col = db["products_raw"]

FILES = [("tiki_products.csv", "tiki"), ("hasaki_products.csv", "hasaki")]

for filename, source in FILES:
    df = pd.read_csv(ROOT / "dataset" / filename, dtype={"sku": str})
    n_csv = len(df)

    # Đếm dòng trùng (source, product_id), phải làm trước khi đổi kiểu dữ liệu
    n_trung = df.duplicated(subset=["source", "product_id"]).sum()
    print(f"{source}: dòng trùng (source, product_id): {n_trung}")

    # NaN -> None để MongoDB lưu thành null
    df = df.astype(object).where(df.notna(), None)

    # Xóa dữ liệu cũ của sàn này, chạy lại không bị nạp trùng
    col.delete_many({"source": source})
    col.insert_many(df.to_dict("records"))

    n_db = col.count_documents({"source": source})
    print(f"{source}: CSV {n_csv} dòng, MongoDB {n_db} bản ghi,",
          "KHỚP" if n_csv == n_db else "KHÔNG KHỚP")

print("Tổng products_raw:", col.count_documents({}))