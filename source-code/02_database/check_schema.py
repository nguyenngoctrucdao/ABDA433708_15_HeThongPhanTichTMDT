import os
from collections import Counter
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")
col = MongoClient(os.getenv("MONGO_URI"), serverSelectionTimeoutMS=10000)[
    os.getenv("MONGO_DB", "ecommerce_db")]["products_raw"]

COMMON = ["source", "product_id", "sku", "name", "brand", "price", "original_price",
          "discount_rate", "rating_average", "review_count", "quantity_sold", "has_gift",
          "category_id", "category_name", "category_path", "url", "thumbnail_url", "crawled_at"]
TIKI = ["seller_id", "seller_name", "discount", "order_count", "favourite_count",
        "availability", "inventory_status", "is_authentic", "has_installment"]
HASAKI = ["order_count_30", "stock_quantity", "has_deal", "english_name"]
EXPECT = {"tiki": COMMON + TIKI, "hasaki": COMMON + HASAKI}

def num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)

for source, expected in EXPECT.items():
    docs = list(col.find({"source": source}, {"_id": 0}))
    print("\n=====", source, "-", len(docs), "documents")
    fields = set()
    for d in docs:
        fields |= set(d.keys())
    print("Có trong schema nhưng thiếu trên Mongo:", sorted(set(expected) - fields))
    print("Có trên Mongo nhưng không có trong schema:", sorted(fields - set(expected)))

    print("\nCột: kiểu dữ liệu thực tế (số document)")
    for f in expected:
        kinds = Counter(type(d.get(f)).__name__ for d in docs)
        print(f"  {f}: {dict(kinds)}")

    print("\nKiểm tra ràng buộc (số document vi phạm)")
    print("  price < 0:", sum(1 for d in docs if num(d.get("price")) and d["price"] < 0))
    print("  price = 0 (bất thường):", sum(1 for d in docs if d.get("price") == 0))
    print("  rating_average ngoài [0,5]:",
          sum(1 for d in docs if num(d.get("rating_average")) and not 0 <= d["rating_average"] <= 5))
    print("  discount_rate ngoài [0,100]:",
          sum(1 for d in docs if num(d.get("discount_rate")) and not 0 <= d["discount_rate"] <= 100))
    print("  review_count < 0:", sum(1 for d in docs if num(d.get("review_count")) and d["review_count"] < 0))
    print("  original_price < price:",
          sum(1 for d in docs if num(d.get("original_price")) and num(d.get("price"))
              and d["original_price"] < d["price"]))
    print("  source không đúng:", sum(1 for d in docs if d.get("source") != source))