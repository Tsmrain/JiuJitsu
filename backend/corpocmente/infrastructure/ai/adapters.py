from typing import Dict, List, Optional
import os
import logging
import re
import mimetypes
from pathlib import Path
from google import genai
from google.genai import types
from google.genai.errors import APIError

from corpocmente.domain.entities.models import EsqueletoBiomecanico
from corpocmente.config import storage_root

logger = logging.getLogger(__name__)

class GeminiRateLimitError(Exception):
    """Excepción lanzada cuando se supera el límite de cuota (Rate Limit 429) de Gemini API."""
    pass

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
RAG_MEDIA_STORAGE_ROOTS = (
    storage_root() / "rag_frames",
    storage_root() / "manuales",
    storage_root() / "manuales" / "video_frames",
)
MAX_RAG_IMAGE_BYTES = 8 * 1024 * 1024
ALLOWED_RAG_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}


def _cargar_imagen_evidencia_rag(media_path: str, payload: Dict):
    """Lee evidencia visual solo desde el almacenamiento de la aplicación."""
    path = Path(media_path).resolve(strict=True)
    allowed = False
    for storage_root in RAG_MEDIA_STORAGE_ROOTS:
        try:
            path.relative_to(storage_root.resolve())
            allowed = True
            break
        except ValueError:
            continue
    if not allowed:
        raise ValueError("La evidencia visual está fuera del almacenamiento permitido.")

    if path.suffix.lower() == ".pdf":
        import fitz
        document = fitz.open(path)
        try:
            if document.page_count < 1:
                raise ValueError("El PDF de evidencia no contiene páginas.")
            page_number = max(1, int(payload.get("pagina") or 1))
            page = document[min(page_number - 1, document.page_count - 1)]
            return page.get_pixmap(dpi=120, alpha=False).tobytes("jpeg"), "image/jpeg"
        finally:
            document.close()

    if path.suffix.lower() not in ALLOWED_RAG_IMAGE_EXTENSIONS:
        raise ValueError("El tipo de archivo de evidencia visual no está permitido.")
    if path.stat().st_size > MAX_RAG_IMAGE_BYTES:
        raise ValueError("La imagen de evidencia supera el límite de tamaño.")
    mime_type = mimetypes.guess_type(path.name)[0] or "image/jpeg"
    if not mime_type.startswith("image/"):
        raise ValueError("El tipo MIME de la evidencia no es una imagen.")
    return path.read_bytes(), mime_type


