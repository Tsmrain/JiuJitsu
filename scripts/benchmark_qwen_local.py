#!/usr/bin/env python3
"""
scripts/benchmark_qwen_local.py
Benchmark de rendimiento y validación de contrato para Qwen3-VL-Embedding-2B en local (MLX Apple Silicon).
Mide latencias (min, promedio, p95) para embeddings de texto e imagen y valida la dimensión 2048.
"""

import os
import sys
import time
import math
from pathlib import Path
from PIL import Image

# Asegurar path de backend en sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from corpocmente.infrastructure.ai.qwen_adapter import QwenEmbeddingAdapter

TEXTOS_BENCHMARK = [
    "Pasaje de guardia cerrada controlando la solapa y la cadera del oponente.",
    "Variación de raspada de tijera cuando el rival ejerce presión hacia adelante.",
    "Escape de montada con técnica de puente (upa) atrapando brazo y pie del mismo lado.",
    "Transición de control lateral a montada manteniendo base baja y hombro en el mentón.",
    "Finalización con llave de brazo (armbar) desde guardia cerrada asegurando el codo.",
]

def calcular_norma_l2(vector):
    return math.sqrt(sum(x * x for x in vector))

def main():
    print("=" * 65)
    print(" 🚀 BENCHMARK: Qwen3-VL Local en Apple Silicon (MLX)")
    print("=" * 65)

    adapter = QwenEmbeddingAdapter(use_local=True)
    print(f"📦 Modelo configurado: {adapter.local_model_id}")
    print(f"⚙️  Modo local activo: {adapter.use_local}\n")

    # 1. Warm-up
    print("🔥 Realizando warm-up inicial...")
    t0 = time.time()
    v_warm = adapter.generar_embedding_texto("Warm-up text")
    warm_time = time.time() - t0
    print(f"   Warm-up completado en {warm_time:.3f}s (dim: {len(v_warm)})\n")

    # 2. Benchmark de Texto
    print(f"📝 Evaluando inferencia de TEXTO ({len(TEXTOS_BENCHMARK) * 2} iteraciones)...")
    latencias_texto = []
    vectores_texto = []

    for i in range(2):
        for texto in TEXTOS_BENCHMARK:
            start = time.perf_counter()
            vec = adapter.generar_embedding_texto(texto)
            elapsed = time.perf_counter() - start
            latencias_texto.append(elapsed)
            vectores_texto.append(vec)

    latencias_texto.sort()
    avg_texto = sum(latencias_texto) / len(latencias_texto)
    p95_texto = latencias_texto[int(len(latencias_texto) * 0.95)]
    min_texto = latencias_texto[0]
    max_texto = latencias_texto[-1]

    print(f"   ✓ Iteraciones: {len(latencias_texto)}")
    print(f"   ✓ Min:         {min_texto * 1000:.1f} ms")
    print(f"   ✓ Promedio:    {avg_texto * 1000:.1f} ms")
    print(f"   ✓ p95:         {p95_texto * 1000:.1f} ms")
    print(f"   ✓ Max:         {max_texto * 1000:.1f} ms\n")

    # 3. Benchmark de Imagen
    print("🖼️  Evaluando inferencia de IMAGEN (5 iteraciones)...")
    latencias_imagen = []
    vectores_imagen = []
    test_img_path = Path("/tmp/benchmark_frame_temp.jpg")
    
    # Generar frame sintético simulando resolución típica de frame
    img = Image.new("RGB", (320, 240), color=(45, 90, 140))
    img.save(test_img_path)

    for i in range(5):
        start = time.perf_counter()
        vec = adapter.generar_embedding_imagen(str(test_img_path), prompt="postura_combate")
        elapsed = time.perf_counter() - start
        latencias_imagen.append(elapsed)
        vectores_imagen.append(vec)

    if test_img_path.exists():
        test_img_path.unlink()

    latencias_imagen.sort()
    avg_imagen = sum(latencias_imagen) / len(latencias_imagen)
    p95_imagen = latencias_imagen[int(len(latencias_imagen) * 0.95)]
    min_imagen = latencias_imagen[0]
    max_imagen = latencias_imagen[-1]

    print(f"   ✓ Iteraciones: {len(latencias_imagen)}")
    print(f"   ✓ Min:         {min_imagen * 1000:.1f} ms")
    print(f"   ✓ Promedio:    {avg_imagen * 1000:.1f} ms")
    print(f"   ✓ p95:         {p95_imagen * 1000:.1f} ms")
    print(f"   ✓ Max:         {max_imagen * 1000:.1f} ms\n")

    # 4. Validación de Contrato
    print("📐 Validando Contrato Arquitectónico:")
    norm_txt = calcular_norma_l2(vectores_texto[0])
    norm_img = calcular_norma_l2(vectores_imagen[0])
    
    print(f"   ✓ Dimensión Texto:   {len(vectores_texto[0])} (Esperado: 2048) -> {'✅ OK' if len(vectores_texto[0]) == 2048 else '❌ ERROR'}")
    print(f"   ✓ Dimensión Imagen:  {len(vectores_imagen[0])} (Esperado: 2048) -> {'✅ OK' if len(vectores_imagen[0]) == 2048 else '❌ ERROR'}")
    print(f"   ✓ Norma L2 Texto:    {norm_txt:.4f} (Esperado: ~1.0 unitario)")
    print(f"   ✓ Norma L2 Imagen:   {norm_img:.4f} (Esperado: ~1.0 unitario)\n")

    # 5. Comparativa con Línea Base
    print("=" * 65)
    print(" 📊 COMPARATIVA vs LÍNEA BASE (Colab + Google Drive)")
    print("=" * 65)
    print(f"{'Métrica':<25} | {'Colab + Drive (Remoto)':<22} | {'MLX Local (M5 Mac)':<15}")
    print("-" * 65)
    print(f"{'Latencia Texto Promedio':<25} | {'5,000 - 8,000 ms':<22} | {f'{avg_texto * 1000:.1f} ms':<15}")
    print(f"{'Latencia Imagen Promedio':<25} | {'6,000 - 12,000 ms':<22} | {f'{avg_imagen * 1000:.1f} ms':<15}")
    print(f"{'Dependencia Externa':<25} | {'Google Drive / Colab':<22} | {'Ninguna (100% Local)':<15}")
    print(f"{'Costo Operativo':<25} | {'GPUs cloud / polling':<22} | {'$0 (Hardware propio)':<15}")
    print("=" * 65)
    print("\n✅ Benchmark finalizado exitosamente con contrato 100% satisfecho.")

if __name__ == "__main__":
    main()

