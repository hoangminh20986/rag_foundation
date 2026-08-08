import streamlit as st
import rag

st.set_page_config(page_title="RAG Workshop - Buổi 06", layout="wide")

st.title("📚 RAG Foundation - Demo Buổi 06")

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
