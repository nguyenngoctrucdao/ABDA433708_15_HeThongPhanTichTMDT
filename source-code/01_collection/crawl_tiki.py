import json, time, requests
import pandas as pd
from datetime import datetime, timezone
from pathlib import Path

# ===== CẤU HÌNH =====
API_URL = "https://tiki.vn/api/personalish/v1/blocks/listings" 
HEADERS = {"User-Agent": "Mozilla/5.0"}
DELAY = 1.0      # giây giữa các request, đừng giảm
MAX_PAGES = 50   

# {category_id: urlKey} lấy từ thanh địa chỉ: tiki.vn/<urlKey>/c<ID>
CATEGORIES = {
    1795: "dien-thoai-smartphone",
    8339: "dinh-duong-cho-be",
    1884: "do-dung-nha-bep",
    4422: "gia-vi-va-che-bien",
    1591: "cham-soc-toc-da-dau",
    8322: "nha-sach-tiki",
    22998: "do-uong"
}

OUT = Path(__file__).resolve().parents[2] / "dataset" / "raw"
OUT.mkdir(parents=True, exist_ok=True)
 

def pick(p, cat_id, url_key, crawled_at):
    qs = p.get("quantity_sold")
    seller = p.get("seller")
    badges = [b.get("code") for b in (p.get("badges_new") or []) if isinstance(b, dict)]
    return {
        "source": "tiki",
        "product_id": p.get("id"),
        "sku": p.get("sku"),
        "name": p.get("name"),
        "brand": p.get("brand_name"),
        "seller_id": p.get("seller_id"),
        "seller_name": seller.get("name") if isinstance(seller, dict) else None,
        "price": p.get("price"),
        "original_price": p.get("original_price"),
        "discount": p.get("discount"),
        "discount_rate": p.get("discount_rate"),
        "rating_average": p.get("rating_average"),
        "review_count": p.get("review_count"),
        "quantity_sold": qs.get("value") if isinstance(qs, dict) else qs,
        "order_count": p.get("order_count"),
        "favourite_count": p.get("favourite_count"),
        "availability": p.get("availability"),
        "inventory_status": p.get("inventory_status"),
        "is_authentic": "authentic_brand" in badges,
        "has_installment": p.get("installment_info") is not None,
        "has_gift": bool(p.get("freegift_items")),
        "category_id": cat_id,
        "category_name": url_key,
        "category_path": p.get("primary_category_path"),
        "url": "https://tiki.vn/" + (p.get("url_path") or ""),
        "thumbnail_url": p.get("thumbnail_url"),
        "crawled_at": crawled_at,
    }


def fetch_page(cat_id, url_key, page):
    for _ in range(3):  # thử lại 3 lần
        try:
            r = requests.get(API_URL, headers=HEADERS, timeout=15, params={
                "limit": 10, "sort": "top_seller", "page": page,
                "urlKey": url_key, "category": cat_id})
            if r.status_code == 200:
                return r.json()
            print(f"  lỗi {r.status_code} ({url_key}, trang {page})")
            if r.status_code in (403, 429):   # bị chặn thì dừng, không cố vượt
                return None
        except requests.RequestException as e:
            print("  lỗi mạng:", e)
        time.sleep(3)
    return None


raw_items, rows, seen = [], [], set()
now = datetime.now(timezone.utc).isoformat()

for cat_id, url_key in CATEGORIES.items():
    count = 0
    for page in range(1, MAX_PAGES + 1):
        data = fetch_page(cat_id, url_key, page)
        items = (data or {}).get("data", [])
        if not items:
            break
        for p in items:
            if p.get("id") in seen:   # bỏ trùng giữa các danh mục
                continue
            seen.add(p.get("id"))
            raw_items.append(p)
            rows.append(pick(p, cat_id, url_key, now))
            count += 1
        if page >= (data.get("paging") or {}).get("last_page", page):
            break
        time.sleep(DELAY)
    print(f"{url_key}: {count} sản phẩm mới (tổng tích lũy {len(rows)})")

    # lưu sau mỗi danh mục để lỗi giữa chừng không mất dữ liệu
    with open(OUT / "tiki_products_raw.json", "w", encoding="utf-8") as f:
        json.dump(raw_items, f, ensure_ascii=False)
    pd.DataFrame(rows).to_csv(OUT / "tiki_products.csv", index=False, encoding="utf-8-sig")

print("TỔNG:", len(rows))
if rows:
    print(pd.DataFrame(rows).head())