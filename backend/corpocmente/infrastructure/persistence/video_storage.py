import logging
import os
import shutil
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

from corpocmente.config import storage_root

logger = logging.getLogger(__name__)

VIDEOS_DIR = "/tmp/corpocmente_videos"
os.makedirs(VIDEOS_DIR, exist_ok=True)

PERSISTENT_REF_VIDEOS_DIR = storage_root() / "reference_videos"
PERSISTENT_REF_VIDEOS_DIR.mkdir(parents=True, exist_ok=True)

# backend/corpocmente/infrastructure/persistence/video_storage.py -> parents[4] = raíz del repo
REPO_ROOT = Path(__file__).resolve().parents[4]

VALID_VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".webm"}
MIN_VALID_VIDEO_BYTES = 1024

_KNOWN_FILENAME_HINTS = {
    "67beb825": "profesor salida de Guardia Parandose.mp4",
    "38f8b98c": "Escape de 100 kilos brazo por debajo.mp4",
    "53062479": "Profesor ensena 1 escape de guardia cerrada.mp4",
    "e74b10ca": "Profesor dill pasaje de guardia abierta.mp4",
    "c92e5499": "Maestro.mp4",
    "b5a33f04": "MaestroAmericana.mov",
}

_KNOWN_TECNICA_HINTS = {
    "5f4566e0-44a8-4cf7-ab1b-341076c50098": "MaestroAmericana.mov",
}


def _archivo_video_valido(path: Optional[str], min_bytes: int = MIN_VALID_VIDEO_BYTES) -> bool:
    """Verifica que el archivo exista físicamente en disco y no sea un marcador vacío."""
    if not path:
        return False
    return os.path.isfile(path) and os.path.getsize(path) > min_bytes


def _respaldo_persistente(src_path: str, filename: str) -> None:
    """Guarda una copia de respaldo en storage persistente para resistir limpiezas de /tmp."""
    try:
        PERSISTENT_REF_VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
        backup_path = PERSISTENT_REF_VIDEOS_DIR / filename
        if not _archivo_video_valido(str(backup_path)) and _archivo_video_valido(src_path):
            shutil.copy2(src_path, backup_path)
    except Exception as exc:
        logger.debug("No se pudo respaldar video de referencia %s: %s", filename, exc)


def persistir_video_referencia(source_path: str, original_filename: Optional[str] = None) -> str:
    """
    Copia físicamente un video de referencia a /tmp/corpocmente_videos/ con nombre UUID único
    (preservando su extensión) y lo respalda en almacenamiento persistente.
    Retorna la ruta canónica en VIDEOS_DIR para guardar en videos_referencia.url_video_gcs.
    """
    os.makedirs(VIDEOS_DIR, exist_ok=True)
    ext = Path(original_filename or source_path).suffix.lower()
    if ext not in VALID_VIDEO_EXTENSIONS:
        ext = ".mp4"

    filename = f"{uuid4()}{ext}"
    dest_path = os.path.join(VIDEOS_DIR, filename)

    if os.path.isfile(source_path):
        shutil.copy2(source_path, dest_path)
        _respaldo_persistente(dest_path, filename)
        return dest_path

    return source_path


def _buscar_video_en_raiz(
    raw_path: Optional[str] = None,
    tecnica_id: Optional[str] = None,
    tecnica_nombre: Optional[str] = None,
) -> Optional[Path]:
    """Busca un video de referencia recuperable en la raíz del repositorio."""
    if not REPO_ROOT.is_dir():
        return None

    candidatos: list[str] = []
    if raw_path:
        base = os.path.basename(raw_path)
        candidatos.append(base)
        for prefix, root_name in _KNOWN_FILENAME_HINTS.items():
            if prefix in base:
                candidatos.append(root_name)

    if tecnica_id and str(tecnica_id) in _KNOWN_TECNICA_HINTS:
        candidatos.append(_KNOWN_TECNICA_HINTS[str(tecnica_id)])

    nombre_lower = (tecnica_nombre or "").lower()
    if "americana" in nombre_lower:
        candidatos.append("MaestroAmericana.mov")

    vistos: set[str] = set()
    for nombre in candidatos:
        if not nombre or nombre in vistos:
            continue
        vistos.add(nombre)
        cand = REPO_ROOT / nombre
        if _archivo_video_valido(str(cand)):
            return cand

    return None


