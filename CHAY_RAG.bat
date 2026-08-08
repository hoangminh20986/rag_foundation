@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion
title RAG Foundation - Buoi 05 / 06 / 07
cd /d "%~dp0"

echo ============================================================
echo   RAG FOUNDATION - CAI DAT VA CHAY UNG DUNG
echo   Thu muc: %CD%
echo ============================================================
echo.

if not exist "buoi_05\app.py" (
    echo [X] Hay dat file nay trong thu muc goc cua repo rag_foundation.
    pause & exit /b 1
)

set "PYCMD="
for %%V in (3.12 3.11 3.10 3.13) do (
    if not defined PYCMD (
        py -%%V -c "import sys" >nul 2>&1 && set "PYCMD=py -%%V"
    )
)
if not defined PYCMD (
    python -c "import sys" >nul 2>&1 && set "PYCMD=python"
)
if not defined PYCMD (
    echo [X] Chua cai Python. Tai Python 3.12 tai https://www.python.org/downloads/
    echo     Khi cai NHO TICH o "Add python.exe to PATH".
    pause & exit /b 1
)
echo [OK] Dung Python: %PYCMD%
%PYCMD% --version
echo.

if not exist ".venv\Scripts\python.exe" (
    echo [..] Dang tao moi truong ao .venv ...
    %PYCMD% -m venv .venv || (echo [X] Tao venv that bai & pause & exit /b 1)
)
set "VPY=%CD%\.venv\Scripts\python.exe"
echo [OK] Moi truong ao san sang.
echo.

"%VPY%" -c "import streamlit, chromadb, dotenv" >nul 2>&1
if errorlevel 1 (
    echo [..] Dang cai thu vien - lan dau mat 3-5 phut, vui long cho...
    "%VPY%" -m pip install --upgrade pip -q
    "%VPY%" -m pip install streamlit chromadb google-genai python-dotenv psycopg2-binary || (
        echo [X] Cai thu vien that bai.
        echo     Neu loi build chromadb: hay cai Python 3.12 roi chay lai file nay.
        pause & exit /b 1
    )
)
echo [OK] Thu vien day du.
echo.

if not exist "buoi_07\.env" if exist "buoi_07\.env.example" copy /Y "buoi_07\.env.example" "buoi_07\.env" >nul

:MENU
echo ============================================================
echo   CHON UNG DUNG DE CHAY
echo ------------------------------------------------------------
echo   [1] Buoi 05 - OCR ^& Chunking Visualizer   (khong can API key)
echo   [2] Buoi 06 - Index ChromaDB ^& Hoi dap    (can GEMINI_API_KEY)
echo   [3] Buoi 07 - RAG Pipeline System         (bat buoc GEMINI_API_KEY)
echo   [4] Mo file .env de dan GEMINI_API_KEY
echo   [0] Thoat
echo ============================================================
set /p "CHOICE=Nhap lua chon roi Enter: "

if "%CHOICE%"=="1" ( set "TARGET=buoi_05" & goto RUN )
if "%CHOICE%"=="2" ( set "TARGET=buoi_06" & goto RUN )
if "%CHOICE%"=="3" ( set "TARGET=buoi_07" & goto RUN )
if "%CHOICE%"=="4" goto EDITENV
if "%CHOICE%"=="0" exit /b 0
echo [!] Lua chon khong hop le.
echo.
goto MENU

:EDITENV
echo.
echo Dan API key vao sau dau = roi LUU (Ctrl+S) va dong Notepad.
echo Lay key mien phi tai: https://aistudio.google.com/apikey
echo.
if exist "buoi_06\.env" start /wait notepad "buoi_06\.env"
if exist "buoi_07\.env" start /wait notepad "buoi_07\.env"
echo [OK] Da luu cau hinh.
echo.
goto MENU

:RUN
echo.
echo ------------------------------------------------------------
echo  Dang khoi dong %TARGET% ...
echo  Trinh duyet se tu mo tai http://localhost:8501
echo  De DUNG ung dung: bam Ctrl+C tai cua so nay.
echo ------------------------------------------------------------
echo.
cd /d "%~dp0%TARGET%"
"%VPY%" -m streamlit run app.py
cd /d "%~dp0"
echo.
echo [i] Ung dung da dung.
echo.
goto MENU
