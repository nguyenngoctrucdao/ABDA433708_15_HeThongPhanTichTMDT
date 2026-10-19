# Mô tả cấu trúc dữ liệu

**Database:** `ecommerce_db` (MongoDB Atlas). Tài liệu này là chuẩn chung của cả nhóm: ai cần thêm hoặc đổi cột thì báo TV2 cập nhật tại đây.

## 0. Quy ước chung

- Tên cột: chữ thường, không dấu, nối bằng `_`.
- `source` chỉ nhận `tiki` hoặc `hasaki`.
- Giá: số nguyên, đơn vị VND (không có dấu chấm, không có chữ "đ").
- Đúng/sai: `True` / `False`.
- `crawled_at`: chuỗi thời gian ISO 8601, múi giờ UTC.
- Khóa định danh một sản phẩm: cặp (`source`, `product_id`).

## 1. Các collection

| Collection | Nội dung | Người ghi | Ghi chú |
|---|---|---|---|
| `products_raw` | Dữ liệu thô Tiki + Hasaki, giữ nguyên như file CSV | TV2 | 6.945 bản ghi (Tiki 3.074, Hasaki 3.871), không xóa cột nào |
| `products_clean` | Dữ liệu sau làm sạch | TV3 | Xem mục 5 |
| `users` | Tài khoản đăng nhập web | TV2 tạo, TV5 dùng | Xem mục 6 |

Hai sàn dùng chung một collection vì phần lớn cột giống nhau; MongoDB không bắt mọi document phải có cùng trường nên cột riêng của từng sàn vẫn lưu được (sàn không có cột nào thì document của sàn đó không có trường ấy; ô có cột nhưng trống thì lưu null).

## 2. Cột chung của hai sàn (`products_raw`)

| Cột | Kiểu | Ý nghĩa | Ràng buộc / lưu ý |
|---|---|---|---|
| `source` | chuỗi | Nguồn dữ liệu | `tiki` hoặc `hasaki` |
| `product_id` | số nguyên | Mã sản phẩm của sàn | Không trùng trong cùng `source` |
| `sku` | chuỗi | Mã kho | Đọc CSV bằng `dtype={"sku": str}` để không mất chữ số. Ít giá trị phân tích |
| `name` | chuỗi | Tên sản phẩm | Bắt buộc |
| `brand` | chuỗi | Thương hiệu | Có thể trống (Tiki thiếu 496 dòng); cần chuẩn hóa hoa/thường |
| `price` | số nguyên | Giá bán hiện tại (VND) | >= 0; giá 0 là bất thường |
| `original_price` | số | Giá gốc / giá thị trường (VND) | >= `price` thông thường. Tiki: số nguyên, đủ dữ liệu. Hasaki: số thực, thiếu 154 dòng (`null`) |
| `discount_rate` | số nguyên | % giảm giá | 0 đến 100 |
| `rating_average` | số thực | Điểm đánh giá trung bình | 0 đến 5. Tiki: 0 thường nghĩa là chưa có đánh giá |
| `review_count` | số nguyên | Số lượt đánh giá | >= 0 |
| `quantity_sold` | số | Số lượng đã bán | Tiki: số thực, thiếu 510 dòng (`null`, thường là sản phẩm mới). Hasaki: số nguyên, đủ dữ liệu |
| `has_gift` | đúng/sai | Có quà tặng kèm | |
| `category_id` | số nguyên | Mã danh mục | Khác nghĩa giữa hai sàn, xem mục 4 |
| `category_name` | chuỗi | Tên danh mục dùng khi crawl | Tiki: `urlKey`; Hasaki: `cate_path` |
| `category_path` | chuỗi | Đường dẫn danh mục | Khác định dạng giữa hai sàn, xem mục 4 |
| `url` | chuỗi | Link sản phẩm | |
| `thumbnail_url` | chuỗi | Link ảnh sản phẩm | |
| `crawled_at` | chuỗi thời gian | Thời điểm thu thập | |

## 3. Cột riêng từng sàn

### Chỉ có ở Tiki

| Cột | Kiểu | Ý nghĩa | Lưu ý |
|---|---|---|---|
| `seller_id` | số nguyên | Mã người bán | |
| `seller_name` | chuỗi | Tên người bán | Rỗng 100% (thiếu 3.074/3.074 dòng), cần TV1 kiểm tra script crawl |
| `discount` | số nguyên | Số tiền giảm (VND) | = `original_price` - `price` |
| `order_count` | số nguyên | Số đơn | Thường bằng 0 (cần xác nhận) |
| `favourite_count` | số nguyên | Số lượt yêu thích | Thường bằng 0 (cần xác nhận) |
| `availability` | số nguyên | Trạng thái còn hàng | |
| `inventory_status` | chuỗi | Trạng thái tồn kho | Rỗng 100% (thiếu 3.074/3.074 dòng), cần TV1 kiểm tra script crawl |
| `is_authentic` | đúng/sai | Có huy hiệu hàng chính hãng | Suy ra từ `badges_new` |
| `has_installment` | đúng/sai | Có hỗ trợ trả góp | Suy ra từ `installment_info` |

