#!/usr/bin/env python3
"""
Data Flywheel Orchestrator (Active Learning MLOps Pipeline)
Metodología: Craig Larman (Arquitectura Robusta, Cero Entrenamiento Ciego, Evidencia Empírica).

Este script administra el ciclo de vida de los datos del "Data Flywheel":
- Extrae frames con incertidumbre (<0.65 de confianza) registrados por el pipeline.
- Filtra duplicados basándose en hashes criptográficos SHA-256.
- Auto-etiqueta los casos borde usando el modelo maestro de alta capacidad (yolo26x-pose.pt).
- Genera datasets estandarizados en formato YOLO Pose (dataset.yaml, images, labels).
- REGLA DE ARQUITECTURA: PROHIBIDO ENTRENAR AUTOMÁTICAMENTE. El entrenamiento debe ser
  un proceso deliberado y manual siguiendo el protocolo de Replay Buffer (70/30) y Gatekeeper Benchmark.
"""

import os
import sys
import argparse
import hashlib
import shutil
import json
import csv
from pathlib import Path
from datetime import datetime, timezone

# Forzar configuración de Ultralytics en /tmp para compatibilidad de entorno y sandbox
os.environ.setdefault("YOLO_CONFIG_DIR", "/tmp/ultralytics")

def calcular_sha256(archivo_path: Path) -> str:
    """Calcula el hash criptográfico SHA-256 de un archivo para deduplicación exacta."""
    hasher = hashlib.sha256()
    with open(archivo_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def cargar_log_incertidumbre(log_csv_path: Path) -> dict:
    """Carga metadatos del log de incertidumbre (confianza, técnica, etc.)."""
    metadatos = {}
    if not log_csv_path.exists():
        return metadatos
    try:
        with open(log_csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                p = row.get("path", "").strip()
                if p:
                    metadatos[Path(p).resolve()] = row
    except Exception as e:
        print(f"⚠️ Error leyendo log.csv: {e}")
    return metadatos

def descubrir_frames(input_dir: Path):
    """Encuentra todos los frames de incertidumbre y filtra duplicados por SHA-256."""
    extensiones = {".jpg", ".jpeg", ".png"}
    todos_los_archivos = [
        f for f in input_dir.rglob("*")
        if f.is_file() and f.suffix.lower() in extensiones
    ]

    hashes_vistos = {}
    unicos = []
    duplicados = []

    for f in sorted(todos_los_archivos):
        h = calcular_sha256(f)
        if h in hashes_vistos:
            duplicados.append({
                "archivo": f,
                "hash": h,
                "original": hashes_vistos[h]
            })
        else:
            hashes_vistos[h] = f
            tecnica = f.parent.name
            unicos.append({
                "archivo": f,
                "hash": h,
                "tecnica": tecnica,
                "tamaño_bytes": f.stat().st_size
            })

    return unicos, duplicados

def ejecutar_dry_run(input_dir: Path, log_csv_path: Path):
    """Ejecuta análisis de deduplicación y reporte sin modificar archivos ni datasets."""
    print("=" * 70)
    print("DATA FLYWHEEL: MODO DRY-RUN (ANÁLISIS Y DEDUPLICACIÓN)")
    print("=" * 70)
    print(f"Directorio de entrada: {input_dir.resolve()}")

    if not input_dir.exists():
        print(f"❌ Error: El directorio {input_dir} no existe.")
        return 1

    unicos, duplicados = descubrir_frames(input_dir)
    total_frames = len(unicos) + len(duplicados)
    log_meta = cargar_log_incertidumbre(log_csv_path)

    print(f"\n📊 RESUMEN DE INVENTARIO:")
    print(f"  • Total de frames detectados:     {total_frames}")
    print(f"  • Frames únicos (candidatos):     {len(unicos)}")
    print(f"  • Frames duplicados (filtrados):  {len(duplicados)}")

    # Desglose por técnica
    por_tecnica = {}
    for item in unicos:
        tec = item["tecnica"]
        por_tecnica[tec] = por_tecnica.get(tec, 0) + 1

    print(f"\n🥋 DISTRIBUCIÓN POR TÉCNICA / CONTEXTO (Únicos):")
    for tec, count in sorted(por_tecnica.items()):
        print(f"  • {tec:<40}: {count:>4} frames")

    # Muestra de duplicados detectados
    if duplicados:
        print(f"\n♻️ EJEMPLOS DE DUPLICADOS ELIMINADOS:")
        for dup in duplicados[:5]:
            print(f"  • Duplicado: {dup['archivo'].name} (SHA: {dup['hash'][:10]}...) -> Original: {dup['original'].relative_to(input_dir)}")
        if len(duplicados) > 5:
            print(f"  • ... y {len(duplicados) - 5} duplicados más.")

    print("\n✅ Conclusión Dry-Run: {0} frames listos para auto-etiquetado con --prepare.".format(len(unicos)))
    print("=" * 70)
    return 0

def ejecutar_prepare(input_dir: Path, output_dir: Path, model_path: Path, log_csv_path: Path):
    """
    Auto-etiqueta frames únicos usando el modelo maestro yolo26x-pose.pt y
    genera el dataset listo en formato YOLO Pose (images, labels, dataset.yaml).
    """
    print("=" * 70)
    print("DATA FLYWHEEL: MODO PREPARE (AUTO-ETIQUETADO CON MODELO MAESTRO)")
    print("=" * 70)
    print(f"Directorio de entrada: {input_dir.resolve()}")
    print(f"Directorio de destino: {output_dir.resolve()}")
    print(f"Modelo maestro:        {model_path.resolve()}")

    if not model_path.exists():
        print(f"❌ Error: Modelo maestro no encontrado en {model_path}")
        return 1

    unicos, duplicados = descubrir_frames(input_dir)
    if not unicos:
        print("⚠️ No hay frames únicos para procesar.")
        return 0

    print(f"\n📦 Preparando {len(unicos)} frames únicos (se omitieron {len(duplicados)} duplicados)...")

    # Preparar directorios de destino
    images_train = output_dir / "images" / "train"
    images_val = output_dir / "images" / "val"
    labels_train = output_dir / "labels" / "train"
    labels_val = output_dir / "labels" / "val"

    for d in [images_train, images_val, labels_train, labels_val]:
        d.mkdir(parents=True, exist_ok=True)

    # Cargar modelo maestro YOLO26x-Pose
    import torch
    from ultralytics import YOLO
    import cv2

    _orig = torch.load
    def _safe_load(*a, **kw):
        kw["weights_only"] = False
        return _orig(*a, **kw)
    torch.load = _safe_load

    _device = "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"Cargando {model_path.name} en {_device.upper()}...")
    master_model = YOLO(str(model_path))

    manifest_records = []
    val_split_modulo = 5  # 80% train, 20% val

    for idx, item in enumerate(unicos):
        src_img = item["archivo"]
        is_val = (idx % val_split_modulo == 0) and len(unicos) >= 5
        target_img_dir = images_val if is_val else images_train
        target_lbl_dir = labels_val if is_val else labels_train

        # Nombre seguro y único: hash_prefijo + stem original
        clean_name = f"{item['tecnica']}_{item['hash'][:8]}_{src_img.stem}"
        dest_img_path = target_img_dir / f"{clean_name}{src_img.suffix}"
        dest_lbl_path = target_lbl_dir / f"{clean_name}.txt"

        # Copiar imagen al dataset
        shutil.copy2(src_img, dest_img_path)

        # Inferencia de alta fidelidad con modelo maestro
        results = master_model.predict(
            source=str(dest_img_path),
            device=_device,
            verbose=False,
            conf=0.20
        )

        r = results[0]
        lineas_yolo = []
        img_h, img_w = r.orig_shape

        if r.boxes is not None and r.keypoints is not None:
            boxes_data = r.boxes.xywhn.cpu().numpy()  # x_center, y_center, width, height normalizados
            kpts_data = r.keypoints.data.cpu().numpy()  # (N, 17, 3) donde [x, y, conf]

            for b_idx in range(len(boxes_data)):
                bx, by, bw, bh = boxes_data[b_idx]
                kpts = kpts_data[b_idx]

                linea_parts = [f"0 {bx:.6f} {by:.6f} {bw:.6f} {bh:.6f}"]
                for k in range(17):
                    kx, ky, kconf = kpts[k]
                    # Normalizar coordenadas de keypoints a [0, 1]
                    norm_kx = max(0.0, min(1.0, kx / img_w))
                    norm_ky = max(0.0, min(1.0, ky / img_h))

                    # Flag de visibilidad YOLO pose: 2 = visible, 1 = ocluido, 0 = no visible
                    if kconf >= 0.40 and 0.0 <= norm_kx <= 1.0 and 0.0 <= norm_ky <= 1.0:
                        v = 2
                    elif kconf >= 0.10:
                        v = 1
                    else:
                        v = 0
                        norm_kx = 0.0
                        norm_ky = 0.0

                    linea_parts.append(f"{norm_kx:.6f} {norm_ky:.6f} {v}")

                lineas_yolo.append(" ".join(linea_parts))

        # Escribir archivo de etiquetas en formato YOLO
        with open(dest_lbl_path, "w", encoding="utf-8") as f_lbl:
            if lineas_yolo:
                f_lbl.write("\n".join(lineas_yolo) + "\n")

        manifest_records.append({
            "image": str(dest_img_path.relative_to(output_dir)),
            "label": str(dest_lbl_path.relative_to(output_dir)),
            "split": "val" if is_val else "train",
            "detected_athletes": len(lineas_yolo),
            "sha256": item["hash"],
            "tecnica": item["tecnica"]
        })

    # Generar dataset.yaml
    dataset_yaml_path = output_dir / "dataset.yaml"
    dataset_yaml_content = f"""# Corpocmente - Continuous Learning Dataset (Auto-generated by Data Flywheel)
# Generated: {datetime.now(timezone.utc).isoformat()}
path: {output_dir.resolve()}
train: images/train
val: images/val

# Keypoints COCO 17
kpt_shape: [17, 3]

names:
  0: person
"""
    with open(dataset_yaml_path, "w", encoding="utf-8") as f_yaml:
        f_yaml.write(dataset_yaml_content)

    # Guardar manifiesto de preparación
    manifest_path = output_dir / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f_man:
        json.dump({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "master_model": str(model_path.resolve()),
            "total_prepared": len(manifest_records),
            "records": manifest_records
        }, f_man, indent=2)

    print(f"\n✅ DATASET PREPARADO EXITOSAMENTE:")
    print(f"  • Imágenes train:   {len(list(images_train.glob('*')))}")
    print(f"  • Imágenes val:     {len(list(images_val.glob('*')))}")
    print(f"  • Etiquetas train:  {len(list(labels_train.glob('*')))}")
    print(f"  • Etiquetas val:    {len(list(labels_val.glob('*')))}")
    print(f"  • Configuración:    {dataset_yaml_path.resolve()}")
    print(f"  • Manifiesto:       {manifest_path.resolve()}")

    print("\n" + "!" * 70)
    print("⚠️ GUARDRAIL DE ARQUITECTURA (CRAIG LARMAN - CERO ENTRENAMIENTO CIEGO):")
    print("El dataset ha sido preparado y etiquetado con el modelo maestro yolo26x-pose.pt.")
    print("EL ENTRENAMIENTO AUTOMÁTICO ESTÁ ESTRICTAMENTE PROHIBIDO EN ESTE SCRIPT.")
    print("Para realizar fine-tuning manual de manera segura, consulte el protocolo en:")
    print(f"{output_dir / 'README_CONTINUOUS_LEARNING.md'}")
    print("!" * 70 + "\n")
    return 0

def main():
    parser = argparse.ArgumentParser(
        description="Data Flywheel Orchestrator: Gestión de casos borde y preparación de datasets para Continuous Learning."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--dry-run",
        action="store_true",
        help="Analiza frames con incertidumbre, elimina duplicados por SHA-256 y muestra métricas sin alterar datasets."
    )
    group.add_argument(
        "--prepare",
        action="store_true",
        help="Auto-etiqueta frames únicos usando el modelo maestro (yolo26x-pose) y genera dataset en formato YOLO."
    )

    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("backend/storage/uncertainty_frames"),
        help="Ruta a los frames de incertidumbre."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("backend/storage/continuous_dataset"),
        help="Ruta de destino para el dataset preparado."
    )
    parser.add_argument(
        "--master-model",
        type=Path,
        default=None,
        help="Ruta al modelo maestro (default: yolo26x-pose.pt)."
    )

    args = parser.parse_args()

    # Resolver rutas relativas si se ejecuta desde backend/ o raíz
    base_dir = Path(__file__).resolve().parents[1]
    input_dir = args.input_dir if args.input_dir.is_absolute() else base_dir / args.input_dir
    output_dir = args.output_dir if args.output_dir.is_absolute() else base_dir / args.output_dir
    log_csv = input_dir / "log.csv"

    # Buscar modelo maestro
    if args.master_model:
        model_path = args.master_model if args.master_model.is_absolute() else base_dir / args.master_model
    else:
        candidatos_modelo = [
            base_dir / "backend" / "yolo26x-pose.pt",
            base_dir / "yolo26x-pose.pt",
            base_dir / "storage" / "models" / "yolo26x-pose.pt",
            base_dir / "backend" / "storage" / "models" / "yolo26x-pose.pt",
        ]
        model_path = next((c for c in candidatos_modelo if c.exists()), base_dir / "yolo26x-pose.pt")

    if args.dry_run:
        sys.exit(ejecutar_dry_run(input_dir, log_csv))
    elif args.prepare:
        sys.exit(ejecutar_prepare(input_dir, output_dir, model_path, log_csv))

if __name__ == "__main__":
    main()
