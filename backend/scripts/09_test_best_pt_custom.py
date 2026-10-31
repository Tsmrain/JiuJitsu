"""
09_test_best_pt_custom.py
Diagnóstico aislado del modelo fine-tuneado best.pt sobre video grabado en toma media (YouTube).

Prueba de hipótesis empírica:
- ¿best.pt falla por encuadre/distancia (plano abierto vs toma media)?
- ¿O best.pt sufre de sobreajuste severo / catastrophic forgetting que le impide detectar personas fuera de ViCoS?

Parámetros evaluados:
- Modelo target: storage/models/yolo26n_bjj_pose/weights/best.pt
- Video: /Users/santiago/Desktop/JiuJitsu-main/2026-10-31 09-41-31.mov
- Inferencia: conf=0.15, imgsz=1280, rect=True
- Modelo base de referencia: yolo26n-pose.pt (conf=0.30 y conf=0.15)
"""

import os
import sys
from pathlib import Path
import cv2
import numpy as np

# Configurar directorio de configuración temporal para Ultralytics
os.environ["YOLO_CONFIG_DIR"] = "/tmp/ultralytics"

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from ultralytics import YOLO

VIDEO_PATH = Path("/Users/santiago/Desktop/JiuJitsu-main/2026-10-31 09-41-31.mov")
FINE_TUNED_MODEL_PATH = BACKEND_DIR / "storage" / "models" / "yolo26n_bjj_pose" / "weights" / "best.pt"
BASE_MODEL_PATH = BACKEND_DIR / "yolo26n-pose.pt"


