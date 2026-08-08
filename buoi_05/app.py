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

# Custom CSS cho giao diện hiện đại & chỉn chu
st.markdown("""
    <style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E293B;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #64748B;
        text-align: center;
        margin-bottom: 2rem;
    }
    .chunk-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 18px;
        margin-bottom: 16px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    .badge-fixed {
        background-color: #DBEAFE;
        color: #1E40AF;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    .badge-semantic {
        background-color: #DCFCE7;
        color: #166534;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    .badge-hierarchical {
        background-color: #F3E8FF;
        color: #6B21A8;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    .stat-box {
        background: linear-gradient(135deg, #F1F5F9 0%, #E2E8F0 100%);
        padding: 15px;
        border-radius: 8px;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

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
    st.markdown('<div class="main-header">📚 TRỰC QUAN HÓA RAG FOUNDATION — BUỔI 05</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Phân tích kết quả OCR & So sánh 3 Chiến lược Chunking (Fixed-size, Semantic, Hierarchical)</div>', unsafe_allow_html=True)

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
            <div class="stat-box">
                <h4>Fixed-size</h4>
                <p><b>Số Chunk:</b> {len(chunks_fixed)}</p>
                <p><b>Độ dài trung bình:</b> {round(sum(len(c['text']) for c in chunks_fixed)/len(chunks_fixed), 1) if chunks_fixed else 0} ký tự</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="stat-box">
                <h4>Semantic</h4>
                <p><b>Số Chunk:</b> {len(chunks_semantic)}</p>
                <p><b>Độ dài trung bình:</b> {round(sum(len(c['text']) for c in chunks_semantic)/len(chunks_semantic), 1) if chunks_semantic else 0} ký tự</p>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div class="stat-box">
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
                <div class="chunk-card">
                    <span class="badge-fixed">ID: {chunk['chunk_id']}</span> | <b>Độ dài:</b> {chunk['metadata'].get('char_count', len(chunk['text']))} ký tự | <b>Trang:</b> {chunk['page_start']}
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
                <div class="chunk-card">
                    <span class="badge-semantic">ID: {chunk['chunk_id']}</span> | <b>Nguyên nhân ngắt:</b> {chunk['metadata'].get('split_reason', 'N/A')} | <b>Độ dài:</b> {chunk['metadata'].get('char_count', len(chunk['text']))} ký tự
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
                <div class="chunk-card">
                    <span class="badge-hierarchical">ID: {chunk['chunk_id']}</span> | <b>Chương:</b> {chapter_info} | <b>Điều:</b> {article_info}
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
