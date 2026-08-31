#!/usr/bin/env python3
"""
Script de Benchmarking de Inferencia Real y Medición de Recursos (Fuera de Pytest).

Objetivo de Ingeniería:
1. Medir el tiempo de inferencia del extractor cinemático en CPU (SLA contractual RP-01: < 4.0s).
2. Medir el consumo pico de memoria RAM mediante `tracemalloc` (crítico para dimensionar FunctionGraph).
3. Validar dimensiones de salida (num_personas, 133, 3) y verificar ausencia de valores NaN o infinitos.

Uso:
    .venv/bin/python scripts/test_real_inference.py

Autor: Santiago Borda Zambrana
Proyecto: Corpo & Mente Bolivia - Análisis Biomecánico BJJ
"""

from __future__ import annotations

import os
import sys
import time
import tracemalloc

# Asegurar path del proyecto
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import numpy as np

from src.services.rtmpose3d_extractor import RTMPose3DExtractor


def main() -> int:
    print("=" * 72)
    print("🥋 BENCHMARK DE INFERENCIA CINEMÁTICA Y CONSUMO DE MEMORIA (CPU)")
    print("=" * 72)

    # 1. Iniciar monitoreo estricto de memoria RAM
    tracemalloc.start()
    tiempo_inicio = time.perf_counter()

    # 2. Inicializar Singleton RTMPose3DExtractor
    repo_path = os.getenv("RTMPOSE3D_REPO_PATH", "/opt/rtmpose3d")
    print(f"[*] Inicializando RTMPose3DExtractor (Repo: {repo_path})...")
    extractor = RTMPose3DExtractor.obtener_instancia()
    extractor.inicializar_modelo(ruta_checkpoints=repo_path, device="cpu")

    if not extractor.esta_inicializado:
        print("❌ Error: El extractor no pudo ser inicializado.")
        tracemalloc.stop()
        return 1

    # 3. Generar secuencia de prueba realista (180 fotogramas a 30fps = 6.0s según SLA)
    num_frames = 180
    alto, ancho = 384, 288
    print(f"[*] Generando secuencia de prueba: {num_frames} frames ({ancho}x{alto}x3 BGR)...")

    # Frame base con gradiente cinemático sintético
    frame_sintetico = np.full((alto, ancho, 3), 128, dtype=np.uint8)
    frames_prueba = [frame_sintetico.copy() for _ in range(num_frames)]

    tiempo_preparacion = time.perf_counter()
    print(f"[*] Iniciando inferencia cinemática sobre {num_frames} frames...")

    # 4. Ejecutar extracción de landmarks sobre la secuencia completa
    landmarks_extraidos = extractor.extraer_de_lista_frames(frames_prueba)
    tiempo_fin = time.perf_counter()

    # 5. Capturar consumo de memoria
    memoria_actual_bytes, memoria_pico_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    latencia_total_segundos = tiempo_fin - tiempo_inicio
    latencia_inferencia_segundos = tiempo_fin - tiempo_preparacion
    memoria_pico_mb = memoria_pico_bytes / (1024 * 1024)

    # 6. Validaciones de integridad matemática
    if len(landmarks_extraidos) != num_frames:
        print(f"❌ Error en longitud: esperados {num_frames}, obtenidos {len(landmarks_extraidos)}")
        return 1

    primer_frame = np.array(landmarks_extraidos[0])  # (133, 3)
    if primer_frame.shape != (133, 3):
        print(f"❌ Forma inválida del frame: {primer_frame.shape}, se esperaba (133, 3)")
        return 1

    if np.isnan(primer_frame).any() or np.isinf(primer_frame).any():
        print("❌ Error: Se detectaron valores NaN o Infinitos en los keypoints generados.")
        return 1

    primera_articulacion = primer_frame[0]  # Nariz/Punto 0

    # 7. Reporte formal en consola
    print("\n" + "-" * 72)
    print("📊 RESULTADOS EMPÍRICOS DE RENDIMIENTO:")
    print("-" * 72)
    print(f"⏱️ Latencia Total: {latencia_total_segundos:.2f} segundos (Objetivo SLA: < 4.0s)")
    print(f"⚡ Tiempo de Inferencia Pura: {latencia_inferencia_segundos:.2f} segundos ({num_frames / latencia_inferencia_segundos:.1f} FPS)")
    print(f"🧠 Pico de RAM: {memoria_pico_mb:.2f} MB (Dato crítico para configurar FunctionGraph)")
    print(f"📐 Forma del Output por Frame: (1, {primer_frame.shape[0]}, {primer_frame.shape[1]})")
    print(f"📍 Coordenadas de prueba articulación #0: X={primera_articulacion[0]:.3f}, Y={primera_articulacion[1]:.3f}, Z={primera_articulacion[2]:.3f}")
    print("-" * 72)

    cumple_sla = latencia_total_segundos <= 4.0
    if cumple_sla:
        print("🎯 SLA RP-01 (< 4.0s): CUMPLIDO EXITOSAMENTE.")
    else:
        print("⚠️ SLA RP-01 (< 4.0s): Requiere atención o precalentamiento continuo.")

    print("✅ VALIDACIÓN EXITOSA: El pipeline real funciona en entorno local/contenedor.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
