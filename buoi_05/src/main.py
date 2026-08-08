"""
Pipeline chính thực thi Buổi 05 - RAG Foundation: OCR & Chunking Strategies
Hỗ trợ tham số CLI: --write (để lưu file vào output/), mặc định là Dry-run.
"""

import sys
import json
import os
import argparse
import asyncio
from pathlib import Path
from typing import Dict, Any

# Nạp các module tự định nghĩa
CURRENT_DIR = Path(__file__).parent.resolve()
BUOI_05_DIR = CURRENT_DIR.parent.resolve()
DATADEMO_DIR = BUOI_05_DIR / "datademo"
OUTPUT_DIR = BUOI_05_DIR / "output"
ENV_FILE = CURRENT_DIR / ".env"

sys.path.append(str(CURRENT_DIR))

from ocr_pipeline import extract_pdf_content
from chunking import (
    chunk_fixed_size,
    chunk_semantic,
    chunk_hierarchical,
    calculate_stats
)

# Nạp .env an toàn
def load_api_key() -> str:
    if ENV_FILE.exists():
        try:
            from dotenv import load_dotenv
            load_dotenv(dotenv_path=ENV_FILE, override=True)
            key = os.getenv("LLAMA_CLOUD_API_KEY", "")
            return key if key != "KEY_CUA_BAN" else ""
        except ImportError:
            pass
    return ""

async def run_pipeline(write_mode: bool = False):
    print("=" * 75)
    print("      RAG FOUNDATION (BUỔI 05) - OCR & CHUNKING STRATEGIES DEMO")
    print("=" * 75)
    print(f"[*] Chế độ thực thi: {'WRITE (--write)' if write_mode else 'DRY-RUN (Mặc định)'}")
    
    api_key = load_api_key()
    if not api_key:
        print("⚠️ [CẢNH BÁO]: Không tìm thấy LLAMA_CLOUD_API_KEY hợp lệ trong .env.")
        print("   Các PDF có Text Layer chuẩn vẫn sẽ được trích xuất bằng PyMuPDF.")
        print("   Nếu gặp trang bị lỗi font/scan, OCR LlamaParse sẽ báo thiếu API Key.")

    # Tìm danh sách PDF trong datademo
    pdf_files = list(DATADEMO_DIR.glob("*.pdf"))
    if not pdf_files:
        print(f"❌ [LỖI]: Không tìm thấy file PDF nào trong thư mục {DATADEMO_DIR}")
        return

    print(f"[*] Tìm thấy {len(pdf_files)} file PDF trong datademo/: {[f.name for f in pdf_files]}")

    for pdf_file in pdf_files:
        try:
            # 1. Trích xuất text (PyMuPDF hoặc OCR Fallback)
            doc_data = await extract_pdf_content(pdf_file, api_key=api_key)
            source_name = doc_data["source"]
            text_content = doc_data["text"]

            print(f"\n---> Phân đoạn văn bản cho file '{source_name}' ({len(text_content)} ký tự):")

            # 2. Thực hiện 3 chiến lược chunking
            chunks_fixed = chunk_fixed_size(text_content, source_name, chunk_size=300, overlap=50)
            chunks_semantic = chunk_semantic(text_content, source_name, target_size=350)
            chunks_hierarchical = chunk_hierarchical(text_content, source_name)

            # 3. Tính toán thống kê
            stats_fixed = calculate_stats(chunks_fixed)
            stats_semantic = calculate_stats(chunks_semantic)
            stats_hierarchical = calculate_stats(chunks_hierarchical)

            # 4. In bảng kết quả thống kê
            print("\n" + "-" * 75)
            print(" BÁO CÁO THỐNG KÊ CHIẾN LƯỢC CHUNKING")
            print("-" * 75)
            print(f"{'Chiến lược':<18} | {'Số Chunk':<10} | {'Độ dài Min':<10} | {'Độ dài Max':<10} | {'Độ dài Trung Bình'}")
            print("-" * 75)
            print(f"{'Fixed-size':<18} | {stats_fixed['total_chunks']:<10} | {stats_fixed['min_len']:<10} | {stats_fixed['max_len']:<10} | {stats_fixed['avg_len']}")
            print(f"{'Semantic':<18} | {stats_semantic['total_chunks']:<10} | {stats_semantic['min_len']:<10} | {stats_semantic['max_len']:<10} | {stats_semantic['avg_len']}")
            print(f"{'Hierarchical':<18} | {stats_hierarchical['total_chunks']:<10} | {stats_hierarchical['min_len']:<10} | {stats_hierarchical['max_len']:<10} | {stats_hierarchical['avg_len']}")
            print("-" * 75)

            # 5. In ví dụ Metadata của 1 chunk đại diện
            if chunks_hierarchical:
                sample_chunk = chunks_hierarchical[0]
                print("\n[VÍ DỤ CHUNK METADATA (Hierarchical)]:")
                print(json.dumps(sample_chunk, ensure_ascii=False, indent=2))

            # 6. Ghi file nếu ở chế độ --write
            if write_mode:
                OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
                
                # Ghi Raw Text
                with open(OUTPUT_DIR / "raw_text.json", "w", encoding="utf-8") as f:
                    json.dump(doc_data, f, ensure_ascii=False, indent=2)

                # Ghi các tập chunks
                with open(OUTPUT_DIR / "chunks_fixed.json", "w", encoding="utf-8") as f:
                    json.dump(chunks_fixed, f, ensure_ascii=False, indent=2)

                with open(OUTPUT_DIR / "chunks_semantic.json", "w", encoding="utf-8") as f:
                    json.dump(chunks_semantic, f, ensure_ascii=False, indent=2)

                with open(OUTPUT_DIR / "chunks_hierarchical.json", "w", encoding="utf-8") as f:
                    json.dump(chunks_hierarchical, f, ensure_ascii=False, indent=2)

                print(f"\n✅ ĐÃ GHI KẾT QUẢ VÀO THƯ MỤC: {OUTPUT_DIR}")

        except Exception as exc:
            print(f"❌ [LỖI TRONG QUÁ TRÌNH XỬ LÝ {pdf_file.name}]: {exc}")
            continue

    if not write_mode:
        print("\n💡 [GHI CHÚ DRY-RUN]: Đây là chế độ chạy thử không ghi file.")
        print("   Để ghi kết quả ra thư mục output/, hãy chạy lệnh với tham số: --write")
    
    print("\n" + "=" * 75)

def main():
    parser = argparse.ArgumentParser(description="Pipeline RAG Foundation - Buổi 05")
    parser.add_argument("--write", action="store_true", help="Ghi kết quả ra thư mục output/")
    args = parser.parse_args()

    asyncio.run(run_pipeline(write_mode=args.write))

if __name__ == "__main__":
    main()
