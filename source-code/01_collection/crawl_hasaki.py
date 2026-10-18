import json, time, requests
import pandas as pd
from datetime import datetime, timezone
from pathlib import Path

# ===== CẤU HÌNH =====
API_URL = "https://hasaki.vn/mobile/v3/main/products"
HEADERS = {"User-Agent": "Mozilla/5.0"}
DELAY = 1.0       # giây giữa các request, đừng giảm
SIZE = 40
MAX_PAGES = 100    

# cate_path đọc từ thanh địa chỉ Hasaki (dạng ten-danh-muc-c<ID>)
CATEGORIES = [
    "cham-soc-da-mat-c4",
    "cham-soc-co-the-c12"
]

OUT = Path(__file__).resolve().parents[2] / "dataset" / "raw"
OUT.mkdir(parents=True, exist_ok=True)


def pick(p, cate_path, crawled_at):
    brand = p.get("brand")
    rating = p.get("rating") or {}
    return {
        "source": "hasaki",
        "product_id": p.get("id"),
        "sku": p.get("sku"),
        "name": p.get("name"),
        "brand": brand.get("name") if isinstance(brand, dict) else None,
        "price": p.get("price"),
        "original_price": p.get("market_price"),
        "discount_rate": p.get("discount_percent"),
        "rating_average": rating.get("average") if isinstance(rating, dict) else None,
        "review_count": rating.get("total") if isinstance(rating, dict) else None,
        "quantity_sold": p.get("bought_count"),
        "order_count_30": p.get("order_count_30"),     # cần kiểm tra ý nghĩa khi làm sạch
        "stock_quantity": p.get("quantity"),           # có thể là tồn kho, cần xác nhận
        "has_deal": p.get("deal") is not None,
        "has_gift": p.get("gift") is not None,
        "category_id": p.get("category_id"),
        "category_name": cate_path,
        "category_path": p.get("category_name_level"),
        "english_name": p.get("english_name"),
        "url": p.get("product_url"),
        "thumbnail_url": p.get("image"),
        "crawled_at": crawled_at,
    }


def fetch_page(cate_path, page):
    for _ in range(3):
        try:
            r = requests.get(API_URL, headers=HEADERS, timeout=15, params={
                "cate_path": cate_path, "page": page, "size": SIZE,
                "has_meta_data": 1, "is_desktop": 1})
            if r.status_code == 200:
                return r.json()
            print(f"  lỗi {r.status_code} ({cate_path}, trang {page})")
            if r.status_code in (403, 429):   # bị chặn thì dừng, không cố vượt
                return None
        except (requests.RequestException, ValueError) as e:
            print("  lỗi:", e)
        time.sleep(3)
    return None


raw_items, rows, seen = [], [], set()
now = datetime.now(timezone.utc).isoformat()

for cate_path in CATEGORIES:
    count = 0
    for page in range(1, MAX_PAGES + 1):
        data = fetch_page(cate_path, page)
        items = ((data or {}).get("data") or {}).get("products") or []
        if not items:
            break
        for p in items:
            if p.get("id") in seen:   # bỏ trùng giữa các danh mục
                continue
            seen.add(p.get("id"))
            raw_items.append(p)
            rows.append(pick(p, cate_path, now))
            count += 1
        time.sleep(DELAY)
    print(f"{cate_path}: {count} sản phẩm mới (tổng tích lũy {len(rows)})")

    # lưu sau mỗi danh mục để lỗi giữa chừng không mất dữ liệu
    with open(OUT / "hasaki_products_raw.json", "w", encoding="utf-8") as f:
        json.dump(raw_items, f, ensure_ascii=False)
    pd.DataFrame(rows).to_csv(OUT / "hasaki_products.csv", index=False, encoding="utf-8-sig")

print("TỔNG:", len(rows))
if rows:
    print(pd.DataFrame(rows).head())