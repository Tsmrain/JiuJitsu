"""
Capa de Servicios del Dominio (Craig Larman / Motores Algorítmicos y Fachada de Pipeline).
Expone los componentes de procesamiento cinemático, alineación DTW, anotación visual y orquestación.
"""

from src.services.dtw_comparator import DTWComparator
from src.services.kalman_filter import (
    KalmanFilterTracker,
    KalmanTracker,
    OclusionProlongadaError,
)
from src.services.opencv_annotator import OpenCVAnnotator
from src.services.pipeline_engine import (
    PipelineBiomecanicoEngine,
    ResultadoPipelineDTO,
)
from src.services.position_similarity import (
    GRUPOS_PUNTOS_CLAVE_28,
    PositionSimilarityService,
)

__all__ = [
    "KalmanTracker",
    "KalmanFilterTracker",
    "OclusionProlongadaError",
    "DTWComparator",
    "OpenCVAnnotator",
    "PipelineBiomecanicoEngine",
    "ResultadoPipelineDTO",
    "PositionSimilarityService",
    "GRUPOS_PUNTOS_CLAVE_28",
]
