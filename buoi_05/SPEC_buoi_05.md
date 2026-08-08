# SPECIFICATION - BUỔI 05: OCR & CHUNKING STRATEGIES FOR VIETNAMESE PDF

## 1. Mục tiêu
Thiết kế và triển khai module xử lý văn bản tiếng Việt từ file PDF, bao gồm trích xuất text layer, OCR dự phòng (fallback) qua LlamaParse (Llama Cloud), chuẩn hóa Unicode NFC, và áp dụng 3 chiến lược phân đoạn dữ liệu (Chunking) độc lập.

## 2. Phạm vi & Ràng buộc (Constraints)
- **Vị trí bài làm:** Chỉ nằm trong `RAG/rag_foundation/buoi_05/`.
- **Đầu vào:** Các file PDF tiếng Việt công khai nằm trong `datademo/`.
- **Đầu ra:** Dữ liệu raw text đã chuẩn hóa NFC và các danh sách Chunk theo từng chiến lược lưu tại `output/`.
- **Bảo mật:** Đọc `LLAMA_CLOUD_API_KEY` từ file `src/.env`. **TẬP TRUNG BẢO MẬT: KHÔNG** log, in ra console hoặc xuất bí mật API key ra bất kỳ file output nào.
- **Giới hạn kỹ thuật Buổi 5:**
  - **KHÔNG** tạo Embedding.
  - **KHÔNG** lưu trữ vào Vector Database.
  - **KHÔNG** gọi mô hình LLM để phân tích/tóm tắt.
  - **KHÔNG** sửa đổi hoặc ghi đè file PDF gốc.
  - **KHÔNG** tự bịa cấu trúc (Heading/Chương/Điều) khi văn bản gốc không có. Nếu thiếu cấu trúc, phải xuất cảnh báo `WARNING`.

## 3. Luồng xử lý chi tiết

### 3.1. Đọc PDF & OCR Fallback Pipeline
1. **PyMuPDF Extraction:** Đọc từng trang của PDF trong `datademo/`.
2. **Chất lượng Text Layer:** Kiểm tra nếu văn bản bị rỗng, chứa nhiều ký tự lỗi (`\ufffd`, font hỏng, encoding lỗi, hoặc tỷ lệ ký tự không đọc được > 15%).
3. **Fallback OCR (LlamaParse):** Nếu trang/file bị lỗi text layer, tự động chuyển đổi render ảnh và gọi API `LlamaCloud` (`AsyncLlamaCloud` tier `agentic`, expand `markdown_full`).
4. **Unicode Normalization:** Chuẩn hóa toàn bộ text trích xuất về dạng **Unicode NFC** (`unicodedata.normalize('NFC', text)`).
5. **Raw Storage:** Lưu dữ liệu thô sau OCR/trích xuất kèm metadata trang vào `output/raw_text.json`.

### 3.2. Cấu trúc Metadata của Document & Chunk
Mỗi chunk được tạo ra phải tuân thủ schema dữ liệu chứa các trường:
- `chunk_id`: Chuỗi định danh duy nhất (dạng `<strategy>_<index>`)
- `strategy`: Tên chiến lược (`fixed-size`, `semantic`, `hierarchical`)
- `source`: Tên file PDF gốc
- `page_start`: Trang bắt đầu (1-indexed)
- `page_end`: Trang kết thúc (1-indexed)
- `text`: Nội dung văn bản của chunk
- `metadata`: Object chứa các thông tin cấu trúc (nếu có): `chapter`, `section`, `article`, `ocr_used`, `language`.

### 3.3. Ba chiến lược Chunking

1. **Fixed-size Chunking (`fixed-size`):**
   - Cắt theo độ dài ký tự cố định (ví dụ: `chunk_size = 300`, `overlap = 50`).
   - Đảm bảo các chunk kế tiếp có đoạn ghi đè (overlap) chính xác.

2. **Semantic Chunking (`semantic`):**
   - Phân đoạn dựa trên ranh giới ngữ nghĩa tự nhiên: ngắt đoạn (`\n\n`), dòng cách (`\n`), ngắt câu (`.`, `?`, `!`).
   - Đảm bảo không cắt giữa câu nếu không bắt buộc.

3. **Hierarchical Chunking (`hierarchical`):**
   - Phân chia dựa trên cấu trúc văn bản pháp quy/báo cáo tiếng Việt: `Chương` → `Mục` → `Điều/Khoản` → `Điểm`.
   - Nếu file PDF không có các mốc cấu trúc này: Xuất cảnh báo `WARNING: PDF không chứa mốc cấu trúc Chương/Điều/Khoản` và giữ nguyên khối văn bản tự nhiên, không bịa heading.

## 4. Chế độ thực thi CLI
- **Dry-run (Mặc định):** Phân tích và in báo cáo thống kê (số chunk, độ dài min/max/avg, mẫu metadata) ra console mà không ghi file.
- **Write Mode (`--write`):** Ghi toàn bộ kết quả raw text và danh sách chunk JSON vào thư mục `output/`.
