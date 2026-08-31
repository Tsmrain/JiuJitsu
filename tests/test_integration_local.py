"""
Pruebas de Integración End-to-End Local (TDD con SQLite en Memoria)

Simula el flujo completo del sistema sin depender de servicios externos en la nube:
    API Gateway Event -> functiongraph_handler -> AnalisisBiomecanicoController
    -> PipelineBiomecanicoEngine -> Repositorios SQLite (:memory:)
    -> AnalisisBiomecanico persistido en Base de Datos.

Autor: Santiago Borda Zambrana
Proyecto: Corpo & Mente Bolivia - Análisis Biomecánico BJJ
"""

from __future__ import annotations

import base64
import json
import unittest
import uuid
from unittest.mock import MagicMock

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from src.domain.models import ReglaBiomecanica, TecnicaMaestra
from src.infrastructure.database.models import AnalisisBiomecanicoDB, Base
from src.infrastructure.repositories.analisis_repository import AnalisisBiomecanicoRepository
from src.infrastructure.repositories.tecnica_repository import TecnicaMaestraRepository
from src.infrastructure.repositories.video_repository import VideoEjecucionRepository
from src.infrastructure.serverless.functiongraph_handler import handler
from src.infrastructure.storage.obs_adapter import HuaweiOBSStorageAdapter
from src.services.controllers.analisis_controller import AnalisisBiomecanicoController
from src.services.dtw_comparator import DTWComparator
from src.services.landmark_adapter import LandmarkAdapter
from src.services.pipeline_engine import PipelineBiomecanicoEngine


class TestIntegrationLocal(unittest.TestCase):
    """Pruebas de integración end-to-end con SQLite en memoria y mock de OBS."""

    def setUp(self) -> None:
        # Configurar base de datos SQLite en memoria con foreign keys activas
        self.engine = create_engine("sqlite:///:memory:", echo=False)

        @event.listens_for(self.engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        Base.metadata.create_all(self.engine)
        self.session_factory = sessionmaker(bind=self.engine)
        self.session: Session = self.session_factory()

        # Repositorios concretos conectados a la sesión SQLite
        self.tecnica_repo = TecnicaMaestraRepository(self.session)
        self.analisis_repo = AnalisisBiomecanicoRepository(self.session)
        self.video_repo = VideoEjecucionRepository(self.session)

        # Mock del cliente de almacenamiento OBS
        self.mock_obs_client = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status = 200
        self.mock_obs_client.putObject.return_value = mock_resp

        self.obs_adapter = HuaweiOBSStorageAdapter(
            server="obs.la-south-2.myhuaweicloud.com",
            bucket_input="bjj-videos-input",
            bucket_output="bjj-reports-output",
            client=self.mock_obs_client,
        )

        # Pipeline biomecánico real
        self.pipeline_engine = PipelineBiomecanicoEngine(
            landmark_adapter=LandmarkAdapter(),
            dtw_comparator=DTWComparator(),
        )

        # Controlador de caso de uso con dependencias cableadas
        self.controller = AnalisisBiomecanicoController(
            pipeline_engine=self.pipeline_engine,
            tecnica_repository=self.tecnica_repo,
            analisis_repository=self.analisis_repo,
            video_repository=self.video_repo,
            obs_adapter=self.obs_adapter,
        )

        # Insertar técnica de referencia en la BD para la prueba
        self.tecnica_id = uuid.uuid4()
        self.tecnica = TecnicaMaestra(
            nombre="Armbar desde Guardia Cerrada",
            categoria="Sumisión",
            posicion_origen="Guardia Cerrada",
            video_url="https://obs.huaweicloud.com/bjj-videos-input/armbar_master.mp4",
            ventana_sakoe_chiba=0.15,
            id_tecnica=self.tecnica_id,
        )
        self.regla = ReglaBiomecanica(
            articulacion_clave="codo_derecho",
            umbral_angular_tolerado=90.0,
            descripcion_error="Brazo hiper-extendido",
        )
        self.tecnica.agregar_regla(self.regla)
        self.tecnica_repo.guardar(self.tecnica)

    def tearDown(self) -> None:
        self.session.close()
        Base.metadata.drop_all(self.engine)

    def test_local_invocation_simulates_apig_success(self) -> None:
        """Flujo completo APIG -> Handler -> Controller -> DB -> 200 OK."""
        video_dummy = b"\x00" * (500 * 1024)  # 500 KB (< 5 MB)
        video_b64 = base64.b64encode(video_dummy).decode("utf-8")

        event = {
            "httpMethod": "POST",
            "body": video_b64,
            "isBase64Encoded": True,
            "headers": {"Content-Type": "application/json"},
            "queryStringParameters": {"tecnica_id": str(self.tecnica_id)},
        }

        # Invocar handler con controlador inyectado
        response = handler(event, controller=self.controller)

        # 1. Verificar respuesta HTTP de API Gateway
        self.assertEqual(response["statusCode"], 200)
        self.assertFalse(response["isBase64Encoded"])
        self.assertEqual(response["headers"]["Content-Type"], "application/json")

        body = json.loads(response["body"])
        self.assertEqual(body["estado_computo"], "EXITOSO")
        self.assertIn("distancia_dtw", body)
        self.assertIn("articulacion_afectada", body)
        self.assertIn("id_analisis", body)

        # 2. Verificar persistencia en base de datos SQLite en memoria
        analisis_guardado = self.session.query(AnalisisBiomecanicoDB).filter_by(
            id=uuid.UUID(body["id_analisis"])
        ).first()

        self.assertIsNotNone(analisis_guardado)
        self.assertEqual(analisis_guardado.estado_computo, "EXITOSO")
        self.assertEqual(analisis_guardado.articulacion_afectada, body["articulacion_afectada"])

    def test_local_invocation_rejects_oversized_video(self) -> None:
        """Video > 5 MB es rechazado con statusCode 400 y mensaje de límite."""
        video_grande = b"\x00" * int(5.5 * 1024 * 1024)  # 5.5 MB (> 5 MB)
        video_b64 = base64.b64encode(video_grande).decode("utf-8")

        event = {
            "httpMethod": "POST",
            "body": video_b64,
            "isBase64Encoded": True,
            "queryStringParameters": {"tecnica_id": str(self.tecnica_id)},
        }

        response = handler(event, controller=self.controller)

        self.assertEqual(response["statusCode"], 400)
        body = json.loads(response["body"])
        self.assertEqual(body["estado_computo"], "ERROR_VALIDACION")
        self.assertIn("peso del video", body["error"].lower())

    def test_local_invocation_tecnica_inexistente_returns_400(self) -> None:
        """ID de técnica que no existe en el repositorio retorna 400."""
        video_dummy = b"\x00" * 1024
        video_b64 = base64.b64encode(video_dummy).decode("utf-8")

        event = {
            "httpMethod": "POST",
            "body": video_b64,
            "isBase64Encoded": True,
            "queryStringParameters": {"tecnica_id": str(uuid.uuid4())},
        }

        response = handler(event, controller=self.controller)

        self.assertEqual(response["statusCode"], 400)
        body = json.loads(response["body"])
        self.assertEqual(body["estado_computo"], "ERROR_VALIDACION")
        self.assertIn("no fue encontrada", body["error"].lower())


if __name__ == "__main__":
    unittest.main()
