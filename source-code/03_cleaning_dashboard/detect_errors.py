from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
FILES = ["tiki_products.csv", "hasaki_products.csv"]
results = []   


def check(name, label, mask):
    n = int(mask.sum())
    results.append((name, label, n))


for fn in FILES:
    df = pd.read_csv(ROOT / "dataset" / fn, dtype={"sku": str})
    cols = set(df.columns)
    print("=" * 70)
    print(fn, "-", df.shape[0], "dòng,", df.shape[1], "cột")

    miss = df.isna().sum()
    miss = miss[miss > 0].to_frame("thiếu")
    miss["%"] = (miss["thiếu"] / len(df) * 100).round(1)
    print("\n[Cột có giá trị thiếu]")
    print(miss.sort_values("thiếu", ascending=False).to_string() if len(miss) else "Không có")

    const = [c for c in df.columns if df[c].nunique(dropna=False) <= 1]
    print("\n[Cột chỉ có 1 giá trị]:", const if const else "Không có")


    check(fn, "Trùng (source + product_id)", df.duplicated(subset=["source", "product_id"], keep=False))
    check(fn, "Trùng toàn bộ dòng", df.duplicated(keep=False))
    if "url" in cols:
        check(fn, "Trùng url", df["url"].duplicated(keep=False) & df["url"].notna())
    if "name" in cols:
        check(fn, "Trùng tên sản phẩm", df["name"].duplicated(keep=False) & df["name"].notna())

    if "name" in cols:
        check(fn, "Tên thiếu hoặc rỗng", df["name"].isna() | (df["name"].astype(str).str.strip() == ""))
        check(fn, "Tên có khoảng trắng thừa đầu/cuối", df["name"].notna() & (df["name"] != df["name"].astype(str).str.strip()))
    if "brand" in cols:
        check(fn, "Brand thiếu", df["brand"].isna())
        b = df["brand"].dropna().astype(str)
        norm = b.str.strip().str.lower()
        variants = b.groupby(norm).nunique()
        bad = variants[variants > 1].index
        check(fn, "Brand viết khác nhau (hoa/thường, khoảng trắng)", norm.reindex(df.index).isin(bad))

    if "price" in cols:
        check(fn, "Giá thiếu hoặc <= 0", df["price"].isna() | (df["price"] <= 0))
    if {"price", "original_price"} <= cols:
        check(fn, "Giá gốc thiếu hoặc <= 0", df["original_price"].isna() | (df["original_price"] <= 0))
        check(fn, "Giá bán > giá gốc", df["price"] > df["original_price"])

    if "discount_rate" in cols:
        check(fn, "discount_rate ngoài 0-100", (df["discount_rate"] < 0) | (df["discount_rate"] > 100))
    if {"price", "original_price", "discount_rate"} <= cols:
        calc = (df["original_price"] - df["price"]) / df["original_price"] * 100
        check(fn, "discount_rate lệch > 3 điểm so với tính từ giá", (calc - df["discount_rate"]).abs() > 3)

    if "rating_average" in cols:
        check(fn, "Rating ngoài 0-5", (df["rating_average"] < 0) | (df["rating_average"] > 5))
    if {"rating_average", "review_count"} <= cols:
        check(fn, "Rating = 0 và review_count = 0 (chưa có đánh giá)", (df["rating_average"] == 0) & (df["review_count"] == 0))
        check(fn, "Rating = 0 nhưng có review", (df["rating_average"] == 0) & (df["review_count"] > 0))
        check(fn, "Có rating nhưng review_count = 0", (df["rating_average"] > 0) & (df["review_count"] == 0))

    for c in ["review_count", "quantity_sold", "order_count", "favourite_count"]:
        if c in cols:
            check(fn, f"{c} < 0", df[c] < 0)
    if "quantity_sold" in cols:
        check(fn, "quantity_sold thiếu", df["quantity_sold"].isna())

    if "price" in cols:
        q1, q3 = df["price"].quantile([0.25, 0.75])
        iqr = q3 - q1
        check(fn, "Giá ngoại lai (IQR x 1.5)", (df["price"] < q1 - 1.5 * iqr) | (df["price"] > q3 + 1.5 * iqr))

    for c in ["order_count_30", "stock_quantity"]:
        if c in cols:
            print(f"\n[{c}] min={df[c].min()}, max={df[c].max()}, trung vị={df[c].median()}  -> cần xác nhận ý nghĩa")

    if "source" in cols:
        print("\n[Giá trị của source]:", df["source"].unique().tolist())
    if "crawled_at" in cols:
        bad_time = pd.to_datetime(df["crawled_at"], errors="coerce", utc=True).isna()
        check(fn, "crawled_at không đọc được", bad_time)

print("\n" + "=" * 70)
print("TỔNG HỢP LỖI")
summary = pd.DataFrame(results, columns=["File", "Kiểm tra", "Số dòng lỗi"])
print(summary[summary["Số dòng lỗi"] > 0].to_string(index=False))
print("\nCác kiểm tra KHÔNG có lỗi:", int((summary["Số dòng lỗi"] == 0).sum()), "/", len(summary))
