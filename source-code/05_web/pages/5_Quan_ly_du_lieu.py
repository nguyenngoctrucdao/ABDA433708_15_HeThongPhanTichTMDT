import io
import re
from datetime import datetime, timezone

import pandas as pd
import streamlit as st
from bson import ObjectId
from pymongo.errors import DuplicateKeyError, PyMongoError

from db import get_collection, clear_data_cache
from permissions import require_login, require_role

user = require_login()
IS_ADMIN = user.get('role') == 'admin'

COLLECTION = 'products_cleaned'
FIELDS = [
    'Nguồn dữ liệu', 'Mã sản phẩm', 'Tên sản phẩm', 'Thương hiệu',
    'Giá bán', 'Giá gốc', 'Số tiền giảm giá', 'Tỷ lệ giảm giá',
    'Điểm đánh giá trung bình', 'Số lượt đánh giá', 'Số lượng đã bán',
    'Mã danh mục', 'Tên danh mục', 'Đường dẫn danh mục',
    'Đường dẫn sản phẩm', 'Đường dẫn ảnh sản phẩm', 'Thời gian thu thập'
]
NUMERIC_FIELDS = {
    'Giá bán', 'Giá gốc', 'Số tiền giảm giá', 'Tỷ lệ giảm giá',
    'Điểm đánh giá trung bình', 'Số lượt đánh giá', 'Số lượng đã bán'
}
INTEGER_FIELDS = {'Số lượt đánh giá', 'Số lượng đã bán'}
REQUIRED_FIELDS = {'Nguồn dữ liệu', 'Mã sản phẩm', 'Tên sản phẩm'}
EDITABLE_FIELDS = [c for c in FIELDS if c != 'Thời gian thu thập']

st.html('''
<style>
[data-testid="stAppViewContainer"] {background:#f4f7fc;}
[data-testid="stMainBlockContainer"] {max-width:1500px;padding-top:2rem;padding-bottom:3rem;}
h1,h2,h3 {color:#152d55;}
[data-testid="stMetric"] {background:#fff;border:1px solid #e2e8f0;border-radius:15px;padding:18px;box-shadow:0 5px 18px rgba(21,45,85,.05);}
[data-testid="stMetricValue"] {color:#152d55;}
[data-testid="stExpander"] {background:#fff;border:1px solid #e2e8f0;border-radius:12px;}
div[data-baseweb="select"]>div {border-radius:11px;}
/* Tiêu đề khu vực đồng bộ các trang Machine Learning */
.section-heading {
    background: #E1ECFF;
    border-left: 5px solid #2563EB;
    border-radius: 9px;
    padding: 13px 18px;
    margin: 24px 0 16px;
    color: #12376B;
    font-size: 23px;
    font-weight: 750;
    line-height: 1.4;
}

</style>
<div style="background:linear-gradient(110deg,#152d55,#2457a6);border-radius:18px;padding:30px 36px;margin-bottom:24px;box-shadow:0 10px 25px rgba(21,45,85,.12)">
<div style="font-size:12px;letter-spacing:1.2px;color:#bfdbfe;font-weight:700">E-COMMERCE ANALYTICS / DATA MANAGEMENT</div>
<div style="color:white;font-size:32px;font-weight:800;margin:10px 0">Quản lý dữ liệu sản phẩm</div>
<div style="color:#dbeafe;font-size:15px">Tra cứu, lọc và quản trị dữ liệu Tiki – Hasaki trên MongoDB.</div>
</div>
''')

@st.cache_data(
    ttl=60,
    show_spinner="Đang tải..."
)
def load_records():
    return list(get_collection(COLLECTION).find({}, {'_id': 1, **{c: 1 for c in FIELDS}}))


def refresh_data():
    load_records.clear()
    clear_data_cache()


def normalize_text(value):
    if value is None:
        return ''
    return str(value).strip()


def parse_optional_number(value, field):
    if value is None or str(value).strip() == '':
        return None
    try:
        n = float(str(value).strip().replace(',', '.'))
    except ValueError:
        raise ValueError(f'{field}: cần nhập số hợp lệ.')
    if not pd.notna(n) or n in (float('inf'), float('-inf')):
        raise ValueError(f'{field}: cần nhập số hữu hạn.')
    if n < 0:
        raise ValueError(f'{field}: không được âm.')
    if field in INTEGER_FIELDS:
        if not n.is_integer():
            raise ValueError(f'{field}: phải là số nguyên.')
        return int(n)
    if field == 'Điểm đánh giá trung bình' and n > 5:
        raise ValueError('Điểm đánh giá trung bình phải từ 0 đến 5.')
    return n


def validate_document(doc):
    result = {}
    for key in EDITABLE_FIELDS:
        raw = doc.get(key)
        if key in NUMERIC_FIELDS:
            result[key] = parse_optional_number(raw, key)
        else:
            result[key] = normalize_text(raw) or None
    for key in REQUIRED_FIELDS:
        if not result.get(key):
            raise ValueError(f'Vui lòng nhập {key}.')
    if result['Nguồn dữ liệu'].lower() not in ('tiki', 'hasaki'):
        raise ValueError('Nguồn dữ liệu chỉ được là tiki hoặc hasaki.')
    result['Nguồn dữ liệu'] = result['Nguồn dữ liệu'].lower()
    return result


