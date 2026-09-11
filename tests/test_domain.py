import pytest
import math
from src.domain.models import Punto3D, MatrizEsqueletica, DesviacionArticular, CalculadoraBiomecanica


class TestPunto3D:
    def test_resta_vectorial(self):
        p1 = Punto3D(1.0, 2.0, 3.0)
        p2 = Punto3D(4.0, 6.0, 8.0)
        # Operador sobrecargado __sub__
        resultado_op = p1 - p2
        assert resultado_op.x == -3.0
        assert resultado_op.y == -4.0
        assert resultado_op.z == -5.0

        # Método explícito restar
        resultado_metodo = p1.restar(p2)
        assert resultado_metodo.x == -3.0
        assert resultado_metodo.y == -4.0
        assert resultado_metodo.z == -5.0

    def test_producto_punto(self):
        u = Punto3D(1.0, 0.0, 0.0)
        v = Punto3D(0.0, 1.0, 0.0)
        assert u.producto_punto(v) == 0.0

        w1 = Punto3D(2.0, 3.0, 4.0)
        w2 = Punto3D(5.0, 6.0, 7.0)
        # 2*5 + 3*6 + 4*7 = 10 + 18 + 28 = 56
        assert w1.producto_punto(w2) == 56.0

    def test_magnitud(self):
        p = Punto3D(3.0, 4.0, 0.0)
        assert p.magnitud() == 5.0
        assert p.norma() == 5.0


class TestMatrizEsqueletica:
    def test_calcular_angulo_90_grados(self):
        # Hombro(0,1,0), Codo(0,0,0), Muñeca(1,0,0) -> Ángulo 90 grados (pi / 2 rad)
        hombro = Punto3D(0.0, 1.0, 0.0)
        codo = Punto3D(0.0, 0.0, 0.0)
        muñeca = Punto3D(1.0, 0.0, 0.0)

        matriz = MatrizEsqueletica({
            'shoulder': hombro,
            'elbow': codo,
            'wrist': muñeca
        })

        angulo_rad = matriz.calcular_angulo('shoulder', 'elbow', 'wrist')
        assert math.isclose(angulo_rad, math.pi / 2, rel_tol=1e-5)

    def test_calcular_angulo_articular_codo(self):
        # Prueba explícitamente requerida en Tarea 1 de la Iteración 1
        hombro = Punto3D(0.0, 1.0, 0.0)
        codo = Punto3D(0.0, 0.0, 0.0)
        muñeca = Punto3D(1.0, 0.0, 0.0)

        matriz = MatrizEsqueletica({
            'left_shoulder': hombro,
            'left_elbow': codo,
            'left_wrist': muñeca
        })

        angulo_rad = matriz.calcular_angulo('left_shoulder', 'left_elbow', 'left_wrist')
        assert math.isclose(angulo_rad, math.pi / 2, rel_tol=1e-5)

    def test_clamping_precision_flotante(self):
        # Simula error de float donde el producto punto dividido magnitudes da ligeramente > 1.0
        # Debe clampear a 1.0 y devolver 0.0 rad sin lanzar ValueError
        matriz = MatrizEsqueletica({
            'a': Punto3D(1.0000000000000002, 1.0, 1.0),
            'centro': Punto3D(0.0, 0.0, 0.0),
            'c': Punto3D(1.0, 1.0, 1.0)
        })
        angulo = matriz.calcular_angulo('a', 'centro', 'c')
        assert math.isclose(angulo, 0.0, abs_tol=1e-7)

    def test_segmento_longitud_cero(self):
        # Segmento degenerado donde el codo y el hombro están en la misma posición (magnitud 0)
        matriz = MatrizEsqueletica({
            'a': Punto3D(0.0, 0.0, 0.0),
            'centro': Punto3D(0.0, 0.0, 0.0),
            'c': Punto3D(1.0, 0.0, 0.0)
        })
        # Debe manejarse de manera controlada retornando 0.0 sin colapsar por ZeroDivisionError
        assert matriz.calcular_angulo('a', 'centro', 'c') == 0.0

    def test_calcular_angulo_180_grados(self):
        # Brazo completamente extendido en línea recta (180 grados = pi rad)
        matriz = MatrizEsqueletica({
            'a': Punto3D(0.0, 1.0, 0.0),
            'centro': Punto3D(0.0, 0.0, 0.0),
            'c': Punto3D(0.0, -1.0, 0.0)
        })
        angulo_rad = matriz.calcular_angulo('a', 'centro', 'c')
        assert math.isclose(angulo_rad, math.pi, rel_tol=1e-5)

    def test_invarianza_traslacion_y_escala(self):
        # El ángulo debe ser invariante ante traslaciones espaciales y cambio de escala
        base = MatrizEsqueletica({
            'a': Punto3D(0.0, 1.0, 0.0),
            'centro': Punto3D(0.0, 0.0, 0.0),
            'c': Punto3D(1.0, 0.0, 0.0)
        })
        # Trasladado por (10, -5, 20) y escalado por un factor de 3.5
        trasladado = MatrizEsqueletica({
            'a': Punto3D(10.0, -5.0 + 3.5, 20.0),
            'centro': Punto3D(10.0, -5.0, 20.0),
            'c': Punto3D(10.0 + 3.5, -5.0, 20.0)
        })
        ang_base = base.calcular_angulo('a', 'centro', 'c')
        ang_tras = trasladado.calcular_angulo('a', 'centro', 'c')
        assert math.isclose(ang_base, ang_tras, rel_tol=1e-5)

    def test_articulacion_no_encontrada(self):
        matriz = MatrizEsqueletica({'a': Punto3D(0.0, 0.0, 0.0)})
        with pytest.raises(KeyError):
            matriz.calcular_angulo('a', 'punto_inexistente', 'c')


