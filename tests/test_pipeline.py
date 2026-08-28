"""
Pruebas Unitarias para la Fachada del Pipeline Biomecánico (PipelineBiomecanicoEngine - Craig Larman / TDD).
"""

import unittest
from uuid import uuid4
import numpy as np

from src.domain.models import ReglaBiomecanica, TecnicaMaestra
from src.services.pipeline_engine import PipelineBiomecanicoEngine, ResultadoPipelineDTO


class TestPipelineBiomecanicoEngine(unittest.TestCase):

    def setUp(self) -> None:
        self.engine = PipelineBiomecanicoEngine(ventana_sakoe_chiba_default=0.15, calidad_jpeg=85)
        
        # Configuración de técnica maestra de prueba (Armbar / Llave de Brazo)
        self.regla_codo = ReglaBiomecanica(
            id=uuid4(),
            articulacion_clave="codo_derecho",
            umbral_angular_tolerado=15.0,
            descripcion_error="Brazo hiper-extendido sin control de muneca",
        )
        self.tecnica = TecnicaMaestra(
            id=uuid4(),
            nombre="Armbar desde Guardia Cerrada",
            categoria_tecnica="Llave de Brazo",
            posicion_origen="Guardia Cerrada",
            ventana_sakoe_chiba=0.15,
            video_url="https://obs.la-santiago.myhuaweicloud.com/bjj-videos-input/armbar_patron.mp4",
            reglas=[self.regla_codo],
        )

    def test_calculo_angulo_3d_invariante(self) -> None:
        """Prueba 1: Verifica que el cálculo vectorial 3D retorne exactamente 90 grados para vectores perpendiculares."""
        p_a = (1.0, 0.0, 0.0)  # Eje X
        p_b = (0.0, 0.0, 0.0)  # Vértice articulación
        p_c = (0.0, 1.0, 0.0)  # Eje Y

        angulo = self.engine.calcular_angulo_3d(p_a, p_b, p_c)
        self.assertAlmostEqual(angulo, 90.0, places=4)

    def test_ejecucion_con_falla_tecnica_genera_entregable(self) -> None:
        """Prueba 2: Serie con discrepancia > 15° genera diagnóstico EXITOSO con imagen anotada."""
        # Patrón maestro: flexión constante a 90 grados
        serie_patron = [90.0] * 30
        # Alumno: error biomecánico en cuadro 15 abriendo el brazo a 130 grados (error = 40° > umbral 15°)
        serie_alumno = [90.0] * 30
        serie_alumno[15] = 130.0

        resultado = self.engine.ejecutar_pipeline_completo(
            video_bytes=b"dummy_video_mp4_bytes",
            tecnica_maestra=self.tecnica,
            series_estudiante_override={"codo_derecho": serie_alumno},
            series_patron_override={"codo_derecho": serie_patron},
            coordenadas_error_override=(300, 200),
        )

        self.assertEqual(resultado.estado_computo, "EXITOSO")
        self.assertEqual(resultado.articulacion_afectada, "codo_derecho")
        self.assertAlmostEqual(resultado.desviacion_maxima, 40.0, places=1)
        self.assertIn("Brazo hiper-extendido", resultado.explicacion_error)
        self.assertIsNotNone(resultado.imagen_jpg_bytes)
        self.assertLess(len(resultado.imagen_jpg_bytes), 100_000)

    def test_ejecucion_limpia_sin_fallas(self) -> None:
        """Prueba 3: Serie con error < tolerancia retorna estado SIN_FALLAS sin generar imagen innecesaria."""
        # Variación menor de solo 5 grados (menor al umbral de 15°)
        serie_patron = [90.0] * 25
        serie_alumno = [95.0] * 25

        resultado = self.engine.ejecutar_pipeline_completo(
            video_bytes=b"dummy_video_mp4_bytes",
            tecnica_maestra=self.tecnica,
            series_estudiante_override={"codo_derecho": serie_alumno},
            series_patron_override={"codo_derecho": serie_patron},
        )

        self.assertEqual(resultado.estado_computo, "SIN_FALLAS")
        self.assertIsNone(resultado.imagen_jpg_bytes)
        self.assertLessEqual(resultado.desviacion_maxima, 15.0)

    def test_aborto_por_oclusion_prolongada_rf11(self) -> None:
        """Prueba 4: Oclusión continua prolongada retorna estado ABORTADO_OCLUSION sin persistencia (RF-11)."""
        resultado = self.engine.ejecutar_pipeline_completo(
            video_bytes=b"dummy_video_mp4_bytes",
            tecnica_maestra=self.tecnica,
            simular_oclusion_prolongada=True,
        )

        self.assertEqual(resultado.estado_computo, "ABORTADO_OCLUSION")
        self.assertIn("Oclusión continua prolongada", resultado.explicacion_error)
        self.assertIsNone(resultado.imagen_jpg_bytes)


if __name__ == "__main__":
    unittest.main()
