#!/usr/bin/env python3
"""
Punto de entrada principal (CLI) para el sistema de análisis biomecánico de Jiu-Jitsu.
Implementa arquitectura en capas (Larman) con Inyección de Dependencias (GoF / GRASP).
"""

import argparse
import sys
import os

from src.infrastructure.adapters.yolo_adapter import YOLOPoseExtractor
from src.infrastructure.storage import LocalStorageProvider
from src.application.pipeline import BiomechanicsPipeline
from src.domain.services import AngleCalculatorImpl, DTWComparatorImpl, FrameAnnotatorImpl
from src.config import VIDEOS_DIR
from src.utils import verificar_videos, formatear_resumen


def main():
    parser = argparse.ArgumentParser(
        description="Sistema de Análisis Biomecánico de Brazilian Jiu-Jitsu (YOLO26-pose + DTW Sakoe-Chiba)"
    )
    parser.add_argument("--maestro", default=None, help="Ruta al video del maestro (default: Videos/Maestro.mp4)")
    parser.add_argument("--alumno", default=None, help="Ruta al video del alumno (default: Videos/Alumno.mp4)")
    parser.add_argument("--output", default="resultados", help="Directorio de salida para fotogramas y reportes")
    args = parser.parse_args()

    # Resolver rutas de video por defecto si no se especifican
    ruta_maestro = args.maestro
    ruta_alumno = args.alumno

    if not ruta_maestro or not ruta_alumno:
        default_m, default_a = verificar_videos(VIDEOS_DIR)
        ruta_maestro = ruta_maestro or default_m
        ruta_alumno = ruta_alumno or default_a

    # Validar existencia de archivos
    if not os.path.exists(ruta_maestro):
        print(f"❌ Error: Video maestro no encontrado: {ruta_maestro}")
        sys.exit(1)

    if not os.path.exists(ruta_alumno):
        print(f"❌ Error: Video alumno no encontrado: {ruta_alumno}")
        sys.exit(1)

    print(f"🥋 Configurando Dependencias de la Arquitectura en Capas...")
    # Configuración de dependencias (Inyección de Dependencias - Inversion of Control)
    storage = LocalStorageProvider()
    pose_extractor = YOLOPoseExtractor()
    angle_calculator = AngleCalculatorImpl()
    dtw_comparator = DTWComparatorImpl()
    frame_annotator = FrameAnnotatorImpl()

    # Creación del controlador de caso de uso (Larman Controller)
    pipeline = BiomechanicsPipeline(
        pose_extractor=pose_extractor,
        angle_calculator=angle_calculator,
        dtw_comparator=dtw_comparator,
        frame_annotator=frame_annotator,
        storage=storage
    )

    # Ejecución
    resultado = pipeline.ejecutar(ruta_maestro, ruta_alumno)

    print(f"\n" + "=" * 60)
    print(f"📋 RESUMEN FINAL DEL ANÁLISIS")
    print(f"=" * 60)
    print(f"Estado de Cómputo:           {resultado.estado_computo.upper()}")
    print(f"Desviación Angular Máxima:   {resultado.desviacion_angular_maxima:.2f}°")
    print(f"Articulación Afectada:       {resultado.articulacion_afectada.replace('_', ' ').upper()}")
    print(f"Total de Errores Detectados: {len(resultado.errores)}")
    if resultado.fotograma_anotado:
        print(f"Fotograma Anotado:           {resultado.fotograma_anotado.imagen_url}")
    print(f"=" * 60)
    return resultado


if __name__ == "__main__":
    main()
