# tests/test_abm_contratos.py
import pytest
from typing import get_type_hints
from src.domain.models import Profesor, TecnicaPatron, FuenteConocimiento, MatrizEsqueletica
from src.domain.interfaces import IProfesorRepository, ITecnicaRepository, IFuenteConocimientoRepository


class TestContratosDominioPuro:
    """Valida Variaciones Protegidas: Cero Optional[Any] en contratos."""

    def test_profesor_repository_no_retorna_any(self):
        hints = get_type_hints(IProfesorRepository.obtener_por_id)
        assert 'Any' not in str(hints.get('return', '')), \
            "VIOLACIÓN GRASP: IProfesorRepository.obtener_por_id retorna Any. Debe ser Optional[Profesor]"

    def test_tecnica_repository_no_retorna_any(self):
        hints = get_type_hints(ITecnicaRepository.obtener_patron)
        assert 'Any' not in str(hints.get('return', '')), \
            "VIOLACIÓN GRASP: ITecnicaRepository.obtener_patron retorna Any. Debe ser Optional[TecnicaPatron]"

    def test_fuente_repository_buscar_contexto_tipo_correcto(self):
        hints = get_type_hints(IFuenteConocimientoRepository.buscar_contexto)
        return_hint = str(hints.get('return', ''))
        assert 'FuenteConocimiento' in return_hint and 'Any' not in return_hint, \
            f"VIOLACIÓN GRASP: Tipo inválido {return_hint}. Debe retornar List[FuenteConocimiento]"


class TestEntidadesInmutablesExpertoInformacion:
    """Valida Experto en Información: Validación intrínseca en entidades puras."""

    def test_profesor_rechaza_email_invalido(self):
        with pytest.raises(ValueError):
            Profesor(id_profesor="P001", nombre="Test", email="email-invalido")

    def test_tecnica_rechaza_matriz_no_tipada(self):
        """Matriz debe ser instancia de MatrizEsqueletica, NO dict crudo (Mannino BCNF)."""
        with pytest.raises(TypeError):
            TecnicaPatron(
                id_tecnica="T001", id_profesor="P001", nombre="Guardia Cerrada",
                categoria="Guardia", matriz_esqueletica={"puntos": [1, 2, 3]},
                video_url="", descripcion=""
            )

    def test_fuente_rechaza_embedding_dimension_incorrecta(self):
        """Embedding debe tener exactamente 2048 dimensiones (Qwen3-VL-Embedding-2B)."""
        with pytest.raises(ValueError, match="La dimensión del embedding debe ser 2048"):
            FuenteConocimiento(
                id_fuente="F001", id_tecnica="T001", titulo="Test",
                tipo_recurso="PDF", embedding_vector=[0.1] * 768,
                chunk_texto="texto", fecha_carga=None
            )
