#!/bin/bash
set -e

echo "=== Instalando YOLO26-pose y dependencias para Google Colab ==="
python3 -m pip install --upgrade pip
pip install "ultralytics>=8.4.0"
pip install opencv-python-headless numpy pytest

echo "=== Instalación completada exitosamente ==="
echo "Ejemplo de uso:"
echo "  from ultralytics import YOLO"
echo "  model = YOLO('yolo26n-pose.pt')  # o 'yolo26x-pose.pt' en A100"
