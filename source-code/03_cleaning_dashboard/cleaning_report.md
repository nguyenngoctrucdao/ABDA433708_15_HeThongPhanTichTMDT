# Kiểm tra dữ liệu trước khi làm sạch
tiki_products.csv - 3074 dòng, 27 cột

[Cột có giá trị thiếu]
                  thiếu      %
seller_name        3074  100.0
inventory_status   3074  100.0
quantity_sold       510   16.6
brand               496   16.1

[Cột chỉ có 1 giá trị]: ['source', 'seller_name', 'order_count', 'favourite_count', 'availability', 'inventory_status', 'has_installment', 'has_gift', 'crawled_at']

[Giá trị của source]: ['tiki']
======================================================================
hasaki_products.csv - 3871 dòng, 22 cột

[Cột có giá trị thiếu]
                thiếu    %
original_price    154  4.0
english_name      120  3.1

[Cột chỉ có 1 giá trị]: ['source', 'crawled_at']

[order_count_30] min=0, max=515290000, trung vị=272000.0  -> cần xác nhận ý nghĩa

[stock_quantity] min=0, max=663709, trung vị=840.0  -> cần xác nhận ý nghĩa

[Giá trị của source]: ['hasaki']

======================================================================
TỔNG HỢP LỖI
               File                                          Kiểm tra  Số dòng lỗi
  tiki_products.csv                                Trùng tên sản phẩm           48
  tiki_products.csv                 Tên có khoảng trắng thừa đầu/cuối           77
  tiki_products.csv                                       Brand thiếu          496
  tiki_products.csv Rating = 0 và review_count = 0 (chưa có đánh giá)         1130
  tiki_products.csv                        Rating = 0 nhưng có review            1
  tiki_products.csv                               quantity_sold thiếu          510
  tiki_products.csv                         Giá ngoại lai (IQR x 1.5)          330
hasaki_products.csv                                Trùng tên sản phẩm            4
hasaki_products.csv                 Tên có khoảng trắng thừa đầu/cuối          126
hasaki_products.csv                           Giá gốc thiếu hoặc <= 0          154
hasaki_products.csv Rating = 0 và review_count = 0 (chưa có đánh giá)         1885
hasaki_products.csv                         Giá ngoại lai (IQR x 1.5)          209

Các kiểm tra KHÔNG có lỗi: 34 / 46



# BÁO CÁO LÀM SẠCH VÀ KIỂM TRA CHẤT LƯỢNG DỮ LIỆU

## 1. Tổng quan dữ liệu

Dữ liệu được thu thập từ hai nguồn thương mại điện tử là Tiki và Hasaki. Sau quá trình làm sạch riêng từng nguồn, hai bộ dữ liệu được ghép theo chiều dọc để tạo thành bộ dữ liệu chung phục vụ cho việc phân tích, trực quan hóa dữ liệu, xây dựng website và huấn luyện các mô hình học máy.

**File dữ liệu đầu ra:** `products_merged.csv`

**Vị trí lưu trữ:** `dataset/cleaned/`

### 1.1. Quy mô dữ liệu

| Tiêu chí | Kết quả |
|---|---:|
| Tổng số sản phẩm | 6.945 |
| Số cột | 17 |
| Sản phẩm từ Tiki | 3.074 |
| Sản phẩm từ Hasaki | 3.871 |

Tỷ trọng dữ liệu theo nguồn:

- Tiki: khoảng 44,29%.
- Hasaki: khoảng 55,71%.

Bộ dữ liệu sau khi ghép gồm 6.945 dòng và 17 cột, với các thông tin về sản phẩm, thương hiệu, giá bán, giá gốc, giảm giá, đánh giá, số lượng đã bán, danh mục, đường dẫn và thời gian thu thập.

## 2. Cấu trúc dữ liệu sau khi ghép

Bộ dữ liệu hiện có 17 cột:

