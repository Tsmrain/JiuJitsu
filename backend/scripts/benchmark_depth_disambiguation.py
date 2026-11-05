import os
import sys
import time
import json
from pathlib import Path
import cv2

# Set ultralytics cache dir to /tmp to avoid sandbox permission issues
os.environ.setdefault("YOLO_CONFIG_DIR", "/tmp/ultralytics")

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from corpocmente.infrastructure.ai.adapters import YOLOPoseAdapter

def main():
    print("=" * 70)
    print("PRUEBA DE FUEGO: BENCHMARK DESAMBIGUACIÓN POR PROFUNDIDAD (YOLO26)")
    print("=" * 70)

    video_origen = Path("2026-10-31 17-15-58.mov")
    if not video_origen.exists():
        video_origen = Path("../2026-10-31 17-15-58.mov")
    if not video_origen.exists():
        print(f"ERROR: Video no encontrado en {video_origen}")
        sys.exit(1)

    # Crear clip de prueba de 300 frames para benchmark riguroso y rápido
    benchmark_dir = Path("backend/storage/benchmark")
    benchmark_dir.mkdir(parents=True, exist_ok=True)
    clip_path = benchmark_dir / "benchmark_clip_300f.mp4"

    cap = cv2.VideoCapture(str(video_origen))
    fps = cap.get(cv2.CAP_PROP_FPS) or 60.0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 1920)
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 1080)

    max_frames = 300
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(clip_path), fourcc, fps, (w, h))

    frames_written = 0
    while cap.isOpened() and frames_written < max_frames:
        ret, frame = cap.read()
        if not ret:
            break
        out.write(frame)
        frames_written += 1
    cap.release()
    out.release()
    print(f"✅ Clip de prueba generado: {clip_path} ({frames_written} frames a {fps:.1f} fps, {w}x{h})")

    adapter = YOLOPoseAdapter()

    # Test 1: Baseline 2D (use_depth=False)
    print("\n--- TEST 1: Baseline 2D Tracking (use_depth=False) ---")
    t0 = time.time()
    res_baseline = adapter.extraer_secuencia(str(clip_path), use_depth=False)
    t_baseline = time.time() - t0
    fps_baseline = res_baseline["total_frames"] / max(0.001, t_baseline)

    print(f"Total frames: {res_baseline['total_frames']}")
    print(f"Frames con persona: {res_baseline['frames_con_persona']}")
    print(f"Cobertura: {res_baseline['cobertura'] * 100:.2f}%")
    print(f"Tiempo total: {t_baseline:.2f}s ({fps_baseline:.1f} FPS)")

    # Test 2: Con Profundidad Nativa YOLO26 (use_depth=True)
    print("\n--- TEST 2: Depth-Assisted Tracking (use_depth=True) ---")
    t0 = time.time()
    res_depth = adapter.extraer_secuencia(str(clip_path), use_depth=True)
    t_depth = time.time() - t0
    fps_depth = res_depth["total_frames"] / max(0.001, t_depth)

    print(f"Total frames: {res_depth['total_frames']}")
    print(f"Frames con persona: {res_depth['frames_con_persona']}")
    print(f"Cobertura: {res_depth['cobertura'] * 100:.2f}%")
    print(f"Oclusiones (>40% IoU) detectadas: {res_depth.get('oclusiones_detectadas', 0)}")
    print(f"Tiempo total: {t_depth:.2f}s ({fps_depth:.1f} FPS)")

    # Test 3: Test unitario directo del método _resolver_oclusion_por_profundidad
    print("\n--- TEST 3: Validación Unitaria de _resolver_oclusion_por_profundidad ---")
    import numpy as np
    depth_mock = np.ones((1080, 1920), dtype=np.float32) * 2.5
    # Atleta B en el fondo (z = 1.80m)
    depth_mock[250:650, 300:700] = 1.80
    # Atleta A en primer plano (z = 1.20m, ocluye a B en la zona de intersección)
    depth_mock[200:600, 200:600] = 1.20

    caja_a = [200, 200, 600, 600]
    caja_b = [300, 250, 700, 650]

    res_unit = adapter._resolver_oclusion_por_profundidad(caja_a, caja_b, depth_mock)
    print(f"Resultado desambiguación unitaria:\n{json.dumps(res_unit, indent=2)}")

    assert res_unit["atleta_frontal"] == "a", f"Error: Debería detectar a Atleta A como frontal (1.20m < 1.80m), fue {res_unit['atleta_frontal']}"
    assert res_unit["iou"] > 0.40, f"Error: IoU debería ser > 0.40, fue {res_unit['iou']}"
    assert res_unit["profundidad_a"] == 1.20, f"Error: profundidad_a debería ser 1.20, fue {res_unit['profundidad_a']}"
    print("✅ Test unitario de _resolver_oclusion_por_profundidad PASÓ con éxito.")

    # Conclusión Empírica Larman
    print("\n" + "=" * 70)
    print("CONCLUSIONES EMPÍRICAS (Metodología Craig Larman):")
    print(f"Cobertura Baseline 2D: {res_baseline['cobertura']*100:.2f}% | Latencia: {t_baseline/res_baseline['total_frames']*1000:.1f} ms/frame")
    print(f"Cobertura Depth 3D:    {res_depth['cobertura']*100:.2f}% | Latencia: {t_depth/res_depth['total_frames']*1000:.1f} ms/frame")
    delta_cobertura = (res_depth['cobertura'] - res_baseline['cobertura']) * 100
    print(f"Delta de Cobertura: {delta_cobertura:+.2f}%")
    print(f"Oclusiones resueltas: {res_depth.get('oclusiones_detectadas', 0)}")

    if res_depth['cobertura'] >= res_baseline['cobertura']:
        print("DECISIÓN DE ARQUITECTURA: La estimación de profundidad mantiene o mejora la cobertura.")
        print("Se conserva use_depth=False como default para producción (cero riesgo/latencia baja)")
        print("y se habilita use_depth=True como flag opcional para análisis de alta precisión en oclusiones.")
    else:
        print("DECISIÓN DE ARQUITECTURA: Depth causó caída en cobertura. Mantener 2D en producción.")
    print("=" * 70)

if __name__ == "__main__":
    main()
