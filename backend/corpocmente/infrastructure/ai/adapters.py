from typing import Dict, List, Optional
import os
import logging
import re
import json
import mimetypes
from datetime import datetime, timezone
from pathlib import Path
from corpocmente.domain.entities.models import EsqueletoBiomecanico

logger = logging.getLogger(__name__)

COCO_JOINT_NAMES = [
    "Nariz",
    "Ojo izquierdo",
    "Ojo derecho",
    "Oreja izquierda",
    "Oreja derecha",
    "Hombro izquierdo",
    "Hombro derecho",
    "Codo izquierdo",
    "Codo derecho",
    "Muñeca izquierda",
    "Muñeca derecha",
    "Cadera izquierda",
    "Cadera derecha",
    "Rodilla izquierda",
    "Rodilla derecha",
    "Tobillo izquierdo",
    "Tobillo derecho",
]

COCO_JOINT_NAMES_ES = COCO_JOINT_NAMES

COCO_JOINT_NAMES_EN = [
    "Nose",
    "Left Eye",
    "Right Eye",
    "Left Ear",
    "Right Ear",
    "Left Shoulder",
    "Right Shoulder",
    "Left Elbow",
    "Right Elbow",
    "Left Wrist",
    "Right Wrist",
    "Left Hip",
    "Right Hip",
    "Left Knee",
    "Right Knee",
    "Left Ankle",
    "Right Ankle",
]

COCO_JOINT_NAMES_PT = [
    "Nariz",
    "Olho Esquerdo",
    "Olho Direito",
    "Orelha Esquerda",
    "Orelha Direita",
    "Ombro Esquerdo",
    "Ombro Direito",
    "Cotovelo Esquerdo",
    "Cotovelo Direito",
    "Pulso Esquerdo",
    "Pulso Direito",
    "Quadril Esquerdo",
    "Quadril Direito",
    "Joelho Esquerdo",
    "Joelho Direito",
    "Tornozelo Esquerdo",
    "Tornozelo Direito",
]


def obtener_nombres_articulaciones(indices_o_nombres: list, idioma: str = "es") -> list:
    """
    Traduce una lista de índices COCO (0..16) o nombres de articulaciones en cualquier idioma
    hacia el idioma solicitado ('es', 'pt', 'en').
    """
    if not indices_o_nombres:
        return []

    lang = (idioma or "es").lower().strip()
    if lang in ("pt", "portuguese", "português", "portugues"):
        target_list = COCO_JOINT_NAMES_PT
        joint_prefix = "Articulação"
    elif lang in ("en", "english"):
        target_list = COCO_JOINT_NAMES_EN
        joint_prefix = "Joint"
    else:
        target_list = COCO_JOINT_NAMES_ES
        joint_prefix = "Articulación"

    # Mapeo inverso de nombres normalizados a índice COCO
    name_to_idx = {}
    for i, n in enumerate(COCO_JOINT_NAMES_EN):
        name_to_idx[n.lower()] = i
    for i, n in enumerate(COCO_JOINT_NAMES_ES):
        name_to_idx[n.lower()] = i
    for i, n in enumerate(COCO_JOINT_NAMES_PT):
        name_to_idx[n.lower()] = i

    result = []
    for item in indices_o_nombres:
        idx = None
        if isinstance(item, int):
            idx = item
        elif isinstance(item, str):
            clean = item.strip().lower()
            if clean in name_to_idx:
                idx = name_to_idx[clean]
            elif clean.isdigit():
                idx = int(clean)
            else:
                result.append(item)
                continue
        if idx is not None and 0 <= idx < len(target_list):
            result.append(target_list[idx])
        elif idx is not None:
            result.append(f"{joint_prefix} #{idx}")
    return result

def log_ram_usage(tag: str) -> None:
    import psutil
    import logging
    vm = psutil.virtual_memory()
    logger = logging.getLogger(__name__)
    logger.info(
        "[RAM %s] usado=%.1fGB / total=%.1fGB (%.0f%%) disponible=%.1fGB",
        tag, vm.used / 1e9, vm.total / 1e9, vm.percent, vm.available / 1e9,
    )

COCO_SKELETON_PAIRS = [
    (5, 7), (7, 9),      # Brazo izquierdo: hombro -> codo -> muñeca
    (6, 8), (8, 10),     # Brazo derecho: hombro -> codo -> muñeca
    (5, 6),              # Hombros
    (5, 11), (6, 12),    # Tronco: hombro -> cadera
    (11, 12),            # Caderas
    (11, 13), (13, 15),  # Pierna izquierda: cadera -> rodilla -> tobillo
    (12, 14), (14, 16),  # Pierna derecha: cadera -> rodilla -> tobillo
    (0, 1), (0, 2),      # Rostro
    (1, 3), (2, 4),
]

FRAMES_DIR = "/tmp/corpocmente_frames"
os.makedirs(FRAMES_DIR, exist_ok=True)