1. `Nguồn dữ liệu`
2. `Mã sản phẩm`
3. `Tên sản phẩm`
4. `Thương hiệu`
5. `Giá bán`
6. `Giá gốc`
7. `Số tiền giảm giá`
8. `Tỷ lệ giảm giá`
9. `Điểm đánh giá trung bình`
10. `Số lượt đánh giá`
11. `Số lượng đã bán`
12. `Mã danh mục`
13. `Tên danh mục`
14. `Đường dẫn danh mục`
15. `Đường dẫn sản phẩm`
16. `Đường dẫn ảnh sản phẩm`
17. `Thời gian thu thập`

Số cột thực tế là 17, thay vì 19 cột như cấu trúc chuẩn dự kiến ban đầu. Hai cột chưa xuất hiện trong kết quả là `Mã người bán` và `Xác thực chính hãng`.

Cần đối chiếu lại cấu trúc của hai file nguồn để xác định nguyên nhân hai cột này không có trong file ghép và thống nhất schema cuối cùng với các thành viên phụ trách mô hình học máy và website.

## 3. Kiểm tra giá trị thiếu

Theo kết quả kiểm tra chất lượng dữ liệu, hai cột có giá trị thiếu đáng chú ý là:

| Cột dữ liệu | Số giá trị thiếu | Tỷ lệ trên tổng dữ liệu |
|---|---:|---:|
| Số lượng đã bán | 510 | 7,34% |
| Giá gốc | 154 | 2,22% |
| Số tiền giảm giá | 154 | 2,22% |

Các cột còn lại được hiển thị trong phần kết quả kiểm tra đều có 0 giá trị thiếu. Tuy nhiên, cần kiểm tra đầy đủ báo cáo đầu ra để xác nhận tình trạng của toàn bộ 17 cột.

### 3.1. Số lượng đã bán

Có 510 sản phẩm bị thiếu thông tin số lượng đã bán. Các giá trị thiếu này chủ yếu xuất phát từ dữ liệu Tiki theo kết quả kiểm tra trước đó.

Do chưa đủ căn cứ để xác định các sản phẩm này thực sự chưa bán được hàng hay nguồn dữ liệu không cung cấp thông tin, các giá trị thiếu được giữ nguyên, không tự động thay thế bằng 0 và không xóa các dòng tương ứng.

### 3.2. Giá gốc và số tiền giảm giá

Có 154 giá trị thiếu ở mỗi cột `Giá gốc` và `Số tiền giảm giá`. Các giá trị này được giữ nguyên nếu không có đủ thông tin để xác định chính xác.

Trong trường hợp có đủ giá bán và giá gốc, số tiền giảm giá có thể được tính theo công thức:

**Số tiền giảm giá = Giá gốc − Giá bán**

Công thức chỉ được áp dụng khi hai mức giá hợp lệ và giá gốc lớn hơn hoặc bằng giá bán. Không tự suy đoán giá gốc cho các sản phẩm chưa có thông tin.

## 4. Xử lý dữ liệu thương hiệu

Đối với các sản phẩm không có thông tin thương hiệu, giá trị thiếu được thay thế bằng nhãn `Chưa xác định` trong cột `Thương hiệu` theo bước xử lý đã thực hiện trên dữ liệu Tiki.

Việc thay thế này giúp phân biệt các sản phẩm chưa có thông tin thương hiệu với những sản phẩm có thương hiệu xác định. Tên danh mục, chẳng hạn “Nhà sách Tiki”, vẫn được lưu trong cột `Tên danh mục`, không được sử dụng thay cho thương hiệu.

Cần kiểm tra riêng file Hasaki để xác nhận việc xử lý thương hiệu đã được thực hiện hay chưa.

## 5. Ghép dữ liệu từ hai nguồn

Hai bộ dữ liệu Tiki và Hasaki được ghép theo chiều dọc bằng `pandas.concat`, sau đó đánh lại chỉ số dòng.

Kết quả thu được:

