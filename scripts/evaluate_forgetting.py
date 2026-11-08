#!/usr/bin/env python3
"""
evaluate_forgetting.py
Evaluación empírica rigurosa de Olvido Catastrófico y Calidad de Aprendizaje:
1. mAP Pose (50-95) en conjunto de validación de técnicas antiguas (data/continuous_dataset).
2. mAP Pose (50-95) en conjunto de validación combinado (data/combined_americana).
3. mAP Pose (50-95) en conjunto exclusivo de la nueva técnica ("Americana desde la montada").
4. Cobertura de tracking y latencia en el Gatekeeper Benchmark (benchmark_clip_300f.mp4).
"""

import os
import sys
import json
import time
from pathlib import Path
import torch

os.environ.setdefault("YOLO_CONFIG_DIR", "/tmp/ultralytics")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "backend"))

from ultralytics import YOLO
from corpocmente.infrastructure.ai.adapters import YOLOPoseAdapter

def evaluar_modelo_en_dataset(modelo_path, dataset_yaml, split="val"):
    model = YOLO(str(modelo_path))
    res = model.val(data=str(dataset_yaml), split=split, device="mps" if torch.backends.mps.is_available() else "cpu", verbose=False)
    
    pose_map50_95 = float(res.pose.map) if hasattr(res, "pose") and res.pose is not None else 0.0
    pose_map50 = float(res.pose.map50) if hasattr(res, "pose") and res.pose is not None else 0.0
    box_map50_95 = float(res.box.map) if hasattr(res, "box") and res.box is not None else 0.0
    box_map50 = float(res.box.map50) if hasattr(res, "box") and res.box is not None else 0.0
    
    return {
        "pose_map50_95": pose_map50_95,
        "pose_map50": pose_map50,
        "box_map50_95": box_map50_95,
        "box_map50": box_map50
    }

def evaluar_gatekeeper_benchmark(modelo_path, clip_path):
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    model = YOLO(str(modelo_path))
    t0 = time.time()
    results = model.predict(source=str(clip_path), stream=True, verbose=False, conf=0.10, device=device)
    total_frames = 0
    frames_con_persona = 0
    for r in results:
        total_frames += 1
        if r.boxes is not None and len(r.boxes) > 0:
            frames_con_persona += 1
    tiempo_total = time.time() - t0
    fps = total_frames / max(0.001, tiempo_total)
    latencia_ms = (tiempo_total / max(1, total_frames)) * 1000.0
    cobertura_pct = (frames_con_persona / max(1, total_frames)) * 100.0

    return {
        "total_frames": total_frames,
        "frames_con_persona": frames_con_persona,
        "cobertura_pct": cobertura_pct,
        "fps": fps,
        "latencia_ms": latencia_ms
    }

