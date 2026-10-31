"""Trang Báo cáo cho hệ thống phân tích Tiki / Hasaki.
Đặt file trong source-code/05_web/pages/6_Bao_cao.py.
Yêu cầu: streamlit, pandas, plotly, pymongo, openpyxl.
"""
import io
import json
from datetime import datetime, date, timezone

import pandas as pd
import plotly.express as px
import streamlit as st
from bson import ObjectId
from pymongo.errors import PyMongoError

from db import get_collection
from permissions import require_login, require_role

user = require_login()
IS_ADMIN = user.get('role') == 'admin'

PRODUCT_COLLECTION = 'products_cleaned'
COLLECTIONS = {
    'Sản phẩm': 'products_cleaned',
    'K-Means': 'ml_kmeans_results',
    'Hồ sơ cụm': 'ml_cluster_profile',
    'Dự đoán điểm đánh giá': 'ml_rating_predictions',
    'Phát hiện bất thường': 'ml_anomalies',
    'Chỉ số mô hình': 'ml_model_metrics',
}
FIELDS = [
    'Nguồn dữ liệu', 'Mã sản phẩm', 'Tên sản phẩm', 'Thương hiệu',
    'Giá bán', 'Giá gốc', 'Số tiền giảm giá', 'Tỷ lệ giảm giá',
    'Điểm đánh giá trung bình', 'Số lượt đánh giá', 'Số lượng đã bán',
    'Mã danh mục', 'Tên danh mục', 'Đường dẫn danh mục',
    'Đường dẫn sản phẩm', 'Đường dẫn ảnh sản phẩm', 'Thời gian thu thập'
]
NUMERIC = ['Giá bán', 'Giá gốc', 'Số tiền giảm giá', 'Tỷ lệ giảm giá',
           'Điểm đánh giá trung bình', 'Số lượt đánh giá', 'Số lượng đã bán']

st.html('''
<style>
[data-testid="stAppViewContainer"] {background:#f4f7fc;}
[data-testid="stMainBlockContainer"] {max-width:1500px;padding-top:2rem;padding-bottom:3rem;}
h1,h2,h3 {color:#152d55;}
/* Tiêu đề khu vực và biểu đồ - đồng bộ giao diện ML */
.report-section-title {background:#E1ECFF;border-left:5px solid #2563EB;border-radius:8px;padding:13px 18px;margin:20px 0 14px;color:#12376B;font-size:21px;font-weight:750;line-height:1.4;}
.report-chart-title {color:#1D4ED8;font-size:17px;font-weight:750;border-bottom:2px solid #BFDBFE;padding-bottom:9px;margin:16px 0 10px;}

[data-testid="stMetric"] {background:white;border:1px solid #e2e8f0;border-radius:15px;padding:18px;box-shadow:0 5px 18px rgba(21,45,85,.05);}
[data-testid="stMetricValue"] {color:#152d55;}
[data-testid="stExpander"] {background:white;border:1px solid #e2e8f0;border-radius:12px;}
</style>
<div style="background:linear-gradient(110deg,#152d55,#2457a6);padding:32px 38px;border-radius:18px;margin-bottom:25px;box-shadow:0 10px 25px rgba(21,45,85,.12)">
<div style="color:#bfdbfe;font-size:12px;font-weight:700;letter-spacing:1.2px">E-COMMERCE ANALYTICS / REPORT CENTER</div>
<div style="color:white;font-size:32px;font-weight:800;margin:10px 0">Báo cáo và xuất dữ liệu</div>
<div style="color:#dbeafe;font-size:15px">Tổng hợp dữ liệu Tiki – Hasaki, kết quả Machine Learning và quản lý bản sao lưu.</div>
</div>
''')




def section_title(label):
    st.html(f'<div class="report-section-title">{label}</div>')

def chart_title(label):
    st.html(f'<div class="report-chart-title">{label}</div>')

def json_safe(value):
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(v) for v in value]
    if isinstance(value, float) and not pd.notna(value):
        return None
    return value


@st.cache_data(
    ttl=120,
    show_spinner="Đang tải..."
)
def read_collection(name):
    return list(get_collection(name).find({}, {'_id': 0}))


def dataframe(name):
    rows = read_collection(name)
    return pd.DataFrame(rows)