- 3.074 sản phẩm từ Tiki.
- 3.871 sản phẩm từ Hasaki.
- Tổng cộng 6.945 sản phẩm.
- 17 cột dữ liệu.

Cột `Nguồn dữ liệu` được sử dụng để phân biệt các bản ghi đến từ Tiki và Hasaki.

Phương pháp ghép này giữ lại các bản ghi từ cả hai nguồn. Các sản phẩm trùng tên không mặc nhiên bị xóa vì có thể là những sản phẩm hoặc biến thể khác nhau.

## 6. Kiểm tra chất lượng dữ liệu

Các nội dung đã được kiểm tra theo kết quả đầu ra hiện có:

- Tổng số dòng và số cột sau khi ghép.
- Phân bố số sản phẩm theo nguồn dữ liệu.
- Số lượng giá trị thiếu theo từng cột.
- Kiểu dữ liệu của các cột.
- Một số dòng dữ liệu đầu tiên để kiểm tra cấu trúc.

Các nội dung cần tiếp tục xác nhận trước khi bàn giao:

- Kiểm tra mã sản phẩm có bị trùng trong cùng một nguồn hay không.
- Kiểm tra các cột giá có đúng kiểu số và có giá trị bất hợp lý hay không.
- Kiểm tra kiểu dữ liệu ngày giờ của cột `Thời gian thu thập`.
- Xác nhận schema cuối cùng và lý do thiếu hai cột so với cấu trúc 19 cột dự kiến.
- Kiểm tra đầy đủ các cột trong báo cáo giá trị thiếu và kiểu dữ liệu, vì kết quả hiển thị hiện tại đã bị rút gọn.

Các phép kiểm tra trên cần được hoàn tất trước khi kết luận bộ dữ liệu đã đạt yêu cầu chất lượng cuối cùng.

## 7. Khả năng sử dụng cho các bước tiếp theo

Sau khi hoàn tất các kiểm tra còn lại, bộ dữ liệu có thể được sử dụng làm đầu vào cho các công việc tiếp theo của dự án:

- **Phân tích và trực quan hóa dữ liệu:** phân tích giá bán, mức giảm giá, điểm đánh giá, số lượt đánh giá và sự khác biệt giữa hai nguồn.
- **K-Means:** phân cụm sản phẩm dựa trên các đặc trưng số đã được xử lý và chuẩn hóa.
- **Random Forest Regressor:** thử nghiệm dự đoán điểm đánh giá hoặc một biến mục tiêu phù hợp khác, sau khi xác định rõ dữ liệu huấn luyện và đánh giá.
- **Isolation Forest:** phát hiện các sản phẩm có đặc điểm giá hoặc giảm giá bất thường.
- **Website Streamlit:** hiển thị danh sách sản phẩm, tìm kiếm, lọc, xem thông tin và trực quan hóa dữ liệu.

Các giá trị thiếu cần được xử lý riêng trong từng quy trình phân tích hoặc mô hình học máy. Không nên thay thế toàn bộ giá trị thiếu bằng 0 một cách tự động.

## 8. Kết luận

Bộ dữ liệu Tiki và Hasaki đã được ghép thành công với 6.945 dòng và 17 cột. Kết quả kiểm tra cho thấy phần lớn các cột được hiển thị không có giá trị thiếu; các giá trị thiếu tập trung ở số lượng đã bán, giá gốc và số tiền giảm giá.

Các giá trị thiếu chưa đủ căn cứ để suy ra được giữ nguyên nhằm hạn chế làm sai lệch dữ liệu. Thông tin thương hiệu thiếu được thay thế bằng nhãn `Chưa xác định` ở bước xử lý đã thực hiện trên dữ liệu Tiki.

Trước khi bàn giao cho các thành viên phụ trách dashboard, mô hình học máy và website, nhóm cần hoàn tất kiểm tra trùng lặp, kiểu dữ liệu, tính hợp lệ của các trường giá và thống nhất cấu trúc schema cuối cùng.