### Chỉ có ở Hasaki

| Cột | Kiểu | Ý nghĩa | Lưu ý |
|---|---|---|---|
| `order_count_30` | số nguyên | Chưa rõ nghĩa | Giá trị rất lớn (hàng trăm triệu), có thể là doanh thu 30 ngày. Cần xác nhận trước khi dùng |
| `stock_quantity` | số nguyên | Có thể là tồn kho | Cần xác nhận |
| `has_deal` | đúng/sai | Đang có deal | |
| `english_name` | chuỗi | Tên tiếng Anh | Ít dùng. Thiếu 120 dòng |

## 4. Điểm khác nhau cần xử lý khi làm sạch (TV3)

| Cột | Tiki | Hasaki |
|---|---|---|
| `category_id` | ID danh mục dùng khi crawl (ví dụ 1795) | ID danh mục con của sản phẩm |
| `category_name` | `urlKey`, ví dụ `dien-thoai-smartphone` | `cate_path`, ví dụ `cham-soc-da-mat-c4` |
| `category_path` | Chuỗi ID, ví dụ `1/2/1789/1795` | Chuỗi tên, ví dụ `Chăm Sóc Da Mặt / Làm Sạch Da / Sữa Rửa Mặt` |
| `rating_average` | 0 khi chưa có đánh giá | Thường có giá trị |

Vì vậy không so sánh trực tiếp các cột danh mục giữa hai sàn; cần tạo cột nhóm ngành chung ở `products_clean` (ví dụ `category_group`).

## 5. Cột của `products_clean`

*TV3 điền sau khi làm sạch xong.* Cần ghi: cột giữ, cột bỏ, cột mới tạo (tên, kiểu, ý nghĩa).

| Cột | Kiểu | Ý nghĩa | Nguồn |
|---|---|---|---|
| (điền sau) | | | |

## 6. Collection `users`

| Cột | Kiểu | Ý nghĩa | Lưu ý |
|---|---|---|---|
| `username` | chuỗi | Tên đăng nhập | Không trùng |
| `name` | chuỗi | Tên hiển thị của tài khoản | Ví dụ: "Quan tri vien", "Nguoi xem" |
| `password_hash` | chuỗi | Mật khẩu đã mã hóa | Tuyệt đối không lưu mật khẩu thô |
| `role` | chuỗi | Quyền | `admin` hoặc `viewer` |
| `created_at` | chuỗi thời gian | Ngày tạo | |

## 7. Ràng buộc và quy tắc nghiệp vụ

- Không có hai bản ghi cùng (`source`, `product_id`).
- `price` >= 0; `rating_average` trong [0, 5]; `discount_rate` trong [0, 100].
- `discount_rate` ≈ (`original_price` - `price`) / `original_price` x 100.
- Dữ liệu thô (`products_raw`) không được sửa; mọi chỉnh sửa thực hiện ở `products_clean`.
- **Kết quả kiểm tra trên `products_raw` (6.945 document, nạp ngày 19/10/2026):** 0 bản ghi trùng (`source`, `product_id`); 0 vi phạm `price` >= 0, `rating_average` trong [0, 5], `discount_rate` trong [0, 100], `review_count` >= 0; không có sản phẩm giá 0; `original_price` >= `price` ở mọi dòng có `original_price` (Hasaki có 154 dòng không có giá gốc nên không so sánh được). Tên cột trên MongoDB khớp hoàn toàn với mục 2 và 3. Chưa kiểm tra công thức `discount_rate` và `discount`.


## 8. Index (TV2 tạo)

   *Trạng thái: đã tạo (4 index, gồm `_id_` mặc định).*

- (`source`, `product_id`) duy nhất
- `category_name`
- `brand`

## 9. Quan hệ

- Một sản phẩm thuộc đúng một sàn (`source`) và một danh mục (`category_name`).
- Một thương hiệu (`brand`) có nhiều sản phẩm.

## 10. Sao lưu và phục hồi

   - `backup.py`: xuất mọi collection ra file JSON trong thư mục `backup/<ngày_giờ>/` (không xuất trường `_id`).
   - `restore.py`: xóa dữ liệu hiện tại của từng collection rồi nạp lại từ bản sao lưu (mặc định lấy bản mới nhất; cần gõ `yes` để xác nhận).
   - Thư mục `backup/` nằm trong `.gitignore`, bản cần chia sẻ để trên Drive.