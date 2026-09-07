from typing import Dict, Optional

from ..entities import TecnicaMaestra, ReglaBiomecanica
from ...config import UMBRAL_ERROR


class RuleEngine:
    """
    Motor de Reglas Biomecánicas Deterministas (RF-10 - Pure Fabrication / Domain Service).
    Evalúa discrepancias angulares contra umbrales tolerados y genera explicaciones pedagógicas.
    """

    MENSAJES_DEFECTO: Dict[str, str] = {
        'codo_izq': "Codo izquierdo desviado {diff:.1f}° del patrón técnico del maestro",
        'codo_der': "Codo derecho desviado {diff:.1f}° del patrón técnico del maestro",
        'rodilla_izq': "Rodilla izquierda desviada {diff:.1f}° del patrón técnico del maestro",
        'rodilla_der': "Rodilla derecha desviada {diff:.1f}° del patrón técnico del maestro",
        'cadera': "Alineación de cadera desviada {diff:.1f}° del patrón técnico del maestro",
        'hombro': "Ángulo de hombro desviado {diff:.1f}° del patrón técnico del maestro"
    }

    @classmethod
    def es_critico(cls, diferencia: float, umbral: float = UMBRAL_ERROR) -> bool:
        """Determina si una desviación angular supera el umbral de tolerancia."""
        return diferencia > umbral

    @classmethod
    def generar_diagnostico(
        cls, articulacion: str, diferencia: float, tecnica: Optional[TecnicaMaestra] = None
    ) -> str:
        """
        Genera la explicación textual determinista del error detectado (RF-10).
        Si la técnica maestra tiene una regla registrada para la articulación, usa su descripción.
        """
        if tecnica and tecnica.reglas:
            for regla in tecnica.reglas:
                if regla.articulacion_clave == articulacion and regla.evaluar(diferencia):
                    return f"{regla.descripcion_error} (Desviación: {diferencia:.1f}°)"

        plantilla = cls.MENSAJES_DEFECTO.get(
            articulacion, "Desviación biomecánica en {articulacion}: {diff:.1f}°"
        )
        return plantilla.format(diff=diferencia, articulacion=articulacion)
