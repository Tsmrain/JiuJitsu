#!/usr/bin/env python3
"""
backend/scripts/autonomous_flywheel.py
Motor de Aprendizaje Continuo Autónomo (Autonomous MLOps Flywheel).
Se ejecuta como subproceso aislado (subprocess.Popen) cuando un profesor registra
el patrón biomecánico de una nueva técnica.

Ciclo de vida autónomo:
1. Cola de tareas con bloqueo POSIX (.autonomous_flywheel.lock) para proteger la Memoria Unificada (24 GB).
2. Extracción de fotogramas del video del profesor y pseudo-etiquetado Teacher-Student (yolo26x-pose.pt)
   invocando data_flywheel_orchestrator.py --prepare.
3. Ensamblaje de Replay Buffer 70/30 (70% poses históricas/canónicas vs. 30% nueva técnica).
4. Fine-tuning supervisado con congelamiento de backbone (freeze=10) y scheduler adaptativo FINCH.
5. Gatekeeper Automático: valida el nuevo modelo contra el dataset histórico de validación.
   Si ΔmAP >= -0.02, promueve atómicamente los pesos a yolo26n_autonomous.pt para Hot-Swap en caliente.
   Si ΔmAP < -0.02, descarta el modelo nuevo y preserva intacto el modelo de producción.
"""

import os
import sys
import json
import time
import random
import shutil
import subprocess
import fcntl
from pathlib import Path
from datetime import datetime, timezone
import cv2
import yaml
import torch

os.environ.setdefault("YOLO_CONFIG_DIR", "/tmp/ultralytics")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")

# Rutas base del repositorio
BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR / "scripts"))
sys.path.insert(0, str(BASE_DIR / "backend"))

from ultralytics import YOLO
from finch_callback import FINCHScheduler

DATA_DIR = BASE_DIR / "data"
AUTONOMOUS_ROOT = DATA_DIR / "autonomous"
LOCK_FILE_PATH = AUTONOMOUS_ROOT / ".autonomous_flywheel.lock"
STATUS_FILE_PATH = AUTONOMOUS_ROOT / "last_run_status.json"
LOG_FILE_PATH = AUTONOMOUS_ROOT / "autonomous_flywheel.log"

HISTORIC_DATASET_DIR = BASE_DIR / "backend" / "storage" / "continuous_dataset"
BJJ_GOLD_DIR = BASE_DIR / "backend" / "storage" / "datasets" / "bjj_pose_yolo"

NEW_MODEL_PATH = BASE_DIR / "yolo26n_autonomous.pt"
NEW_MODEL_STORAGE_PATH = BASE_DIR / "storage" / "models" / "yolo26n_autonomous.pt"


def resolve_prod_model() -> Path:
    """Resuelve el modelo base actual en producción para aprendizaje acumulativo."""
    candidates = [
        NEW_MODEL_PATH,
        NEW_MODEL_STORAGE_PATH,
        BASE_DIR / "yolo26n-pose.pt",
        BASE_DIR / "storage" / "models" / "yolo26n-pose.pt",
    ]
    for c in candidates:
        if c.exists() and c.stat().st_size > 1_000_000:
            return c
    return BASE_DIR / "storage" / "models" / "yolo26n-pose.pt"


def log(msg: str) -> None:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    formatted = f"[{timestamp}] [AUTONOMOUS FLYWHEEL] {msg}"
    print(formatted, flush=True)
    try:
        AUTONOMOUS_ROOT.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
            f.write(formatted + "\n")
    except Exception:
        pass


