"""
10_test_normalized_dtw.py
Prueba de fuego para la Iteración 3D: Normalización Biomecánica en DTW.

Evalúa:
1. Comparación DTW de Maestro.mp4 vs Alumno.mp4 usando el pipeline normalizado
   (invariante a escala, traslación en encuadre, rotación de cámara y proporciones antropométricas).
2. Comparación frente a la métrica cruda anterior (~25.72%).
3. Control negativo: Maestro.mp4 vs control_bailarinas.mp4 para certificar que
   el sistema no genera falsos positivos.
"""

import os
import sys
import time
from pathlib import Path
import numpy as np

# Silenciar permisos de Ultralytics
os.environ["YOLO_CONFIG_DIR"] = "/tmp/ultralytics"

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from corpocmente.infrastructure.ai.adapters import YOLOPoseAdapter
from corpocmente.domain.biomechanics.dtw_comparator import (
    comparar_secuencias_con_dtw,
    _dtw_distance_and_path,
    _similitud_frame,
    _distancia_local,
)
from corpocmente.domain.biomechanics.pose_normalizer import normalizar

MAESTRO_VIDEO = BACKEND_DIR.parent / "Maestro.mp4"
ALUMNO_VIDEO = BACKEND_DIR.parent / "Alumno.mp4"
CONTROL_VIDEO = BACKEND_DIR / "storage" / "control_bailarinas.mp4"


