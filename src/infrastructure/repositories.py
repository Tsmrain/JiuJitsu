import os
import json
from typing import List, Optional, Dict
from datetime import datetime
from uuid import UUID

from ..domain.entities import TecnicaMaestra, AnalisisBiomecanico, ReglaBiomecanica, FotogramaAnotado
from ..domain.value_objects import ErrorBiomecanico


def _json_serial(obj):
    """Serializador para tipos UUID, datetime y dataclasses."""
    if isinstance(obj, UUID):
        return str(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    if hasattr(obj, '__dict__'):
        return obj.__dict__
    raise TypeError(f"Type {type(obj)} not serializable")


class TecnicaMaestraRepository:
    """
    Repositorio de catálogo de técnicas maestras (Patrón Repository - Mannino / Larman).
    """

    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path or os.path.join("data", "tecnicas.json")
        self._catalogo: Dict[UUID, TecnicaMaestra] = {}
        self._cargar()

    def _cargar(self):
        if not os.path.exists(self.storage_path):
            return
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data:
                    t_id = UUID(item['id']) if isinstance(item['id'], str) else item['id']
                    reglas = [
                        ReglaBiomecanica(**r) for r in item.get('reglas', [])
                    ]
                    tecnica = TecnicaMaestra(
                        id=t_id,
                        nombre=item.get('nombre', ''),
                        categoria=item.get('categoria', ''),
                        posicion_origen=item.get('posicion_origen', ''),
                        video_url=item.get('video_url', ''),
                        ventana_sakoe_chiba=item.get('ventana_sakoe_chiba', 0.15),
                        fecha_carga=datetime.fromisoformat(item['fecha_carga']) if 'fecha_carga' in item else datetime.now(),
                        reglas=reglas
                    )
                    self._catalogo[tecnica.id] = tecnica
        except (json.JSONDecodeError, KeyError, ValueError):
            pass

    def _guardar(self):
        dir_name = os.path.dirname(self.storage_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            lista = [
                {
                    'id': str(t.id),
                    'nombre': t.nombre,
                    'categoria': t.categoria,
                    'posicion_origen': t.posicion_origen,
                    'video_url': t.video_url,
                    'ventana_sakoe_chiba': t.ventana_sakoe_chiba,
                    'fecha_carga': t.fecha_carga.isoformat(),
                    'reglas': [r.__dict__ for r in t.reglas]
                }
                for t in self._catalogo.values()
            ]
            json.dump(lista, f, indent=2, ensure_ascii=False)

    def guardar(self, tecnica: TecnicaMaestra) -> TecnicaMaestra:
        self._catalogo[tecnica.id] = tecnica
        self._guardar()
        return tecnica

    def obtener_por_id(self, id: UUID) -> Optional[TecnicaMaestra]:
        return self._catalogo.get(id)

    def obtener_todas(self) -> List[TecnicaMaestra]:
        return list(self._catalogo.values())

    def eliminar(self, id: UUID) -> bool:
        if id in self._catalogo:
            del self._catalogo[id]
            self._guardar()
            return True
        return False


class AnalisisRepository:
    """
    Repositorio de análisis biomecánicos persistidos (Patrón Repository).
    """

    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path or os.path.join("data", "analisis.json")
        self._analisis: List[AnalisisBiomecanico] = []
        self._cargar()

    def _cargar(self):
        if not os.path.exists(self.storage_path):
            return
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data:
                    a_id = UUID(item['id']) if isinstance(item['id'], str) else item['id']
                    v_id = UUID(item['video_id']) if isinstance(item['video_id'], str) else item['video_id']
                    fotograma = None
                    if item.get('fotograma_anotado'):
                        fotograma = FotogramaAnotado(**item['fotograma_anotado'])
                    errores = [
                        ErrorBiomecanico(**e) for e in item.get('errores', [])
                    ]
                    analisis = AnalisisBiomecanico(
                        id=a_id,
                        video_id=v_id,
                        fecha_procesamiento=datetime.fromisoformat(item['fecha_procesamiento']) if 'fecha_procesamiento' in item else datetime.now(),
                        desviacion_angular_maxima=item.get('desviacion_angular_maxima', 0.0),
                        articulacion_afectada=item.get('articulacion_afectada', ''),
                        estado_computo=item.get('estado_computo', 'completado'),
                        fotograma_anotado=fotograma,
                        errores=errores
                    )
                    self._analisis.append(analisis)
        except (json.JSONDecodeError, KeyError, ValueError):
            pass

    def _guardar(self):
        dir_name = os.path.dirname(self.storage_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            lista = [
                {
                    'id': str(a.id),
                    'video_id': str(a.video_id),
                    'fecha_procesamiento': a.fecha_procesamiento.isoformat(),
                    'desviacion_angular_maxima': a.desviacion_angular_maxima,
                    'articulacion_afectada': a.articulacion_afectada,
                    'estado_computo': a.estado_computo,
                    'fotograma_anotado': a.fotograma_anotado.__dict__ if a.fotograma_anotado else None,
                    'errores': [e.__dict__ for e in a.errores]
                }
                for a in self._analisis
            ]
            json.dump(lista, f, indent=2, ensure_ascii=False)

    def guardar(self, analisis: AnalisisBiomecanico) -> AnalisisBiomecanico:
        self._analisis.append(analisis)
        self._guardar()
        return analisis

    def obtener_por_id(self, id: UUID) -> Optional[AnalisisBiomecanico]:
        for a in self._analisis:
            if a.id == id:
                return a
        return None

    def obtener_por_video(self, video_id: UUID) -> List[AnalisisBiomecanico]:
        return [a for a in self._analisis if a.video_id == video_id]

    def obtener_todos(self) -> List[AnalisisBiomecanico]:
        return list(self._analisis)
