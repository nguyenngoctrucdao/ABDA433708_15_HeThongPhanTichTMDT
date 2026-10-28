import os, json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")
db = MongoClient(os.getenv("MONGO_URI"), serverSelectionTimeoutMS=10000)[os.getenv("MONGO_DB", "ecommerce_db")]

out = ROOT / "backup" / datetime.now().strftime("%Y%m%d_%H%M")
out.mkdir(parents=True, exist_ok=True)

for name in db.list_collection_names():
    docs = list(db[name].find({}, {"_id": 0}))
    with open(out / f"{name}.json", "w", encoding="utf-8") as f:
        json.dump(docs, f, ensure_ascii=False, default=str)
    print(f"{name}: {len(docs)} bản ghi")

print("Đã sao lưu vào:", out)
