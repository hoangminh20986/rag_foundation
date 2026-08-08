"""
Script kiểm tra môi trường xử lý văn bản tiếng Việt & OCR cho RAG Foundation (Buổi 05).
Kiểm tra Python, PyMuPDF, Pillow, llama-cloud, Pydantic, Streamlit, python-dotenv và file .env.
"""

import sys
import os
from pathlib import Path

# Thêm đường dẫn thư mục hiện tại để đọc .env
CURRENT_DIR = Path(__file__).parent.resolve()
ENV_FILE = CURRENT_DIR / ".env"

def check_environment():
    results = []
    remediations = []

    # 1. Kiểm tra phiên bản Python
    python_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    if sys.version_info >= (3, 9):
        results.append(("Python 3.9+", f"PASS (v{python_ver})", "Đã đạt yêu cầu"))
    else:
        results.append(("Python 3.9+", f"FAIL (v{python_ver})", "Cần nâng cấp Python lên 3.9+"))
        remediations.append("Tải và cài đặt Python 3.9 trở lên tại: https://www.python.org/downloads/")

    # 2. Danh sách các thư viện cần kiểm tra
    packages = [
        ("PyMuPDF (fitz)", "fitz", "pymupdf"),
        ("Pillow", "PIL", "Pillow"),
        ("Llama Cloud", "llama_cloud", "llama-cloud"),
        ("Pydantic", "pydantic", "pydantic"),
        ("Streamlit", "streamlit", "streamlit"),
        ("Python Dotenv", "dotenv", "python-dotenv"),
    ]

    missing_packages = []

    for label, module_name, pip_name in packages:
        try:
            mod = __import__(module_name)
            version = getattr(mod, "__version__", "Đã cài đặt")
            results.append((label, f"PASS ({version})", "Sẵn sàng sử dụng"))
        except ImportError:
            results.append((label, "FAIL", f"Chưa cài đặt gói '{pip_name}'"))
            missing_packages.append(pip_name)

    if missing_packages:
        cmd = f"{sys.executable} -m pip install " + " ".join(missing_packages)
        remediations.append(f"Chạy lệnh cài đặt các thư viện thiếu:\n   {cmd}")

    # 3. Kiểm tra file .env & LLAMA_CLOUD_API_KEY (không in secret)
    if ENV_FILE.exists():
        # Thử đọc qua dotenv nếu có
        api_key_status = "Chưa cấu hình API Key"
        try:
            from dotenv import load_dotenv
            load_dotenv(dotenv_path=ENV_FILE, override=True)
            key = os.getenv("LLAMA_CLOUD_API_KEY", "")
            if key and key != "KEY_CUA_BAN":
                api_key_status = "Đã cấu hình (Đã ẩn vì lý do bảo mật)"
                results.append(("LLAMA_CLOUD_API_KEY", "PASS", api_key_status))
            else:
                results.append(("LLAMA_CLOUD_API_KEY", "FAIL", "Cần thay 'KEY_CUA_BAN' bằng API key thật trong file .env"))
                remediations.append(f"Mở file {ENV_FILE} và cập nhật LLAMA_CLOUD_API_KEY với key từ https://cloud.llamaindex.ai/")
        except ImportError:
            results.append(("LLAMA_CLOUD_API_KEY", "WARNING", "Không thể load .env do thiếu gói python-dotenv"))
    else:
        results.append(("File .env", "FAIL", f"Không tìm thấy file .env tại {ENV_FILE}"))
        remediations.append(f"Tạo file .env tại {ENV_FILE} với nội dung: LLAMA_CLOUD_API_KEY='KEY_CỦA_BẠN'")

    # In kết quả dạng bảng PASS/FAIL
    print("\n" + "=" * 70)
    print(" BẢNG KIỂM TRA MÔI TRƯỜNG OCR & RAG FOUNDATION (BUỔI 05)")
    print("=" * 70)
    print(f"{'Công cụ / Thư viện':<22} | {'Trạng thái':<18} | {'Ghi chú'}")
    print("-" * 70)
    for tool, status, note in results:
        print(f"{tool:<22} | {status:<18} | {note}")
    print("=" * 70)

    # In hướng dẫn khắc phục nếu có lỗi
    if remediations:
        print("\n[HƯỚNG DẪN KHẮC PHỤC CÁC TRẠNG THÁI FAIL]:")
        for idx, item in enumerate(remediations, 1):
            print(f"{idx}. {item}")
        print("\n" + "=" * 70)

if __name__ == "__main__":
    check_environment()
