import json
import uuid
import os
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Union

from src.config import UPLOAD_FOLDER, RESULTS_DIR, ARTICULACIONES, UMBRAL_ERROR
from src.infrastructure.repositories import SQLiteDB, AnalisisRepository, TecnicaMaestraRepository
from src.domain.entities import AnalisisBiomecanico, FotogramaAnotado
from src.domain.value_objects import ErrorBiomecanico
from src.infrastructure.storage import LocalStorageAdapter
from src.domain.interfaces import (
    IPoseExtractor, IAngleCalculator, IDTWComparator,
    IFrameAnnotator, IStorageProvider
)


class AnalysisPipeline:
    """Controlador GRASP para orquestar el análisis biomecánico híbrido (Edge-Colab)."""

    def __init__(
        self,
        pose_extractor: Optional[IPoseExtractor] = None,
        angle_calculator: Optional[IAngleCalculator] = None,
        dtw_comparator: Optional[IDTWComparator] = None,
        frame_annotator: Optional[IFrameAnnotator] = None,
        storage: Optional[IStorageProvider] = None,
        db: Optional[SQLiteDB] = None,
        analisis_repo: Optional[AnalisisRepository] = None,
        tecnica_repo: Optional[TecnicaMaestraRepository] = None
    ):
        if storage is None:
            storage = LocalStorageAdapter()
        if angle_calculator is None:
            from src.domain.services import AngleCalculatorImpl
            angle_calculator = AngleCalculatorImpl()
        if dtw_comparator is None:
            from src.domain.services import DTWComparatorImpl
            dtw_comparator = DTWComparatorImpl()
        if frame_annotator is None:
            from src.infrastructure.frame_annotator import FrameAnnotatorImpl
            frame_annotator = FrameAnnotatorImpl()

        self.storage = storage
        self.angle_calculator = angle_calculator
        self.dtw_comparator = dtw_comparator
        self.frame_annotator = frame_annotator
        self.pose_extractor = pose_extractor
        self.db = db or SQLiteDB()
        self.analisis_repo = analisis_repo or AnalisisRepository()
        self.tecnica_repo = tecnica_repo or TecnicaMaestraRepository()

        self._articulaciones = ARTICULACIONES
        self._umbral_error = UMBRAL_ERROR

    def procesar_resultado_colab(
        self, json_path: str, video_id: Optional[str] = None, tecnica_id: Optional[str] = None
    ) -> AnalisisBiomecanico:
        """
        Ingesta el JSON exportado por Google Colab y persiste el análisis en SQLite (Mannino).
        """
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        errores_detectados: List[ErrorBiomecanico] = []
        max_desviacion = 0.0
        articulacion_critica = ""

        # Caso 1: El JSON contiene lista explícita de errores
        if 'errores' in data and data['errores']:
            for error in data['errores']:
                e = ErrorBiomecanico(
                    articulacion=error['articulacion'],
                    angulo_alumno=error['angulo_alumno'],
                    angulo_maestro=error['angulo_maestro'],
                    diferencia=error['diferencia'],
                    frame=error['frame'],
                    mensaje=error.get('mensaje', f"Desviación de {error['diferencia']:.2f}° en {error['articulacion']}")
                )
                errores_detectados.append(e)
                if abs(error['diferencia']) > max_desviacion:
                    max_desviacion = abs(error['diferencia'])
                    articulacion_critica = error['articulacion']

        # Caso 2: El JSON contiene keypoints crudos de Colab
        elif 'keypoints_alumno' in data:
            kpts_alumno = np.array(data['keypoints_alumno'])
            kpts_maestro = np.array(data.get('keypoints_maestro', data['keypoints_alumno']))
            if len(kpts_maestro) == 0:
                kpts_maestro = kpts_alumno

            angulos_maestro = [self.angle_calculator.extraer_angulos(k) for k in kpts_maestro]
            angulos_alumno = [self.angle_calculator.extraer_angulos(k) for k in kpts_alumno]
            errores_detectados = self._detectar_errores(angulos_maestro, angulos_alumno)

            mejor_err = self._encontrar_error_maximo(errores_detectados)
            if mejor_err:
                max_desviacion = mejor_err.diferencia
                articulacion_critica = mejor_err.articulacion

        # Resolver video_id de forma segura
        try:
            v_uuid = uuid.UUID(video_id) if video_id else uuid.uuid4()
        except (ValueError, TypeError):
            v_uuid = uuid.uuid4()

        analisis_id = uuid.uuid4()
        analisis = AnalisisBiomecanico(
            id=analisis_id,
            video_id=v_uuid,
            desviacion_angular_maxima=max_desviacion,
            articulacion_afectada=articulacion_critica,
            estado_computo="completado",
            errores=errores_detectados
        )

        # Persistencia Relacional (Mannino)
        self.analisis_repo.guardar(analisis)
        return analisis

    def obtener_historial_estudiante(self, estudiante_id: str):
        """Consulta el historial de progresión longitudinal desde SQLite."""
        cursor = self.db.get_cursor()
        cursor.execute('''
            SELECT a.fecha_procesamiento, a.puntuacion_global, t.nombre as tecnica
            FROM analisis_biomecanico a
            JOIN video_ejecucion v ON a.video_id = v.id_video
            JOIN tecnica_maestra t ON v.tecnica_id = t.id_tecnica
            WHERE v.estudiante_id = ?
            ORDER BY a.fecha_procesamiento DESC
        ''', (estudiante_id,))
        return [dict(row) for row in cursor.fetchall()]

    def ejecutar(self, video_maestro: str, video_alumno: str, tecnica: Optional[str] = None) -> AnalisisBiomecanico:
        """
        Ejecución directa en la laptop local (modo Edge).
        """
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        if self.pose_extractor is None:
            from src.infrastructure.adapters.yolo_adapter import YOLOPoseExtractor
            self.pose_extractor = YOLOPoseExtractor()

        kpts_maestro, frames_maestro = self.pose_extractor.extraer_keypoints(video_maestro)
        kpts_alumno, frames_alumno = self.pose_extractor.extraer_keypoints(video_alumno)

        if len(kpts_maestro) == 0 or len(kpts_alumno) == 0:
            raise ValueError("No se detectaron poses en uno o ambos videos.")

        angulos_maestro = [self.angle_calculator.extraer_angulos(k) for k in kpts_maestro]
        angulos_alumno = [self.angle_calculator.extraer_angulos(k) for k in kpts_alumno]
        errores = self._detectar_errores(angulos_maestro, angulos_alumno)
        mejor_error = self._encontrar_error_maximo(errores)

        fotograma = None
        if mejor_error and len(frames_alumno) > mejor_error.frame:
            frame = frames_alumno[mejor_error.frame]
            kpts = kpts_alumno[mejor_error.frame]
            frame_anotado = self.frame_annotator.anotar_error(
                frame, kpts, mejor_error.articulacion,
                mejor_error.diferencia, mejor_error.frame
            )
            nombre_img = f"frame_error_{session_id}.jpg"
            url_img = self.storage.guardar_imagen(frame_anotado, nombre_img)
            fotograma = FotogramaAnotado(
                imagen_url=url_img,
                coordenada_error_x=int(kpts[0][0]) if len(kpts) > 0 else 0,
                coordenada_error_y=int(kpts[0][1]) if len(kpts) > 0 else 0,
                explicacion_causa=f"Error en {mejor_error.articulacion}: {mejor_error.diferencia:.1f}°"
            )

        similitud = self._calcular_similitud(angulos_maestro, angulos_alumno)
        self._generar_grafica(similitud, mejor_error, session_id)
        self._exportar_csv(angulos_alumno, similitud, session_id)

        analisis = AnalisisBiomecanico(
            id=uuid.uuid4(),
            video_id=uuid.uuid4(),
            fecha_procesamiento=datetime.now(),
            desviacion_angular_maxima=mejor_error.diferencia if mejor_error else 0.0,
            articulacion_afectada=mejor_error.articulacion if mejor_error else "",
            estado_computo="completado",
            fotograma_anotado=fotograma,
            errores=errores
        )
        return analisis

    def exportar_payload_colab(self, video_maestro: str, video_alumno: str, ruta_salida: Optional[str] = None) -> str:
        payload = {
            "version": "2.0-hybrid",
            "fecha": datetime.now().isoformat(),
            "video_maestro": os.path.basename(video_maestro),
            "video_alumno": os.path.basename(video_alumno),
            "articulaciones": self._articulaciones,
            "umbral_error": self._umbral_error
        }
        dest = ruta_salida or os.path.join(str(RESULTS_DIR), "colab_payload.json")
        with open(dest, 'w', encoding='utf-8') as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        return dest

    def ejecutar_desde_colab_json(self, colab_json: Union[str, dict]) -> AnalisisBiomecanico:
        if isinstance(colab_json, str):
            return self.procesar_resultado_colab(colab_json)
        temp_dest = os.path.join(str(RESULTS_DIR), "temp_colab_eval.json")
        with open(temp_dest, 'w', encoding='utf-8') as f:
            json.dump(colab_json, f)
        res = self.procesar_resultado_colab(temp_dest)
        if os.path.exists(temp_dest):
            os.unlink(temp_dest)
        return res

    def _detectar_errores(self, angulos_maestro: List[dict], angulos_alumno: List[dict]) -> List[ErrorBiomecanico]:
        errores = []
        n_frames = min(len(angulos_maestro), len(angulos_alumno))
        for art in self._articulaciones:
            for i in range(n_frames):
                if art in angulos_maestro[i] and art in angulos_alumno[i]:
                    diff = abs(angulos_maestro[i][art] - angulos_alumno[i][art])
                    if diff > self._umbral_error:
                        errores.append(ErrorBiomecanico(
                            articulacion=art,
                            angulo_alumno=angulos_alumno[i][art],
                            angulo_maestro=angulos_maestro[i][art],
                            diferencia=diff,
                            frame=i,
                            mensaje=f"Desviación de {diff:.2f}° en {art}"
                        ))
        return errores

    def _encontrar_error_maximo(self, errores: List[ErrorBiomecanico]) -> Optional[ErrorBiomecanico]:
        if not errores:
            return None
        return max(errores, key=lambda e: e.diferencia)

    def _calcular_similitud(self, angulos_maestro: List[dict], angulos_alumno: List[dict]) -> List[float]:
        similitud = []
        n_frames = min(len(angulos_maestro), len(angulos_alumno))
        for i in range(n_frames):
            errores_frame = []
            for art in self._articulaciones:
                if art in angulos_maestro[i] and art in angulos_alumno[i]:
                    errores_frame.append(abs(angulos_maestro[i][art] - angulos_alumno[i][art]))
            if errores_frame:
                similitud.append(max(0.0, float(100.0 - np.mean(errores_frame) * 2.0)))
            else:
                similitud.append(0.0)
        return similitud

    def _generar_grafica(self, similitud: List[float], mejor_error: Optional[ErrorBiomecanico], session_id: str):
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(similitud, color='#D90429', linewidth=2, label='Similitud (%)')
        ax.set_title('Evolución de Similitud Angular')
        ax.set_ylim(0, 105)
        ax.grid(True, linestyle=':', alpha=0.6)
        ax.legend()
        self.storage.guardar_imagen(fig, f"similitud_{session_id}.png")
        plt.close(fig)

    def _exportar_csv(self, angulos: List[dict], similitud: List[float], session_id: str):
        self.storage.guardar_csv(angulos, f"angulos_{session_id}.csv")


# Alias de compatibilidad canónica
BiomechanicsPipeline = AnalysisPipeline
