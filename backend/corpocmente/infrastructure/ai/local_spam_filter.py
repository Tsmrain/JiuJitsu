import pickle
import logging
import numpy as np
import cv2
from pathlib import Path

logger = logging.getLogger(__name__)

# Clases que NO cuentan como BJJ activo (bailarinas paradas también son "standing")
NO_BJJ = {"standing"}

# Clases con modelo débil (F1 < 0.85): umbral de confianza más bajo
CLASES_DEBILES = {"takedown", "half_guard"}
CONF_DEBIL = 0.60
CONF_FUERTE = 0.70

class LocalSpamFilter:
    def __init__(self, yolo_adapter,
                 classifier_path="storage/models/position_classifier_grouped.pkl",
                 min_bjj_ratio=0.60,
                 num_frames=12,
                 min_interaction_frames=None):
        path = Path(classifier_path)
        if not path.exists():
            alt_path = Path(__file__).resolve().parents[3] / classifier_path
            if alt_path.exists():
                path = alt_path
            else:
                alt_path2 = Path(__file__).resolve().parents[3] / "backend" / classifier_path
                if alt_path2.exists():
                    path = alt_path2
        with open(path, "rb") as f:
            data = pickle.load(f)
        self.clf = data["model"]
        self.labels = data["labels"]
        self.yolo = yolo_adapter
        self.min_bjj_ratio = min_bjj_ratio
        self.num_frames = num_frames
        self.min_interaction_frames = min_interaction_frames
        logger.info("LocalSpamFilter cargado: accuracy=%s, f1=%s, min_bjj_ratio=%.2f, min_interaction_frames=%s",
                    data.get("accuracy_test"), data.get("f1_macro_test"),
                    self.min_bjj_ratio,
                    str(self.min_interaction_frames) if self.min_interaction_frames is not None else "dynamic(min=3, 15%)")

    def _kpts_to_flat(self, pose):
        if len(pose) == 1 and len(pose[0]) >= 51:
            return [float(x) for x in pose[0][:51]]
        if len(pose) >= 51 and isinstance(pose[0], (int, float)):
            return [float(x) for x in pose[:51]]
        flat = []
        for kp in pose[:17]:
            flat.extend([float(kp[0]), float(kp[1]), float(kp[2]) if len(kp) > 2 else 1.0])
        return flat

    def _features(self, pose1, pose2):
        from corpocmente.domain.biomechanics.pose_normalizer import normalizar
        v1 = normalizar(self._kpts_to_flat(pose1))["vector"]
        v2 = normalizar(self._kpts_to_flat(pose2))["vector"]
        return np.concatenate([v1, v2]).astype(np.float32).reshape(1, -1)

    def _extraer_poses(self, frame):
        model = self.yolo._get_model()
        results = model.predict(source=frame, conf=0.3, verbose=False)
        if not results or results[0].keypoints is None:
            return None
        kpts = results[0].keypoints.data.cpu().numpy()
        valid_raw = [p for p in kpts if p.shape == (17, 3)
                     and ((p[:, 2] > 0.3) & (p[:, 0] > 0)).sum() >= 8]
        if len(valid_raw) < 2:
            return None

        # Extraer centros, alturas y pelvis para cada detección candidata
        cands = []
        for p in valid_raw:
            pts = p[(p[:, 2] > 0.3) & (p[:, 0] > 0)]
            min_xy = pts[:, :2].min(axis=0)
            max_xy = pts[:, :2].max(axis=0)
            center = (min_xy + max_xy) / 2.0
            height = max_xy[1] - min_xy[1]
            pelvis = p[[11, 12], :2].mean(axis=0) if ((p[[11, 12], 2] > 0.3).all()) else center
            cands.append({
                "pose": p,
                "center": center,
                "height": height,
                "pelvis": pelvis,
            })

        # 1. Deduplicación: descartar detecciones duplicadas de la misma persona (NMS imperfecto)
        unique = []
        for c in cands:
            is_dup = False
            for u in unique:
                pelv_d = np.linalg.norm(c["pelvis"] - u["pelvis"])
                cent_d = np.linalg.norm(c["center"] - u["center"])
                if pelv_d < 35.0 or cent_d < 35.0:
                    is_dup = True
                    break
            if not is_dup:
                unique.append(c)

        if len(unique) < 2:
            return None

        # 2. Fase 1 (Iteración 3I): Encontrar el par más cercano (pareja interactuando)
        best_pair = None
        min_dist = float("inf")
        for i in range(len(unique)):
            for j in range(i + 1, len(unique)):
                dist = float(np.linalg.norm(unique[i]["center"] - unique[j]["center"]))
                if dist < min_dist:
                    min_dist = dist
                    best_pair = (unique[i], unique[j])

        # 3. Guardia de proximidad de interacción física en Jiu-Jitsu:
        # Si la distancia entre centros supera 1.2 veces la altura máxima del cuerpo,
        # están dispersos en el espacio y no interactúan en combate/grappling
        p1, p2 = best_pair
        max_h = max(p1["height"], p2["height"])
        if max_h <= 0 or min_dist > 1.2 * max_h:
            return None

        return p1["pose"].tolist(), p2["pose"].tolist()

    def validar_es_jiujitsu(self, video_path: str) -> bool:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.warning("No se pudo abrir %s", video_path)
            return False
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        if total <= 0:
            cap.release()
            return False
        step = max(1, total // self.num_frames)
        bjj_frames = 0
        interaction_frames = 0  # solo frames con interacción de 2 personas
        total_checked = 0

        try:
            for i in range(0, total, step):
                cap.set(cv2.CAP_PROP_POS_FRAMES, i)
                ok, frame = cap.read()
                if not ok:
                    break
                total_checked += 1
                poses = self._extraer_poses(frame)
                if poses is None:
                    # Frame sin señal: no vota ni a favor ni en contra
                    logger.debug("Frame %d: sin 2 personas -> ABSTENCIÓN", i)
                    continue

                interaction_frames += 1
                feat = self._features(poses[0], poses[1])
                proba = self.clf.predict_proba(feat)[0]
                idx = int(np.argmax(proba))
                conf = float(proba[idx])
                label = str(self.labels[idx])
                umbral = CONF_DEBIL if label in CLASES_DEBILES else CONF_FUERTE
                if label not in NO_BJJ and conf >= umbral:
                    bjj_frames += 1
                    logger.debug("Frame %d: %s (%.2f) -> BJJ", i, label, conf)
                else:
                    logger.debug("Frame %d: %s (%.2f) -> NO BJJ", i, label, conf)
        finally:
            cap.release()

        # Fase 2 (Iteración 3I): Umbral de interacción dinámico
        umbral_interaccion = (
            self.min_interaction_frames
            if self.min_interaction_frames is not None
            else max(3, int(total_checked * 0.15))
        )

        if interaction_frames < umbral_interaccion:
            logger.warning(
                "Spam filter %s: RECHAZADO por evidencia insuficiente "
                "(solo %d frames con interacción, mínimo dinámico %d)",
                Path(video_path).name, interaction_frames, umbral_interaccion,
            )
            return False

        ratio = bjj_frames / interaction_frames
        logger.info(
            "Spam filter %s: %d/%d frames BJJ (ratio=%.2f, umbral=%.2f) | muestreados=%d, interacción=%d, umbral_min=%d",
            Path(video_path).name, bjj_frames, interaction_frames, ratio,
            self.min_bjj_ratio, total_checked, interaction_frames, umbral_interaccion,
        )
        return ratio >= self.min_bjj_ratio
