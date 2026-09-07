import os
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt

from .config import ARTICULACIONES, UMBRAL_ERROR, GRAFICAS_DIR
from .pose_extractor import PoseExtractor
from .angle_calculator import AngleCalculator
from .dtw_comparator import DTWComparator
from .frame_annotator import FrameAnnotator
from .csv_exporter import CSVExporter


class BiomechanicsPipeline:
    """
    Pipeline orquestador de análisis biomecánico de Jiu-Jitsu Brasileño.
    Integra extracción de poses (YOLO26-pose), normalización antropomórfica,
    alineación temporal (DTW con ventana Sakoe-Chiba), detección de error crítico,
    anotación gráfica con OpenCV y exportación tabular.
    """

    def __init__(self, modelo_path=None):
        self.pose_extractor = PoseExtractor(modelo_path=modelo_path)
        self.angle_calculator = AngleCalculator()
        self.dtw_comparator = DTWComparator()
        self.frame_annotator = FrameAnnotator()
        self.csv_exporter = CSVExporter()

    def ejecutar(self, ruta_maestro, ruta_alumno):
        """
        Ejecuta el pipeline completo comparando el video del alumno contra el maestro.
        """
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        resultados = {
            'session_id': session_id,
            'articulaciones': ARTICULACIONES,
            'errores': {},
            'distancias_dtw': {},
            'similitud': [],
            'mejor_error': None,
            'archivos': {}
        }

        # 1. Extracción de poses
        print("📹 Extrayendo keypoints...")
        kpts_maestro, frames_maestro = self.pose_extractor.procesar_video(ruta_maestro)
        kpts_alumno, frames_alumno = self.pose_extractor.procesar_video(ruta_alumno)
        print(f"   Maestro: {len(kpts_maestro)} frames extraídos")
        print(f"   Alumno:  {len(kpts_alumno)} frames extraídos")

        if len(kpts_maestro) == 0 or len(kpts_alumno) == 0:
            raise ValueError("No se pudieron detectar keypoints en uno o ambos videos.")

        # 2. Cálculo de ángulos articulares
        print("📐 Calculando ángulos articulares relativos...")
        angulos_maestro = self.angle_calculator.extraer_angulos_secuencia(kpts_maestro)
        angulos_alumno = self.angle_calculator.extraer_angulos_secuencia(kpts_alumno)

        # 3. Alineación temporal DTW por articulación
        print("🔄 Aplicando DTW con restricción de Sakoe-Chiba...")
        for art in ARTICULACIONES:
            dist, path, serie_m, serie_a = self.dtw_comparator.comparar_articulacion(
                angulos_maestro, angulos_alumno, art
            )
            if dist is not None:
                resultados['distancias_dtw'][art] = dist
                print(f"   {art:<12}: DTW = {dist:.2f}")

        # 4. Localización del error máximo global (RF-04)
        print("🎯 Identificando error biomecánico crítico...")
        errores_globales = []
        n_frames_comp = min(len(angulos_maestro), len(angulos_alumno))

        for art in ARTICULACIONES:
            errores_art = []
            for i in range(n_frames_comp):
                if art in angulos_maestro[i] and art in angulos_alumno[i]:
                    diff = abs(angulos_maestro[i][art] - angulos_alumno[i][art])
                    if diff > UMBRAL_ERROR:
                        errores_art.append((i, diff))
            if errores_art:
                max_error = max(errores_art, key=lambda x: x[1])
                errores_globales.append((art, max_error[0], max_error[1]))
                resultados['errores'][art] = {
                    'frame': max_error[0],
                    'error_grados': max_error[1]
                }

        if errores_globales:
            mejor_art, mejor_frame, mejor_error = max(errores_globales, key=lambda x: x[2])
            resultados['mejor_error'] = {
                'articulacion': mejor_art,
                'frame': mejor_frame,
                'error': mejor_error
            }
            print(f"\n   🔴 ERROR MÁXIMO GLOBAL: {mejor_art} con {mejor_error:.2f}° en frame {mejor_frame}")

        # 5. Anotación gráfica del fotograma clave (RF-05, RF-06)
        if resultados['mejor_error'] and len(frames_alumno) > resultados['mejor_error']['frame']:
            print("🖍️ Generando fotograma clave anotado con OpenCV...")
            me = resultados['mejor_error']
            frame = frames_alumno[me['frame']]
            kpts = kpts_alumno[me['frame']]
            anotado = self.frame_annotator.anotar_error(
                frame, kpts, me['articulacion'], me['error'], me['frame']
            )
            nombre_fotograma = f"frame_error_{session_id}.jpg"
            ruta_fotograma = self.frame_annotator.guardar(anotado, nombre_fotograma)
            resultados['archivos']['fotograma_anotado'] = ruta_fotograma
            print(f"   ✅ Fotograma guardado en: {ruta_fotograma}")

        # 6. Cálculo y guardado de curva de similitud angular temporal (RF-15)
        print("📊 Generando curva de similitud angular...")
        similitud = []
        for i in range(n_frames_comp):
            errores_frame = []
            for art in ARTICULACIONES:
                if art in angulos_maestro[i] and art in angulos_alumno[i]:
                    errores_frame.append(abs(angulos_maestro[i][art] - angulos_alumno[i][art]))
            if errores_frame:
                sim_val = max(0.0, float(100.0 - np.mean(errores_frame) * 2.0))
                similitud.append(sim_val)
            else:
                similitud.append(0.0)

        resultados['similitud'] = similitud

        # Guardar gráfico en disco
        plt.figure(figsize=(12, 5))
        plt.plot(similitud, color='#D90429', linewidth=2, label='Similitud Angular (%)')
        if resultados['mejor_error']:
            plt.axvline(x=resultados['mejor_error']['frame'], color='#2B2D42', linestyle='--',
                        label=f"Pico de Error (Frame {resultados['mejor_error']['frame']})")
        plt.title('Evolución de Similitud Angular por Frame (Jiu-Jitsu Biomechanics)', fontsize=13)
        plt.xlabel('Número de Frame', fontsize=11)
        plt.ylabel('Similitud (%)', fontsize=11)
        plt.ylim(0, 105)
        plt.grid(True, linestyle=':', alpha=0.6)
        plt.legend(loc='lower right')
        
        os.makedirs(GRAFICAS_DIR, exist_ok=True)
        ruta_grafica = os.path.join(GRAFICAS_DIR, f"similitud_{session_id}.png")
        plt.savefig(ruta_grafica, dpi=150, bbox_inches='tight')
        plt.close()
        resultados['archivos']['grafica_similitud'] = ruta_grafica
        print(f"   ✅ Gráfica de similitud guardada en: {ruta_grafica}")

        # 7. Exportación de datos a formato CSV (RF-14)
        print("📄 Exportando series de datos a CSV...")
        ruta_angulos = self.csv_exporter.exportar_angulos(
            angulos_alumno, f"skeleton_angle_similarity_{session_id}.csv"
        )
        ruta_sim = self.csv_exporter.exportar_similitud(
            similitud, f"skeleton_eachframe_similarity_{session_id}.csv"
        )
        resultados['archivos']['csv_angulos'] = ruta_angulos
        resultados['archivos']['csv_similitud'] = ruta_sim
        print(f"   ✅ CSVs guardados: {ruta_angulos}, {ruta_sim}")

        print("\n✅ Pipeline ejecutado exitosamente.")
        return resultados
