"""
Module triển khai 3 chiến lược Phân đoạn dữ liệu (Chunking):
1. Fixed-size (Cắt cố định kèm overlap)
2. Semantic (Ưu tiên ranh giới đoạn văn & câu)
3. Hierarchical (Dựa theo mốc cấu trúc Chương/Điều/Khoản)
"""

import re
from typing import List, Dict, Any

def create_chunk_payload(
    chunk_id: str,
    strategy: str,
    source: str,
    page_start: int,
    page_end: int,
    text: str,
    metadata: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Tạo dict payload chuẩn hóa theo SPEC (không làm biến đổi dict truyền vào)."""
    meta = (metadata or {}).copy()
    meta["char_count"] = len(text)
    return {
        "chunk_id": chunk_id,
        "strategy": strategy,
        "source": source,
        "page_start": page_start,
        "page_end": page_end,
        "text": text,
        "metadata": meta
    }

def chunk_fixed_size(
    text: str,
    source: str,
    chunk_size: int = 300,
    overlap: int = 50
) -> List[Dict[str, Any]]:
    """
    Chiến lược 1: Fixed-size Chunking (cắt theo số ký tự kèm overlap).
    """
    chunks = []
    if not text:
        return chunks

    start = 0
    text_len = len(text)
    index = 1
    # Đảm bảo bước nhảy > 0 để tránh lặp vô hạn khi overlap >= chunk_size
    step = max(1, chunk_size - overlap)

    while start < text_len:
        end = min(start + chunk_size, text_len)
        chunk_text = text[start:end].strip()
        
        if chunk_text:
            chunk_id = f"fixed_{index}"
            chunks.append(create_chunk_payload(
                chunk_id=chunk_id,
                strategy="fixed-size",
                source=source,
                page_start=1,
                page_end=1,
                text=chunk_text,
                metadata={"chunk_size_param": chunk_size, "overlap_param": overlap}
            ))
            index += 1
            
        if end >= text_len:
            break
            
        start += step

    return chunks

def chunk_semantic(
    text: str,
    source: str,
    target_size: int = 350
) -> List[Dict[str, Any]]:
    """
    Chiến lược 2: Semantic Chunking (ngắt theo đoạn văn \\n\\n, câu kết thúc ., ?, !).
    """
    chunks = []
    if not text:
        return chunks

    # Tách theo đoạn văn trước
    raw_paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    paragraphs = []

    # Nếu một đoạn quá dài (> target_size), tách nhỏ hơn theo dấu câu (. ? !)
    for para in raw_paragraphs:
        if len(para) > target_size:
            sentences = re.split(r"(?<=[.?!])\s+", para)
            paragraphs.extend([s.strip() for s in sentences if s.strip()])
        else:
            paragraphs.append(para)

    current_chunk_texts = []
    current_len = 0
    index = 1

    for para in paragraphs:
        if current_len + len(para) <= target_size:
            current_chunk_texts.append(para)
            current_len += len(para) + 2
        else:
            if current_chunk_texts:
                chunk_str = "\n\n".join(current_chunk_texts)
                chunks.append(create_chunk_payload(
                    chunk_id=f"semantic_{index}",
                    strategy="semantic",
                    source=source,
                    page_start=1,
                    page_end=1,
                    text=chunk_str,
                    metadata={"split_reason": "paragraph_or_sentence_boundary"}
                ))
                index += 1

            current_chunk_texts = [para]
            current_len = len(para)

    if current_chunk_texts:
        chunk_str = "\n\n".join(current_chunk_texts)
        chunks.append(create_chunk_payload(
            chunk_id=f"semantic_{index}",
            strategy="semantic",
            source=source,
            page_start=1,
            page_end=1,
            text=chunk_str,
            metadata={"split_reason": "paragraph_or_sentence_boundary"}
        ))

    return chunks

def chunk_hierarchical(
    text: str,
    source: str
) -> List[Dict[str, Any]]:
    """
    Chiến lược 3: Hierarchical Chunking (chia theo mốc cấu trúc Chương/Điều/Khoản).
    Lưu ý: Không tự bịa heading khi PDF không có mốc cấu trúc; phải xuất WARNING.
    """
    chunks = []
    if not text:
        return chunks

    # Biểu thức chính quy phát hiện mốc Chương hoặc Điều
    chapter_pattern = r"(Chuong|Chương)\s+([0-9IVXLCDM]+[:\.\s–-].*)"
    article_pattern = r"(Dieu|Điều)\s+([0-9]+[\.\:]?.*)"

    lines = text.splitlines()
    has_structure = False

    # Kiểm tra nhanh xem văn bản có mốc cấu trúc không
    for line in lines:
        if re.match(chapter_pattern, line.strip(), re.IGNORECASE) or re.match(article_pattern, line.strip(), re.IGNORECASE):
            has_structure = True
            break

    if not has_structure:
        print("   ⚠️ WARNING: PDF không chứa mốc cấu trúc Chương/Điều/Khoản tiêu chuẩn. Giữ nguyên khối văn bản và KHÔNG bịa heading.")
        # Fallback an toàn: Coi toàn bộ văn bản là 1 khối duy nhất kèm cảnh báo
        return [create_chunk_payload(
            chunk_id="hierarchical_1",
            strategy="hierarchical",
            source=source,
            page_start=1,
            page_end=1,
            text=text,
            metadata={"warning": "Không phát hiện cấu trúc Chương/Điều tiêu chuẩn."}
        )]

    # Tiến hành phân tách theo mốc cấu trúc nếu tìm thấy
    current_chapter = "Chương I (Mặc định)"
    current_article = ""
    current_lines = []
    index = 1

    for line in lines:
        line_str = line.strip()
        if not line_str:
            continue

        match_chap = re.match(chapter_pattern, line_str, re.IGNORECASE)
        match_art = re.match(article_pattern, line_str, re.IGNORECASE)

        if match_chap or match_art:
            # Lưu chunk trước đó nếu có
            if current_lines:
                chunk_str = "\n".join(current_lines).strip()
                if chunk_str:
                    chunks.append(create_chunk_payload(
                        chunk_id=f"hierarchical_{index}",
                        strategy="hierarchical",
                        source=source,
                        page_start=1,
                        page_end=1,
                        text=chunk_str,
                        metadata={
                            "chapter": current_chapter,
                            "article": current_article or "Phần mở đầu"
                        }
                    ))
                    index += 1
                current_lines = []

            if match_chap:
                current_chapter = line_str
                current_article = ""
            elif match_art:
                current_article = line_str

        current_lines.append(line_str)

    # Lưu chunk cuối cùng
    if current_lines:
        chunk_str = "\n".join(current_lines).strip()
        if chunk_str:
            chunks.append(create_chunk_payload(
                chunk_id=f"hierarchical_{index}",
                strategy="hierarchical",
                source=source,
                page_start=1,
                page_end=1,
                text=chunk_str,
                metadata={
                    "chapter": current_chapter,
                    "article": current_article or "Phần kết"
                }
            ))

    return chunks

def calculate_stats(chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Tính toán thống kê số chunk, min, max, trung bình độ dài."""
    if not chunks:
        return {"total_chunks": 0, "min_len": 0, "max_len": 0, "avg_len": 0}

    lengths = [len(c["text"]) for c in chunks]
    return {
        "total_chunks": len(chunks),
        "min_len": min(lengths),
        "max_len": max(lengths),
        "avg_len": round(sum(lengths) / len(lengths), 1)
    }
