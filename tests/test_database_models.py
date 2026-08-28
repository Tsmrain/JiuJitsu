"""
Pruebas Unitarias para los Modelos Relacionales ORM (SQLAlchemy 2.0 / Michael V. Mannino / TDD).
"""

import unittest
import uuid
from datetime import date, datetime, timezone

from src.infrastructure.database.models import (
    AnalisisBiomecanico,
    Base,
    CodigoActivacion,
    EscuelaBJJ,
    Estudiante,
    FotogramaAnotado,
    HeadCoach,
    HistorialProgresion,
    ReglaBiomecanica,
    TecnicaMaestra,
    UsuarioAcademia,
    VideoEjecucion,
)


class TestDatabaseModels(unittest.TestCase):

    def test_todas_las_11_tablas_registradas_en_metadata(self) -> None:
        """Prueba 1: Verifica que las 11 tablas del diseño Mannino estén mapeadas en el metadata."""
        nombres_esperados = {
            "escuela_bjj",
            "usuario_academia",
            "head_coach",
            "estudiante",
            "codigo_activacion",
            "tecnica_maestra",
            "regla_biomecanica",
            "video_ejecucion",
            "analisis_biomecanico",
            "fotograma_anotado",
            "historial_progresion",
        }
        tablas_registradas = set(Base.metadata.tables.keys())
        self.assertTrue(
            nombres_esperados.issubset(tablas_registradas),
            f"Faltan tablas en el metadata: {nombres_esperados - tablas_registradas}",
        )

    def test_herencia_table_per_subclass_comparticion_pk(self) -> None:
        """Prueba 2: Verifica que HeadCoach y Estudiante compartan la PK id_usuario con UsuarioAcademia."""
        tabla_usuario = Base.metadata.tables["usuario_academia"]
        tabla_coach = Base.metadata.tables["head_coach"]
        tabla_estudiante = Base.metadata.tables["estudiante"]

        self.assertIn("id_usuario", tabla_coach.primary_key.columns)
        self.assertIn("id_usuario", tabla_estudiante.primary_key.columns)

        # Verificar Foreign Key con CASCADE hacia usuario_academia.id_usuario
        fks_coach = list(tabla_coach.foreign_keys)
        self.assertEqual(len(fks_coach), 1)
        self.assertEqual(fks_coach[0].target_fullname, "usuario_academia.id_usuario")
        self.assertEqual(fks_coach[0].ondelete, "CASCADE")

        fks_estudiante = list(tabla_estudiante.foreign_keys)
        self.assertEqual(len(fks_estudiante), 1)
        self.assertEqual(fks_estudiante[0].target_fullname, "usuario_academia.id_usuario")
        self.assertEqual(fks_estudiante[0].ondelete, "CASCADE")

    def test_restriccion_unicidad_compuesta_tecnica_origen(self) -> None:
        """Prueba 3: Verifica el UniqueConstraint ('categoria_tecnica', 'posicion_origen')."""
        tabla_tecnica = Base.metadata.tables["tecnica_maestra"]
        nombres_unique = [c.name for c in tabla_tecnica.constraints if hasattr(c, "columns")]
        self.assertIn("uq_tecnica_origen", nombres_unique)

        # Encontrar el constraint específico y verificar columnas
        uq_constraint = next(c for c in tabla_tecnica.constraints if c.name == "uq_tecnica_origen")
        columnas_uq = {col.name for col in uq_constraint.columns}
        self.assertEqual(columnas_uq, {"categoria_tecnica", "posicion_origen"})

    def test_cardinalidad_uno_a_cero_o_uno_fotograma_anotado(self) -> None:
        """Prueba 4: Verifica que FotogramaAnotado tenga analisis_id con UniqueConstraint (1:0..1)."""
        tabla_fotograma = Base.metadata.tables["fotograma_anotado"]
        col_analisis_id = tabla_fotograma.columns["analisis_id"]
        self.assertTrue(
            col_analisis_id.unique,
            "analisis_id en fotograma_anotado debe ser UNIQUE para forzar la relación 1:0..1",
        )

    def test_instanciacion_correcta_entidades_dominio_orm(self) -> None:
        """Prueba 5: Verifica la instanciación de objetos ORM y sus propiedades básicas."""
        escuela = EscuelaBJJ(
            nombre="Corpo & Mente Bolivia",
            sede="Knock Out - Mia Plaza",
            ciudad="Santa Cruz de la Sierra",
            comunidad_whatsapp="https://chat.whatsapp.com/sample",
        )
        self.assertEqual(escuela.nombre, "Corpo & Mente Bolivia")

        coach = HeadCoach(
            escuela_id=escuela.id_escuela,
            nombre_completo="Ricardo De La Riva",
            telefono_whatsapp="+59170012345",
            correo_electronico="coach@corpoemente.bo",
            grado_cinturon="Faixa Preta 4to Dan",
            licencia_federativa="IBJJF-98231",
        )
        self.assertEqual(coach.tipo_usuario, "head_coach")
        self.assertEqual(coach.grado_cinturon, "Faixa Preta 4to Dan")

        alumno = Estudiante(
            escuela_id=escuela.id_escuela,
            nombre_completo="Carlos Gracie",
            telefono_whatsapp="+59171198765",
            correo_electronico="carlos@corpoemente.bo",
            grado_cinturon="Faixa Branca",
            peso_kg=78.5,
            estado_membresia="activa",
        )
        self.assertEqual(alumno.tipo_usuario, "estudiante")
        self.assertEqual(float(alumno.peso_kg), 78.5)


if __name__ == "__main__":
    unittest.main()