class TestCalculadoraBiomecanica:
    def test_evaluar_desviacion(self):
        # Patrón perfecto: codo a 90 grados
        patron = MatrizEsqueletica({
            'left_shoulder': Punto3D(0.0, 1.0, 0.0),
            'left_elbow': Punto3D(0.0, 0.0, 0.0),
            'left_wrist': Punto3D(1.0, 0.0, 0.0)
        })
        # Alumno: codo a 180 grados (brazo completamente estirado)
        alumno = MatrizEsqueletica({
            'left_shoulder': Punto3D(0.0, 1.0, 0.0),
            'left_elbow': Punto3D(0.0, 0.0, 0.0),
            'left_wrist': Punto3D(0.0, -1.0, 0.0)
        })

        calc = CalculadoraBiomecanica(articulaciones=[
            ('left_elbow', 'left_shoulder', 'left_elbow', 'left_wrist')
        ])
        desviaciones = calc.evaluar(alumno, patron)

        assert len(desviaciones) == 1
        desv = desviaciones[0]
        assert desv.nombre_articulacion == 'left_elbow'
        assert math.isclose(desv.angulo_esperado, 90.0, abs_tol=1e-3)
        assert math.isclose(desv.angulo_real, 180.0, abs_tol=1e-3)
        assert math.isclose(desv.desviacion_grados, 90.0, abs_tol=1e-3)

    def test_evaluar_desviacion_articular(self):
        # Prueba requerida en Tarea 1 de la Iteración 1
        patron = MatrizEsqueletica({
            'left_shoulder': Punto3D(0.0, 1.0, 0.0),
            'left_elbow': Punto3D(0.0, 0.0, 0.0),
            'left_wrist': Punto3D(1.0, 0.0, 0.0)
        })
        alumno = MatrizEsqueletica({
            'left_shoulder': Punto3D(0.0, 1.0, 0.0),
            'left_elbow': Punto3D(0.0, 0.0, 0.0),
            'left_wrist': Punto3D(1.0, 1.0, 0.0)  # ~45 grados
        })
        calc = CalculadoraBiomecanica(articulaciones=[
            ('left_elbow', 'left_shoulder', 'left_elbow', 'left_wrist')
        ])
        desviaciones = calc.evaluar(alumno, patron)
        assert len(desviaciones) == 1
        assert isinstance(desviaciones[0], DesviacionArticular)
        assert desviaciones[0].nombre_articulacion == 'left_elbow'
        assert desviaciones[0].desviacion_grados > 0.0

    def test_evaluar_con_umbral(self):
        patron = MatrizEsqueletica({
            'left_shoulder': Punto3D(0.0, 1.0, 0.0),
            'left_elbow': Punto3D(0.0, 0.0, 0.0),
            'left_wrist': Punto3D(1.0, 0.0, 0.0)
        })
        alumno = MatrizEsqueletica({
            'left_shoulder': Punto3D(0.0, 1.0, 0.0),
            'left_elbow': Punto3D(0.0, 0.0, 0.0),
            'left_wrist': Punto3D(1.0, 0.05, 0.0)  # Desviación pequeña (~2.86 grados)
        })
        calc = CalculadoraBiomecanica(articulaciones=[
            ('left_elbow', 'left_shoulder', 'left_elbow', 'left_wrist')
        ])
        # Con umbral de 5 grados, no debe reportar desviación
        desviaciones = calc.evaluar(alumno, patron, umbral=5.0)
        assert len(desviaciones) == 0
        # Con umbral de 1 grado, sí la reporta
        desviaciones_sensibles = calc.evaluar(alumno, patron, umbral=1.0)
        assert len(desviaciones_sensibles) == 1


class TestDominioPuroAislamiento:
    def test_sin_dependencias_de_frameworks(self):
        """Verifica que src.domain.models no importe pydantic, fastapi ni sqlalchemy."""
        import sys
        import src.domain.models as models_module

        # Inspeccionar código fuente de models.py
        with open(models_module.__file__, "r", encoding="utf-8") as f:
            contenido = f.read()

        prohibidos = ["pydantic", "fastapi", "sqlalchemy"]
        for framework in prohibidos:
            assert f"import {framework}" not in contenido, f"Violación de pureza: se encontró 'import {framework}'"
            assert f"from {framework}" not in contenido, f"Violación de pureza: se encontró 'from {framework}'"

