@echo off
REM =========================================================================
REM Instalador automatizado para Windows con GPU (YOLO26-pose + CUDA)
REM =========================================================================

echo [1/4] Verificando entorno de Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no se encuentra en el PATH. Instala Python 3.10+ y marca "Add Python to PATH".
    exit /b 1
)

echo [2/4] Creando entorno virtual .venv...
if not exist .venv (
    python -m venv .venv
)

echo [3/4] Activando entorno virtual e instalando dependencias...
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install "ultralytics>=8.4.0"
pip install -r requirements-core.txt

echo [4/4] Verificando modelo y aceleracion GPU...
python -c "import torch; print('CUDA disponible:', torch.cuda.is_available()); from ultralytics import YOLO; print('Ultralytics OK')"

echo =========================================================================
echo Instalacion de YOLO26-pose completada exitosamente.
echo Para ejecutar pruebas:
echo   .venv\Scripts\activate.bat
echo   pytest -m real_model -v
echo =========================================================================
