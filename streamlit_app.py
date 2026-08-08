"""
RAG FOUNDATION — Ứng dụng hợp nhất Buổi 05 / 06 / 07
Giao diện theo bộ nhận diện thương hiệu Agribank.
Entry point cho Streamlit Community Cloud.
"""

# --- Patch sqlite3 cho ChromaDB trên Streamlit Cloud (sqlite hệ thống quá cũ) ---
try:
    __import__("pysqlite3")
    import sys as _sys
    _sys.modules["sqlite3"] = _sys.modules.pop("pysqlite3")
except Exception:
    pass

import os
import sys
import json
import importlib.util
from pathlib import Path

import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
IS_CLOUD = Path("/mount/src").exists() or os.environ.get("RAG_CLOUD") == "1"

st.set_page_config(
    page_title="RAG Foundation — Agribank",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
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
}
.stApp { background-color: #FFFFFF; }

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

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, var(--agri-red) 0%, var(--agri-red-dark) 100%);
}
section[data-testid="stSidebar"] * { color: #FFF7EC !important; }
section[data-testid="stSidebar"] hr { border-color: rgba(245,166,35,0.45); }

h2, h3 { color: var(--agri-red) !important; }

.stButton > button {
    background-color: var(--agri-red); color: #FFFFFF;
    border: 1px solid var(--agri-red-dark); border-radius: 8px;
    font-weight: 600; padding: 8px 18px;
}
.stButton > button:hover {
    background-color: var(--agri-gold); color: var(--agri-red-dark);
    border-color: var(--agri-gold);
}

.agri-card {
    background-color: #FFFBF4;
    border: 1px solid #EADFCB;
    border-left: 5px solid var(--agri-red);
    border-radius: 10px; padding: 16px; margin-bottom: 14px;
}

.agri-stat {
    background: linear-gradient(135deg, var(--agri-red) 0%, var(--agri-red-dark) 100%);
    border-bottom: 3px solid var(--agri-gold);
    border-radius: 10px; padding: 16px; text-align: center; color: #FFFFFF;
}
.agri-stat h4 { color: var(--agri-gold) !important; margin: 0 0 8px 0; }
.agri-stat p { color: #FFFFFF; margin: 2px 0; }

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

.stTextInput input, .stTextArea textarea { border: 1px solid #D8C7A8 !important; }
div[data-testid="stExpander"] { border: 1px solid #EADFCB !important; border-radius: 8px; }
</style>
"""
st.markdown(AGRIBANK_CSS, unsafe_allow_html=True)


# ------------------------------------------------------------
# Nạp cấu hình từ Streamlit Secrets sang biến môi trường
# ------------------------------------------------------------
SECRET_KEYS = (
    "GEMINI_API_KEY",
    "GEMINI_EMBEDDING_MODEL",
    "GEMINI_EMBEDDING_DIM",
    "GEMINI_GENERATION_MODEL",
    "DEFAULT_TOP_K",
    "RAG_MAX_DISTANCE",
)


def bootstrap_secrets() -> None:
    for key in SECRET_KEYS:
        try:
            value = st.secrets.get(key, "")
        except Exception:
            value = ""
        if value:
            os.environ[key] = str(value)


bootstrap_secrets()


@st.cache_resource(show_spinner=False)
def load_module(alias: str, relative_path: str):
    """Nạp rag.py của từng buổi dưới tên module riêng để tránh trùng tên."""
    path = BASE_DIR / relative_path
    spec = importlib.util.spec_from_file_location(alias, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[alias] = module
    spec.loader.exec_module(module)
    return module


def banner(title: str, subtitle: str) -> None:
    st.markdown(
        f'<div class="agri-banner"><h1>{title}</h1><p>{subtitle}</p></div>',
        unsafe_allow_html=True,
    )


# ============================================================
# BUỔI 05 — OCR & Chunking Visualizer
# ============================================================
def load_json_file(file_name: str):
    for candidate in (
        BASE_DIR / "buoi_05" / "output" / file_name,
        BASE_DIR / "buoi_05" / "output" / "chunks" / file_name,
    ):
        if candidate.exists():
            with open(candidate, "r", encoding="utf-8") as f:
                return json.load(f)
    return None


def render_buoi_05() -> None:
    banner(
        "📚 TRỰC QUAN HÓA RAG FOUNDATION — BUỔI 05",
        "Phân tích kết quả OCR &amp; So sánh 3 Chiến lược Chunking (Fixed-size, Semantic, Hierarchical)",
    )

    raw_data = load_json_file("raw_text.json")
    chunks_fixed = load_json_file("chunks_fixed.json") or []
    chunks_semantic = load_json_file("chunks_semantic.json") or []
    chunks_hierarchical = load_json_file("chunks_hierarchical.json") or []

    if not raw_data:
        st.warning("⚠️ Chưa tìm thấy dữ liệu trong thư mục `buoi_05/output/`.")
        return

    st.sidebar.divider()
    st.sidebar.markdown(f"**Tập tin xử lý:** `{raw_data.get('source', 'N/A')}`")
    st.sidebar.markdown(
        f"**OCR LlamaParse:** `{'Có' if raw_data.get('ocr_used') else 'Không (PyMuPDF Text Layer)'}`"
    )
    st.sidebar.markdown(f"**Tổng số trang:** `{raw_data.get('total_pages', 1)}`")

    selected = st.sidebar.radio(
        "Chọn chiến lược để xem chi tiết:",
        [
            "So sánh tổng quan",
            "Fixed-size Chunking",
            "Semantic Chunking",
            "Hierarchical Chunking",
            "Văn bản gốc (Raw Text)",
        ],
    )
    search_kw = st.sidebar.text_input("🔍 Tìm kiếm từ khóa trong Chunk:", "")

    def avg_len(items):
        return round(sum(len(c["text"]) for c in items) / len(items), 1) if items else 0

    if selected == "So sánh tổng quan":
        st.subheader("📊 Báo cáo so sánh 3 Chiến lược Chunking")
        cols = st.columns(3)
        for col, name, items in zip(
            cols,
            ["Fixed-size", "Semantic", "Hierarchical"],
            [chunks_fixed, chunks_semantic, chunks_hierarchical],
        ):
            with col:
                st.markdown(
                    f"""
                    <div class="agri-stat">
                        <h4>{name}</h4>
                        <p><b>Số Chunk:</b> {len(items)}</p>
                        <p><b>Độ dài trung bình:</b> {avg_len(items)} ký tự</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        st.markdown("---")
        st.subheader("💡 Đặc điểm từng chiến lược")
        st.markdown(
            "- **Fixed-size:** Cắt văn bản theo kích thước ký tự/token cố định kèm overlap. "
            "Đơn giản, đồng đều nhưng có thể làm đứt đoạn câu/ngữ nghĩa.\n"
            "- **Semantic:** Ưu tiên ngắt theo đoạn văn hoặc dấu kết thúc câu. "
            "Giữ trọn vẹn ngữ nghĩa của từng khối thông tin.\n"
            "- **Hierarchical:** Phân chia dựa vào mốc cấu trúc pháp lý (Chương, Mục, Điều, Khoản). "
            "Thích hợp nhất cho tài liệu luật, hợp đồng, văn bản có tiêu đề rõ ràng."
        )
        return

    if selected == "Văn bản gốc (Raw Text)":
        st.subheader("📄 Văn bản thô sau khi trích xuất & Chuẩn hóa Unicode NFC")
        st.text_area("Nội dung Raw Text:", raw_data.get("text", ""), height=450)
        return

    mapping = {
        "Fixed-size Chunking": ("📏 Danh sách Chunks: Fixed-size", chunks_fixed, "agri-badge"),
        "Semantic Chunking": ("🧠 Danh sách Chunks: Semantic", chunks_semantic, "agri-badge-gold"),
        "Hierarchical Chunking": ("🏛️ Danh sách Chunks: Hierarchical", chunks_hierarchical, "agri-badge"),
    }
    title, source, badge = mapping[selected]
    st.subheader(title)
    filtered = [c for c in source if search_kw.lower() in c["text"].lower()] if search_kw else source
    st.caption(f"Hiển thị {len(filtered)} / {len(source)} chunk")
    for chunk in filtered:
        meta = chunk.get("metadata", {})
        extra = ""
        if selected == "Semantic Chunking":
            extra = f" | <b>Nguyên nhân ngắt:</b> {meta.get('split_reason', 'N/A')}"
        elif selected == "Hierarchical Chunking":
            extra = f" | <b>Chương:</b> {meta.get('chapter', 'Không có')} | <b>Điều:</b> {meta.get('article', 'Không có')}"
        else:
            extra = f" | <b>Trang:</b> {chunk.get('page_start', 1)}"
        st.markdown(
            f"""
            <div class="agri-card">
                <span class="{badge}">ID: {chunk['chunk_id']}</span>
                | <b>Độ dài:</b> {meta.get('char_count', len(chunk['text']))} ký tự{extra}
                <hr style="margin: 10px 0;">
                <p style="white-space: pre-wrap; font-size: 0.95rem;">{chunk['text']}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================
# BUỔI 06 — Index ChromaDB & Hỏi đáp RAG
# ============================================================
def render_buoi_06() -> None:
    banner(
        "📚 RAG FOUNDATION — DEMO BUỔI 06",
        "Index dữ liệu vào ChromaDB &amp; Hỏi đáp RAG (Retrieval + Gemini)",
    )
    rag = load_module("rag06", "buoi_06/rag.py")

    st.sidebar.divider()
    st.sidebar.subheader("⚙️ Trạng thái hệ thống")

    if not IS_CLOUD:
        st.sidebar.markdown(f"**PostgreSQL:** {rag.check_postgres_status()}")

    chroma_status_str, chroma_client = rag.check_chroma_status()
    st.sidebar.markdown(f"**ChromaDB:** {chroma_status_str}")

    gemini_status = rag.check_gemini_status()
    if "Có" in gemini_status:
        st.sidebar.success(f"**Gemini API Key:** {gemini_status}")
    else:
        st.sidebar.warning(f"**Gemini API Key:** {gemini_status}")

    st.subheader("1. Đánh chỉ mục dữ liệu (Index)")
    st.caption("Bộ chỉ mục mẫu đã có sẵn trong repo — chỉ bấm khi muốn tạo lại.")
    if st.button("🚀 Thực hiện Index Chunks"):
        with st.spinner("Đang index dữ liệu vào ChromaDB..."):
            success, message = rag.index_chunks(chroma_client)
        (st.success if success else st.error)(message)

    st.divider()
    st.subheader("2. Hỏi đáp RAG (Retrieval & Answer)")
    question = st.text_input(
        "Nhập câu hỏi của bạn:",
        placeholder="Ví dụ: Quy định về nhận dạng OCR và chunking như thế nào?",
    )
    top_k = st.slider("Số lượng chunk truy vấn (Top-K):", 1, 5, 3)

    if not question.strip():
        return

    with st.spinner("Đang tìm kiếm thông tin liên quan (Retrieval)..."):
        results = rag.retrieve_top_k(chroma_client, question, top_k=top_k)

    st.markdown("### 📋 Kết quả Top-k Retrieval")
    if not results:
        st.info("Không tìm thấy kết quả phù hợp (hãy thử bấm nút Index ở trên).")
    else:
        for idx, res in enumerate(results):
            meta = res.get("metadata", {})
            label = f"Chunk {idx + 1} | ID: {res['id']} | Nguồn: {meta.get('source', 'N/A')} (Trang {meta.get('page_start', 1)})"
            with st.expander(label, expanded=True):
                st.write(res["text"])
                st.caption(f"Strategy: {meta.get('strategy', 'N/A')}")

    st.markdown("### 💡 Câu trả lời (Answer)")
    api_key = rag.get_env_var("GEMINI_API_KEY")
    if not api_key or not api_key.strip():
        st.warning(
            "⚠️ Chưa cấu hình GEMINI_API_KEY. Chỉ hiển thị kết quả Retrieval ở trên, không gọi Gemini."
        )
    elif results:
        with st.spinner("Đang tổng hợp câu trả lời với Gemini..."):
            st.info(rag.generate_answer(api_key, question, results))


# ============================================================
# BUỔI 07 — RAG Pipeline System
# ============================================================
def render_buoi_07() -> None:
    banner(
        "📚 RAG PIPELINE SYSTEM — BUỔI 07",
        "Hỏi đáp RAG với Semantic Retrieval, Confidence Gate &amp; Citation Mapping",
    )
    rag = load_module("rag07", "buoi_07/rag.py")

    try:
        config = rag.get_config()
    except Exception as e:
        st.error(f"Lỗi đọc cấu hình: {e}")
        return

    st.sidebar.divider()
    st.sidebar.subheader("⚙️ Cấu hình & Trạng thái")
    if config["API_KEY_PRESENT"]:
        st.sidebar.success("🔑 GEMINI_API_KEY: Có")
    else:
        st.sidebar.error("🔑 GEMINI_API_KEY: Thiếu")

    strategy = st.sidebar.selectbox(
        "Chiến lược Chunking (Strategy):",
        ["hierarchical", "semantic", "fixed-size"],
    )
    top_k = st.sidebar.slider("Số lượng evidence (Top-K):", 1, 10, int(config["DEFAULT_TOP_K"]))

    st.sidebar.divider()
    st.sidebar.text(f"• Embedding: {config['GEMINI_EMBEDDING_MODEL']}")
    st.sidebar.text(f"• Dim: {config['GEMINI_EMBEDDING_DIM']}")
    st.sidebar.text(f"• Generation: {config['GEMINI_GENERATION_MODEL']}")
    st.sidebar.text(f"• Max Distance: {config['RAG_MAX_DISTANCE']}")

    try:
        status_info = rag.run_status(strategy=strategy)
    except Exception as e:
        st.sidebar.error(f"Lỗi đọc status: {e}")
        status_info = {"collection_name": "Lỗi", "exists": False, "record_count": 0}

    st.sidebar.divider()
    st.sidebar.subheader("🗄️ Trạng thái ChromaDB")
    st.sidebar.text(f"Collection: {status_info['collection_name']}")
    if status_info["exists"]:
        st.sidebar.success(f"Đã tồn tại ({status_info['record_count']} records)")
    else:
        st.sidebar.warning("Chưa tồn tại (0 records)")

    st.subheader("📥 1. Lập chỉ mục dữ liệu (Indexing)")
    with st.expander("Quản lý Index & Vector Collection", expanded=not status_info["exists"]):
        if IS_CLOUD:
            st.caption(
                "Lưu ý: bộ nhớ trên Streamlit Cloud là tạm thời — chỉ mục sẽ mất khi app khởi động lại."
            )
        reset_option = st.checkbox("Reset collection trước khi index")
        if st.button("🚀 Index dữ liệu"):
            if not config["API_KEY_PRESENT"]:
                st.error("Không thể index: thiếu GEMINI_API_KEY.")
            else:
                with st.spinner(f"Đang sinh embedding cho strategy '{strategy}'..."):
                    try:
                        res = rag.run_index(
                            input_dir=rag.DEFAULT_INPUT_DIR,
                            strategy=strategy,
                            reset=reset_option,
                        )
                        st.success(
                            f"Indexing hoàn tất — {res['indexed_chunks']} chunks, "
                            f"tổng {res['total_records']} records."
                        )
                        st.rerun()
                    except Exception as ex:
                        st.error(f"Lỗi trong quá trình index: {ex}")

    st.divider()
    st.subheader("💬 2. Hỏi đáp với tài liệu (RAG Query)")
    question_input = st.text_area(
        "Nhập câu hỏi của bạn (tối đa 2000 ký tự):",
        placeholder="Ví dụ: Quy định về quy trình và lãi suất như thế nào?",
        height=100,
    )

    if not st.button("🔍 Gửi câu hỏi", type="primary"):
        return
    if not question_input.strip():
        st.warning("Vui lòng nhập nội dung câu hỏi trước khi gửi.")
        return
    if not config["API_KEY_PRESENT"]:
        st.error("Không thể truy vấn: thiếu GEMINI_API_KEY.")
        return

    with st.spinner("Đang truy xuất và tổng hợp câu trả lời..."):
        try:
            q_res = rag.run_query(question=question_input.strip(), strategy=strategy, top_k=top_k)
        except Exception as ex:
            st.error(f"Lỗi truy vấn: {ex}")
            return

    st.markdown("### 📋 Kết quả")
    st.markdown("#### 💡 Câu trả lời:")
    st.markdown(q_res.get("answer", ""))

    citations = q_res.get("citations") or []
    if citations:
        st.markdown("#### 📌 Trích dẫn nguồn (Citations):")
        for c in citations:
            st.markdown(f"- **{c['evidence_id']}**: `{c['display']}`")

    warnings = q_res.get("warnings") or []
    if warnings:
        st.markdown("#### ⚠️ Cảnh báo:")
        for w in warnings:
            st.warning(w)

    evidences = q_res.get("evidence") or []
    if evidences:
        st.markdown("### 📄 Nguồn tham khảo")
        for ev in evidences:
            with st.expander(f"{ev.get('evidence_id', '')} — khoảng cách {ev.get('distance', 0):.4f}"):
                st.markdown("**Nội dung Chunk:**")
                st.write(ev.get("text", ""))


# ============================================================
# ĐIỀU HƯỚNG
# ============================================================
PAGES = {
    "Buổi 05 — OCR & Chunking": render_buoi_05,
    "Buổi 06 — Index & Hỏi đáp": render_buoi_06,
    "Buổi 07 — RAG Pipeline": render_buoi_07,
}

st.sidebar.markdown("### 📚 RAG Foundation")
choice = st.sidebar.radio("Chọn buổi thực hành:", list(PAGES.keys()))
PAGES[choice]()

st.sidebar.divider()
st.sidebar.caption("Giao diện theo tông màu thương hiệu Agribank")
