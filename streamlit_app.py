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
from typing import Any, Dict, Tuple

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
section[data-testid="stSidebar"] input {
    background-color: #FFFFFF !important;
    color: #3A0D1C !important;
}

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


# ============================================================
# QUẢN LÝ GEMINI_API_KEY NGAY TRÊN GIAO DIỆN
# ------------------------------------------------------------
# Nguyên tắc bảo mật:
#   - Khóa do người dùng nhập chỉ nằm trong st.session_state (theo từng phiên
#     trình duyệt), KHÔNG ghi vào os.environ (biến môi trường dùng chung cho cả
#     tiến trình -> sẽ rò rỉ sang phiên của người dùng khác trên Streamlit Cloud),
#     KHÔNG ghi ra file .env, KHÔNG commit lên GitHub.
#   - Khóa được truyền xuống module rag của Buổi 06/07 qua tham số hàm.
# ============================================================
KEY_STATE = "gemini_api_key"
KEY_CHECK_STATE = "gemini_api_key_check"
NONCE_STATE = "gemini_key_nonce"
EMB_MODEL_STATE = "gemini_embedding_model_input"
GEN_MODEL_STATE = "gemini_generation_model_input"


def get_api_key() -> str:
    """Khóa đang hiệu lực: ưu tiên khóa người dùng nhập, sau đó tới Secrets/ENV."""
    session_key = str(st.session_state.get(KEY_STATE, "") or "").strip()
    if session_key:
        return session_key
    return os.environ.get("GEMINI_API_KEY", "").strip()


def get_key_source() -> str:
    if str(st.session_state.get(KEY_STATE, "") or "").strip():
        return "Người dùng nhập trong phiên này"
    if os.environ.get("GEMINI_API_KEY", "").strip():
        return "Streamlit Secrets / biến môi trường"
    return "Chưa có"


def mask_key(key: str) -> str:
    if not key:
        return ""
    if len(key) <= 8:
        return "•" * len(key)
    return f"{key[:4]}{'•' * 8}{key[-4:]}"


def verify_api_key(key: str) -> Tuple[bool, str]:
    """Gọi thử Gemini API để xác thực khóa. Trả về (hợp_lệ, thông_điệp)."""
    if not key:
        return False, "Chưa có khóa để kiểm tra."
    try:
        from google import genai
    except Exception as e:
        return False, f"Chưa cài đặt thư viện google-genai: {e}"

    try:
        client = genai.Client(api_key=key)
        try:
            next(iter(client.models.list()), None)
        except AttributeError:
            client.models.generate_content(model="gemini-2.5-flash", contents="ping")
        return True, "Khóa hợp lệ — đã kết nối được Gemini API."
    except Exception as e:
        return False, f"Khóa không dùng được: {str(e).replace(key, '***')[:400]}"


def render_api_key_panel() -> None:
    """Ô nhập + các nút thao tác GEMINI_API_KEY trên sidebar."""
    st.sidebar.divider()
    active_key = get_api_key()

    with st.sidebar.expander("🔑 Cấu hình GEMINI_API_KEY", expanded=not bool(active_key)):
        st.caption(
            "Khóa chỉ lưu tạm trong phiên trình duyệt của bạn: không ghi ra file, "
            "không commit lên GitHub, tự mất khi đóng/tải lại trang."
        )

        nonce = st.session_state.setdefault(NONCE_STATE, 0)
        input_widget_key = f"gemini_api_key_input_{nonce}"
        st.text_input(
            "Dán GEMINI_API_KEY vào đây",
            key=input_widget_key,
            type="password",
            placeholder="AIza...",
            help="Lấy khóa miễn phí tại Google AI Studio: https://aistudio.google.com/app/apikey",
        )
        typed_key = str(st.session_state.get(input_widget_key, "") or "").strip()

        col_save, col_test, col_clear = st.columns(3)
        save_clicked = col_save.button("💾 Lưu", use_container_width=True, key="btn_save_key")
        test_clicked = col_test.button("🔍 Kiểm tra", use_container_width=True, key="btn_test_key")
        clear_clicked = col_clear.button("🗑️ Xóa", use_container_width=True, key="btn_clear_key")

        if clear_clicked:
            st.session_state.pop(KEY_STATE, None)
            st.session_state[KEY_CHECK_STATE] = None
            st.session_state[NONCE_STATE] = nonce + 1
            st.rerun()

        if save_clicked:
            if not typed_key:
                st.error("Chưa nhập khóa.")
            else:
                st.session_state[KEY_STATE] = typed_key
                st.session_state[KEY_CHECK_STATE] = None
                st.success("Đã lưu khóa cho phiên làm việc này.")
                active_key = typed_key

        if test_clicked:
            candidate = typed_key or get_api_key()
            if not candidate:
                st.error("Chưa có khóa để kiểm tra.")
            else:
                with st.spinner("Đang gọi thử Gemini API..."):
                    st.session_state[KEY_CHECK_STATE] = verify_api_key(candidate)

        check_result = st.session_state.get(KEY_CHECK_STATE)
        if check_result:
            ok, message = check_result
            (st.success if ok else st.error)(message)

        st.markdown(
            "[→ Lấy API key tại Google AI Studio](https://aistudio.google.com/app/apikey)"
        )

        st.divider()
        st.caption("Tùy chọn nâng cao — để trống nếu dùng cấu hình mặc định (áp dụng cho Buổi 07)")
        st.text_input(
            "GEMINI_EMBEDDING_MODEL",
            key=EMB_MODEL_STATE,
            placeholder=os.environ.get("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001"),
        )
        st.text_input(
            "GEMINI_GENERATION_MODEL",
            key=GEN_MODEL_STATE,
            placeholder=os.environ.get("GEMINI_GENERATION_MODEL", "gemini-2.5-flash"),
        )

    active_key = get_api_key()
    if active_key:
        st.sidebar.success(f"🔑 GEMINI_API_KEY: {mask_key(active_key)}")
        st.sidebar.caption(f"Nguồn: {get_key_source()}")
    else:
        st.sidebar.error("🔑 GEMINI_API_KEY: Chưa cấu hình")
        st.sidebar.caption("Mở mục 🔑 phía trên để nhập khóa rồi bấm 💾 Lưu.")


