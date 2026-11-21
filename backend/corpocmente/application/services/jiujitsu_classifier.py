"""
Clasificador heurístico de Jiu-Jitsu basado en VLM local (Qwen3-VL vía MLX).
No requiere entrenamiento ni dataset adicional. Muestrea N frames uniformes del
video y agrega veredictos por mayoría de forma agnóstica al nombre del archivo.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
import logging
import os

import cv2

logger = logging.getLogger(__name__)

PROMPT_JIUJITSU = (
    "Observa la imagen. ¿Es una práctica de Jiu-Jitsu brasileño (BJJ), "
    "grappling en tatami, o dos personas en contacto físico de lucha en el suelo/de pie? "
    "Responde ESTRICTAMENTE con una sola palabra: SI o NO. "
    "NO si es: ballet, danza, gimnasia artística, pelea de pie con guantes, "
    "yoga, fitness, retrato en escritorio o cualquier otra actividad sin tatami/lucha cuerpo a cuerpo."
)


def _extraer_frames_clasificacion(video_path: Path, n_frames: int = 6) -> List[str]:
    """Extrae N frames uniformemente distribuidos y redimensionados a disco temporal."""
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        return []
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    safe_stem = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in video_path.stem)
    out_dir = Path("/tmp/jj_clf_frames") / safe_stem
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: List[str] = []
    try:
        if total <= 0:
            return paths
        step_count = min(n_frames, total)
        for i in range(step_count):
            idx = int(i * total / step_count)
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ok, frame = cap.read()
            if not ok or frame is None:
                continue
            # Redimensionar lado mayor a 512px para mantener bajo el consumo térmico/VRAM en MPS/MLX
            h, w = frame.shape[:2]
            max_side = max(h, w)
            if max_side > 512:
                scale = 512.0 / float(max_side)
                frame = cv2.resize(frame, (max(1, int(w * scale)), max(1, int(h * scale))), interpolation=cv2.INTER_AREA)
            p = out_dir / f"f_{i:02d}.jpg"
            cv2.imwrite(str(p), frame)
            paths.append(str(p))
    finally:
        cap.release()
    return paths


def _inferir_frame_vlm(vlm_adapter: Any, image_path: str, prompt: str, max_tokens: int = 8) -> str:
    """Invoca el método disponible en LocalVLMAdapter (o mlx_vlm.generate directo) sobre una imagen."""
    if hasattr(vlm_adapter, "inferir_imagen"):
        return str(vlm_adapter.inferir_imagen(image_path, prompt, max_tokens=max_tokens) or "")

    from mlx_vlm import generate

    processor = vlm_adapter.processor
    model = vlm_adapter.model
    if hasattr(processor, "apply_chat_template"):
        content = [{"type": "image"}, {"type": "text", "text": prompt}]
        formatted_prompt = processor.apply_chat_template(
            [{"role": "user", "content": content}],
            add_generation_prompt=True,
        )
    else:
        formatted_prompt = prompt

    try:
        import mlx.core as mx
        if hasattr(mx, "clear_cache"):
            mx.clear_cache()
    except Exception:
        pass

    raw = generate(
        model,
        processor,
        formatted_prompt,
        [image_path],
        max_tokens=max_tokens,
        temperature=0.0,
        verbose=False,
    )
    return str(raw.text if hasattr(raw, "text") else raw)


def clasificar_video_jiujitsu(
    video_path: Path,
    vlm_adapter: Optional[Any] = None,
    n_frames: int = 6,
    threshold: float = 0.5,
) -> Dict[str, Any]:
    """
    Clasifica si un video corresponde a Jiu-Jitsu Brasileño o Grappling por contenido visual.
    Retorna {'es_jiujitsu': bool, 'score': float, 'frames_si': int,
             'frames_total': int, 'veredictos': list}.
    """
    vpath = Path(video_path)
    if not vpath.exists():
        return {
            "es_jiujitsu": False,
            "score": 0.0,
            "frames_si": 0,
            "frames_total": 0,
            "veredictos": [],
            "error": f"not_found:{vpath}",
        }

    if vlm_adapter is None:
        from corpocmente.infrastructure.ai.local_vlm_adapter import LocalVLMAdapter
        vlm_adapter = LocalVLMAdapter()

    frames = _extraer_frames_clasificacion(vpath, n_frames=n_frames)
    if not frames:
        return {
            "es_jiujitsu": False,
            "score": 0.0,
            "frames_si": 0,
            "frames_total": 0,
            "veredictos": [],
            "error": "no_frames",
        }

    veredictos = []
    for fp in frames:
        try:
            resp = _inferir_frame_vlm(vlm_adapter, fp, PROMPT_JIUJITSU, max_tokens=8)
            txt = (resp or "").strip().upper()
            token0 = txt.split()[0].strip(".,:;!?\"'") if txt else ""
            es_si = token0 in {"SI", "SÍ", "YES"} or txt.startswith(("SI", "SÍ", "YES"))
            veredictos.append({"frame": os.path.basename(fp), "raw": txt, "si": es_si})
        except Exception as e:
            logger.warning("VLM fallo en %s: %s", fp, e)
            veredictos.append({"frame": os.path.basename(fp), "raw": f"ERROR:{e}", "si": False})

    frames_si = sum(1 for v in veredictos if v["si"])
    score = frames_si / len(veredictos) if veredictos else 0.0
    return {
        "es_jiujitsu": score >= threshold,
        "score": round(score, 3),
        "frames_si": frames_si,
        "frames_total": len(veredictos),
        "veredictos": veredictos,
    }
