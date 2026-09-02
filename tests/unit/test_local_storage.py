"""
Prueba Unitaria TDD para LocalStorageAdapter.

Verifica el contrato de la interfaz IStorageProvider:
1. Guardado / Subida de un archivo de prueba simulado.
2. Recuperación / Descarga del archivo y validación de integridad de datos.
3. Manejo de excepciones ante archivos inexistentes.
"""

import os
import tempfile
import unittest
from pathlib import Path

from src.domain.interfaces import IStorageProvider
from src.infrastructure.storage.local_storage_adapter import LocalStorageAdapter


class TestLocalStorageAdapter(unittest.TestCase):
    """Suite de pruebas TDD para el adaptador de almacenamiento local."""

    def setUp(self):
        """Prepara directorios temporales aislados para cada prueba."""
        self.test_dir = tempfile.TemporaryDirectory()
        self.base_storage_dir = os.path.join(self.test_dir.name, "storage_root")
        self.adapter = LocalStorageAdapter(base_directory=self.base_storage_dir)

    def tearDown(self):
        """Limpia los directorios temporales creados."""
        self.test_dir.cleanup()

    def test_implements_istorage_provider_interface(self):
        """Verifica que LocalStorageAdapter cumpla con la interfaz IStorageProvider."""
        self.assertIsInstance(self.adapter, IStorageProvider)

    def test_upload_and_download_simulated_video(self):
        """
        Prueba TDD Core:
        - Crea un archivo de video simulado con contenido binario conocido.
        - Sube el archivo al almacenamiento local.
        - Descarga el archivo a una nueva ubicación.
        - Valida que el contenido recuperado sea idéntico byte a byte.
        """
        # 1. Crear archivo simulado original
        source_file_path = os.path.join(self.test_dir.name, "armbar_technique_sample.mp4")
        sample_payload = b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00isommp42simulated_bjj_data_stream_12345"
        
        with open(source_file_path, "wb") as f:
            f.write(sample_payload)

        # 2. Subir / Guardar en el almacenamiento local
        destination_name = "techniques/master/armbar_v1.mp4"
        stored_path = self.adapter.upload_video(
            source_path=source_file_path,
            destination_name=destination_name
        )

        # Validar que el archivo exista en el almacenamiento interno
        self.assertTrue(os.path.exists(stored_path))
        self.assertTrue(Path(stored_path).is_file())

        # 3. Descargar / Recuperar a una nueva ruta de destino
        download_target_path = os.path.join(self.test_dir.name, "downloads", "retrieved_armbar.mp4")
        retrieved_path = self.adapter.download_video(
            storage_path=stored_path,
            target_local_path=download_target_path
        )

        # 4. Validar existencia y consistencia bit a bit
        self.assertTrue(os.path.exists(retrieved_path))
        with open(retrieved_path, "rb") as f:
            retrieved_payload = f.read()

        self.assertEqual(retrieved_payload, sample_payload)

    def test_upload_non_existent_file_raises_filenotfound(self):
        """Verifica que intentar subir un archivo inexistente lance FileNotFoundError."""
        invalid_source = os.path.join(self.test_dir.name, "non_existent_video.mp4")
        with self.assertRaises(FileNotFoundError):
            self.adapter.upload_video(
                source_path=invalid_source,
                destination_name="test.mp4"
            )

    def test_download_non_existent_file_raises_filenotfound(self):
        """Verifica que intentar descargar un archivo inexistente lance FileNotFoundError."""
        invalid_storage_path = "non_existent_folder/missing_technique.mp4"
        target_path = os.path.join(self.test_dir.name, "output.mp4")
        
        with self.assertRaises(FileNotFoundError):
            self.adapter.download_video(
                storage_path=invalid_storage_path,
                target_local_path=target_path
            )


if __name__ == "__main__":
    unittest.main()