def apply_runtime_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Ghi đè config của rag.py bằng khóa/model người dùng nhập trên giao diện."""
    api_key = get_api_key()
    if api_key:
        config["GEMINI_API_KEY"] = api_key
        config["API_KEY_PRESENT"] = True

    emb_model = str(st.session_state.get(EMB_MODEL_STATE, "") or "").strip()
    gen_model = str(st.session_state.get(GEN_MODEL_STATE, "") or "").strip()
    if emb_model:
        config["GEMINI_EMBEDDING_MODEL"] = emb_model
    if gen_model:
        config["GEMINI_GENERATION_MODEL"] = gen_model
    return config


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

    api_key = get_api_key()
    if api_key:
        st.sidebar.success("**Gemini API Key:** Có (Valid)")
    else:
        st.sidebar.warning("**Gemini API Key:** Thiếu — nhập tại mục 🔑 trên sidebar")

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
    if not api_key:
        st.warning(
            "⚠️ Chưa cấu hình GEMINI_API_KEY. Chỉ hiển thị kết quả Retrieval ở trên, không gọi Gemini. "
            "Hãy nhập khóa tại mục 🔑 Cấu hình GEMINI_API_KEY trên sidebar rồi bấm 💾 Lưu."
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
        config = apply_runtime_config(rag.get_config())
    except Exception as e:
        st.error(f"Lỗi đọc cấu hình: {e}")
        return

    st.sidebar.divider()
    st.sidebar.subheader("⚙️ Cấu hình & Trạng thái")
    if config["API_KEY_PRESENT"]:
        st.sidebar.success("🔑 GEMINI_API_KEY: Có")
    else:
        st.sidebar.error("🔑 GEMINI_API_KEY: Thiếu — nhập tại mục 🔑 trên sidebar")

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
        status_info = rag.run_status(strategy=strategy, config=config)
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
                st.error("Không thể index: thiếu GEMINI_API_KEY. Nhập khóa tại mục 🔑 trên sidebar.")
            else:
                with st.spinner(f"Đang sinh embedding cho strategy '{strategy}'..."):
                    try:
                        res = rag.run_index(
                            input_dir=rag.DEFAULT_INPUT_DIR,
                            strategy=strategy,
                            reset=reset_option,
                            config=config,
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
        st.error("Không thể truy vấn: thiếu GEMINI_API_KEY. Nhập khóa tại mục 🔑 trên sidebar.")
        return

    with st.spinner("Đang truy xuất và tổng hợp câu trả lời..."):
        try:
            q_res = rag.run_query(
                question=question_input.strip(),
                strategy=strategy,
                top_k=top_k,
                config=config,
            )
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

# Ô nhập GEMINI_API_KEY hiển thị ở mọi trang
render_api_key_panel()

PAGES[choice]()

st.sidebar.divider()
st.sidebar.caption("Giao diện theo tông màu thương hiệu Agribank")
