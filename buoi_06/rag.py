import os
import json
import dotenv

dotenv.load_dotenv()

def get_env_var(key, default=""):
    return os.getenv(key, default)

def get_psycopg():
    try:
        import psycopg
        return psycopg
    except ImportError:
        try:
            import psycopg2
            return psycopg2
        except ImportError:
            return None

def check_postgres_status():
    host = get_env_var("POSTGRES_HOST", "localhost")
    port = get_env_var("POSTGRES_PORT", "5432")
    db = get_env_var("POSTGRES_DB", "rag_db")
    user = get_env_var("POSTGRES_USER", "postgres")
    password = get_env_var("POSTGRES_PASSWORD", "")
    
    psycopg_mod = get_psycopg()
    if not psycopg_mod:
        return "Lỗi: Chưa cài đặt module psycopg / psycopg2"

    try:
        # 1. Try connecting directly to rag_db
        conn = psycopg_mod.connect(
            f"host={host} port={port} dbname={db} user={user} password={password}",
            connect_timeout=3
        )
        conn.close()
        return f"Kết nối thành công ({db})"
    except Exception as e:
        try:
            # 2. If rag_db doesn't exist, connect to default DB 'postgres' and auto-create rag_db
            conn = psycopg_mod.connect(
                f"host={host} port={port} dbname=postgres user={user} password={password}",
                autocommit=True,
                connect_timeout=3
            )
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db,))
            if not cursor.fetchone():
                cursor.execute(f'CREATE DATABASE "{db}"')
            cursor.close()
            conn.close()
            return f"Kết nối PostgreSQL thành công (Đã tự động tạo DB '{db}')"
        except Exception as err:
            return f"Không kết nối được: {str(err)}"

def check_chroma_status():
    try:
        import chromadb
        try:
            client = chromadb.HttpClient(host="localhost", port=8000)
            client.heartbeat()
            return "Server (localhost:8000)", client
        except Exception:
            storage_path = os.path.join(os.path.dirname(__file__), "storage", "chroma")
            client = chromadb.PersistentClient(path=storage_path)
            return "Embedded Local (storage/chroma/)", client
    except Exception as e:
        return f"Lỗi ChromaDB: {str(e)}", None

def check_gemini_status():
    key = get_env_var("GEMINI_API_KEY")
    if key and key.strip():
        return "Có (Valid)"
    return "Thiếu (Missing)"

def index_chunks(client):
    if not client:
        return False, "ChromaDB client chưa sẵn sàng."
    
    try:
        collection = client.get_or_create_collection(name="rag_chunks")
        
        current_dir = os.path.dirname(__file__)
        output_dir = os.path.abspath(os.path.join(current_dir, "../buoi_05/output"))
        if not os.path.exists(output_dir):
            output_dir = os.path.abspath("RAG/rag_foundation/buoi_05/output")
        
        if not os.path.exists(output_dir):
            return False, f"Không tìm thấy thư mục chunks: {output_dir}"
        
        total_indexed = 0
        for fname in os.listdir(output_dir):
            if fname.startswith("chunks_") and fname.endswith(".json"):
                fpath = os.path.join(output_dir, fname)
                with open(fpath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        ids, documents, metadatas = [], [], []
                        for idx, item in enumerate(data):
                            cid = str(item.get("chunk_id", f"{fname}_{idx}"))
                            txt = item.get("text", "")
                            if txt:
                                ids.append(cid)
                                documents.append(txt)
                                metadatas.append({
                                    "source": str(item.get("source", "")),
                                    "strategy": str(item.get("strategy", "")),
                                    "page_start": int(item.get("page_start", 1))
                                })
                        if ids:
                            collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
                            total_indexed += len(ids)
                            
        return True, f"Đã index thành công {total_indexed} chunks vào ChromaDB!"
    except Exception as e:
        return False, f"Lỗi khi index: {str(e)}"

def retrieve_top_k(client, query, top_k=3):
    if not client or not query.strip():
        return []
    try:
        collection = client.get_collection(name="rag_chunks")
        results = collection.query(query_texts=[query], n_results=top_k)
        
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        ids = results.get("ids", [[]])[0]
        
        items = []
        for i in range(len(docs)):
            items.append({
                "id": ids[i],
                "text": docs[i],
                "metadata": metas[i] if i < len(metas) else {}
            })
        return items
    except Exception:
        return []

def generate_answer(api_key, query, retrieved_docs):
    if not api_key or not api_key.strip():
        return "Thiếu GEMINI_API_KEY trong .env. Chỉ hiển thị kết quả Retrieval."
    
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        
        context_parts = []
        for i, doc in enumerate(retrieved_docs):
            source = doc['metadata'].get('source', 'Unknown')
            page = doc['metadata'].get('page_start', 1)
            context_parts.append(f"--- Chunk {i+1} (Nguồn: {source}, Trang {page}) ---\n{doc['text']}")
        
        context = "\n\n".join(context_parts)
        prompt = f"""Bạn là trợ lý AI. Hãy dựa vào thông tin ngữ cảnh dưới đây để trả lời câu hỏi của người dùng. Nếu ngữ cảnh không chứa thông tin để trả lời, hãy nêu rõ là không tìm thấy thông tin.

[Ngữ cảnh]:
{context}

[Câu hỏi]:
{query}

[Trả lời]:"""
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"Lỗi khi gọi Gemini API: {str(e)}"
