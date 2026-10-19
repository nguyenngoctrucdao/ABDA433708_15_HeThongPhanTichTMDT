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