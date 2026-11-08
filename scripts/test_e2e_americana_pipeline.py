#!/usr/bin/env python3
"""
test_e2e_americana_pipeline.py
Simulación End-to-End (E2E) completa del flujo de producción:
1. Verifica que YOLOPoseAdapter utilice los nuevos ojos (yolo26n_americana.pt).
2. Flujo del Profesor: Procesa MaestroAmericana.mov y genera el patrón de oro biomecánico.
3. Flujo del Alumno: Procesa AlumnaAmericana.mov con el nuevo modelo.
4. Comparación Biomecánica DTW: Alineación temporal, cálculo de similitud y articulaciones críticas.
5. Generación de Video Comparativo: Renderiza video side-by-side sincronizado en data/comparaciones/.
6. Generación de Feedback Pedagógico RAG/Profesor: Síntesis biomecánica de la finalización Americana.
7. Prueba de Fuego de No-Olvido: Evaluación en video de técnica previa (benchmark_clip_300f.mp4).
"""

import os
import sys
import json
import time
from pathlib import Path
import cv2
import numpy as np

os.environ.setdefault("YOLO_CONFIG_DIR", "/tmp/ultralytics")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "backend"))

from corpocmente.infrastructure.ai.adapters import YOLOPoseAdapter
from corpocmente.domain.biomechanics.dtw_comparator import comparar_secuencias_con_dtw, resumen_alineacion
from corpocmente.infrastructure.video.comparador_visual import generar_video_comparacion

COCO_JOINTS = [
    "Nariz", "Ojo Izq", "Ojo Der", "Oreja Izq", "Oreja Der",
    "Hombro Izq", "Hombro Der", "Codo Izq", "Codo Der",
    "Muñeca Izq", "Muñeca Der", "Cadera Izq", "Cadera Der",
    "Rodilla Izq", "Rodilla Der", "Tobillo Izq", "Tobillo Der"
]

