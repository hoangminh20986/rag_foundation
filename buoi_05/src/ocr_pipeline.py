"""
Module xử lý trích xuất văn bản từ PDF (PyMuPDF + LlamaParse Fallback + Unicode NFC Normalization)
"""

import os
import re
import asyncio
import unicodedata
from pathlib import Path
from typing import Dict, Any, Tuple, List

# Thử import fitz (PyMuPDF)
try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

# Thử import AsyncLlamaCloud
try:
    from llama_cloud import AsyncLlamaCloud
except ImportError:
    AsyncLlamaCloud = None

def check_text_quality(text: str) -> Tuple[bool, str]:
    """
    Kiểm tra chất lượng văn bản tách từ PyMuPDF.
    Trả về (is_good, reason).
    """
    if not text or not text.strip():
        return False, "Trang PDF rỗng hoặc không có text layer."
    
    # Kiểm tra ký tự thay thế lỗi (\ufffd)
    if "\ufffd" in text:
        return False, "Text chứa ký tự thay thế lỗi (Unicode replacement character \\ufffd)."
    
    # Kiểm tra tỷ lệ ký tự hợp lệ (chữ cái/chữ số/khoảng trắng)
    total_len = len(text)
    if total_len > 0:
        valid_chars = sum(1 for c in text if c.isalnum() or c.isspace() or c in ".,;:!?-()[]/\"'")
        ratio = valid_chars / total_len
        if ratio < 0.70:
            return False, f"Tỷ lệ ký tự không đọc được quá cao (tỷ lệ ký tự chuẩn: {ratio:.2%})."

    return True, "Chất lượng text tốt."

def normalize_nfc(text: str) -> str:
    """Chuẩn hóa chuỗi văn bản về định dạng Unicode NFC chuẩn tiếng Việt."""
    if not text:
        return ""
    # Chuẩn hóa Unicode NFC
    normalized = unicodedata.normalize("NFC", text)
    # Rửa khoảng trắng thừa nhưng giữ ranh giới ngắt dòng
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in normalized.splitlines()]
    return "\n".join(lines).strip()

async def ocr_fallback_llamaparse(pdf_path: Path, api_key: str) -> str:
    """
    Gọi LlamaParse API thông qua AsyncLlamaCloud để OCR file PDF.
    """
    if not AsyncLlamaCloud:
        raise RuntimeError("Gói 'llama-cloud' chưa được cài đặt. Hãy chạy: pip install llama-cloud")
    
    if not api_key or api_key == "KEY_CUA_BAN":
        raise ValueError("LLAMA_CLOUD_API_KEY chưa được cấu hình hợp lệ trong file .env")

    print(f"   [OCR Fallback] Đang gửi file '{pdf_path.name}' tới LlamaParse API...")
    client = AsyncLlamaCloud(api_key=api_key)
    
    # 1. Tải file lên Llama Cloud
    file_obj = await client.files.create(file=str(pdf_path), purpose="parse")
    
    # 2. Thực hiện parse OCR
    result = await client.parsing.parse(
        file_id=file_obj.id,
        tier="agentic",
        version="latest",
        expand=["markdown_full"],
    )
    
    print(f"   [OCR Fallback] OCR hoàn tất thành công từ LlamaParse.")
    return result.markdown_full or ""

async def extract_pdf_content(pdf_path: Path, api_key: str = "") -> Dict[str, Any]:
    """
    Đọc PDF: Thử trích xuất PyMuPDF trước. Nếu lỗi/hỏng text layer -> Fallback sang LlamaParse.
    """
    if not pdf_path.exists():
        raise FileNotFoundError(f"File PDF không tồn tại: {pdf_path}")

    print(f"\n---> Bắt đầu xử lý file PDF: {pdf_path.name}")
    ocr_used = False
    full_text = ""
    pages_data = []

    # Thử lấy text layer bằng PyMuPDF
    if fitz is not None:
        try:
            doc = fitz.open(pdf_path)
            total_pages = len(doc)
            need_ocr = False

            for page_num in range(total_pages):
                page = doc[page_num]
                page_text = page.get_text("text")
                is_good, reason = check_text_quality(page_text)
                
                if not is_good:
                    print(f"   ⚠️ Trang {page_num + 1}/{total_pages} nghi ngờ lỗi font/layer: {reason}")
                    need_ocr = True
                    break
                
                pages_data.append({
                    "page": page_num + 1,
                    "text": normalize_nfc(page_text)
                })

            if not need_ocr and pages_data:
                full_text = "\n\n".join(p["text"] for p in pages_data)
                print(f"   ✅ Trích xuất thành công {total_pages} trang bằng PyMuPDF (Text Layer khả dụng).")

        except Exception as e:
            print(f"   ⚠️ Lỗi đọc PyMuPDF: {e}. Chuyển sang OCR Fallback.")
            need_ocr = True
    else:
        print("   ⚠️ Không tìm thấy PyMuPDF (fitz). Chuyển sang OCR Fallback.")
        need_ocr = True

    # Fallback sang LlamaParse nếu PyMuPDF không dùng được hoặc text bị lỗi
    if need_ocr or not full_text:
        ocr_used = True
        try:
            raw_ocr_text = await ocr_fallback_llamaparse(pdf_path, api_key)
            full_text = normalize_nfc(raw_ocr_text)
            pages_data = [{"page": 1, "text": full_text}]
        except Exception as err:
            print(f"   ❌ [LỖI OCR] Không thể OCR bằng LlamaParse: {err}")
            print("   -> Giữ lại text fallback khả dụng tối thiểu.")
            if pages_data:
                full_text = "\n\n".join(p["text"] for p in pages_data)

    # Chuẩn hóa Unicode NFC lần cuối
    final_text = normalize_nfc(full_text)

    return {
        "source": pdf_path.name,
        "ocr_used": ocr_used,
        "language": "vi",
        "total_pages": len(pages_data),
        "text": final_text,
        "pages": pages_data
    }
