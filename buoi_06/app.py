import streamlit as st
import rag

st.set_page_config(page_title="RAG Workshop - Buổi 06", page_icon="📚", layout="wide")

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

st.markdown(
    '<div class="agri-banner">'
    '<h1>📚 RAG FOUNDATION — DEMO BUỔI 06</h1>'
    '<p>Index dữ liệu vào ChromaDB &amp; Hỏi đáp RAG (Retrieval + Gemini)</p>'
    '</div>',
    unsafe_allow_html=True
)

# --- SIDEBAR: System Status ---
st.sidebar.header("⚙️ Trạng Thái Hệ Thống")

pg_status = rag.check_postgres_status()
st.sidebar.markdown(f"**PostgreSQL:** {pg_status}")

chroma_status_str, chroma_client = rag.check_chroma_status()
st.sidebar.markdown(f"**ChromaDB:** {chroma_status_str}")

gemini_status = rag.check_gemini_status()
if "Có" in gemini_status:
    st.sidebar.success(f"**Gemini API Key:** {gemini_status}")
else:
    st.sidebar.warning(f"**Gemini API Key:** {gemini_status}")

# --- MAIN AREA ---
st.subheader("1. Đánh chỉ mục dữ liệu (Index)")
if st.button("🚀 Thực hiện Index Chunks"):
    with st.spinner("Đang index dữ liệu vào ChromaDB..."):
        success, message = rag.index_chunks(chroma_client)
        if success:
            st.success(message)
        else:
            st.error(message)

st.divider()

st.subheader("2. Hỏi đáp RAG (Retrieval & Answer)")
question = st.text_input("Nhập câu hỏi của bạn:", placeholder="Ví dụ: Quy định về nhận dạng OCR và chunking như thế nào?")
top_k = st.slider("Số lượng chunk truy vấn (Top-K):", min_value=1, max_value=5, value=3)

if st.button("🔍 Gửi câu hỏi") or question:
    if not question.strip():
        st.warning("Vui lòng nhập câu hỏi.")
    else:
        with st.spinner("Đang tìm kiếm thông tin liên quan (Retrieval)..."):
            results = rag.retrieve_top_k(chroma_client, question, top_k=top_k)
        
        st.markdown("### 📋 Kết quả Top-k Retrieval")
        if not results:
            st.info("Không tìm thấy kết quả phù hợp (Hãy đảm bảo bạn đã bấm nút Index).")
        else:
            for idx, res in enumerate(results):
                with st.expander(f"Chunk {idx+1} | ID: {res['id']} | Nguồn: {res['metadata'].get('source', 'N/A')} (Trang {res['metadata'].get('page_start', 1)})", expanded=True):
                    st.write(res['text'])
                    st.caption(f"Strategy: {res['metadata'].get('strategy', 'N/A')}")

        st.markdown("### 💡 Câu trả lời (Answer)")
        api_key = rag.get_env_var("GEMINI_API_KEY")
        
        if not api_key or not api_key.strip():
            st.warning("⚠️ Thiếu GEMINI_API_KEY trong tệp .env. Chỉ hiển thị kết quả Retrieval ở trên, không gọi Gemini.")
        elif results:
            with st.spinner("Đang tổng hợp câu trả lời với Gemini..."):
                answer = rag.generate_answer(api_key, question, results)
                st.info(answer)
