@echo off
echo 🚀 Iniciando configuración para Entorno Windows/GPU...

:: 1. Verificar si Python está instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Error: Python no está instalado o no está en el PATH.
    echo Por favor, instala Python 3.10+ desde python.org y marca la opción "Add to PATH".
    pause
    exit /b 1
)

:: 2. Crear entorno virtual
if not exist .venv (
    echo 📦 Creando entorno virtual .venv...
    python -m venv .venv
)

:: 3. Activar entorno virtual
echo 📦 Activando entorno virtual...
call .venv\Scripts\activate.bat

:: 4. Actualizar herramientas base
echo 📦 Actualizando pip y setuptools...
python -m pip install --upgrade pip setuptools wheel

:: 5. Instalar PyTorch con soporte CUDA 11.8 (Compatible con la mayoría de GPUs NVIDIA en Windows)
echo 🔥 Instalando PyTorch con soporte CUDA...
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

:: 6. Instalar OpenMMLab stack vía MIM
echo 📦 Instalando stack OpenMMLab (mmcv, mmdet, mmpose)...
pip install openmim
mim install mmcv
mim install mmdet
mim install mmpose

:: 7. Instalar rtmpose3d y dependencias del proyecto
echo 📦 Instalando rtmpose3d y dependencias del proyecto...
pip install git+https://github.com/b-arac/rtmpose3d.git
pip install -r requirements-core.txt

:: 8. Verificación de videos Ground Truth
echo 📦 Verificando activos de video reales en Videos\...
if exist Videos\Maestro.mp4 (
    if exist Videos\Alumno.mp4 (
        echo ✔ Videos reales detectados: Videos\Maestro.mp4 y Videos\Alumno.mp4
    ) else (
        echo ⚠ ADVERTENCIA: No se encontró Videos\Alumno.mp4
    )
) else (
    echo ⚠ ADVERTENCIA: Asegúrese de colocar Maestro.mp4 y Alumno.mp4 dentro de la carpeta Videos\
)

echo ✅ ¡Configuración completada!
echo Para usar el sistema, ejecuta: .venv\Scripts\activate.bat
pause