def actualizar_estado(estado: str, tecnica_id: str, detalles: dict = None) -> None:
    try:
        AUTONOMOUS_ROOT.mkdir(parents=True, exist_ok=True)
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "estado": estado,
            "tecnica_id": tecnica_id,
            "pid": os.getpid(),
        }
        if detalles:
            payload.update(detalles)
        with open(STATUS_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
    except Exception as exc:
        log(f"Advertencia actualizando estado JSON: {exc}")


def paso_1_extraer_y_etiquetar(video_path: Path, tecnica_id: str, new_dataset_dir: Path) -> Path:
    """
    Extrae fotogramas del video del profesor e invoca data_flywheel_orchestrator.py --prepare
    para pseudo-etiquetarlos con el modelo maestro yolo26x-pose.pt.
    """
    log(f"Paso 1: Extrayendo y pseudo-etiquetando nueva técnica ({tecnica_id}) desde {video_path.name}...")
    raw_frames_dir = new_dataset_dir / "raw_frames" / tecnica_id
    prepared_dir = new_dataset_dir / "prepared"

    if raw_frames_dir.exists():
        shutil.rmtree(raw_frames_dir)
    if prepared_dir.exists():
        shutil.rmtree(prepared_dir)

    raw_frames_dir.mkdir(parents=True, exist_ok=True)
    prepared_dir.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"No se pudo abrir el video {video_path}")

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    every_n = max(1, total_frames // 80) if total_frames > 80 else 5

    idx = 0
    saved = 0
    while True:
        ret, frame = cap.read()
        if not ret or frame is None:
            break
        if idx % every_n == 0:
            frame_file = raw_frames_dir / f"frame_{idx:05d}.jpg"
            cv2.imwrite(str(frame_file), frame)
            saved += 1
        idx += 1
    cap.release()

    if saved == 0:
        raise RuntimeError(f"No se pudieron extraer fotogramas válidos de {video_path}")

    log(f"Extraídos {saved} fotogramas de {video_path.name}. Ejecutando data_flywheel_orchestrator.py --prepare...")

    orchestrator_script = BASE_DIR / "scripts" / "data_flywheel_orchestrator.py"
    subprocess.run(
        [
            sys.executable,
            str(orchestrator_script),
            "--prepare",
            "--input-dir",
            str(new_dataset_dir / "raw_frames"),
            "--output-dir",
            str(prepared_dir),
        ],
        check=True,
    )
    return prepared_dir


def paso_2_combinar_replay_buffer(prepared_dir: Path, new_dataset_dir: Path) -> Path:
    """
    Construye el Replay Buffer 70/30 mezclando:
    - 70% de fotogramas históricos/canónicos (continuous_dataset + bjj_pose_yolo)
    - 30% de fotogramas nuevos auto-etiquetados de la técnica recién subida
    """
    log("Paso 2: Creando Replay Buffer 70/30 (70% histórico canónico / 30% nueva técnica)...")
    combined_dir = new_dataset_dir / "combined"
    if combined_dir.exists():
        shutil.rmtree(combined_dir)

    train_img_dir = combined_dir / "images" / "train"
    train_lbl_dir = combined_dir / "labels" / "train"
    val_img_dir = combined_dir / "images" / "val"
    val_lbl_dir = combined_dir / "labels" / "val"

    for d in [train_img_dir, train_lbl_dir, val_img_dir, val_lbl_dir]:
        d.mkdir(parents=True, exist_ok=True)

    # 1. Recolectar fotogramas nuevos auto-etiquetados con al menos un atleta detectado
    new_pairs = []
    for split in ["train", "val"]:
        s_img_dir = prepared_dir / "images" / split
        s_lbl_dir = prepared_dir / "labels" / split
        if s_img_dir.exists():
            for img in sorted(s_img_dir.glob("*")):
                if img.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
                    continue
                lbl = s_lbl_dir / f"{img.stem}.txt"
                if lbl.exists() and lbl.stat().st_size > 0:
                    new_pairs.append((img, lbl))

    if not new_pairs:
        raise RuntimeError("El modelo maestro no detectó atletas válidos en los fotogramas extraídos.")

    # 2. Recolectar fotogramas antiguos (Continuous Dataset + BJJ Gold Standard)
    old_pairs = []
    hist_train_img = HISTORIC_DATASET_DIR / "images" / "train"
    hist_train_lbl = HISTORIC_DATASET_DIR / "labels" / "train"
    if hist_train_img.exists():
        for img in sorted(hist_train_img.glob("*")):
            if img.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
                continue
            lbl = hist_train_lbl / f"{img.stem}.txt"
            if lbl.exists() and lbl.stat().st_size > 0:
                old_pairs.append((img, lbl))

    bjj_train_img = BJJ_GOLD_DIR / "train" / "images"
    bjj_train_lbl = BJJ_GOLD_DIR / "train" / "labels"
    if bjj_train_img.exists():
        all_bjj = sorted(bjj_train_img.glob("*.jpg"))
        random.seed(42)
        sampled_bjj = random.sample(all_bjj, min(120, len(all_bjj)))
        for img in sampled_bjj:
            lbl = bjj_train_lbl / f"{img.stem}.txt"
            if lbl.exists() and lbl.stat().st_size > 0:
                old_pairs.append((img, lbl))

    if not old_pairs:
        raise RuntimeError("No se encontraron fotogramas históricos para construir el Replay Buffer 70/30.")

    # 3. Balancear estrictamente en proporción 70% Antiguos / 30% Nuevos
    random.seed(42)
    random.shuffle(new_pairs)
    random.shuffle(old_pairs)

    # Determinar cantidad manteniendo proporción exacta 70/30
    target_new = min(len(new_pairs), int(len(old_pairs) * 0.30 / 0.70))
    target_new = max(1, target_new)
    target_old = max(1, int(round(target_new * 0.70 / 0.30)))
    if target_old > len(old_pairs):
        target_old = len(old_pairs)
        target_new = max(1, int(round(target_old * 0.30 / 0.70)))

    selected_old = old_pairs[:target_old]
    selected_new = new_pairs[:target_new]

    total_combined = len(selected_old) + len(selected_new)
    pct_old = (len(selected_old) / total_combined) * 100.0
    pct_new = (len(selected_new) / total_combined) * 100.0
    log(
        f"Replay Buffer ensamblado: {len(selected_old)} antiguos ({pct_old:.1f}%) + "
        f"{len(selected_new)} nuevos ({pct_new:.1f}%) = {total_combined} frames totales."
    )

    for idx, (img, lbl) in enumerate(selected_old):
        shutil.copy2(img, train_img_dir / f"old_{idx:04d}_{img.name}")
        shutil.copy2(lbl, train_lbl_dir / f"old_{idx:04d}_{lbl.name}")

    for idx, (img, lbl) in enumerate(selected_new):
        shutil.copy2(img, train_img_dir / f"new_{idx:04d}_{img.name}")
        shutil.copy2(lbl, train_lbl_dir / f"new_{idx:04d}_{lbl.name}")

    # 4. Copiar conjunto de validación histórico para monitoreo
    hist_val_img = HISTORIC_DATASET_DIR / "images" / "val"
    hist_val_lbl = HISTORIC_DATASET_DIR / "labels" / "val"
    if hist_val_img.exists():
        for img in sorted(hist_val_img.glob("*")):
            if img.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
                continue
            lbl = hist_val_lbl / f"{img.stem}.txt"
            if lbl.exists():
                shutil.copy2(img, val_img_dir / img.name)
                shutil.copy2(lbl, val_lbl_dir / lbl.name)

    dataset_yaml_path = combined_dir / "dataset.yaml"
    dataset_config = {
        "path": str(combined_dir.resolve()),
        "train": "images/train",
        "val": "images/val",
        "kpt_shape": [17, 3],
        "flip_idx": [0, 2, 1, 4, 3, 6, 5, 8, 7, 10, 9, 12, 11, 14, 13, 16, 15],
        "names": {0: "person"},
    }
    with open(dataset_yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(dataset_config, f, sort_keys=False)

    return dataset_yaml_path


def paso_3_entrenar_finch(dataset_yaml_path: Path, prod_model_path: Path, tecnica_id: str, epochs: int = 30) -> Path:
    """
    Entrena el modelo con FINCHScheduler (Loss-Adaptive Learning Rate) y freeze=10.
    """
    log(f"Paso 3: Entrenando con FINCH y freeze=10 sobre {prod_model_path.name} ({epochs} épocas)...")

    _orig = torch.load
    def _safe_load(*a, **kw):
        kw["weights_only"] = False
        return _orig(*a, **kw)
    torch.load = _safe_load

    device = "mps" if torch.backends.mps.is_available() else "cpu"
    model = YOLO(str(prod_model_path))

    finch = FINCHScheduler(base_lr=0.001, min_lr=1e-5, max_lr=0.01, ref_loss=2.0, alpha=0.5)
    model.add_callback("on_train_batch_end", finch.on_train_batch_end)

    project_dir = BASE_DIR / "runs" / "autonomous"
    results = model.train(
        data=str(dataset_yaml_path),
        epochs=epochs,
        batch=16,
        imgsz=640,
        freeze=10,
        warmup_epochs=0.0,
        device=device,
        project=str(project_dir.resolve()),
        name=str(tecnica_id),
        exist_ok=True,
        patience=8,
        verbose=False,
        plots=False,
    )

    save_dir = Path(results.save_dir) if hasattr(results, "save_dir") else (project_dir / str(tecnica_id))
    best_pt = save_dir / "weights" / "best.pt"
    if not best_pt.exists():
        best_pt = save_dir / "weights" / "last.pt"

    if not best_pt.exists():
        raise RuntimeError(f"No se encontró el archivo de pesos resultante en {save_dir / 'weights'}")

    return best_pt


def paso_4_gatekeeper(modelo_nuevo_path: Path, prod_model_path: Path) -> tuple[bool, dict]:
    """
    Evalúa el nuevo modelo contra el modelo actual sobre el dataset histórico de validación.
    Si ΔmAP >= -0.02, realiza promoción atómica a yolo26n_autonomous.pt para Hot-Swap.
    """
    log("Paso 4: Gatekeeper Automático (Evaluando ausencia de olvido catastrófico)...")

    _orig = torch.load
    def _safe_load(*a, **kw):
        kw["weights_only"] = False
        return _orig(*a, **kw)
    torch.load = _safe_load

    device = "mps" if torch.backends.mps.is_available() else "cpu"
    val_data = str((HISTORIC_DATASET_DIR / "dataset.yaml").resolve())

    model_old = YOLO(str(prod_model_path))
    model_new = YOLO(str(modelo_nuevo_path))

    res_old = model_old.val(data=val_data, split="val", device=device, verbose=False)
    res_new = model_new.val(data=val_data, split="val", device=device, verbose=False)

    map_box_old = float(res_old.box.map) if hasattr(res_old, "box") and res_old.box is not None else 0.0
    map_box_new = float(res_new.box.map) if hasattr(res_new, "box") and res_new.box is not None else 0.0
    map_pose_old = float(res_old.pose.map) if hasattr(res_old, "pose") and res_old.pose is not None else map_box_old
    map_pose_new = float(res_new.pose.map) if hasattr(res_new, "pose") and res_new.pose is not None else map_box_new

    delta_box = map_box_new - map_box_old
    delta_pose = map_pose_new - map_pose_old

    log(
        f"Gatekeeper Métricas -> Box mAP Old: {map_box_old:.4f} | New: {map_box_new:.4f} (Δ={delta_box:+.4f}) || "
        f"Pose mAP Old: {map_pose_old:.4f} | New: {map_pose_new:.4f} (Δ={delta_pose:+.4f})"
    )

    metrics_summary = {
        "map_box_old": round(map_box_old, 4),
        "map_box_new": round(map_box_new, 4),
        "delta_box": round(delta_box, 4),
        "map_pose_old": round(map_pose_old, 4),
        "map_pose_new": round(map_pose_new, 4),
        "delta_pose": round(delta_pose, 4),
    }

    if delta_pose >= -0.02 and delta_box >= -0.02:
        log("✅ Gatekeeper SUPERADO (ΔmAP >= -0.02). Promoviendo atómicamente a yolo26n_autonomous.pt...")
        # Promoción atómica con archivo temporal + os.replace para que FastAPI nunca lea un archivo parcial
        tmp_root = BASE_DIR / ".yolo26n_autonomous.pt.tmp"
        shutil.copy2(modelo_nuevo_path, tmp_root)
        os.replace(tmp_root, NEW_MODEL_PATH)

        NEW_MODEL_STORAGE_PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp_storage = NEW_MODEL_STORAGE_PATH.parent / ".yolo26n_autonomous.pt.tmp"
        shutil.copy2(modelo_nuevo_path, tmp_storage)
        os.replace(tmp_storage, NEW_MODEL_STORAGE_PATH)

        log(f"🔥 Modelo promovido en {NEW_MODEL_PATH} (Hot-Swap listo para el próximo request).")
        return True, metrics_summary
    else:
        log("❌ Gatekeeper FALLIDO (ΔmAP < -0.02). Olvido catastrófico detectado. Descartando pesos nuevos.")
        try:
            if modelo_nuevo_path.exists():
                modelo_nuevo_path.unlink()
        except Exception:
            pass
        return False, metrics_summary


def main():
    if len(sys.argv) < 3:
        print("Uso: python autonomous_flywheel.py <NEW_VIDEO_PATH> <TECNICA_ID> [--epochs N]", file=sys.stderr)
        sys.exit(1)

    new_video_path = Path(sys.argv[1]).resolve()
    tecnica_id = str(sys.argv[2]).strip()

    epochs = int(os.getenv("AUTONOMOUS_FLYWHEEL_EPOCHS", "30"))
    if "--epochs" in sys.argv:
        idx = sys.argv.index("--epochs")
        if idx + 1 < len(sys.argv):
            epochs = int(sys.argv[idx + 1])

    AUTONOMOUS_ROOT.mkdir(parents=True, exist_ok=True)

    # Cola de tareas con archivo .lock para serializar entrenamientos en Apple Silicon
    with open(LOCK_FILE_PATH, "w", encoding="utf-8") as lock_file:
        log(f"Solicitud recibida para técnica {tecnica_id}. Adquiriendo turno en cola de entrenamiento...")
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        lock_file.write(f"{os.getpid()}:{tecnica_id}\n")
        lock_file.flush()

        t_start = time.time()
        prod_model = resolve_prod_model()
        new_dataset_dir = AUTONOMOUS_ROOT / tecnica_id

        log(f"Iniciando ciclo autónomo para técnica {tecnica_id} (Modelo base: {prod_model.name})")
        actualizar_estado("entrenando", tecnica_id, {"video_path": str(new_video_path), "base_model": str(prod_model)})

        try:
            if not new_video_path.exists() or new_video_path.stat().st_size < 10_000:
                raise RuntimeError(f"Archivo de video inválido o demasiado pequeño para entrenamiento: {new_video_path}")

            prepared_dir = paso_1_extraer_y_etiquetar(new_video_path, tecnica_id, new_dataset_dir)
            dataset_yaml = paso_2_combinar_replay_buffer(prepared_dir, new_dataset_dir)
            best_weights = paso_3_entrenar_finch(dataset_yaml, prod_model, tecnica_id, epochs=epochs)
            exito, metrics = paso_4_gatekeeper(best_weights, prod_model)

            elapsed = round(time.time() - t_start, 2)
            if exito:
                actualizar_estado(
                    "completado_promovido",
                    tecnica_id,
                    {
                        "elapsed_seconds": elapsed,
                        "promoted_model": str(NEW_MODEL_PATH),
                        "metrics": metrics,
                    },
                )
                log(f"🎉 Ciclo autónomo finalizado con ÉXITO en {elapsed}s.")
            else:
                actualizar_estado(
                    "abortado_gatekeeper",
                    tecnica_id,
                    {
                        "elapsed_seconds": elapsed,
                        "metrics": metrics,
                    },
                )
                log(f"⚠️ Ciclo abortado por Gatekeeper en {elapsed}s. El modelo en producción no ha sido modificado.")

        except Exception as e:
            elapsed = round(time.time() - t_start, 2)
            log(f"ERROR CRÍTICO en el ciclo autónomo: {e}")
            actualizar_estado("error", tecnica_id, {"error": str(e), "elapsed_seconds": elapsed})
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


if __name__ == "__main__":
    main()