def product_view(data):
    view = data.copy()
    for col in NUMERIC:
        if col in view.columns:
            view[col] = pd.to_numeric(view[col], errors='coerce')
    return view


def csv_bytes(data):
    return data.to_csv(index=False).encode('utf-8-sig')


def excel_bytes(sheets):
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        for sheet_name, data in sheets.items():
            safe = data.copy()
            for col in safe.columns:
                safe[col] = safe[col].map(
                    lambda x: json.dumps(json_safe(x), ensure_ascii=False)
                    if isinstance(x, (dict, list, tuple)) else json_safe(x)
                )
            # Excel giới hạn 1,048,576 dòng / sheet.
            safe.to_excel(writer, sheet_name=sheet_name[:31], index=False)
            ws = writer.sheets[sheet_name[:31]]
            ws.freeze_panes = 'A2'
            ws.auto_filter.ref = ws.dimensions
            for column in ws.columns:
                letter = column[0].column_letter
                max_len = max((len(str(cell.value or '')) for cell in list(column)[:100]), default=12)
                ws.column_dimensions[letter].width = min(max(13, max_len + 2), 46)
    return buffer.getvalue()


def bar_style(fig, height=360):
    fig.update_layout(
        template='plotly_white', height=height,
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#334155'), margin=dict(l=20, r=20, t=30, b=25)
    )
    fig.update_yaxes(gridcolor='#e8eef6')
    return fig


def anomaly_flag(value):
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {'-1', 'true', '1', 'anomaly'}


try:
    products = product_view(dataframe(PRODUCT_COLLECTION))
except PyMongoError as exc:
    st.error(f'Không đọc được MongoDB: {exc}')
    st.stop()

if products.empty:
    st.warning('Collection products_cleaned chưa có dữ liệu để lập báo cáo.')
    st.stop()

source_col = 'Nguồn dữ liệu'
category_col = 'Tên danh mục'
source_options = sorted(products[source_col].dropna().astype(str).unique().tolist()) if source_col in products else []

section_title('Phạm vi báo cáo')
selected_source = st.selectbox('Nguồn dữ liệu', ['Tất cả'] + source_options)
report_products = products.copy()
if selected_source != 'Tất cả':
    report_products = report_products[report_products[source_col].astype(str) == selected_source].copy()

# Phần tổng quan và xuất dữ liệu luôn dùng cùng một tập dữ liệu sau lọc.
tab_overview, tab_ml, tab_export, tab_backup = st.tabs([
    'Tổng quan', 'Machine Learning', 'Xuất báo cáo', 'Sao lưu & phục hồi'
])

