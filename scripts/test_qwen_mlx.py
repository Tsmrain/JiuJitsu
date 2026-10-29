#!/usr/bin/env python3
"""
scripts/test_qwen_mlx.py
PoC para verificar la carga e inferencia local de Qwen3-VL-Embedding-2B usando MLX.
Verifica que las dimensiones del vector sean exactamente 2048 para texto e imagen.
"""

import os
import sys
import time
from pathlib import Path
from PIL import Image

import mlx.core as mx
from mlx_embeddings import load

MODEL_ID = os.getenv("LOCAL_QWEN_MODEL", "mlx-community/Qwen3-VL-Embedding-2B-8bit")

def main():
    print(f"=== Prueba de Concepto: Qwen3-VL Local (MLX) ===")
    print(f"Modelo objetivo: {MODEL_ID}")
    
    start_load = time.time()
    print("⏳ Descargando / cargando pesos del modelo en memoria...")
    try:
        model, processor = load(MODEL_ID)
    except Exception as e:
        print(f"❌ Error al cargar el modelo: {e}")
        sys.exit(1)
    load_time = time.time() - start_load
    print(f"✅ Modelo y procesador cargados exitosamente en {load_time:.2f}s\n")

    # --- 1. Prueba de Embedding de Texto ---
    texto_prueba = "El pasaje de guardia en Jiu-Jitsu requiere controlar las caderas."
    print(f"🧪 [1/2] Generando embedding para texto: '{texto_prueba}'")
    
    t0 = time.time()
    inputs_text = processor.prepare_embedding_inputs([{"text": texto_prueba}])
    outputs_text = model(**inputs_text)
    mx.eval(outputs_text.text_embeds)
    text_vector = outputs_text.text_embeds[0].tolist()
    text_time = time.time() - t0
    
    dim_texto = len(text_vector)
    print(f"   ⏱️ Tiempo de inferencia texto: {text_time:.4f}s")
    print(f"   📏 Dimensión del vector de texto: {dim_texto}")
    assert dim_texto == 2048, f"Dimensión incorrecta: {dim_texto} != 2048"
    print("   ✅ Embedding de texto verificado (2048 dimensiones).\n")

    # --- 2. Prueba de Embedding de Imagen ---
    test_img_path = Path("/tmp/test_jiujitsu_poc.jpg")
    img = Image.new("RGB", (256, 256), color=(30, 80, 160))
    img.save(test_img_path)
    print(f"🧪 [2/2] Generando embedding para imagen: {test_img_path}")

    t0 = time.time()
    inputs_img = processor.prepare_embedding_inputs([{"image": str(test_img_path), "text": "consulta_visual"}])
    outputs_img = model(**inputs_img)
    mx.eval(outputs_img.text_embeds)
    img_vector = outputs_img.text_embeds[0].tolist()
    img_time = time.time() - t0
    
    dim_img = len(img_vector)
    print(f"   ⏱️ Tiempo de inferencia imagen: {img_time:.4f}s")
    print(f"   📏 Dimensión del vector de imagen: {dim_img}")
    assert dim_img == 2048, f"Dimensión incorrecta: {dim_img} != 2048"
    print("   ✅ Embedding de imagen verificado (2048 dimensiones).\n")

    if test_img_path.exists():
        test_img_path.unlink()

    print("🎉 ¡PoC completado con éxito! Ambos vectores cumplen la especificación de 2048 dimensiones.")

if __name__ == "__main__":
    main()