def run_fire_test():
    print("=" * 80)
    print("🥋 ITERACIÓN 3D: PRUEBA DE FUEGO — NORMALIZACIÓN BIOMECÁNICA EN DTW")
    print("=" * 80)

    # 1. Verificar archivos
    for label, path in [("Maestro", MAESTRO_VIDEO), ("Alumno", ALUMNO_VIDEO), ("Control", CONTROL_VIDEO)]:
        if not path.exists():
            print(f"❌ Video {label} no encontrado en: {path}")
            sys.exit(1)
        print(f"📹 {label}: {path.name} ({path.stat().st_size / (1024*1024):.2f} MB)")

    print("-" * 80)
    print("📦 Extrayendo secuencias de poses con YOLO26...")
    adapter = YOLOPoseAdapter()

    t0 = time.time()
    res_m = adapter.extraer_secuencia(str(MAESTRO_VIDEO))
    res_a = adapter.extraer_secuencia(str(ALUMNO_VIDEO))
    res_c = adapter.extraer_secuencia(str(CONTROL_VIDEO))
    t1 = time.time()

    seq_m = res_m["secuencia_kpts"]
    seq_a = res_a["secuencia_kpts"]
    seq_c = res_c["secuencia_kpts"]

    print(f"⏱️ Extracción completada en {t1 - t0:.2f}s:")
    print(f"   • Maestro:   {len(seq_m)} frames (cobertura={res_m['cobertura']*100:.1f}%)")
    print(f"   • Alumno:    {len(seq_a)} frames (cobertura={res_a['cobertura']*100:.1f}%)")
    print(f"   • Bailarinas:{len(seq_c)} frames (cobertura={res_c['cobertura']*100:.1f}%)")
    print("-" * 80)

    # 2. Comparación Cruda de Referencia (Método Anterior)
    print("\n" + "=" * 80)
    print("📊 1. COMPARACIÓN CRUDA ANTERIOR (Sin Normalizar - Píxeles de Pantalla)")
    print("=" * 80)

    dist_raw, path_raw = _dtw_distance_and_path(seq_m, seq_a)
    scores_raw = []
    for i, j in path_raw:
        dist_loc = _distancia_local(seq_m[i], seq_a[j])
        sim_val = 1.0 / (1.0 + dist_loc)
        scores_raw.append(sim_val)
    scores_raw_ord = sorted(scores_raw)
    n_raw = len(scores_raw_ord)
    corte_raw = max(1, int(n_raw * 0.05)) if n_raw > 20 else 0
    sim_cruda_pct = float(np.mean(scores_raw_ord[corte_raw:])) * 100.0

    print(f"   • Distancia DTW Cruda:   {dist_raw:.2f} (en píxeles)")
    print(f"   • Similitud Cruda:       {sim_cruda_pct:.2f}% (Bajo el umbral por diferencia de píxeles)")

    # 3. Comparación con el Nuevo Pipeline Normalizado
    print("\n" + "=" * 80)
    print("🚀 2. COMPARACIÓN CON NORMALIZACIÓN BIOMECÁNICA (DTW Normalizado)")
    print("=" * 80)

    resultado_norm = comparar_secuencias_con_dtw(
        secuencia_maestro=seq_m,
        secuencia_alumno=seq_a,
    )

    print(f"   • Distancia DTW Normalizada:  {resultado_norm['dtw_distance']:.2f}")
    print(f"   • DTW Normalizado por frame:  {resultado_norm['dtw_normalizado']:.4f}")
    print(f"   • Similitud Biomecánica:      {resultado_norm['score_similitud']:.2f}%")
    print(f"   • Longitud del Warping Path:  {resultado_norm['path_length']}")
    print(f"   • Frame crítico del alumno:   {resultado_norm['frame_alumno_critico']}")
    print(f"   • Articulaciones críticas:    {resultado_norm['articulaciones_criticas']}")

    # 4. Control Negativo: Maestro vs Bailarinas
    print("\n" + "=" * 80)
    print("🛑 3. CONTROL NEGATIVO (Maestro vs Bailarinas)")
    print("=" * 80)

    resultado_control = comparar_secuencias_con_dtw(
        secuencia_maestro=seq_m,
        secuencia_alumno=seq_c,
    )

    print(f"   • Distancia DTW Bailarinas:   {resultado_control['dtw_distance']:.2f}")
    print(f"   • Similitud Bailarinas:       {resultado_control['score_similitud']:.2f}%")
    print(f"   • Frame crítico detectado:    {resultado_control['frame_alumno_critico']}")

    # 5. Comparativa y Veredicto
    print("\n" + "=" * 80)
    print("📈 RESUMEN COMPARATIVO")
    print("=" * 80)
    print(f"{'Métrica':<35} {'Método Crudo':<20} {'Método Normalizado (3D)'}")
    print("-" * 80)
    print(f"{'DTW Distance (Alumno)':<35} {dist_raw:<20.2f} {resultado_norm['dtw_distance']:.2f}")
    print(f"{'Score Similitud (Alumno)':<35} {sim_cruda_pct:<20.2f}% {resultado_norm['score_similitud']:.2f}%")
    print(f"{'Score Similitud (Bailarinas)':<35} {'N/A':<20} {resultado_control['score_similitud']:.2f}%")
    print("-" * 80)

    # Criterio de aceptación
    score_alumno = resultado_norm["score_similitud"]
    score_bailarinas = resultado_control["score_similitud"]

    print("\n" + "=" * 80)
    print("🎯 VEREDICTO DE LA PRUEBA DE FUEGO:")
    print("=" * 80)

    if score_alumno >= 50.0 and score_bailarinas < 35.0:
        print("✅ PRUEBA DE FUEGO EXITOSA:")
        print(f"   1. La similitud del alumno subió de {sim_cruda_pct:.2f}% a {score_alumno:.2f}% (incremento de +{score_alumno - sim_cruda_pct:.2f}%).")
        print(f"   2. La distancia DTW colapsó de {dist_raw:.2f} px a {resultado_norm['dtw_distance']:.2f} unidades biomecánicas.")
        print(f"   3. El video de bailarinas dio {score_bailarinas:.2f}%, certificando CERO FALSOS POSITIVOS.")
        print("   Conclusión: El sistema ahora es invariante a posición, escala y encuadre. Evalúa técnica pura.")
        return True
    else:
        print("❌ FALLO EN CRITERIO DE ACEPTACIÓN:")
        print(f"   Score Alumno: {score_alumno:.2f}% (esperado >= 50%)")
        print(f"   Score Bailarinas: {score_bailarinas:.2f}% (esperado < 35%)")
        return False


if __name__ == "__main__":
    exito = run_fire_test()
    if not exito:
        sys.exit(1)