with tab_overview:
    section_title('Tổng quan dữ liệu sản phẩm')
    total = len(report_products)
    avg_price = report_products['Giá bán'].mean() if 'Giá bán' in report_products else float('nan')
    rated = report_products.copy()
    if {'Số lượt đánh giá', 'Điểm đánh giá trung bình'}.issubset(rated.columns):
        rated = rated[rated['Số lượt đánh giá'] > 0]
        avg_rating = rated['Điểm đánh giá trung bình'].mean()
    else:
        avg_rating = float('nan')
    a, b, c, d = st.columns(4)
    a.metric('Số sản phẩm', f'{total:,}')
    b.metric('Số danh mục', report_products[category_col].nunique() if category_col in report_products else 'N/A')
    c.metric('Giá bán trung bình', f'{avg_price:,.0f} đ' if pd.notna(avg_price) else 'N/A')
    d.metric('Điểm đánh giá TB', f'{avg_rating:.2f}/5' if pd.notna(avg_rating) else 'N/A')

    left, right = st.columns(2)
    with left:
        chart_title('Phân bố theo nguồn')
        if source_col in report_products:
            counts = report_products[source_col].fillna('Chưa xác định').value_counts().reset_index()
            counts.columns = ['Nguồn', 'Số sản phẩm']
            fig = px.bar(counts, x='Nguồn', y='Số sản phẩm', text='Số sản phẩm', color='Nguồn',
                         color_discrete_sequence=['#2563eb', '#0891b2'])
            fig.update_layout(showlegend=False)
            st.plotly_chart(bar_style(fig), use_container_width=True)
    with right:
        chart_title('Top 10 danh mục')
        if category_col in report_products:
            counts = report_products[category_col].fillna('Chưa xác định').value_counts().head(10).reset_index()
            counts.columns = ['Danh mục', 'Số sản phẩm']
            fig = px.bar(counts, x='Số sản phẩm', y='Danh mục', orientation='h',
                         color_discrete_sequence=['#2563eb'])
            fig.update_layout(yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(bar_style(fig, 410), use_container_width=True)

    chart_title('Bảng thống kê theo nguồn')
    if source_col in report_products:
        grouped = report_products.groupby(source_col, dropna=False).agg(
            **{'Số sản phẩm': ('Giá bán', 'size'), 'Giá trung bình': ('Giá bán', 'mean')}
        ).reset_index()
        st.dataframe(grouped, hide_index=True, use_container_width=True)
    st.caption('Điểm đánh giá trung bình chỉ tính các sản phẩm có ít nhất một lượt đánh giá.')

with tab_ml:
    section_title('Tổng hợp kết quả Machine Learning')
    try:
        kmeans = dataframe('ml_kmeans_results')
        profile = dataframe('ml_cluster_profile')
        predictions = dataframe('ml_rating_predictions')
        anomalies = dataframe('ml_anomalies')
        model_metrics = dataframe('ml_model_metrics')
    except PyMongoError as exc:
        st.error(f'Không đọc được collection ML: {exc}')
        st.stop()


    def filter_ml(frame):
        if selected_source == 'Tất cả' or frame.empty:
            return frame
        col = next((c for c in ['nguon', 'Nguồn dữ liệu', 'source'] if c in frame.columns), None)
        if col is None:
            return frame
        return frame[frame[col].astype(str).str.lower() == selected_source.lower()].copy()

    kmeans_f = filter_ml(kmeans)
    predictions_f = filter_ml(predictions)
    anomalies_f = filter_ml(anomalies)
    m1, m2, m3 = st.columns(3)
    m1.metric('K-Means: bản ghi', f'{len(kmeans_f):,}')
    m2.metric('Random Forest: bản ghi', f'{len(predictions_f):,}')
    m3.metric('Isolation Forest: bản ghi', f'{len(anomalies_f):,}')

    chart_title('K-Means – phân bố cụm')
    if not kmeans_f.empty and 'cluster' in kmeans_f:
        counts = kmeans_f['cluster'].value_counts().reset_index()
        counts.columns = ['Cụm', 'Số sản phẩm']
        counts['Cụm'] = counts['Cụm'].astype(str)
        fig = px.bar(counts, x='Cụm', y='Số sản phẩm', text='Số sản phẩm', color='Cụm',
                     color_discrete_sequence=['#2563eb', '#0891b2', '#7c3aed', '#0d9488'])
        fig.update_layout(showlegend=False)
        st.plotly_chart(bar_style(fig), use_container_width=True)
    else:
        st.info('Chưa có dữ liệu K-Means hoặc thiếu cột cluster.')
    if not profile.empty:
        with st.expander('Xem hồ sơ đặc điểm các cụm'):
            st.dataframe(profile, hide_index=True, use_container_width=True)

    chart_title('Random Forest – kết quả dự đoán')
    if {'rating_thuc', 'rating_du_doan'}.issubset(predictions_f.columns):
        temp = predictions_f.copy()
        for col in ['rating_thuc', 'rating_du_doan']:
            temp[col] = pd.to_numeric(temp[col], errors='coerce')
        temp = temp.dropna(subset=['rating_thuc', 'rating_du_doan'])
        if not temp.empty:
            mae = (temp['rating_thuc'] - temp['rating_du_doan']).abs().mean()
            st.metric('MAE của các bản ghi đang báo cáo', f'{mae:.4f}')
            fig = px.scatter(temp, x='rating_thuc', y='rating_du_doan', opacity=.65,
                             labels={'rating_thuc': 'Điểm thực tế', 'rating_du_doan': 'Điểm dự đoán'},
                             color_discrete_sequence=['#2563eb'])
            low = min(temp['rating_thuc'].min(), temp['rating_du_doan'].min())
            high = max(temp['rating_thuc'].max(), temp['rating_du_doan'].max())
            fig.add_shape(type='line', x0=low, y0=low, x1=high, y1=high,
                          line=dict(color='#10b981', dash='dash'))
            st.plotly_chart(bar_style(fig), use_container_width=True)
            st.caption('MAE tính từ bản ghi đang báo cáo, không mặc định là MAE trên tập kiểm tra.')
        else:
            st.info('Không có cặp điểm dự đoán và điểm thực tế hợp lệ.')
    else:
        st.info('Chưa có kết quả dự đoán hoặc thiếu cột rating_thuc / rating_du_doan.')

    chart_title('Isolation Forest – sản phẩm cần kiểm tra')
    if not anomalies_f.empty and 'is_anomaly' in anomalies_f:
        flagged = anomalies_f['is_anomaly'].map(anomaly_flag)
        x, y = st.columns(2)
        x.metric('Bản ghi bị gắn cờ', f'{int(flagged.sum()):,}')
        y.metric('Tỷ lệ gắn cờ', f'{flagged.mean() * 100:.2f}%')
        st.caption('Gắn cờ bất thường không có nghĩa dữ liệu chắc chắn sai.')
    else:
        st.info('Chưa có kết quả bất thường hoặc thiếu cột is_anomaly.')

    if not model_metrics.empty:
        with st.expander('Xem chỉ số và thông số mô hình đã lưu'):
            st.dataframe(model_metrics, hide_index=True, use_container_width=True)

with tab_export:
    section_title('Xuất báo cáo')
    st.caption('CSV dùng cho bảng sản phẩm; Excel gồm nhiều sheet về dữ liệu và kết quả ML.')
    st.download_button('Tải dữ liệu sản phẩm (CSV)', data=csv_bytes(report_products),
                       file_name='bao_cao_san_pham.csv', mime='text/csv', use_container_width=True)
    try:
        sheet_data = {'San_pham': report_products}
        for label, collection, sheet in [
            ('K-Means', 'ml_kmeans_results', 'KMeans'),
            ('Hồ sơ cụm', 'ml_cluster_profile', 'Ho_so_cum'),
            ('Dự đoán', 'ml_rating_predictions', 'Du_doan'),
            ('Bất thường', 'ml_anomalies', 'Bat_thuong'),
            ('Chỉ số mô hình', 'ml_model_metrics', 'Chi_so_ML'),
        ]:
            temp = dataframe(collection)
            if not temp.empty:
                if selected_source != 'Tất cả':
                    src = next((c for c in ['nguon', 'Nguồn dữ liệu', 'source'] if c in temp), None)
                    if src:
                        temp = temp[temp[src].astype(str).str.lower() == selected_source.lower()]
                sheet_data[sheet] = temp
        excel = excel_bytes(sheet_data)
        st.download_button('Tải báo cáo tổng hợp (Excel)', data=excel,
                           file_name='bao_cao_tiki_hasaki.xlsx',
                           mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                           use_container_width=True)
        st.caption('Các sheet ML không có trường nguồn sẽ giữ nguyên toàn bộ bản ghi và không được lọc theo Tiki/Hasaki.')
    except (ImportError, ValueError, PyMongoError) as exc:
        st.warning(f'Không thể tạo Excel: {exc}. Kiểm tra openpyxl và dữ liệu MongoDB.')

with tab_backup:
    section_title('Sao lưu dữ liệu JSON')
    st.caption('Bản sao lưu chỉ chứa dữ liệu sản phẩm và các kết quả phân tích; không xuất tài khoản hoặc mật khẩu người dùng.')
    backup_names = st.multiselect('Chọn collection cần sao lưu', list(COLLECTIONS),
                                  default=['Sản phẩm'])
    if backup_names:
        try:
            payload = {
                'format': 'ecommerce_backup_v1',
                'created_at': datetime.now(timezone.utc).isoformat(),
                'collections': {
                    COLLECTIONS[label]: json_safe(read_collection(COLLECTIONS[label]))
                    for label in backup_names
                }
            }
            backup_data = json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False).encode('utf-8')
            st.download_button('Tải bản sao lưu JSON', data=backup_data,
                               file_name='ecommerce_backup.json', mime='application/json',
                               use_container_width=True)
        except (TypeError, ValueError, PyMongoError) as exc:
            st.error(f'Không thể tạo bản sao lưu: {exc}')

    st.divider()
    section_title('Phục hồi dữ liệu sản phẩm')
    if not IS_ADMIN:
        st.warning('Chỉ tài khoản Admin được phục hồi dữ liệu.')
    else:
        uploaded = st.file_uploader('Chọn file JSON đã sao lưu', type=['json'], key='restore_json')
        if uploaded is not None:
            if uploaded.size > 15 * 1024 * 1024:
                st.error('File lớn hơn 15 MB. Hãy chia nhỏ bản sao lưu.')
            else:
                try:
                    payload = json.loads(uploaded.getvalue().decode('utf-8-sig'))
                    if not isinstance(payload, dict) or payload.get('format') != 'ecommerce_backup_v1':
                        raise ValueError('Định dạng bản sao lưu không hợp lệ.')
                    rows = payload.get('collections', {}).get(PRODUCT_COLLECTION)
                    if not isinstance(rows, list):
                        raise ValueError('File không chứa collection products_cleaned.')
                    if len(rows) > 10000:
                        raise ValueError('Tối đa 10.000 sản phẩm trong một lần phục hồi.')
                    clean_rows = []
                    keys = set()
                    for i, row in enumerate(rows):
                        if not isinstance(row, dict):
                            raise ValueError(f'Bản ghi {i + 1} không hợp lệ.')
                        source = str(row.get('Nguồn dữ liệu') or '').strip().lower()
                        pid = str(row.get('Mã sản phẩm') or '').strip()
                        name = str(row.get('Tên sản phẩm') or '').strip()
                        if source not in {'tiki', 'hasaki'} or not pid or not name:
                            raise ValueError(f'Bản ghi {i + 1} thiếu nguồn, mã hoặc tên sản phẩm.')
                        key = (source, pid)
                        if key in keys:
                            raise ValueError(f'Mã sản phẩm bị lặp trong file: {source}/{pid}')
                        keys.add(key)
                        doc = {field: row.get(field) for field in FIELDS}
                        doc['Nguồn dữ liệu'] = source
                        doc['Mã sản phẩm'] = pid
                        doc['Tên sản phẩm'] = name
                        for field in NUMERIC:
                            val = doc.get(field)
                            if val is not None and val != '':
                                try:
                                    val = float(val)
                                except (TypeError, ValueError):
                                    raise ValueError(f'Bản ghi {i + 1}: {field} không phải số.')
                                if not pd.notna(val) or val < 0 or val == float('inf'):
                                    raise ValueError(f'Bản ghi {i + 1}: {field} không hợp lệ.')
                                if field == 'Điểm đánh giá trung bình' and val > 5:
                                    raise ValueError(f'Bản ghi {i + 1}: điểm đánh giá lớn hơn 5.')
                                if field in ('Số lượt đánh giá', 'Số lượng đã bán'):
                                    if not val.is_integer():
                                        raise ValueError(f'Bản ghi {i + 1}: {field} phải là số nguyên.')
                                    val = int(val)
                                doc[field] = val
                            else:
                                doc[field] = None
                        clean_rows.append(doc)
                    st.success(f'File hợp lệ: {len(clean_rows):,} bản ghi.')
                    st.dataframe(pd.DataFrame(clean_rows).head(10), hide_index=True, use_container_width=True)
                    confirmed = st.checkbox('Tôi xác nhận chỉ thêm sản phẩm chưa có và không ghi đè dữ liệu hiện tại.', key='restore_confirm')
                    if st.button('Bắt đầu phục hồi', type='primary', disabled=not confirmed):
                        require_role('admin')
                        collection = get_collection(PRODUCT_COLLECTION)
                        inserted = 0
                        skipped = 0
                        for doc in clean_rows:
                            key = {'Nguồn dữ liệu': doc['Nguồn dữ liệu'], 'Mã sản phẩm': doc['Mã sản phẩm']}
                            # Upsert theo cặp nguồn + mã, chỉ insert nếu chưa tồn tại.
                            result = collection.update_one(key, {'$setOnInsert': doc}, upsert=True)
                            if result.upserted_id is None:
                                skipped += 1
                            else:
                                inserted += 1
                        read_collection.clear()
                        st.success(f'Đã thêm {inserted:,} sản phẩm; bỏ qua {skipped:,} sản phẩm đã tồn tại.')
                        st.warning('Nếu đã có kết quả ML, cần chạy lại pipeline để cập nhật kết quả theo dữ liệu mới.')
                except (UnicodeError, json.JSONDecodeError, ValueError, TypeError, PyMongoError) as exc:
                    st.error(f'Không thể phục hồi: {exc}')