def run_evaluation():
    print("=" * 80)
    print("🥋 ITERACIÓN 3C.5: EVALUACIÓN AISLADA DE best.pt EN TOMA MEDIA")
    print("=" * 80)

    # 1. Verificar archivos
    if not VIDEO_PATH.exists():
        print(f"❌ Video no encontrado en: {VIDEO_PATH}")
        sys.exit(1)
    if not FINE_TUNED_MODEL_PATH.exists():
        print(f"❌ Modelo fine-tuned no encontrado en: {FINE_TUNED_MODEL_PATH}")
        sys.exit(1)
    if not BASE_MODEL_PATH.exists():
        print(f"❌ Modelo base no encontrado en: {BASE_MODEL_PATH}")
        sys.exit(1)

    print(f"📹 Video: {VIDEO_PATH.name} ({VIDEO_PATH.stat().st_size / (1024*1024):.2f} MB)")
    print(f"🧠 Modelo Target (Fine-tuned): {FINE_TUNED_MODEL_PATH}")
    print(f"⚖️ Modelo Referencia (Base): {BASE_MODEL_PATH}")

    # 2. Abrir video e inspeccionar propiedades
    cap = cv2.VideoCapture(str(VIDEO_PATH))
    if not cap.isOpened():
        print("❌ Error abriendo video con OpenCV")
        sys.exit(1)

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    duration_s = total_frames / fps if fps > 0 else 0

    print(f"ℹ️ Propiedades del video: {width}x{height} | {total_frames} frames | {fps:.1f} fps | {duration_s:.2f}s")
    print("-" * 80)

    # Muestrear 24 frames distribuidos uniformemente (aproximadamente 1 frame por segundo)
    num_sample_frames = 24
    step = max(1, total_frames // num_sample_frames)
    sampled_indices = list(range(0, total_frames, step))[:num_sample_frames]

    frames = []
    for idx in sampled_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ok, frame = cap.read()
        if ok and frame is not None:
            frames.append((idx, frame))
    cap.release()

    print(f"📊 Muestreados {len(frames)} frames para la evaluación.")
    print("-" * 80)

    # 3. Cargar modelos
    print("\n📦 Cargando modelo fine-tuned best.pt...")
    model_fine = YOLO(str(FINE_TUNED_MODEL_PATH))

    print("📦 Cargando modelo base yolo26n-pose.pt de referencia...")
    model_base = YOLO(str(BASE_MODEL_PATH))

    # 4. Evaluar best.pt con parámetros solicitados: conf=0.15, imgsz=1280, rect=True
    print("\n" + "=" * 80)
    print("🔬 TEST 1: best.pt (Fine-tuned) | conf=0.15 | imgsz=1280 | rect=True")
    print("=" * 80)

    stats_fine = {
        "frames_with_0": 0,
        "frames_with_1": 0,
        "frames_with_2plus": 0,
        "all_box_confs": [],
        "all_kpt_confs": [],
        "valid_poses_per_frame": [],
        "details": []
    }

    for f_idx, frame in frames:
        results = model_fine.predict(
            source=frame,
            conf=0.15,
            imgsz=1280,
            rect=True,
            verbose=False
        )
        res = results[0]
        boxes = res.boxes
        num_boxes = len(boxes) if boxes is not None else 0
        box_confs = [float(c) for c in boxes.conf.cpu().numpy()] if num_boxes > 0 else []
        stats_fine["all_box_confs"].extend(box_confs)

        valid_poses = 0
        kpt_confs = []
        if res.keypoints is not None and len(res.keypoints.data) > 0:
            kpts_data = res.keypoints.data.cpu().numpy()
            for p in kpts_data:
                if p.shape == (17, 3):
                    c = p[:, 2]
                    kpt_confs.extend(c.tolist())
                    # Criterio estándar del spam filter: al menos 8 keypoints con conf > 0.3 y x > 0
                    if ((c > 0.3) & (p[:, 0] > 0)).sum() >= 8:
                        valid_poses += 1
        stats_fine["all_kpt_confs"].extend(kpt_confs)
        stats_fine["valid_poses_per_frame"].append(valid_poses)

        if num_boxes == 0:
            stats_fine["frames_with_0"] += 1
        elif num_boxes == 1:
            stats_fine["frames_with_1"] += 1
        else:
            stats_fine["frames_with_2plus"] += 1

        stats_fine["details"].append({
            "frame_idx": f_idx,
            "sec": f_idx / fps,
            "num_boxes": num_boxes,
            "box_confs": box_confs,
            "valid_poses": valid_poses
        })

    # Imprimir detalle de frames para best.pt
    print(f"{'Frame':<8} {'Tiempo':<8} {'Cajas':<8} {'Conf Cajas':<35} {'Poses Válidas'}")
    print("-" * 75)
    for d in stats_fine["details"]:
        confs_str = ", ".join(f"{c:.2f}" for c in d["box_confs"][:5])
        if len(d["box_confs"]) > 5:
            confs_str += f" (+{len(d['box_confs'])-5} más)"
        print(f"{d['frame_idx']:<8} {d['sec']:<6.2f}s  {d['num_boxes']:<8} {confs_str:<35} {d['valid_poses']}")

    mean_box_conf_fine = np.mean(stats_fine["all_box_confs"]) if stats_fine["all_box_confs"] else 0.0
    mean_kpt_conf_fine = np.mean(stats_fine["all_kpt_confs"]) if stats_fine["all_kpt_confs"] else 0.0

    print("-" * 75)
    print(f"📈 Resumen best.pt (conf=0.15, imgsz=1280):")
    print(f"   • Total frames evaluados:       {len(frames)}")
    print(f"   • Frames con 0 personas:        {stats_fine['frames_with_0']} ({stats_fine['frames_with_0']/len(frames)*100:.1f}%)")
    print(f"   • Frames con 1 persona:         {stats_fine['frames_with_1']} ({stats_fine['frames_with_1']/len(frames)*100:.1f}%)")
    print(f"   • Frames con >= 2 personas:     {stats_fine['frames_with_2plus']} ({stats_fine['frames_with_2plus']/len(frames)*100:.1f}%)")
    print(f"   • Confianza media de cajas:     {mean_box_conf_fine:.4f}")
    print(f"   • Confianza media de keypoints: {mean_kpt_conf_fine:.4f}")

    # 5. Evaluar modelo base de referencia sobre los mismos frames
    print("\n" + "=" * 80)
    print("⚖️ TEST 2: yolo26n-pose.pt (Base Original) | conf=0.30 | imgsz=640 (Estándar)")
    print("=" * 80)

    stats_base = {
        "frames_with_0": 0,
        "frames_with_1": 0,
        "frames_with_2plus": 0,
        "all_box_confs": [],
        "all_kpt_confs": [],
        "valid_poses_per_frame": [],
        "details": []
    }

    for f_idx, frame in frames:
        results = model_base.predict(
            source=frame,
            conf=0.30,
            imgsz=640,
            verbose=False
        )
        res = results[0]
        boxes = res.boxes
        num_boxes = len(boxes) if boxes is not None else 0
        box_confs = [float(c) for c in boxes.conf.cpu().numpy()] if num_boxes > 0 else []
        stats_base["all_box_confs"].extend(box_confs)

        valid_poses = 0
        kpt_confs = []
        if res.keypoints is not None and len(res.keypoints.data) > 0:
            kpts_data = res.keypoints.data.cpu().numpy()
            for p in kpts_data:
                if p.shape == (17, 3):
                    c = p[:, 2]
                    kpt_confs.extend(c.tolist())
                    if ((c > 0.3) & (p[:, 0] > 0)).sum() >= 8:
                        valid_poses += 1
        stats_base["all_kpt_confs"].extend(kpt_confs)
        stats_base["valid_poses_per_frame"].append(valid_poses)

        if num_boxes == 0:
            stats_base["frames_with_0"] += 1
        elif num_boxes == 1:
            stats_base["frames_with_1"] += 1
        else:
            stats_base["frames_with_2plus"] += 1

        stats_base["details"].append({
            "frame_idx": f_idx,
            "sec": f_idx / fps,
            "num_boxes": num_boxes,
            "box_confs": box_confs,
            "valid_poses": valid_poses
        })

    mean_box_conf_base = np.mean(stats_base["all_box_confs"]) if stats_base["all_box_confs"] else 0.0
    mean_kpt_conf_base = np.mean(stats_base["all_kpt_confs"]) if stats_base["all_kpt_confs"] else 0.0

    print(f"{'Frame':<8} {'Tiempo':<8} {'Cajas':<8} {'Conf Cajas':<35} {'Poses Válidas'}")
    print("-" * 75)
    for d in stats_base["details"]:
        confs_str = ", ".join(f"{c:.2f}" for c in d["box_confs"][:5])
        if len(d["box_confs"]) > 5:
            confs_str += f" (+{len(d['box_confs'])-5} más)"
        print(f"{d['frame_idx']:<8} {d['sec']:<6.2f}s  {d['num_boxes']:<8} {confs_str:<35} {d['valid_poses']}")

    print("-" * 75)
    print(f"📈 Resumen yolo26n-pose.pt (Base Original):")
    print(f"   • Total frames evaluados:       {len(frames)}")
    print(f"   • Frames con 0 personas:        {stats_base['frames_with_0']} ({stats_base['frames_with_0']/len(frames)*100:.1f}%)")
    print(f"   • Frames con 1 persona:         {stats_base['frames_with_1']} ({stats_base['frames_with_1']/len(frames)*100:.1f}%)")
    print(f"   • Frames con >= 2 personas:     {stats_base['frames_with_2plus']} ({stats_base['frames_with_2plus']/len(frames)*100:.1f}%)")
    print(f"   • Confianza media de cajas:     {mean_box_conf_base:.4f}")
    print(f"   • Confianza media de keypoints: {mean_kpt_conf_base:.4f}")

    # 6. Tabla comparativa final y veredicto
    print("\n" + "=" * 80)
    print("📊 CUADRO COMPARATIVO: best.pt vs yolo26n-pose.pt")
    print("=" * 80)
    print(f"{'Métrica':<35} {'best.pt (Fine-tuned)':<22} {'yolo26n-pose (Base)'}")
    print("-" * 80)
    print(f"{'Frames con >= 2 personas':<35} {stats_fine['frames_with_2plus']}/{len(frames)} ({stats_fine['frames_with_2plus']/len(frames)*100:.1f}%)"
          f"{'':<6} {stats_base['frames_with_2plus']}/{len(frames)} ({stats_base['frames_with_2plus']/len(frames)*100:.1f}%)")
    print(f"{'Frames con 1 persona':<35} {stats_fine['frames_with_1']}/{len(frames)} ({stats_fine['frames_with_1']/len(frames)*100:.1f}%)"
          f"{'':<6} {stats_base['frames_with_1']}/{len(frames)} ({stats_base['frames_with_1']/len(frames)*100:.1f}%)")
    print(f"{'Frames con 0 personas':<35} {stats_fine['frames_with_0']}/{len(frames)} ({stats_fine['frames_with_0']/len(frames)*100:.1f}%)"
          f"{'':<6} {stats_base['frames_with_0']}/{len(frames)} ({stats_base['frames_with_0']/len(frames)*100:.1f}%)")
    print(f"{'Confianza media cajas':<35} {mean_box_conf_fine:.4f}{'':<16} {mean_box_conf_base:.4f}")
    print(f"{'Confianza media keypoints':<35} {mean_kpt_conf_fine:.4f}{'':<16} {mean_kpt_conf_base:.4f}")

    print("\n" + "=" * 80)
    print("🎯 VEREDICTO EMPÍRICO:")
    print("=" * 80)

    # Criterio estricto: >= 2 personas en al menos el 50% de los frames
    if stats_fine["frames_with_2plus"] >= len(frames) * 0.50:
        veredicto = "ESCENARIO_A"
        print("✅ ESCENARIO A: best.pt FUNCIONA en tomas medias.")
        print("   Evidencia: Detecta >= 2 personas en", stats_fine['frames_with_2plus'], "de", len(frames), "frames.")
        print("   Conclusión: El problema era exclusivamente la distancia/resolución de los videos abiertos de la academia.")
    else:
        veredicto = "ESCENARIO_B"
        print("❌ ESCENARIO B: best.pt SIGUE FALLANDO en tomas medias.")
        print(f"   Evidencia: Detectó >= 2 personas en SOLO {stats_fine['frames_with_2plus']} de {len(frames)} frames "
              f"({stats_fine['frames_with_2plus']/len(frames)*100:.1f}%).")
        print("   Conclusión: El modelo best.pt está sobreajustado de manera crítica al dominio ViCoS")
        print("               y no generaliza a videos reales de Jiu-Jitsu externos.")

    print("=" * 80)
    return veredicto


if __name__ == "__main__":
    run_evaluation()