def edit_form(prefix, initial=None):
    initial = initial or {}
    values = {}
    for field in EDITABLE_FIELDS:
        default = initial.get(field)
        if field in NUMERIC_FIELDS:
            values[field] = st.text_input(
                field,
                value='' if default is None or pd.isna(default) else str(default),
                placeholder='Để trống nếu chưa có dữ liệu',
                key=f'{prefix}_{field}',
            )
        elif field == 'Nguồn dữ liệu':
            opts = ['tiki', 'hasaki']
            val = str(default or 'tiki').lower()
            values[field] = st.selectbox(field, opts, index=opts.index(val) if val in opts else 0, key=f'{prefix}_{field}')
        else:
            values[field] = st.text_input(field, value=normalize_text(default), key=f'{prefix}_{field}')
    return values

try:
    records = load_records()
except PyMongoError:
    st.error('Không thể đọc dữ liệu từ MongoDB. Kiểm tra kết nối và cấu hình cơ sở dữ liệu.')
    st.stop()

raw_df = pd.DataFrame(records)
if raw_df.empty:
    raw_df = pd.DataFrame(columns=['_id'] + FIELDS)
for field in FIELDS:
    if field not in raw_df.columns:
        raw_df[field] = None
for field in NUMERIC_FIELDS:
    raw_df[field] = pd.to_numeric(raw_df[field], errors='coerce')

m1, m2, m3, m4 = st.columns(4)
m1.metric('Tổng sản phẩm', f'{len(raw_df):,}')
m2.metric('Nguồn dữ liệu', raw_df['Nguồn dữ liệu'].nunique())
m3.metric('Số danh mục', raw_df['Tên danh mục'].nunique())
m4.metric('Quyền truy cập', 'Quản trị viên' if IS_ADMIN else 'Chỉ xem')

st.html('<div class="section-heading">Tìm kiếm và bộ lọc</div>')
f1, f2, f3 = st.columns([2, 1, 1])
with f1:
    keyword = st.text_input('Tìm kiếm sản phẩm', placeholder='Nhập mã, tên sản phẩm hoặc thương hiệu...')
with f2:
    sources = sorted(raw_df['Nguồn dữ liệu'].dropna().astype(str).unique().tolist())
    source = st.selectbox('Nguồn dữ liệu', ['Tất cả'] + sources)
with f3:
    categories = sorted(raw_df['Tên danh mục'].dropna().astype(str).unique().tolist())
    chosen_categories = st.multiselect('Danh mục', categories, placeholder='Chọn danh mục')

p1, p2 = st.columns(2)
with p1:
    price_min = st.number_input('Giá bán từ (VNĐ)', min_value=0.0, value=0.0, step=10000.0)
with p2:
    price_max_text = st.text_input('Giá bán đến (VNĐ)', placeholder='Để trống nếu không giới hạn')

filtered = raw_df.copy()
if keyword.strip():
    needle = re.escape(keyword.strip())
    mask = pd.Series(False, index=filtered.index)
    for col in ['Mã sản phẩm', 'Tên sản phẩm', 'Thương hiệu']:
        mask |= filtered[col].fillna('').astype(str).str.contains(needle, case=False, regex=True)
    filtered = filtered[mask]
if source != 'Tất cả':
    filtered = filtered[filtered['Nguồn dữ liệu'] == source]
if chosen_categories:
    filtered = filtered[filtered['Tên danh mục'].isin(chosen_categories)]
if price_min > 0:
    filtered = filtered[filtered['Giá bán'] >= price_min]
if price_max_text.strip():
    try:
        price_max = float(price_max_text.strip().replace(',', '.'))
        if price_max < price_min:
            st.warning('Giá tối đa phải lớn hơn hoặc bằng giá tối thiểu.')
            filtered = filtered.iloc[0:0]
        else:
            filtered = filtered[filtered['Giá bán'] <= price_max]
    except ValueError:
        st.warning('Giá tối đa phải là số hợp lệ.')
        filtered = filtered.iloc[0:0]

st.html('<div class="section-heading">Danh sách sản phẩm</div>')
st.caption(f'Đang hiển thị {len(filtered):,} / {len(raw_df):,} sản phẩm. Các ô chưa có dữ liệu được giữ trống.')
view_cols = ['Nguồn dữ liệu', 'Mã sản phẩm', 'Tên sản phẩm', 'Thương hiệu', 'Giá bán', 'Giá gốc', 'Tỷ lệ giảm giá', 'Điểm đánh giá trung bình', 'Số lượt đánh giá', 'Số lượng đã bán', 'Tên danh mục']
st.dataframe(filtered[view_cols], hide_index=True, use_container_width=True, height=440)

with st.expander('Xem toàn bộ 17 trường dữ liệu'):
    st.dataframe(filtered[FIELDS], hide_index=True, use_container_width=True, height=380)