def _actualizar_url_en_bd(
    db: Any,
    tecnica_id: Optional[str],
    profesor_id: Optional[str],
    nueva_ruta: str,
) -> None:
    """Actualiza videos_referencia.url_video_gcs tras auto-curar un archivo desde raíz."""
    if db is None or not tecnica_id:
        return
    try:
        target_prof = str(profesor_id) if profesor_id else None
        if not target_prof:
            rows = db.get("videos_referencia", {"tecnica_id": f"eq.{tecnica_id}", "select": "profesor_id"})
            if rows:
                target_prof = rows[0].get("profesor_id")
        if target_prof:
            db.rpc(
                "admin_save_video_referencia",
                {
                    "p_tecnica_id": str(tecnica_id),
                    "p_profesor_id": str(target_prof),
                    "p_url_video": nueva_ruta,
                },
            )
    except Exception as exc:
        logger.warning("Auto-curación: archivo restaurado pero falló actualización en BD: %s", exc)


def resolver_video_estatico(
    raw_path: Optional[str],
    *,
    es_referencia: bool = False,
    tecnica_id: Optional[str] = None,
    tecnica_nombre: Optional[str] = None,
    profesor_id: Optional[str] = None,
    db: Any = None,
) -> Optional[str]:
    """
    Resuelve una ruta de video a su URL pública /static/videos/<archivo> solo si el archivo
    físico existe y es válido (>1KB). Para videos de referencia intenta auto-curación desde
    almacenamiento persistente o raíz del proyecto y actualiza la BD si repara el enlace.
    Retorna None si el archivo físico no existe.
    """
    os.makedirs(VIDEOS_DIR, exist_ok=True)
    filename = os.path.basename(raw_path) if raw_path else ""
    target = os.path.join(VIDEOS_DIR, filename) if filename else ""

    if _archivo_video_valido(target):
        if es_referencia:
            _respaldo_persistente(target, filename)
        return f"/static/videos/{filename}"

    if raw_path and _archivo_video_valido(raw_path) and target:
        try:
            shutil.copy2(raw_path, target)
            if es_referencia:
                _respaldo_persistente(target, filename)
            return f"/static/videos/{filename}"
        except Exception as exc:
            logger.warning("Error copiando video %s a %s: %s", raw_path, target, exc)

    if es_referencia:
        if filename:
            backup = PERSISTENT_REF_VIDEOS_DIR / filename
            if _archivo_video_valido(str(backup)):
                try:
                    shutil.copy2(backup, target)
                    return f"/static/videos/{filename}"
                except Exception as exc:
                    logger.warning("Error restaurando backup %s: %s", backup, exc)

        src_root = _buscar_video_en_raiz(raw_path, tecnica_id=tecnica_id, tecnica_nombre=tecnica_nombre)
        if src_root is not None:
            repaired_path = persistir_video_referencia(str(src_root))
            repaired_name = os.path.basename(repaired_path)
            _actualizar_url_en_bd(db, tecnica_id=tecnica_id, profesor_id=profesor_id, nueva_ruta=repaired_path)
            logger.info(
                "[AUTO-CURACION] Video de referencia reparado (%s): %s -> %s",
                tecnica_nombre or tecnica_id or filename,
                src_root,
                repaired_path,
            )
            return f"/static/videos/{repaired_name}"

    return None


def autocurar_videos_referencia_en_arranque() -> None:
    """
    Al iniciar la app, siembra copias de respaldo conocidas y auto-cura enlaces rotos en
    videos_referencia cuando el archivo original existe en la raíz del repositorio.
    """
    for legacy_name, src_name in _KNOWN_FILENAME_HINTS.items():
        src = REPO_ROOT / src_name
        if not _archivo_video_valido(str(src)):
            continue
        # Solo si existe exactamente ese archivo legacy en raíz o ya fue sembrado
        for existing_ext in (".mp4", ".mov"):
            candidate = os.path.join(VIDEOS_DIR, f"{legacy_name}{existing_ext}")
            if os.path.exists(candidate) and not _archivo_video_valido(candidate):
                try:
                    shutil.copy2(src, candidate)
                except Exception:
                    pass

    try:
        from corpocmente.infrastructure.persistence.postgrest_client import PostgrestClient

        db = PostgrestClient()
        rows = db.rpc("get_tecnicas_with_videos", {}) or []
        for row in rows:
            raw_url = row.get("video_url")
            if not raw_url and not row.get("tiene_patron"):
                continue
            resolver_video_estatico(
                raw_url,
                es_referencia=True,
                tecnica_id=row.get("id"),
                tecnica_nombre=row.get("nombre"),
                profesor_id=row.get("video_profesor_id"),
                db=db,
            )
    except Exception as exc:
        logger.debug("Auto-curación en arranque omitida (BD no disponible aún): %s", exc)
