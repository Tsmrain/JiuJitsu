import os
import cv2
import numpy as np


def verificar_videos(videos_dir):
    """
    Verifica la existencia de los videos de referencia Maestro.mp4 y Alumno.mp4.
    """
    ruta_maestro = os.path.join(videos_dir, "Maestro.mp4")
    ruta_alumno = os.path.join(videos_dir, "Alumno.mp4")

    # Búsqueda insensible a mayúsculas si no se encuentran exactamente
    if not os.path.exists(ruta_maestro):
        for f in os.listdir(videos_dir):
            if f.lower() == "maestro.mp4":
                ruta_maestro = os.path.join(videos_dir, f)
                break

    if not os.path.exists(ruta_alumno):
        for f in os.listdir(videos_dir):
            if f.lower() == "alumno.mp4":
                ruta_alumno = os.path.join(videos_dir, f)
                break

    return ruta_maestro, ruta_alumno


def obtener_info_video(ruta_video):
    """
    Obtiene metadatos de un archivo de video (fps, frames totales, duración, resolución).
    """
    if not os.path.exists(ruta_video):
        return None

    cap = cv2.VideoCapture(ruta_video)
    if not cap.isOpened():
        return None

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duracion = total_frames / fps if fps > 0 else 0.0

    cap.release()
    return {
        'fps': fps,
        'total_frames': total_frames,
        'width': width,
        'height': height,
        'duracion_segundos': duracion,
        'peso_mb': os.path.getsize(ruta_video) / (1024 * 1024)
    }


def formatear_resumen(resultados):
    """
    Formatea el diccionario de resultados en un reporte legible para consola.
    """
    lineas = [
        "=" * 60,
        "📋 RESUMEN DE ANÁLISIS BIOMECÁNICO (JiuJitsu Tesis)",
        "=" * 60,
        f"Sesión ID: {resultados.get('session_id', 'N/A')}"
    ]

    me = resultados.get('mejor_error')
    if me:
        lineas.extend([
            f"🔴 Error Máximo Global: {me['articulacion'].replace('_', ' ').upper()}",
            f"   - Desviación Angular: {me['error']:.2f}°",
            f"   - Frame de Ocurrencia: {me['frame']}"
        ])

    sim = resultados.get('similitud', [])
    if len(sim) > 0:
        lineas.append(f"📊 Similitud Angular Media: {np.mean(sim):.2f}%")

    lineas.append("\nDistancias DTW por Articulación:")
    for art, dist in resultados.get('distancias_dtw', {}).items():
        lineas.append(f"   - {art:<14}: {dist:.2f}")

    archivos = resultados.get('archivos', {})
    if archivos:
        lineas.append("\nArchivos Generados:")
        for k, v in archivos.items():
            lineas.append(f"   - {k}: {v}")

    lineas.append("=" * 60)
    return "\n".join(lineas)
