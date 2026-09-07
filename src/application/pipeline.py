import os
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
from typing import List, Optional, Dict
from uuid import uuid4

from ..domain.interfaces import (
    IPoseExtractor, IAngleCalculator, IDTWComparator,
    IFrameAnnotator, IStorageProvider
)
from ..domain.entities import AnalisisBiomecanico, FotogramaAnotado
from ..domain.value_objects import ErrorBiomecanico
from ..config import ARTICULACIONES, UMBRAL_ERROR


class BiomechanicsPipeline:
    """
    Controlador de Caso de Uso (Larman Controller - GRASP).
    Orquesta el flujo completo de análisis biomecánico con bajo acoplamiento (Low Coupling)
    comunicándose exclusivamente a través de interfaces de dominio e inyección de dependencias.
    """

    def __init__(
        self,
        pose_extractor: Optional[IPoseExtractor] = None,
        angle_calculator: Optional[IAngleCalculator] = None,
        dtw_comparator: Optional[IDTWComparator] = None,
        frame_annotator: Optional[IFrameAnnotator] = None,
        storage: Optional[IStorageProvider] = None
    ):
        if pose_extractor is None:
            from ..infrastructure.adapters.yolo_adapter import YOLOPoseExtractor
            pose_extractor = YOLOPoseExtractor()
        if angle_calculator is None:
            from ..domain.services import AngleCalculatorImpl
            angle_calculator = AngleCalculatorImpl()
        if dtw_comparator is None:
            from ..domain.services import DTWComparatorImpl
            dtw_comparator = DTWComparatorImpl()
        if frame_annotator is None:
            from ..infrastructure.frame_annotator import FrameAnnotatorImpl
            frame_annotator = FrameAnnotatorImpl()
        if storage is None:
            from ..infrastructure.storage import LocalStorageProvider
            storage = LocalStorageProvider()

        self.pose_extractor = pose_extractor
        self.angle_calculator = angle_calculator
        self.dtw_comparator = dtw_comparator
        self.frame_annotator = frame_annotator
        self.storage = storage

        self._articulaciones = ARTICULACIONES
        self._umbral_error = UMBRAL_ERROR

    def ejecutar(self, video_maestro: str, video_alumno: str, tecnica: Optional[str] = None) -> AnalisisBiomecanico:
        """
        Ejecuta el pipeline completo comparando el video del alumno contra el patrón del maestro.
        Retorna: AnalisisBiomecanico (Entidad de dominio con identidad y estado consolidado).
        """
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        print(f"\n{'='*55}")
        print(f"🥋 INICIANDO ANÁLISIS BIOMECÁNICO - {session_id}")
        print(f"{'='*55}")

        # 1. Extraer keypoints mediante IPoseExtractor
        print("\n📹 1. Extrayendo keypoints...")
        kpts_maestro, frames_maestro = self.pose_extractor.extraer_keypoints(video_maestro)
        kpts_alumno, frames_alumno = self.pose_extractor.extraer_keypoints(video_alumno)
        print(f"   Maestro: {len(kpts_maestro)} frames leídos")
        print(f"   Alumno:  {len(kpts_alumno)} frames leídos")

        if len(kpts_maestro) == 0 or len(kpts_alumno) == 0:
            raise ValueError("No se detectaron poses en uno o ambos videos.")

        # 2. Calcular ángulos cinemáticos mediante IAngleCalculator
        print("\n📐 2. Calculando ángulos articulares...")
        angulos_maestro = [self.angle_calculator.extraer_angulos(k) for k in kpts_maestro]
        angulos_alumno = [self.angle_calculator.extraer_angulos(k) for k in kpts_alumno]

        count_m = sum(1 for a in angulos_maestro if a)
        count_a = sum(1 for a in angulos_alumno if a)
        print(f"   Maestro: {count_m}/{len(angulos_maestro)} frames válidos")
        print(f"   Alumno:  {count_a}/{len(angulos_alumno)} frames válidos")

        # 3. Detectar errores biomecánicos y calcular DTW
        print("\n🔄 3. Aplicando DTW y calculando discrepancias...")
        distancias_dtw = {}
        for art in self._articulaciones:
            dist, path, sm, sa = self.dtw_comparator.comparar_articulacion(
                angulos_maestro, angulos_alumno, art
            )
            if dist is not None:
                distancias_dtw[art] = dist
                print(f"   {art:<12}: DTW = {dist:.2f}")

        errores = self._detectar_errores(angulos_maestro, angulos_alumno)

        # 4. Encontrar error máximo global (RF-04)
        mejor_error = self._encontrar_error_maximo(errores)
        if mejor_error:
            print(f"\n   🔴 ERROR MÁXIMO GLOBAL: {mejor_error.articulacion.replace('_', ' ').upper()} "
                  f"con {mejor_error.diferencia:.2f}° en frame {mejor_error.frame}")

        # 5. Anotar fotograma clave con IFrameAnnotator y persistir con IStorageProvider
        print("\n🖍️ 4. Generando entregable visual anotado...")
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
                explicacion_causa=f"Error crítico en {mejor_error.articulacion}: {mejor_error.diferencia:.1f}°"
            )
            print(f"   ✅ Fotograma anotado guardado en: {url_img}")

        # 6. Generar gráfica de similitud angular temporal
        print("\n📊 5. Generando curva de evolución temporal de similitud...")
        similitud = self._calcular_similitud(angulos_maestro, angulos_alumno)
        self._generar_grafica(similitud, mejor_error, session_id)

        # 7. Exportar series tabulares a CSV
        print("\n📄 6. Exportando datos a formato CSV...")
        self._exportar_csv(angulos_alumno, similitud, session_id)

        # 8. Consolidar entidad AnalisisBiomecanico
        analisis = AnalisisBiomecanico(
            id=uuid4(),
            video_id=uuid4(),
            fecha_procesamiento=datetime.now(),
            desviacion_angular_maxima=mejor_error.diferencia if mejor_error else 0.0,
            articulacion_afectada=mejor_error.articulacion if mejor_error else "",
            estado_computo="completado",
            fotograma_anotado=fotograma,
            errores=errores
        )

        print(f"\n✅ ANÁLISIS BIOMECÁNICO COMPLETADO EXITOSAMENTE - {session_id}")
        return analisis

    def _detectar_errores(self, angulos_maestro: List[dict], angulos_alumno: List[dict]) -> List[ErrorBiomecanico]:
        """Detecta discrepancias angulares en las articulaciones evaluadas."""
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
                            mensaje=self._generar_mensaje_error(art, diff)
                        ))
        return errores

    def _encontrar_error_maximo(self, errores: List[ErrorBiomecanico]) -> Optional[ErrorBiomecanico]:
        """Identifica el error con mayor discrepancia angular (Information Expert)."""
        if not errores:
            return None
        return max(errores, key=lambda e: e.diferencia)

    def _calcular_similitud(self, angulos_maestro: List[dict], angulos_alumno: List[dict]) -> List[float]:
        """Calcula el porcentaje de similitud angular por frame."""
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

    def _generar_mensaje_error(self, articulacion: str, diff: float) -> str:
        from ..domain.services import RuleEngine
        return RuleEngine.generar_diagnostico(articulacion, diff)

    def _generar_grafica(self, similitud: List[float], mejor_error: Optional[ErrorBiomecanico], session_id: str):
        fig, ax = plt.subplots(figsize=(12, 5))
        ax.plot(similitud, color='#D90429', linewidth=2, label='Similitud Angular (%)')
        ax.fill_between(range(len(similitud)), 0, similitud, color='#D90429', alpha=0.1)

        if mejor_error and mejor_error.frame < len(similitud):
            frame = mejor_error.frame
            ax.axvline(x=frame, color='#2B2D42', linestyle='--', alpha=0.7,
                       label=f"Pico de Error (Frame {frame})")
            ax.scatter(frame, similitud[frame], color='#D90429', s=130, zorder=5,
                       edgecolors='white', linewidth=2)

        ax.set_title('Evolución de Similitud Angular por Frame - Análisis Biomecánico', fontsize=12)
        ax.set_xlabel('Número de Frame', fontsize=11)
        ax.set_ylabel('Similitud (%)', fontsize=11)
        ax.set_ylim(0, 105)
        ax.grid(True, linestyle=':', alpha=0.6)
        ax.legend(loc='lower right')

        nombre_grafica = f"similitud_{session_id}.png"
        self.storage.guardar_imagen(fig, nombre_grafica)
        plt.close(fig)

    def _exportar_csv(self, angulos: List[dict], similitud: List[float], session_id: str):
        self.storage.guardar_csv(angulos, f"skeleton_angle_similarity_{session_id}.csv")
        self.storage.guardar_csv(
            {'frame': range(len(similitud)), 'similitud_angular': similitud},
            f"skeleton_eachframe_similarity_{session_id}.csv"
        )