class YOLOPoseAdapter:
    def __init__(self, colab_url: str = None):
        self.colab_url = colab_url if colab_url is not None else os.getenv("COLAB_TUNNEL_URL", "").strip()

    def extraer_secuencia(
        self,
        video_path: str,
        persona_idx_inicial: Optional[int] = None,
        max_disp_norm: float = 0.25,
        evaluacion_id: Optional[str] = None
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
            import torch
            from ultralytics import YOLO

            _orig = torch.load
            def _safe_load(*args, **kwargs):
                kwargs["weights_only"] = False
                return _orig(*args, **kwargs)
            torch.load = _safe_load

            model_name = "yolo26n-pose.pt" if os.path.exists("yolo26n-pose.pt") else "yolo11n-pose.pt"
            model = YOLO(model_name)
            results = model.predict(source=video_path, stream=True, verbose=False, conf=0.3)

            secuencia_kpts = []
            persona_anterior = None
            frames_con_persona = 0
            frames_evaluados = 0
            frames_sin_deteccion = 0

            for f_idx, r in enumerate(results):
                frames_evaluados += 1
                if r.keypoints is None or len(r.keypoints.data) == 0:
                    secuencia_kpts.append([0.0] * 133)
                    frames_sin_deteccion += 1
                    continue

                raw = r.keypoints.data.cpu().numpy()
                candidatos = [
                    p for p in raw
                    if p.shape == (17, 3) and np.count_nonzero((p[:, 2] > 0.3) & (p[:, 0] > 0)) >= 8
                ]
                if not candidatos:
                    secuencia_kpts.append([0.0] * 133)
                    frames_sin_deteccion += 1
                    continue

                if persona_anterior is None:
                    if persona_idx_inicial is not None:
                        idx = min(persona_idx_inicial, len(candidatos) - 1)
                    else:
                        confianzas = [float(p[:, 2].mean()) for p in candidatos]
                        idx = int(np.argmax(confianzas))
                    persona_actual = candidatos[idx]
                else:
                    distancias = []
                    for c in candidatos:
                        mask = (c[:, 2] > 0.3) & (persona_anterior[:, 2] > 0.3) & (c[:, 0] > 0) & (persona_anterior[:, 0] > 0)
                        if np.count_nonzero(mask) >= 5:
                            dx = (c[mask, 0] - persona_anterior[mask, 0]) / w
                            dy = (c[mask, 1] - persona_anterior[mask, 1]) / h
                            d = float(np.mean(np.sqrt(dx**2 + dy**2)))
                        else:
                            c1 = c[c[:, 0] > 0, :2].mean(axis=0) / np.array([w, h])
                            c0 = persona_anterior[persona_anterior[:, 0] > 0, :2].mean(axis=0) / np.array([w, h])
                            d = float(np.linalg.norm(c1 - c0))
                        distancias.append(d)

                    mejor_idx = int(np.argmin(distancias))
                    if distancias[mejor_idx] > max_disp_norm:
                        # Salto espacial excesivo (probable salto al fondo/espectador)
                        secuencia_kpts.append([0.0] * 133)
                        frames_sin_deteccion += 1
                        if frames_sin_deteccion > 5:
                            persona_anterior = None
                        continue

                    persona_actual = candidatos[mejor_idx]

                persona_anterior = persona_actual
                frames_con_persona += 1
                frames_sin_deteccion = 0

                kpts = persona_actual.flatten().tolist()
                if len(kpts) < 133:
                    kpts.extend([0.0] * (133 - len(kpts)))
                secuencia_kpts.append(kpts[:133])

            total = max(1, frames_evaluados)
            cobertura = frames_con_persona / total
            return {
                "secuencia_kpts": secuencia_kpts,
                "frame_idxs": list(range(len(secuencia_kpts))),
                "total_frames": frames_evaluados,
                "frames_con_persona": frames_con_persona,
                "cobertura": round(cobertura, 4)
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
        tecnica_nombre: str = ""
    ) -> str:
        """
        Extrae el fotograma exacto con mayor diferencia biomecánica del video del alumno
        y dibuja el esqueleto COCO con las articulaciones en error resaltadas visualmente.
        Si clean_output_path es provisto, guarda primero el fotograma limpio sin anotaciones.
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

        # 2. Parsear keypoints si están disponibles
        pts: dict[int, tuple[int, int, float]] = {}
        if keypoints133 and len(keypoints133) >= 51:
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

                # Etiqueta con el nombre de la articulación
                nombre_art = COCO_JOINT_NAMES[art_idx] if art_idx < len(COCO_JOINT_NAMES) else f"Joint {art_idx}"
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
        header_text = f"FOTOGRAMA CRITICO #{frame_idx} | {tecnica_nombre.upper()} | ERROR BIOMECANICO DETECTADO"
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

from corpocmente.config import settings

class GeminiApiAdapter:
    """
    Adaptador (GoF Adapter) para encapsular las llamadas a la API de Google Gemini
    utilizando el SDK oficial google-genai.
    
    Aísla al dominio de los detalles de red, autenticación y manejo de tokens.
    """
    
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-2.5-flash-lite"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or settings.GEMINI_API_KEY
        if not self.api_key:
            raise ValueError("Se requiere una API Key válida para instanciar GeminiApiAdapter.")
        
        self.model_name = model_name
        self.client = genai.Client(api_key=self.api_key)

    def validar_es_jiujitsu(self, video_path: str) -> bool:
        """
        Valida mediante visión multimodal de Gemini si el video corresponde a una técnica de Jiu-Jitsu.
        Resuelve el paso 2 del Flujo Principal y el Flujo Alternativo 2a (Prevención de SPAM).
        """
        if not os.path.exists(video_path):
            logger.error(f"El archivo de video no existe en la ruta: {video_path}")
            return False

        prompt_validacion = (
            "Analiza brevemente este video. ¿El contenido muestra a personas practicando o ejecutando "
            "una técnica, movimiento o lucha de Jiu-Jitsu Brasileño (BJJ) o Artes Marciales Grappling? "
            "Responde estrictamente con la palabra 'SI' o 'NO'."
        )

        try:
            # Cargar el archivo utilizando la Files API de Gemini para procesamiento multimodal
            video_file = self.client.files.upload(path=video_path)
            
            # Si el video está en estado PROCESSING, esperar a que pase a ACTIVE
            import time
            while video_file.state == "PROCESSING":
                time.sleep(1)
                video_file = self.client.files.get(name=video_file.name)

            if video_file.state == "FAILED":
                logger.error("El archivo de video falló en el procesamiento de Gemini.")
                return False

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[video_file, prompt_validacion]
            )
            
            # Limpieza del archivo temporal en la nube de Google
            try:
                self.client.files.delete(name=video_file.name)
            except Exception as del_err:
                logger.warning(f"No se pudo eliminar el archivo temporal de Gemini: {del_err}")
            
            resultado = response.text.strip().upper() if response.text else "NO"
            return "SI" in resultado or "SÍ" in resultado

        except APIError as e:
            if getattr(e, "code", None) == 429 or "RESOURCE_EXHAUSTED" in str(e):
                logger.warning("Límite de cuota superado en la API de Gemini durante la validación.")
                raise GeminiRateLimitError("Cuota de Gemini API agotada (429).") from e
            logger.error(f"Error de API al validar video con Gemini: {e}")
            return False
        except Exception as e:
            logger.error(f"Error inesperado en validar_es_jiujitsu: {e}")
            return False

    def generar_texto_feedback(
        self,
        prompt: str,
        frame_image_path: str,
        evidencias_visuales: Optional[List[Dict]] = None,
    ) -> str:
        """
        Genera la evaluación cualitativa estructurada en el idioma seleccionado (ES/PT)
        enviando el prompt de la estrategia y la imagen del fotograma con la discrepancia clave.
        """
        if not os.path.exists(frame_image_path):
            raise FileNotFoundError(f"Fotograma de análisis no encontrado en: {frame_image_path}")

        try:
            with open(frame_image_path, "rb") as f_img:
                image_bytes = f_img.read()
            image_part = types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")
            contents = [image_part]
            for evidencia in (evidencias_visuales or [])[:3]:
                payload = evidencia.get("payload", evidencia)
                media_path = payload.get("media_path")
                if not media_path:
                    continue
                try:
                    visual_bytes, mime_type = _cargar_imagen_evidencia_rag(media_path, payload)
                    contents.append(types.Part.from_bytes(data=visual_bytes, mime_type=mime_type))
                except Exception as evidence_error:
                    logger.warning("No se pudo cargar una imagen recuperada del RAG: %s", evidence_error)
            contents.append(prompt)

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    temperature=0.2, # Baja temperatura para respuestas consistentes y técnicas
                    max_output_tokens=250
                )
            )

            if response.text:
                return self._limpiar_feedback(response.text)
            else:
                raise ValueError("Gemini API retornó una respuesta vacía.")

        except APIError as e:
            if getattr(e, "code", None) == 429 or "RESOURCE_EXHAUSTED" in str(e):
                logger.warning("Límite de cuota (429) alcanzado al generar feedback.")
                raise GeminiRateLimitError("Límite de velocidad/cuota excedido en Gemini API.") from e
            logger.error(f"Error en llamada a Gemini API: {e}")
            raise e

    @staticmethod
    def _limpiar_feedback(texto: str) -> str:
        """Reduce respuestas largas y elimina formato Markdown antes de mostrarlas."""
        texto = re.sub(r"```[^`]*```", "", texto, flags=re.DOTALL)
        texto = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", texto)
        texto = re.sub(r"(?m)^\s{0,3}#{1,6}\s*", "", texto)
        texto = re.sub(r"(?m)^\s*[-*+]\s+", "", texto)
        texto = re.sub(r"(?m)^\s*\d+[.)]\s+", "", texto)
        texto = re.sub(r"[*_`~]", "", texto)
        texto = re.sub(r"\s+", " ", texto).strip()
        frases = re.split(r"(?<=[.!?])\s+", texto)
        reducido = " ".join(frases[:2]).strip()
        palabras = reducido.split()
        if len(palabras) > 45:
            reducido = " ".join(palabras[:45]).rstrip(" ,;:") + "."
        return reducido[:450].strip()


