"""
Ứng dụng Streamlit Trực quan hóa các chiến lược Chunking & Kết quả OCR (Buổi 05 - RAG Foundation)
Giao diện Tiếng Việt thân thiện dành cho người học RAG.
"""

import json
import streamlit as st
from pathlib import Path

# Cấu hình đường dẫn
BASE_DIR = Path(__file__).parent.resolve()
OUTPUT_DIR = BASE_DIR / "output"

# Thiết lập giao diện Streamlit
st.set_page_config(
    page_title="RAG Foundation - Buổi 05: OCR & Chunking Visualizer",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# GIAO DIỆN THEO BỘ NHẬN DIỆN THƯƠNG HIỆU AGRIBANK
# Màu chủ đạo: Đỏ burgundy #8B1538  |  Vàng kim #F5A623
# ============================================================
AGRIBANK_CSS = """
<style>
:root {
    --agri-red: #8B1538;
    --agri-red-dark: #6E0F2C;
    --agri-gold: #F5A623;
    --agri-gold-soft: #FDF3E2;
    --agri-text: #2B2B2B;
}
.stApp { background-color: #FFFFFF; }

/* Thanh tiêu đề thương hiệu */
.agri-banner {
    background: linear-gradient(135deg, var(--agri-red) 0%, var(--agri-red-dark) 100%);
    border-bottom: 4px solid var(--agri-gold);
    border-radius: 10px;
    padding: 18px 24px;
    margin-bottom: 22px;
}
.agri-banner h1 {
    color: #FFFFFF; font-size: 1.9rem; font-weight: 800;
    margin: 0; letter-spacing: 0.3px;
}
.agri-banner p { color: var(--agri-gold-soft); margin: 6px 0 0 0; font-size: 1rem; }

/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, var(--agri-red) 0%, var(--agri-red-dark) 100%);
}
section[data-testid="stSidebar"] * { color: #FFF7EC !important; }
section[data-testid="stSidebar"] hr { border-color: rgba(245,166,35,0.45); }

/* Tiêu đề mục */
h2, h3 { color: var(--agri-red) !important; }

/* Nút bấm */
.stButton > button {
    background-color: var(--agri-red); color: #FFFFFF;
    border: 1px solid var(--agri-red-dark); border-radius: 8px;
    font-weight: 600; padding: 8px 18px;
}
.stButton > button:hover {
    background-color: var(--agri-gold); color: var(--agri-red-dark);
    border-color: var(--agri-gold);
}

/* Thẻ nội dung */
.agri-card {
    background-color: #FFFBF4;
    border: 1px solid #EADFCB;
    border-left: 5px solid var(--agri-red);
    border-radius: 10px; padding: 16px; margin-bottom: 14px;
}

/* Ô chỉ số */
.agri-stat {
    background: linear-gradient(135deg, var(--agri-red) 0%, var(--agri-red-dark) 100%);
    border-bottom: 3px solid var(--agri-gold);
    border-radius: 10px; padding: 16px; text-align: center; color: #FFFFFF;
}
.agri-stat h4 { color: var(--agri-gold) !important; margin: 0 0 8px 0; }
.agri-stat p { color: #FFFFFF; margin: 2px 0; }

/* Nhãn (badge) */
.agri-badge {
    background-color: var(--agri-red); color: #FFFFFF;
    padding: 4px 12px; border-radius: 12px;
    font-size: 0.85rem; font-weight: 600;
}
.agri-badge-gold {
    background-color: var(--agri-gold); color: #5A3A00;
    padding: 4px 12px; border-radius: 12px;
    font-size: 0.85rem; font-weight: 600;
}

/* Ô nhập liệu & expander */
.stTextInput input, .stTextArea textarea { border: 1px solid #D8C7A8 !important; }
div[data-testid="stExpander"] {
    border: 1px solid #EADFCB !important; border-radius: 8px;
}
</style>
"""

st.markdown(AGRIBANK_CSS, unsafe_allow_html=True)

# Hàm tải dữ liệu an toàn
def load_json_file(file_name: str):
    file_path = OUTPUT_DIR / file_name
    if file_path.exists():
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Lỗi khi đọc file {file_name}: {e}")
            return None
    return None

def main():
    st.markdown(
        '<div class="agri-banner">'
        '<h1>📚 TRỰC QUAN HÓA RAG FOUNDATION — BUỔI 05</h1>'
        '<p>Phân tích kết quả OCR &amp; So sánh 3 Chiến lược Chunking '
        '(Fixed-size, Semantic, Hierarchical)</p>'
        '</div>',
        unsafe_allow_html=True
    )

    # Tải dữ liệu từ thư mục output
    raw_data = load_json_file("raw_text.json")
    chunks_fixed = load_json_file("chunks_fixed.json") or []
    chunks_semantic = load_json_file("chunks_semantic.json") or []
    chunks_hierarchical = load_json_file("chunks_hierarchical.json") or []

    # Kiểm tra xem đã có kết quả trong output/ chưa
    if not raw_data:
        st.warning("⚠️ Chưa tìm thấy dữ liệu trong thư mục `output/`!")
        st.info("💡 **Hướng dẫn khởi chạy:** Vui lòng thực hiện lệnh sau tại terminal để tạo dữ liệu:\n`python RAG/rag_foundation/buoi_05/src/main.py --write`")
        return

    # Sidebar điều hướng & thông tin file
    st.sidebar.header("⚙️ Bảng điều khiển")
    st.sidebar.markdown(f"**Tập tin xử lý:** `{raw_data.get('source', 'N/A')}`")
    st.sidebar.markdown(f"**Sử dụng OCR LlamaParse:** `{'Có' if raw_data.get('ocr_used') else 'Không (PyMuPDF Text Layer)'}`")
    st.sidebar.markdown(f"**Tổng số trang:** `{raw_data.get('total_pages', 1)}`")

    st.sidebar.divider()
    selected_strategy = st.sidebar.radio(
        "Chọn chiến lược để xem chi tiết:",
        ["So sánh tổng quan", "Fixed-size Chunking", "Semantic Chunking", "Hierarchical Chunking", "Văn bản gốc (Raw Text)"]
    )

    search_kw = st.sidebar.text_input("🔍 Tìm kiếm từ khóa trong Chunk:", "")

    # Tab 1: So sánh tổng quan
    if selected_strategy == "So sánh tổng quan":
        st.subheader("📊 Báo cáo so sánh 3 Chiến lược Chunking")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""
            <div class="agri-stat">
                <h4>Fixed-size</h4>
                <p><b>Số Chunk:</b> {len(chunks_fixed)}</p>
                <p><b>Độ dài trung bình:</b> {round(sum(len(c['text']) for c in chunks_fixed)/len(chunks_fixed), 1) if chunks_fixed else 0} ký tự</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="agri-stat">
                <h4>Semantic</h4>
                <p><b>Số Chunk:</b> {len(chunks_semantic)}</p>
                <p><b>Độ dài trung bình:</b> {round(sum(len(c['text']) for c in chunks_semantic)/len(chunks_semantic), 1) if chunks_semantic else 0} ký tự</p>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div class="agri-stat">
                <h4>Hierarchical</h4>
                <p><b>Số Chunk:</b> {len(chunks_hierarchical)}</p>
                <p><b>Độ dài trung bình:</b> {round(sum(len(c['text']) for c in chunks_hierarchical)/len(chunks_hierarchical), 1) if chunks_hierarchical else 0} ký tự</p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("💡 Đặc điểm từng chiến lược")
        st.markdown("""
        - **Fixed-size:** Cắt văn bản theo kích thước ký tự/token cố định kèm overlap. Đơn giản, đồng đều nhưng có thể làm đứt đoạn câu/ngữ nghĩa.
        - **Semantic:** Ưu tiên ngắt theo đoạn văn (`\\n\\n`) hoặc dấu kết thúc câu (`.`, `?`, `!`). Giữ trọn vẹn ngữ nghĩa của từng khối thông tin.
        - **Hierarchical:** Phân chia dựa vào mốc cấu trúc pháp lý (Chương, Mục, Điều, Khoản). Thích hợp nhất cho tài liệu luật, hợp đồng, văn bản có tiêu đề rõ ràng.
        """)

    # Tab 2: Fixed-size Chunking
    elif selected_strategy == "Fixed-size Chunking":
        st.subheader("📏 Danh sách Chunks: Fixed-size")
        filtered = [c for c in chunks_fixed if search_kw.lower() in c["text"].lower()] if search_kw else chunks_fixed
        
        st.caption(f"Hiển thị {len(filtered)} / {len(chunks_fixed)} chunk")
        for chunk in filtered:
            with st.container():
                st.markdown(f"""
                <div class="agri-card">
                    <span class="agri-badge">ID: {chunk['chunk_id']}</span> | <b>Độ dài:</b> {chunk['metadata'].get('char_count', len(chunk['text']))} ký tự | <b>Trang:</b> {chunk['page_start']}
                    <hr style="margin: 10px 0;">
                    <p style="white-space: pre-wrap; font-family: monospace; font-size: 0.95rem;">{chunk['text']}</p>
                </div>
                """, unsafe_allow_html=True)

    # Tab 3: Semantic Chunking
    elif selected_strategy == "Semantic Chunking":
        st.subheader("🧠 Danh sách Chunks: Semantic")
        filtered = [c for c in chunks_semantic if search_kw.lower() in c["text"].lower()] if search_kw else chunks_semantic

        st.caption(f"Hiển thị {len(filtered)} / {len(chunks_semantic)} chunk")
        for chunk in filtered:
            with st.container():
                st.markdown(f"""
                <div class="agri-card">
                    <span class="agri-badge-gold">ID: {chunk['chunk_id']}</span> | <b>Nguyên nhân ngắt:</b> {chunk['metadata'].get('split_reason', 'N/A')} | <b>Độ dài:</b> {chunk['metadata'].get('char_count', len(chunk['text']))} ký tự
                    <hr style="margin: 10px 0;">
                    <p style="white-space: pre-wrap; font-size: 0.95rem;">{chunk['text']}</p>
                </div>
                """, unsafe_allow_html=True)

    # Tab 4: Hierarchical Chunking
    elif selected_strategy == "Hierarchical Chunking":
        st.subheader("🏛️ Danh sách Chunks: Hierarchical (Cấu trúc)")
        filtered = [c for c in chunks_hierarchical if search_kw.lower() in c["text"].lower()] if search_kw else chunks_hierarchical

        st.caption(f"Hiển thị {len(filtered)} / {len(chunks_hierarchical)} chunk")
        for chunk in filtered:
            chapter_info = chunk['metadata'].get('chapter', 'Không có')
            article_info = chunk['metadata'].get('article', 'Không có')
            with st.container():
                st.markdown(f"""
                <div class="agri-card">
                    <span class="agri-badge">ID: {chunk['chunk_id']}</span> | <b>Chương:</b> {chapter_info} | <b>Điều:</b> {article_info}
                    <hr style="margin: 10px 0;">
                    <p style="white-space: pre-wrap; font-size: 0.95rem; font-weight: 500;">{chunk['text']}</p>
                </div>
                """, unsafe_allow_html=True)

    # Tab 5: Raw Text
    elif selected_strategy == "Văn bản gốc (Raw Text)":
        st.subheader("📄 Văn bản thô sau khi trích xuất & Chuẩn hóa Unicode NFC")
        st.text_area("Nội dung Raw Text:", raw_data.get("text", ""), height=450)

if __name__ == "__main__":
    main()