def main():
    print("=" * 75)
    print("PRUEBA DE FUEGO: EVALUACIÓN EMPÍRICA DE OLVIDO CATASTRÓFICO (FINCH)")
    print("=" * 75)

    old_model_path = BASE_DIR / "yolo26n-pose.pt"
    new_model_path = BASE_DIR / "yolo26n_americana.pt"

    if not new_model_path.exists():
        print(f"❌ Error: {new_model_path} no encontrado. Espera a que termine el entrenamiento.")
        sys.exit(1)

    dataset_old = BASE_DIR / "data" / "continuous_dataset" / "dataset.yaml"
    dataset_comb = BASE_DIR / "data" / "combined_americana" / "dataset.yaml"
    dataset_ame = BASE_DIR / "data" / "americana_val" / "dataset.yaml"
    benchmark_clip = BASE_DIR / "backend" / "storage" / "benchmark" / "benchmark_clip_300f.mp4"

    print("\n🔍 1. Evaluando sobre Dataset de Técnicas Antiguas (data/continuous_dataset)...")
    m_old_cont = evaluar_modelo_en_dataset(old_model_path, dataset_old)
    m_new_cont = evaluar_modelo_en_dataset(new_model_path, dataset_old)

    print("🔍 2. Evaluando sobre Dataset Combinado (data/combined_americana)...")
    m_old_comb = evaluar_modelo_en_dataset(old_model_path, dataset_comb)
    m_new_comb = evaluar_modelo_en_dataset(new_model_path, dataset_comb)

    print("🔍 3. Evaluando sobre Dataset Nuevo Exclusivo (Americana desde la montada)...")
    m_old_ame = evaluar_modelo_en_dataset(old_model_path, dataset_ame)
    m_new_ame = evaluar_modelo_en_dataset(new_model_path, dataset_ame)

    print("🔍 4. Ejecutando Gatekeeper Benchmark de 300 fotogramas...")
    bench_old = evaluar_gatekeeper_benchmark(old_model_path, benchmark_clip)
    bench_new = evaluar_gatekeeper_benchmark(new_model_path, benchmark_clip)

    # Cálculo de métricas delta de olvido (Pose mAP50-95)
    delta_map_cont = m_new_cont["pose_map50_95"] - m_old_cont["pose_map50_95"]
    delta_map_comb = m_new_comb["pose_map50_95"] - m_old_comb["pose_map50_95"]
    gain_ame = m_new_ame["pose_map50_95"] - m_old_ame["pose_map50_95"]
    delta_cobertura = bench_new["cobertura_pct"] - bench_old["cobertura_pct"]

    # Criterio estricto de aceptación:
    # 1. delta_map >= -0.02 (máximo 2% de caída en técnicas antiguas)
    # 2. cobertura en benchmark = 100%
    # 3. latencia <= 30 ms/frame
    exito_no_olvido = (delta_map_cont >= -0.02) and (delta_map_comb >= -0.02)
    exito_benchmark = (bench_new["cobertura_pct"] >= 100.0)
    exito_latencia = (bench_new["latencia_ms"] <= 30.0)
    exito_aprendizaje = (m_new_ame["pose_map50_95"] >= m_old_ame["pose_map50_95"])

    decision_aprobado = exito_no_olvido and exito_benchmark and exito_latencia

    print("\n" + "=" * 75)
    print("📊 RESULTADOS COMPARATIVOS: MODELO BASE vs. MODELO ADAPTADO FINCH")
    print("=" * 75)
    print(f"{'Métrica':<42} | {'Modelo Base':<12} | {'Modelo FINCH':<12} | {'Δ':<10}")
    print("-" * 83)
    print(f"{'mAP@50-95 Pose (Técnicas Antiguas - Flywheel)':<42} | {m_old_cont['pose_map50_95']:.4f}       | {m_new_cont['pose_map50_95']:.4f}       | {delta_map_cont:+.4f}")
    print(f"{'mAP@50-95 Pose (Técnicas Antiguas - BJJ Gold)':<42} | {m_old_comb['pose_map50_95']:.4f}       | {m_new_comb['pose_map50_95']:.4f}       | {delta_map_comb:+.4f}")
    print(f"{'mAP@50-95 Pose (Nueva Técnica: Americana)':<42} | {m_old_ame['pose_map50_95']:.4f}       | {m_new_ame['pose_map50_95']:.4f}       | {gain_ame:+.4f}")
    print(f"{'Cobertura Tracking en Benchmark (300f)':<42} | {bench_old['cobertura_pct']:.2f}%      | {bench_new['cobertura_pct']:.2f}%      | {delta_cobertura:+.2f}%")
    print(f"{'Latencia Inferencia MPS (ms/frame)':<42} | {bench_old['latencia_ms']:.1f} ms       | {bench_new['latencia_ms']:.1f} ms       | {bench_new['latencia_ms']-bench_old['latencia_ms']:+.1f} ms")
    print(f"{'Tasa de Procesamiento (FPS)':<42} | {bench_old['fps']:.1f} FPS      | {bench_new['fps']:.1f} FPS      | {bench_new['fps']-bench_old['fps']:+.1f} FPS")
    print("=" * 75)

    if delta_map_cont < -0.05:
        veredicto = "❌ FALLO: Olvido catastrófico severo detectado. Modelo DESCARTADO."
    elif delta_map_cont < -0.02:
        veredicto = "⚠️ ADVERTENCIA: Ligero olvido (>2%). Requiere calibrar Replay Buffer."
    else:
        veredicto = "✅ ÉXITO: El modelo aprendió 'Americana desde la montada' SIN olvidar las técnicas previas."

    print(f"\n📢 Veredicto de la Prueba de Fuego: {veredicto}")
    print(f"   Decisión Gatekeeper: {'PROMOVER A PRODUCCIÓN' if decision_aprobado else 'MANTENER BASELINE'}")

    report = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "base_model": str(old_model_path),
        "new_model": str(new_model_path),
        "metrics_continuous_dataset": {
            "old": m_old_cont,
            "new": m_new_cont,
            "delta_map_pose": delta_map_cont
        },
        "metrics_combined_dataset": {
            "old": m_old_comb,
            "new": m_new_comb,
            "delta_map_pose": delta_map_comb
        },
        "metrics_americana_exclusive": {
            "old": m_old_ame,
            "new": m_new_ame,
            "gain_map_pose": gain_ame
        },
        "gatekeeper_benchmark": {
            "old": bench_old,
            "new": bench_new,
            "delta_cobertura": delta_cobertura
        },
        "veredicto": veredicto,
        "aprobado": decision_aprobado
    }

    report_path = BASE_DIR / "runs" / "pose" / "americana_finch" / "evaluation_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f_rep:
        json.dump(report, f_rep, indent=2)
    print(f"💾 Reporte completo guardado en: {report_path}")

if __name__ == "__main__":
    main()