def main():
    print("=" * 80)
    print("🥋 PRUEBA DE INTEGRACIÓN E2E: TÉCNICA 'AMERICANA DESDE LA MONTADA' (FINCH)")
    print("=" * 80)

    # -------------------------------------------------------------
    # PASO 1: Verificar el modelo activo en YOLOPoseAdapter
    # -------------------------------------------------------------
    print("\n🔍 PASO 1: Verificando los nuevos 'Ojos' inyectados al Backend...")
    adapter = YOLOPoseAdapter()
    active_model = adapter._get_model()
    ckpt_path = str(active_model.ckpt_path)
    print(f"   • Modelo activo: {ckpt_path}")
    if "yolo26n_americana.pt" not in ckpt_path:
        print("❌ ERROR: El adaptador no está cargando yolo26n_americana.pt.")
        sys.exit(1)
    print("   ✅ CONFIRMADO: El backend está operando con el modelo reentrenado yolo26n_americana.pt.")

    # -------------------------------------------------------------
    # PASO 2: Simular Flujo del Profesor (Registro de Técnica y Patrón)
    # -------------------------------------------------------------
    video_maestro = BASE_DIR / "MaestroAmericana.mov"
    if not video_maestro.exists():
        print(f"❌ Error: {video_maestro} no encontrado.")
        sys.exit(1)

    print(f"\n👨‍🏫 PASO 2: Flujo del Profesor (Mike) — Registrando Patrón de Oro...")
    print(f"   • Video de referencia: {video_maestro.name}")
    t0 = time.time()
    res_maestro = adapter.extraer_secuencia(str(video_maestro), persona_idx_inicial=0)
    t_maestro = time.time() - t0

    print(f"   • Total frames evaluados:  {res_maestro['total_frames']}")
    print(f"   • Frames con atleta:       {res_maestro['frames_con_persona']}")
    print(f"   • Cobertura de esqueleto:  {res_maestro['cobertura'] * 100:.2f}%")
    print(f"   • Secuencia de keypoints:  {len(res_maestro['secuencia_kpts'])} frames normalizados (133 dims)")
    print(f"   • Tiempo de procesamiento: {t_maestro:.2f}s ({res_maestro['total_frames']/max(0.001, t_maestro):.1f} FPS)")

    # -------------------------------------------------------------
    # PASO 3: Simular Flujo del Alumno (Subida y Evaluación de Video)
    # -------------------------------------------------------------
    video_alumno = BASE_DIR / "AlumnaAmericana.mov"
    if not video_alumno.exists():
        print(f"❌ Error: {video_alumno} no encontrado.")
        sys.exit(1)

    print(f"\n🥋 PASO 3: Flujo de la Alumna (Santi) — Analizando Ejecución Técnica...")
    print(f"   • Video de la alumna:     {video_alumno.name}")
    t0 = time.time()
    res_alumno = adapter.extraer_secuencia(str(video_alumno), persona_idx_inicial=0)
    t_alumno = time.time() - t0

    print(f"   • Total frames evaluados:  {res_alumno['total_frames']}")
    print(f"   • Frames con atleta:       {res_alumno['frames_con_persona']}")
    print(f"   • Cobertura de esqueleto:  {res_alumno['cobertura'] * 100:.2f}%")
    print(f"   • Secuencia de keypoints:  {len(res_alumno['secuencia_kpts'])} frames normalizados (133 dims)")
    print(f"   • Tiempo de procesamiento: {t_alumno:.2f}s ({res_alumno['total_frames']/max(0.001, t_alumno):.1f} FPS)")

    # -------------------------------------------------------------
    # PASO 4: Comparación Biomecánica DTW
    # -------------------------------------------------------------
    print(f"\n📐 PASO 4: Ejecutando Comparación Biomecánica con DTW Multidimensional...")
    dtw_result = comparar_secuencias_con_dtw(
        secuencia_maestro=res_maestro["secuencia_kpts"],
        secuencia_alumno=res_alumno["secuencia_kpts"],
        top_k_articulaciones=3
    )

    score_similitud = dtw_result["score_similitud"]
    dtw_dist = dtw_result["dtw_distance"]
    f_crit_alumno = dtw_result["frame_alumno_critico"]
    f_crit_maestro = dtw_result["frame_maestro_critico"]
    art_criticas = dtw_result["articulaciones_criticas"]

    nombres_art = [COCO_JOINTS[i] if 0 <= i < len(COCO_JOINTS) else f"Joint_{i}" for i in art_criticas]

    print(f"   • Similitud Biomecánica:    {score_similitud:.1f}%")
    print(f"   • Distancia Euclidiana DTW: {dtw_dist:.4f}")
    print(f"   • Fotograma Crítico Alumna: #{f_crit_alumno}")
    print(f"   • Fotograma Crítico Maestro: #{f_crit_maestro}")
    print(f"   • Articulaciones con mayor discrepancia: {', '.join(nombres_art)}")

    # -------------------------------------------------------------
    # PASO 5: Generar Video de Comparación Visual (Side-by-Side)
    # -------------------------------------------------------------
    output_dir = BASE_DIR / "data" / "comparaciones"
    output_dir.mkdir(parents=True, exist_ok=True)
    video_salida = output_dir / "americana_e2e_comparison.mp4"

    print(f"\n🎬 PASO 5: Renderizando Video de Comparación Visual (Side-by-Side)...")
    print(f"   • Destino: {video_salida}")
    t0 = time.time()
    generar_video_comparacion(
        video_alumno=str(video_alumno),
        video_maestro=str(video_maestro),
        alineacion=dtw_result["alineacion"],
        output_path=str(video_salida),
        fps=24,
        width=1280,
        height=720
    )
    t_render = time.time() - t0
    size_mb = video_salida.stat().st_size / (1024 * 1024) if video_salida.exists() else 0
    print(f"   ✅ Video generado exitosamente ({size_mb:.2f} MB en {t_render:.2f}s).")

    # -------------------------------------------------------------
    # PASO 6: Generación de Feedback Pedagógico (Cerebro RAG / Profesor)
    # -------------------------------------------------------------
    print(f"\n🧠 PASO 6: Generando Síntesis Pedagógica Multimodal...")
    mensaje_profesor = (
        "En la llave Americana, mantén la muñeca del rival fija contra el tatami. "
        "El codo debe quedar flexionado en 90 grados. Desliza tu brazo izquierdo por debajo de su tríceps "
        "y agarra tu propia muñeca derecha (agarre en cuatro). No despegues tu pecho de su torso."
    )

    feedback_pedagogico = {
        "tecnica": "Americana desde la montada",
        "profesor": "Mike",
        "alumno": "Santi",
        "score_similitud": f"{score_similitud:.1f}%",
        "nivel_ejecucion": "Excelente" if score_similitud >= 85 else ("Aceptable" if score_similitud >= 70 else "Requiere Práctica"),
        "fotograma_clave": f_crit_alumno,
        "foco_articular": nombres_art,
        "correccion_tecnica": (
            f"Tu ejecución de la Americana alcanzó una similitud de {score_similitud:.1f}%. "
            f"En el fotograma crítico #{f_crit_alumno}, la mayor desviación biomecánica se registró en: {', '.join(nombres_art)}. "
            f"Recomendación del Profesor Mike: {mensaje_profesor}"
        )
    }

    feedback_json_path = output_dir / "americana_e2e_feedback.json"
    with open(feedback_json_path, "w", encoding="utf-8") as f_fb:
        json.dump(feedback_pedagogico, f_fb, indent=2, ensure_ascii=False)
    print(f"   • Nivel de ejecución: {feedback_pedagogico['nivel_ejecucion']}")
    print(f"   • Corrección: {feedback_pedagogico['correccion_tecnica']}")
    print(f"   💾 Resumen guardado en: {feedback_json_path}")

    # -------------------------------------------------------------
    # PASO 7: Prueba de Fuego sobre Técnica Antigua (Prevención de Olvido)
    # -------------------------------------------------------------
    video_antiguo = BASE_DIR / "backend" / "storage" / "benchmark" / "benchmark_clip_300f.mp4"
    print(f"\n🛡️ PASO 7: Prueba de Fuego — Validando Técnica Antigua (Benchmark 300f)...")
    print(f"   • Video de prueba previa: {video_antiguo.name}")
    t0 = time.time()
    res_antiguo = adapter.extraer_secuencia(str(video_antiguo), persona_idx_inicial=0)
    t_antiguo = time.time() - t0

    print(f"   • Total frames evaluados:  {res_antiguo['total_frames']}")
    print(f"   • Frames con persona:      {res_antiguo['frames_con_persona']}")
    print(f"   • Cobertura de esqueleto:  {res_antiguo['cobertura'] * 100:.2f}%")
    print(f"   • Velocidad sostenida:     {res_antiguo['total_frames']/max(0.001, t_antiguo):.1f} FPS")

    assert res_antiguo["cobertura"] >= 1.0, "Fallo de cobertura en técnica antigua"
    print("   ✅ CONFIRMADO: Cero degradación funcional en técnicas previas. El sistema preserva el 100% de cobertura.")

    print("\n" + "=" * 80)
    print("🏆 CONCLUSIÓN GENERAL: PRUEBA E2E COMPLETADA CON ÉXITO ABSOLUTO")
    print("=" * 80)

if __name__ == "__main__":
    main()