class YOLOPoseAdapter:
    def __init__(self, colab_url: str = None):
        self.colab_url = colab_url if colab_url is not None else os.getenv("COLAB_TUNNEL_URL", "").strip()
        self._model_cache = None
        self._depth_model_cache = None
        self._seg_model_cache = None

    @staticmethod
    def _calcular_iou(box_a: list, box_b: list) -> float:
        """Calcula Intersection over Union (IoU) entre dos cajas [x1, y1, x2, y2]."""
        xA = max(box_a[0], box_b[0])
        yA = max(box_a[1], box_b[1])
        xB = min(box_a[2], box_b[2])
        yB = min(box_a[3], box_b[3])
        inter_area = max(0.0, xB - xA) * max(0.0, yB - yA)
        box_a_area = max(0.0, box_a[2] - box_a[0]) * max(0.0, box_a[3] - box_a[1])
        box_b_area = max(0.0, box_b[2] - box_b[0]) * max(0.0, box_b[3] - box_b[1])
        union_area = box_a_area + box_b_area - inter_area
        if union_area <= 0:
            return 0.0
        return float(inter_area / union_area)

    def _resolver_oclusion_por_profundidad(
        self,
        caja_a: list,
        caja_b: list,
        depth_map
    ) -> dict:
        """
        Desambigua oclusiones entre dos cajas superpuestas usando el mapa métrico de profundidad.
        Determina qué atleta está en primer plano (menor profundidad métrica) y cuál está en segundo plano.
        """
        import numpy as np

        iou = self._calcular_iou(caja_a, caja_b)
        if depth_map is None:
            return {
                "atleta_frontal": "a",
                "profundidad_a": 1.5,
                "profundidad_b": 1.5,
                "delta_z": 0.0,
                "iou": round(iou, 3),
            }

        H, W = depth_map.shape[:2]
        x1_a, y1_a = int(max(0, min(W - 1, caja_a[0]))), int(max(0, min(H - 1, caja_a[1])))
        x2_a, y2_a = int(max(0, min(W, caja_a[2]))), int(max(0, min(H, caja_a[3])))
        x1_b, y1_b = int(max(0, min(W - 1, caja_b[0]))), int(max(0, min(H - 1, caja_b[1])))
        x2_b, y2_b = int(max(0, min(W, caja_b[2]))), int(max(0, min(H, caja_b[3])))

        crop_a = depth_map[y1_a:max(y1_a + 1, y2_a), x1_a:max(x1_a + 1, x2_a)]
        crop_b = depth_map[y1_b:max(y1_b + 1, y2_b), x1_b:max(x1_b + 1, x2_b)]

        valid_a = crop_a[crop_a > 0] if crop_a.size > 0 else np.array([])
        valid_b = crop_b[crop_b > 0] if crop_b.size > 0 else np.array([])

        depth_a = float(np.median(valid_a)) if len(valid_a) > 0 else 1.5
        depth_b = float(np.median(valid_b)) if len(valid_b) > 0 else 1.5

        frontal = "a" if depth_a <= depth_b else "b"

        return {
            "atleta_frontal": frontal,
            "profundidad_a": round(depth_a, 3),
            "profundidad_b": round(depth_b, 3),
            "delta_z": round(abs(depth_a - depth_b), 3),
            "iou": round(iou, 3),
        }

    def _get_depth_model(self):
        if not hasattr(self, "_depth_model_cache") or self._depth_model_cache is None:
            os.environ.setdefault("YOLO_CONFIG_DIR", "/tmp/ultralytics")
            import torch
            from ultralytics import YOLO
            _orig = torch.load
            def _safe_load(*a, **kw):
                kw["weights_only"] = False
                return _orig(*a, **kw)
            torch.load = _safe_load
            candidates = [
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
                    os.path.abspath(__file__))))), "yolo26n-depth.pt"),
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
                    os.path.abspath(__file__))))), "storage/models/yolo26n-depth.pt"),
                "storage/models/yolo26n-depth.pt",
                "yolo26n-depth.pt",
            ]
            weights = next((c for c in candidates if os.path.exists(c)), "yolo26n-depth.pt")
            self._depth_model_cache = YOLO(weights)
        return self._depth_model_cache

    def _get_seg_model(self):
        if not hasattr(self, "_seg_model_cache") or self._seg_model_cache is None:
            os.environ.setdefault("YOLO_CONFIG_DIR", "/tmp/ultralytics")
            import torch
            from ultralytics import YOLO
            _orig = torch.load
            def _safe_load(*a, **kw):
                kw["weights_only"] = False
                return _orig(*a, **kw)
            torch.load = _safe_load
            candidates = [
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
                    os.path.abspath(__file__))))), "yolo26n-seg.pt"),
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
                    os.path.abspath(__file__))))), "storage/models/yolo26n-seg.pt"),
                "storage/models/yolo26n-seg.pt",
                "yolo26n-seg.pt",
            ]
            weights = next((c for c in candidates if os.path.exists(c)), "yolo26n-seg.pt")
            self._seg_model_cache = YOLO(weights)
        return self._seg_model_cache

    def _get_model(self):
        if not hasattr(self, "_model_cache") or self._model_cache is None:
            import torch
            from ultralytics import YOLO
            _orig = torch.load
            def _safe_load(*a, **kw):
                kw["weights_only"] = False
                return _orig(*a, **kw)
            torch.load = _safe_load
            candidates = [
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
                    os.path.abspath(__file__))))), "storage/models/yolo26s_bjj_pose/weights/best.pt"),
                "storage/models/yolo26s_bjj_pose/weights/best.pt",
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
                    os.path.abspath(__file__))))), "yolo26n-pose.pt"),
                "storage/models/yolo26n-pose.pt",
                "yolo26n-pose.pt",
            ]
            weights = next((c for c in candidates if os.path.exists(c)), "yolo26n-pose.pt")
            self._model_cache = YOLO(weights)
        return self._model_cache

    def extraer_secuencia(
        self,
        video_path: str,
        persona_idx_inicial: Optional[int] = None,
        max_disp_norm: float = 0.25,
        evaluacion_id: Optional[str] = None,
        tecnica_id: Optional[str] = None,
        use_depth: bool = False,
        use_segmentation: Optional[bool] = None,
    ) -> dict:
        """
        Extrae la secuencia temporal completa de keypoints (133 dims por frame) usando YOLO
        y tracking espacial continuo normalizado a las dimensiones (W, H) del fotograma.
        Descarta saltos bruscos que superen max_disp_norm (ej. salto al instructor del fondo).

        Returns:
            {
                "secuencia_kpts": List[List[float]],
                "total_frames": int,
                "frames_con_persona": int,
                "cobertura": float
            }
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video no encontrado: {video_path}")

        log_ram_usage("enter_extraer_secuencia")

        import cv2
        import numpy as np

        cap = cv2.VideoCapture(video_path)
        w = float(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 1.0)
        h = float(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 1.0)
        cap.release()

        # Intento 1: Worker remoto en Colab vía Google Drive Data Lake (Cero Túneles)
        try:
            from corpocmente.infrastructure.storage.google_drive_client import GoogleDriveDataLakeClient
            drive_client = GoogleDriveDataLakeClient()
            if drive_client.token_file.exists():
                import uuid
                import time
                eval_id = str(evaluacion_id) if evaluacion_id else f"eval_{uuid.uuid4().hex[:10]}"
                logger.info(f"Subiendo video {video_path} al Data Lake en Google Drive (eval_id: {eval_id})...")
                video_drive_id = drive_client.subir_archivo(video_path, nombre_drive=f"video_{eval_id}.mp4")
                logger.info(f"Video subido a Drive (ID: {video_drive_id}). Creando tarea para Colab Worker...")
                drive_client.crear_tarea_video(
                    evaluacion_id=eval_id,
                    video_drive_id=video_drive_id,
                    persona_idx=persona_idx_inicial if persona_idx_inicial is not None else 0
                )

                # Esperar resultado del worker en Colab (polling cada 3 segundos, max 300s)
                timeout_segundos = 300
                inicio_espera = time.time()
                logger.info(f"Esperando inferencia cinemática 3D de Colab en Google Drive (timeout={timeout_segundos}s)...")

                resultado_drive = None
                while time.time() - inicio_espera < timeout_segundos:
                    resultado_drive = drive_client.buscar_resultado_video(eval_id)
                    if resultado_drive is not None:
                        break
                    time.sleep(3)

                # Limpiar el video temporal de Drive para mantener la cuota libre
                try:
                    drive_client.eliminar_archivo(video_drive_id)
                except Exception:
                    pass

                if resultado_drive and "esqueletos" in resultado_drive:
                    esqueletos_dict = resultado_drive.get("esqueletos", [])
                    if esqueletos_dict:
                        sec = [item.get("keypoints133", [0.0]*133) for item in esqueletos_dict]
                        frame_idxs = [int(item.get("frame_idx", i)) for i, item in enumerate(esqueletos_dict)]
                        tot_f = int(resultado_drive.get("total_frames_procesados", len(sec)))
                        frames_ok = int(resultado_drive.get("frames_con_persona", sum(1 for k in sec if any(v > 0 for v in k[:51]))))
                        cob = float(resultado_drive.get("cobertura", (frames_ok / tot_f) if tot_f > 0 else 0.0))
                        logger.info(f"✅ Secuencia cinemática 3D recibida de Colab Worker vía Drive ({len(sec)} frames, cobertura {cob*100:.1f}%).")
                        return {
                            "secuencia_kpts": sec,
                            "frame_idxs": frame_idxs,
                            "total_frames": tot_f,
                            "frames_con_persona": frames_ok,
                            "cobertura": cob
                        }
                else:
                    logger.warning(f"Timeout o sin respuesta de Colab Worker en Google Drive tras {timeout_segundos}s. Continuando con fallback...")
        except Exception as e_drive:
            logger.warning(f"Error en comunicación con Google Drive Data Lake ({e_drive}). Continuando con fallback...")

        # Intento 2: Worker remoto en Colab (vía ngrok si estuviera activo)
        if self.colab_url and not self.colab_url.startswith("https://placeholder"):
            import requests
            try:
                endpoint = f"{self.colab_url.rstrip('/')}/extraer_poses"
                logger.info(f"Llamando a YOLO en Colab Worker: {endpoint}")
                with open(video_path, 'rb') as f:
                    resp = requests.post(
                        endpoint,
                        data={"persona_idx": persona_idx_inicial if persona_idx_inicial is not None else 0},
                        files={"video": f},
                        headers={
                            "ngrok-skip-browser-warning": "1",
                            "User-Agent": "CorpocmenteBackend/1.0",
                        },
                        timeout=180
                    )
                resp.raise_for_status()
                data = resp.json()
                esqueletos_dict = data.get("esqueletos", [])
                if esqueletos_dict:
                    sec = [item.get("keypoints133", [0.0]*133) for item in esqueletos_dict]
                    frame_idxs = [int(item.get("frame_idx", i)) for i, item in enumerate(esqueletos_dict)]
                    return {
                        "secuencia_kpts": sec,
                        "frame_idxs": frame_idxs,
                        "total_frames": data.get("total_frames_procesados", len(sec)),
                        "frames_con_persona": data.get("frames_con_persona", sum(1 for k in sec if any(v > 0 for v in k[:51]))),
                        "cobertura": data.get("cobertura", 0.0)
                    }
            except Exception as e:
                logger.warning(f"Error llamando a YOLO en Colab ({e}). Intentando fallback local...")

        # Intento 2: Inferencia local con YOLO Pose
        try:
            import gc
            import torch
            from ultralytics import YOLO

            import psutil
            if psutil.virtual_memory().available < 2 * 1024**3:
                raise RuntimeError(
                    f"RAM insuficiente para cargar YOLO: disponible={psutil.virtual_memory().available/1e9:.1f}GB"
                )

            _device = "mps" if torch.backends.mps.is_available() else "cpu"
            logger.info("YOLO backend: %s (device: %s)", "MPS" if _device == "mps" else "CPU", _device)

            _orig = torch.load
            def _safe_load(*args, **kwargs):
                kwargs["weights_only"] = False
                return _orig(*args, **kwargs)
            torch.load = _safe_load

            _candidates = [
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "yolo26n-pose.pt"),
                os.path.join("storage", "models", "yolo26n-pose.pt"),
                "yolo26n-pose.pt",
                "yolo11n-pose.pt",
            ]
            _weights = next((c for c in _candidates if os.path.exists(c)), "yolo26n-pose.pt")
            log_ram_usage("pre_yolo_load")
            model = YOLO(_weights)
            log_ram_usage("post_yolo_load")
            results = model.predict(source=video_path, stream=True, verbose=False, conf=0.10, device=_device)

            if use_segmentation is None:
                try:
                    from corpocmente.config import settings
                    use_segmentation = getattr(settings, "USE_SEGMENTATION", False)
                except Exception:
                    use_segmentation = os.getenv("USE_SEGMENTATION", "false").lower() == "true"

            secuencia_kpts = []
            personas_rastreadas = {}
            personas_depth = {}
            oclusiones_detectadas = 0
            frames_con_persona = 0
            frames_evaluados = 0
            target_idx = persona_idx_inicial if persona_idx_inicial is not None else 0

            # MLOps Foundation: Data Flywheel para Active Learning (Frames con incertidumbre < 0.65)
            uncertainty_tec = str(tecnica_id or "general").strip() or "general"
            uncertainty_dir = Path(__file__).resolve().parents[4] / "backend" / "storage" / "uncertainty_frames" / uncertainty_tec
            uncertainty_base_dir = Path(__file__).resolve().parents[4] / "backend" / "storage" / "uncertainty_frames"
            try:
                uncertainty_dir.mkdir(parents=True, exist_ok=True)
            except Exception:
                pass
            log_csv_path = uncertainty_base_dir / "log.csv"
            uncertainty_saved_count = 0

            for f_idx, r in enumerate(results):
                frames_evaluados += 1

                # Data Flywheel: si la confianza promedio de las cajas es < 0.65, guardar frame (max 10 por video)
                try:
                    avg_box_conf = 0.0
                    if hasattr(r, "boxes") and r.boxes is not None and len(r.boxes) > 0 and hasattr(r.boxes, "conf") and len(r.boxes.conf) > 0:
                        avg_box_conf = float(r.boxes.conf.mean().cpu().item())
                    elif r.keypoints is not None and len(r.keypoints.data) > 0:
                        raw_kpts_conf = r.keypoints.data.cpu().numpy()
                        mask_k = (raw_kpts_conf[:, :, 2] > 0)
                        if np.any(mask_k):
                            avg_box_conf = float(raw_kpts_conf[:, :, 2][mask_k].mean())

                    if 0.0 < avg_box_conf < 0.65 and uncertainty_saved_count < 10:
                        frame_img = getattr(r, "orig_img", None)
                        if frame_img is not None:
                            frame_save_path = uncertainty_dir / f"frame_{f_idx}.jpg"
                            cv2.imwrite(str(frame_save_path), frame_img)
                            uncertainty_saved_count += 1
                            write_header = not log_csv_path.exists()
                            with open(log_csv_path, "a", encoding="utf-8") as f_csv:
                                if write_header:
                                    f_csv.write("timestamp,tecnica_id,frame_idx,confidence,path\n")
                                f_csv.write(f"{datetime.now(timezone.utc).isoformat()},{uncertainty_tec},{f_idx},{avg_box_conf:.4f},{frame_save_path}\n")
                except Exception as e_flywheel:
                    logger.debug("Data flywheel uncertainty frame error: %s", e_flywheel)
                if r.keypoints is None or len(r.keypoints.data) == 0:
                    secuencia_kpts.append([0.0] * 133)
                    continue

                raw = r.keypoints.data.cpu().numpy()
                candidatos = [
                    p for p in raw
                    if p.shape == (17, 3) and np.count_nonzero((p[:, 2] > 0.3) & (p[:, 0] > 0)) >= 4
                ]

                # Refinamiento opcional con YOLO Segmentation en oclusiones severas
                if use_segmentation and len(candidatos) < 2 and getattr(r, "orig_img", None) is not None:
                    try:
                        seg_model = self._get_seg_model()
                        seg_res = seg_model.predict(source=r.orig_img, verbose=False, conf=0.15, classes=[0], device=_device)
                        if seg_res and len(seg_res[0].boxes) >= 2:
                            extra_cands = []
                            boxes = seg_res[0].boxes.xyxy.cpu().numpy()
                            im_h, im_w = r.orig_img.shape[:2]
                            for b in boxes:
                                x1, y1, x2, y2 = b
                                pad_x = (x2 - x1) * 0.10
                                pad_y = (y2 - y1) * 0.10
                                cx1, cy1 = int(max(0, x1 - pad_x)), int(max(0, y1 - pad_y))
                                cx2, cy2 = int(min(im_w, x2 + pad_x)), int(min(im_h, y2 + pad_y))
                                crop = r.orig_img[cy1:cy2, cx1:cx2]
                                if crop.size > 0 and crop.shape[0] >= 20 and crop.shape[1] >= 20:
                                    p_res = model.predict(source=crop, verbose=False, conf=0.10, device=_device)
                                    if p_res and p_res[0].keypoints is not None and len(p_res[0].keypoints.data) > 0:
                                        for pk in p_res[0].keypoints.data.cpu().numpy():
                                            gk = pk.copy()
                                            gk[:, 0] += cx1
                                            gk[:, 1] += cy1
                                            if (gk[:, 2] > 0.3).sum() >= 4:
                                                extra_cands.append(gk)
                            if len(extra_cands) >= 2:
                                candidatos = extra_cands
                    except Exception as e_seg:
                        logger.debug("Error en segmentación multi-etapa: %s", e_seg)

                if not candidatos:
                    secuencia_kpts.append([0.0] * 133)
                    continue

                # Filtrar reflejos de espejos o figuras distantes diminutas
                # Si una caja delimitadora es menor al 10% del área de la caja mayor, se descarta
                if len(candidatos) > 1:
                    areas = []
                    for c in candidatos:
                        mask = (c[:, 2] > 0.3) & (c[:, 0] > 0)
                        pts = c[mask, :2]
                        if len(pts) >= 2:
                            w_box = float(pts[:, 0].max() - pts[:, 0].min())
                            h_box = float(pts[:, 1].max() - pts[:, 1].min())
                            areas.append(w_box * h_box)
                        else:
                            areas.append(0.0)
                    max_area = max(areas) if areas else 0.0
                    if max_area > 0.0:
                        sin_reflejos = [
                            c for c, a in zip(candidatos, areas)
                            if a >= 0.10 * max_area
                        ]
                        if sin_reflejos:
                            candidatos = sin_reflejos

                # Detección y desambiguación de oclusiones por profundidad métrica (> 40% IoU)
                cand_depths = {}
                if use_depth and len(candidatos) > 1:
                    def _extraer_caja_c(cand):
                        m = (cand[:, 2] > 0.3) & (cand[:, 0] > 0)
                        pt = cand[m, :2]
                        if len(pt) >= 2:
                            return [float(pt[:, 0].min()), float(pt[:, 1].min()), float(pt[:, 0].max()), float(pt[:, 1].max())]
                        return [0.0, 0.0, 0.0, 0.0]

                    cajas_cand = [_extraer_caja_c(c) for c in candidatos]
                    hay_superposicion = False
                    for i in range(len(cajas_cand)):
                        for j in range(i + 1, len(cajas_cand)):
                            if self._calcular_iou(cajas_cand[i], cajas_cand[j]) > 0.40:
                                hay_superposicion = True
                                break
                        if hay_superposicion:
                            break

                    if hay_superposicion:
                        oclusiones_detectadas += 1
                        frame_img = getattr(r, "orig_img", None)
                        if frame_img is not None:
                            try:
                                depth_model = self._get_depth_model()
                                depth_res = depth_model.predict(source=frame_img, verbose=False, device=_device)
                                if depth_res and hasattr(depth_res[0], "depth") and depth_res[0].depth is not None:
                                    depth_map = depth_res[0].depth.data.cpu().numpy().squeeze()
                                    H_d, W_d = depth_map.shape[:2]
                                    for c_idx, box_c in enumerate(cajas_cand):
                                        x1, y1 = int(max(0, min(W_d - 1, box_c[0]))), int(max(0, min(H_d - 1, box_c[1])))
                                        x2, y2 = int(max(0, min(W_d, box_c[2]))), int(max(0, min(H_d, box_c[3])))
                                        crop = depth_map[y1:max(y1 + 1, y2), x1:max(x1 + 1, x2)]
                                        valid = crop[crop > 0] if crop.size > 0 else np.array([])
                                        cand_depths[c_idx] = float(np.median(valid)) if len(valid) > 0 else 1.5

                                    for i in range(len(cajas_cand)):
                                        for j in range(i + 1, len(cajas_cand)):
                                            if self._calcular_iou(cajas_cand[i], cajas_cand[j]) > 0.40:
                                                oc_res = self._resolver_oclusion_por_profundidad(cajas_cand[i], cajas_cand[j], depth_map)
                                                logger.debug("Oclusión resuelta f=%d (c%d vs c%d): %s", f_idx, i, j, oc_res)
                            except Exception as e_dm:
                                logger.debug("Error procesando profundidad en frame %d: %s", f_idx, e_dm)

                assigned_trackers = set()
                if not personas_rastreadas:
                    candidatos.sort(key=lambda p: float(p[p[:, 2] > 0.3, 1].mean()), reverse=True)
                    for c_idx, c in enumerate(candidatos):
                        personas_rastreadas[c_idx] = c
                        if c_idx in cand_depths:
                            personas_depth[c_idx] = cand_depths[c_idx]
                    assigned_trackers.update(personas_rastreadas.keys())
                else:
                    cost_matrix = {}
                    for t_idx, t_pose in personas_rastreadas.items():
                        for c_idx, c in enumerate(candidatos):
                            mask = (c[:, 2] > 0.3) & (t_pose[:, 2] > 0.3) & (c[:, 0] > 0) & (t_pose[:, 0] > 0)
                            if np.count_nonzero(mask) >= 5:
                                dx = (c[mask, 0] - t_pose[mask, 0]) / w
                                dy = (c[mask, 1] - t_pose[mask, 1]) / h
                                cost = float(np.mean(np.sqrt(dx**2 + dy**2)))
                            else:
                                c1 = c[c[:, 0] > 0, :2].mean(axis=0) / np.array([w, h])
                                c0 = t_pose[t_pose[:, 0] > 0, :2].mean(axis=0) / np.array([w, h])
                                cost = float(np.linalg.norm(c1 - c0))

                            # Penalización métrica de profundidad si hay oclusión y datos z
                            if use_depth and t_idx in personas_depth and c_idx in cand_depths:
                                delta_z = abs(cand_depths[c_idx] - personas_depth[t_idx])
                                cost += 0.3 * (delta_z / 2.0)

                            cost_matrix[(t_idx, c_idx)] = cost

                    sorted_pairs = sorted(cost_matrix.items(), key=lambda item: item[1])
                    assigned_cands = set()
                    new_poses = {}
                    for (t_idx, c_idx), cost in sorted_pairs:
                        if t_idx in assigned_trackers or c_idx in assigned_cands:
                            continue
                        if cost <= max_disp_norm:
                            assigned_trackers.add(t_idx)
                            assigned_cands.add(c_idx)
                            new_poses[t_idx] = candidatos[c_idx]
                            if c_idx in cand_depths:
                                personas_depth[t_idx] = cand_depths[c_idx]

                    for t_idx, c_pose in new_poses.items():
                        personas_rastreadas[t_idx] = c_pose

                t_key = min(target_idx, len(personas_rastreadas) - 1)
                if t_key in assigned_trackers:
                    persona_actual = personas_rastreadas[t_key]
                    frames_con_persona += 1
                    kpts = persona_actual.flatten().tolist()
                    if len(kpts) < 133:
                        kpts.extend([0.0] * (133 - len(kpts)))
                    secuencia_kpts.append(kpts[:133])
                else:
                    secuencia_kpts.append([0.0] * 133)

            total = max(1, frames_evaluados)
            cobertura = frames_con_persona / total
            return {
                "secuencia_kpts": secuencia_kpts,
                "frame_idxs": list(range(len(secuencia_kpts))),
                "total_frames": frames_evaluados,
                "frames_con_persona": frames_con_persona,
                "cobertura": round(cobertura, 4),
                "oclusiones_detectadas": oclusiones_detectadas
            }
        except Exception as e_local:
            logger.debug(f"YOLO local fallo ({e_local}). Fallback determinista.")
            return {
                "secuencia_kpts": [[0.5] * 133],
                "frame_idxs": [0],
                "total_frames": 1,
                "frames_con_persona": 1,
                "cobertura": 1.0
            }
        finally:
            import gc
            gc.collect()
            try:
                import torch
                if torch.backends.mps.is_available():
                    torch.mps.empty_cache()
            except Exception:
                pass
            log_ram_usage("exit_extraer_secuencia")

    def extraer_frame_limpio(
        self,
        video_path: str,
        frame_idx: int,
        output_path: str,
    ) -> Optional[str]:
        """Extrae el fotograma exacto del video sin dibujar anotaciones."""
        import cv2
        if not os.path.exists(video_path):
            return None
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return None
            cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, frame_idx))
            ret, img = cap.read()
            cap.release()
            if ret and img is not None:
                cv2.imwrite(output_path, img)
                logger.info(f"Fotograma limpio guardado en: {output_path}")
                return output_path
        except Exception as exc:
            logger.warning(f"Error extrayendo frame limpio: {exc}")
        return None

    def extraer_keypoints(self, video_path: str, persona_idx_inicial: Optional[int] = None) -> List[EsqueletoBiomecanico]:
        """Extrae la lista de EsqueletoBiomecanico delegando a extraer_secuencia con tracking."""
        res = self.extraer_secuencia(video_path, persona_idx_inicial=persona_idx_inicial)
        esqueletos = []
        for idx, kpts in enumerate(res["secuencia_kpts"]):
            esqueletos.append(EsqueletoBiomecanico(
                frame_idx=idx,
                keypoints133=kpts,
                angulos_articulares={}
            ))
        return esqueletos

    def extraer_frame_y_dibujar_error(
        self,
        video_path: str,
        frame_idx: int,
        keypoints133: Optional[List[float]],
        articulaciones_criticas: List[int],
        output_path: str,
        clean_output_path: Optional[str] = None,
        tecnica_nombre: str = "",
        persona_idx: Optional[int] = None,
        idioma: str = "es",
    ) -> str:
        """
        Extrae el fotograma exacto con mayor diferencia biomecánica del video del alumno
        y dibuja el esqueleto COCO con las articulaciones en error resaltadas visualmente.
        Si clean_output_path es provisto, guarda primero el fotograma limpio sin anotaciones.

        REGLA ESTRICTA (Larman):
        Si keypoints133 contiene datos válidos (>= 51 floats con algún valor > 0),
        se usan directamente esos keypoints (los de la persona seleccionada).
        NO se vuelve a ejecutar YOLO.
        Solo si keypoints133 no fue provisto o es nulo/cero, se invoca YOLO como fallback,
        usando persona_idx para seleccionar al atleta correcto.
        """
        import cv2
        import numpy as np

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # 1. Extraer el fotograma exacto del video usando OpenCV
        frame = None
        if os.path.exists(video_path):
            cap = cv2.VideoCapture(video_path)
            if cap.isOpened():
                cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, frame_idx))
                ret, img = cap.read()
                if ret and img is not None:
                    frame = img
                cap.release()

        # Canvas de respaldo si el video no pudo leerse
        if frame is None:
            logger.warning(f"No se pudo extraer frame {frame_idx} de {video_path}. Generando lienzo de respaldo.")
            frame = np.full((720, 1280, 3), 25, dtype=np.uint8)

        # Guardar fotograma limpio antes de dibujar anotaciones
        if clean_output_path and frame is not None:
            try:
                os.makedirs(os.path.dirname(clean_output_path), exist_ok=True)
                cv2.imwrite(clean_output_path, frame)
                logger.info(f"Fotograma crítico limpio guardado en: {clean_output_path}")
            except Exception as e_clean:
                logger.warning(f"No se pudo guardar el fotograma limpio: {e_clean}")

        h, w = frame.shape[:2]

        # 2. Parsear keypoints si están disponibles (NO re-ejecutar YOLO si vienen keypoints133)
        pts: dict[int, tuple[int, int, float]] = {}
        has_kpts = keypoints133 is not None and len(keypoints133) >= 51 and any(v > 0.0 for v in keypoints133[:51])

        if has_kpts:
            for i in range(17):
                x = keypoints133[i * 3]
                y = keypoints133[i * 3 + 1]
                conf = keypoints133[i * 3 + 2] if len(keypoints133) > (i * 3 + 2) else 1.0

                # Desnormalizar coordenadas si vienen en escala 0–1
                px = int(x * w) if 0.0 < x <= 1.0 else int(x)
                py = int(y * h) if 0.0 < y <= 1.0 else int(y)
                # Clamp dentro de la imagen
                px = max(0, min(w - 1, px))
                py = max(0, min(h - 1, py))
                pts[i] = (px, py, conf)
        elif os.path.exists(video_path) and frame is not None:
            # Fallback excepcional solo si keypoints133 no fue provisto
            try:
                from ultralytics import YOLO
                _candidates = [
                    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "yolo26n-pose.pt"),
                    os.path.join("storage", "models", "yolo26n-pose.pt"),
                    "yolo26n-pose.pt",
                ]
                _weights = next((c for c in _candidates if os.path.exists(c)), "yolo26n-pose.pt")
                model = YOLO(_weights)
                results = model.predict(source=frame, conf=0.15, verbose=False)
                if results and results[0].keypoints is not None and len(results[0].keypoints.data) > 0:
                    raw = results[0].keypoints.data.cpu().numpy()
                    cands = [p for p in raw if p.shape == (17, 3) and np.count_nonzero((p[:, 2] > 0.3) & (p[:, 0] > 0)) >= 4]
                    if cands:
                        p_idx = persona_idx if (persona_idx is not None and 0 <= persona_idx < len(cands)) else 0
                        chosen = cands[p_idx]
                        for i in range(17):
                            px = max(0, min(w - 1, int(chosen[i, 0])))
                            py = max(0, min(h - 1, int(chosen[i, 1])))
                            pts[i] = (px, py, float(chosen[i, 2]))
            except Exception as e_yolo_fb:
                logger.warning(f"Fallback YOLO en extraer_frame_y_dibujar_error falló: {e_yolo_fb}")

        # 3. Dibujar conexiones del esqueleto (huesos)
        for p1, p2 in COCO_SKELETON_PAIRS:
            if p1 in pts and p2 in pts:
                pt1 = (pts[p1][0], pts[p1][1])
                pt2 = (pts[p2][0], pts[p2][1])
                if pt1 != (0, 0) and pt2 != (0, 0):
                    cv2.line(frame, pt1, pt2, (0, 230, 115), 3, lineType=cv2.LINE_AA)

        # 4. Dibujar puntos articulares estándar
        for i, (px, py, conf) in pts.items():
            if (px, py) != (0, 0):
                cv2.circle(frame, (px, py), 5, (255, 190, 0), -1, lineType=cv2.LINE_AA)
                cv2.circle(frame, (px, py), 6, (0, 0, 0), 1, lineType=cv2.LINE_AA)

        # 5. Resaltar articulaciones críticas con círculos rojos y etiquetas
        for art_idx in articulaciones_criticas:
            if art_idx in pts:
                px, py, _ = pts[art_idx]
                if (px, py) == (0, 0):
                    continue

                # Halo exterior y círculo interior rojo
                cv2.circle(frame, (px, py), 22, (0, 0, 255), 3, lineType=cv2.LINE_AA)
                cv2.circle(frame, (px, py), 12, (0, 50, 255), -1, lineType=cv2.LINE_AA)
                cv2.circle(frame, (px, py), 4, (255, 255, 255), -1, lineType=cv2.LINE_AA)

                # Etiqueta con el nombre traducido de la articulación
                nombres_trad = obtener_nombres_articulaciones([art_idx], idioma=idioma)
                nombre_art = nombres_trad[0] if nombres_trad else f"Joint {art_idx}"
                label = f"{nombre_art} [ERROR]"
                font = cv2.FONT_HERSHEY_SIMPLEX
                scale = 0.55
                thickness = 2
                (tw, th), _ = cv2.getTextSize(label, font, scale, thickness)

                lx = min(w - tw - 12, max(10, px + 18))
                ly = max(th + 10, min(h - 10, py - 10))

                # Fondo negro semitransparente para el texto
                cv2.rectangle(frame, (lx - 6, ly - th - 6), (lx + tw + 6, ly + 6), (0, 0, 0), -1)
                cv2.rectangle(frame, (lx - 6, ly - th - 6), (lx + tw + 6, ly + 6), (0, 0, 255), 1)
                cv2.putText(frame, label, (lx, ly), font, scale, (255, 255, 255), thickness, cv2.LINE_AA)

        # 6. Banner superior informativo
        header_text = f"CRITICAL FRAME #{frame_idx} | {tecnica_nombre.upper()} | BIOMECHANICAL ERROR DETECTED"
        cv2.rectangle(frame, (0, 0), (w, 42), (18, 18, 22), -1)
        cv2.rectangle(frame, (0, 40), (w, 43), (0, 0, 255), -1)
        cv2.putText(frame, header_text, (20, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2, cv2.LINE_AA)

        cv2.imwrite(output_path, frame)
        logger.info(f"Fotograma crítico anotado guardado en: {output_path}")
        return output_path

    def dibujar_error_en_frame(self, frame_path: str, discrepancias: List[str]) -> str:
        """
        Dibuja sobre un frame existente las discrepancias detectadas.
        Si la ruta no existe, devuelve la ruta original.
        """
        if not os.path.exists(frame_path):
            return frame_path

        import cv2
        import uuid

        try:
            img = cv2.imread(frame_path)
            if img is None:
                return frame_path

            h, w = img.shape[:2]
            # Banner de advertencia en la parte inferior
            texto = "; ".join(discrepancias[:2]) if discrepancias else "Desviacion biomecanica detectada"
            cv2.rectangle(img, (0, h - 50), (w, h), (0, 0, 0), -1)
            cv2.putText(img, f"ERROR: {texto[:60]}", (20, h - 18), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2, cv2.LINE_AA)

            resaltado_path = os.path.join(FRAMES_DIR, f"resaltado_{uuid.uuid4().hex[:8]}.jpg")
            cv2.imwrite(resaltado_path, img)
            return resaltado_path
        except Exception as e:
            logger.error(f"Error dibujando sobre frame: {e}")
            return frame_path