csv_bytes = filtered[FIELDS].to_csv(index=False).encode('utf-8-sig')
st.download_button('Tải dữ liệu đang lọc (CSV)', csv_bytes, 'products_filtered.csv', 'text/csv')

if not IS_ADMIN:
    st.info('Tài khoản của bạn có quyền xem, tìm kiếm, lọc và tải dữ liệu. Chỉ Admin được thêm, sửa hoặc xóa sản phẩm.')
    st.stop()

st.divider()
st.html('<div class="section-heading">Quản trị dữ liệu (Admin)</div>')
tab_add, tab_edit, tab_delete = st.tabs(['Thêm sản phẩm', 'Chỉnh sửa sản phẩm', 'Xóa sản phẩm'])

with tab_add:
    st.caption('Các trường số chưa có thông tin có thể để trống. Thời gian thu thập sẽ được ghi tự động.')
    with st.form('add_product', clear_on_submit=False):
        new_data = edit_form('add')
        add_submitted = st.form_submit_button('Lưu sản phẩm mới', type='primary')
    if add_submitted:
        try:
            require_role('admin')
            payload = validate_document(new_data)
            coll = get_collection(COLLECTION)
            existing = coll.find_one({'Nguồn dữ liệu': payload['Nguồn dữ liệu'], 'Mã sản phẩm': payload['Mã sản phẩm']}, {'_id': 1})
            if existing:
                st.error('Mã sản phẩm đã tồn tại trong nguồn dữ liệu này.')
            else:
                payload['Thời gian thu thập'] = datetime.now(timezone.utc).isoformat()
                coll.insert_one(payload)
                refresh_data()
                st.success('Đã thêm sản phẩm.')
                st.rerun()
        except (ValueError, DuplicateKeyError) as exc:
            st.error(str(exc))
        except PyMongoError:
            st.error('Không thể lưu sản phẩm vào MongoDB.')


def record_options(frame):
    return [str(v) for v in frame['_id'].tolist()]


def record_label(id_text):
    row = filtered.loc[filtered['_id'].astype(str) == id_text]
    if row.empty:
        return id_text
    r = row.iloc[0]
    return f"{r['Nguồn dữ liệu']} | {r['Mã sản phẩm']} | {str(r['Tên sản phẩm'])[:65]}"

with tab_edit:
    ids = record_options(filtered)
    if not ids:
        st.info('Không có sản phẩm để chỉnh sửa. Hãy điều chỉnh bộ lọc.')
    else:
        selected_id = st.selectbox('Chọn sản phẩm cần sửa', ids, format_func=record_label, key='edit_id')
        chosen = next((r for r in records if str(r['_id']) == selected_id), None)
        if chosen is not None:
            with st.form(f'edit_form_{selected_id}'):
                edited = edit_form(f'edit_{selected_id}', chosen)
                edit_submitted = st.form_submit_button('Lưu thay đổi', type='primary')
            if edit_submitted:
                try:
                    require_role('admin')
                    payload = validate_document(edited)
                    coll = get_collection(COLLECTION)
                    conflict = coll.find_one({
                        'Nguồn dữ liệu': payload['Nguồn dữ liệu'],
                        'Mã sản phẩm': payload['Mã sản phẩm'],
                        '_id': {'$ne': ObjectId(selected_id)},
                    }, {'_id': 1})
                    if conflict:
                        st.error('Đã có sản phẩm khác mang mã này trong cùng nguồn dữ liệu.')
                    else:
                        result = coll.update_one({'_id': ObjectId(selected_id)}, {'$set': payload})
                        if result.matched_count == 0:
                            st.error('Bản ghi không còn tồn tại.')
                        else:
                            refresh_data()
                            st.success('Đã cập nhật sản phẩm.')
                            st.rerun()
                except (ValueError, DuplicateKeyError) as exc:
                    st.error(str(exc))
                except PyMongoError:
                    st.error('Không thể cập nhật MongoDB.')

with tab_delete:
    ids = record_options(filtered)
    if not ids:
        st.info('Không có sản phẩm để xóa. Hãy điều chỉnh bộ lọc.')
    else:
        delete_id = st.selectbox('Chọn sản phẩm cần xóa', ids, format_func=record_label, key='delete_id')
        st.warning('Xóa sản phẩm là thao tác không thể hoàn tác từ trang này. Hãy sao lưu dữ liệu trước khi xóa.')
        with st.form('delete_form'):
            confirm = st.checkbox('Tôi xác nhận muốn xóa sản phẩm đã chọn')
            delete_submitted = st.form_submit_button('Xóa sản phẩm')
        if delete_submitted:
            if not confirm:
                st.error('Bạn cần xác nhận trước khi xóa.')
            else:
                try:
                    require_role('admin')
                    result = get_collection(COLLECTION).delete_one({'_id': ObjectId(delete_id)})
                    if result.deleted_count:
                        refresh_data()
                        st.success('Đã xóa sản phẩm.')
                        st.rerun()
                    else:
                        st.error('Không tìm thấy sản phẩm cần xóa.')
                except PyMongoError:
                    st.error('Không thể xóa sản phẩm khỏi MongoDB.')
