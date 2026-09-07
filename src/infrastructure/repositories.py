import sqlite3
import uuid
import json
from pathlib import Path
from typing import List, Optional, Union, Dict, Any
from datetime import datetime
from uuid import UUID

from ..config import DB_PATH
from ..domain.entities import TecnicaMaestra, AnalisisBiomecanico, ReglaBiomecanica, FotogramaAnotado
from ..domain.value_objects import ErrorBiomecanico


class SQLiteDB:
    """Singleton para gestión de conexión SQLite con Integridad Referencial (Mannino)."""
    _instance = None

    def __new__(cls, db_path: Optional[Union[str, Path]] = None):
        if cls._instance is None:
            cls._instance = super(SQLiteDB, cls).__new__(cls)
            target_path = Path(db_path) if db_path else Path(DB_PATH)
            target_path.parent.mkdir(parents=True, exist_ok=True)
            cls._instance.conn = sqlite3.connect(str(target_path), check_same_thread=False)
            cls._instance.conn.row_factory = sqlite3.Row
            # CRÍTICO (Mannino): Activar Foreign Keys en SQLite
            cls._instance.conn.execute("PRAGMA foreign_keys = ON;")
            cls._instance._create_tables()
        return cls._instance

    def _create_tables(self):
        cursor = self.conn.cursor()
        cursor.executescript('''
            CREATE TABLE IF NOT EXISTS escuela_bjj (
                id_escuela TEXT PRIMARY KEY,
                nombre TEXT NOT NULL,
                ciudad TEXT
            );

            CREATE TABLE IF NOT EXISTS usuario_academia (
                id_usuario TEXT PRIMARY KEY,
                escuela_id TEXT,
                nombre_completo TEXT NOT NULL,
                correo_electronico TEXT UNIQUE,
                fecha_registro DATE DEFAULT CURRENT_DATE,
                FOREIGN KEY (escuela_id) REFERENCES escuela_bjj(id_escuela)
            );

            CREATE TABLE IF NOT EXISTS estudiante (
                id_usuario TEXT PRIMARY KEY,
                grado_cinturon TEXT,
                peso_kg REAL,
                estado_membresia TEXT DEFAULT 'activa',
                FOREIGN KEY (id_usuario) REFERENCES usuario_academia(id_usuario) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS tecnica_maestra (
                id_tecnica TEXT PRIMARY KEY,
                nombre TEXT NOT NULL,
                categoria_tecnica TEXT NOT NULL,
                posicion_origen TEXT NOT NULL,
                video_url TEXT,
                ventana_sakoe_chiba REAL DEFAULT 0.15,
                fecha_carga TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(categoria_tecnica, posicion_origen)
            );

            CREATE TABLE IF NOT EXISTS regla_biomecanica (
                id_regla TEXT PRIMARY KEY,
                tecnica_id TEXT NOT NULL,
                articulacion_clave TEXT NOT NULL,
                umbral_angular_tolerado REAL DEFAULT 15.0,
                descripcion_error TEXT,
                FOREIGN KEY (tecnica_id) REFERENCES tecnica_maestra(id_tecnica) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS video_ejecucion (
                id_video TEXT PRIMARY KEY,
                estudiante_id TEXT,
                tecnica_id TEXT,
                video_url TEXT NOT NULL,
                fecha_carga TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (estudiante_id) REFERENCES estudiante(id_usuario) ON DELETE CASCADE,
                FOREIGN KEY (tecnica_id) REFERENCES tecnica_maestra(id_tecnica)
            );

            CREATE TABLE IF NOT EXISTS analisis_biomecanico (
                id_analisis TEXT PRIMARY KEY,
                video_id TEXT NOT NULL,
                desviacion_angular_maxima REAL DEFAULT 0.0,
                articulacion_afectada TEXT,
                puntuacion_global REAL DEFAULT 100.0,
                cantidad_errores INTEGER DEFAULT 0,
                estado_computo TEXT CHECK(estado_computo IN ('completado', 'fallo_tecnico')),
                errores_json TEXT,
                fecha_procesamiento TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS fotograma_anotado (
                id_fotograma TEXT PRIMARY KEY,
                analisis_id TEXT UNIQUE NOT NULL,
                imagen_url TEXT NOT NULL,
                coordenada_error_x INTEGER,
                coordenada_error_y INTEGER,
                explicacion_causa TEXT,
                FOREIGN KEY (analisis_id) REFERENCES analisis_biomecanico(id_analisis) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS rol_usuario (
                id_rol TEXT PRIMARY KEY CHECK(id_rol IN ('profesor', 'alumno')),
                descripcion TEXT NOT NULL
            );

            INSERT OR IGNORE INTO rol_usuario (id_rol, descripcion) VALUES
            ('profesor', 'Head Coach / Administrador de Técnicas y Cátedra'),
            ('alumno', 'Practicante / Atleta en Tatami para Auditoría Biomecánica');

            CREATE INDEX IF NOT EXISTS idx_video_estudiante ON video_ejecucion(estudiante_id);
            CREATE INDEX IF NOT EXISTS idx_tecnica_categoria_posicion ON tecnica_maestra(categoria_tecnica, posicion_origen);
            CREATE INDEX IF NOT EXISTS idx_analisis_video ON analisis_biomecanico(video_id);
        ''')
        self.conn.commit()

    def get_cursor(self):
        return self.conn.cursor()

    def commit(self):
        self.conn.commit()


class TecnicaMaestraRepository:
    """Repositorio de catálogo de técnicas maestras (Patrón Repository - Mannino)."""

    def __init__(self, db_path: Optional[Union[str, Path]] = None):
        self.db = SQLiteDB(db_path)

    def guardar(
        self,
        tecnica: Optional[TecnicaMaestra] = None,
        id_tecnica: Optional[Any] = None,
        nombre: Optional[str] = None,
        categoria: Optional[str] = None,
        posicion: Optional[str] = None,
        video_url: Optional[str] = None,
        ventana_sakoe_chiba: float = 0.15
    ) -> TecnicaMaestra:
        """Permite guardar pasando la entidad TecnicaMaestra o parámetros individuales."""
        if isinstance(tecnica, TecnicaMaestra):
            t_id = str(tecnica.id)
            t_nom = tecnica.nombre
            t_cat = tecnica.categoria
            t_pos = tecnica.posicion_origen
            t_url = tecnica.video_url
            t_ven = tecnica.ventana_sakoe_chiba
            entidad = tecnica
        else:
            t_id = str(id_tecnica or uuid.uuid4())
            t_nom = nombre or ""
            t_cat = categoria or ""
            t_pos = posicion or ""
            t_url = video_url or ""
            t_ven = ventana_sakoe_chiba
            entidad = TecnicaMaestra(
                id=UUID(t_id),
                nombre=t_nom,
                categoria=t_cat,
                posicion_origen=t_pos,
                video_url=t_url,
                ventana_sakoe_chiba=t_ven
            )

        cursor = self.db.get_cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO tecnica_maestra 
            (id_tecnica, nombre, categoria_tecnica, posicion_origen, video_url, ventana_sakoe_chiba)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (t_id, t_nom, t_cat, t_pos, t_url, t_ven))

        if entidad.reglas:
            for r in entidad.reglas:
                r_id = str(uuid.uuid4())
                cursor.execute('''
                    INSERT OR REPLACE INTO regla_biomecanica
                    (id_regla, tecnica_id, articulacion_clave, umbral_angular_tolerado, descripcion_error)
                    VALUES (?, ?, ?, ?, ?)
                ''', (r_id, t_id, r.articulacion_clave, r.umbral_angular_tolerado, r.descripcion_error))

        self.db.commit()
        return entidad

    def obtener_por_id(self, id: Union[UUID, str]) -> Optional[TecnicaMaestra]:
        cursor = self.db.get_cursor()
        cursor.execute('SELECT * FROM tecnica_maestra WHERE id_tecnica = ?', (str(id),))
        row = cursor.fetchone()
        if not row:
            return None
        return self._row_to_entity(row)

    def obtener_todas(self) -> List[TecnicaMaestra]:
        cursor = self.db.get_cursor()
        cursor.execute('SELECT * FROM tecnica_maestra')
        return [self._row_to_entity(row) for row in cursor.fetchall()]

    def eliminar(self, id: Union[UUID, str]) -> bool:
        cursor = self.db.get_cursor()
        cursor.execute('DELETE FROM tecnica_maestra WHERE id_tecnica = ?', (str(id),))
        self.db.commit()
        return cursor.rowcount > 0

    def _row_to_entity(self, row: sqlite3.Row) -> TecnicaMaestra:
        t_id = UUID(row['id_tecnica'])
        cursor = self.db.get_cursor()
        cursor.execute('SELECT * FROM regla_biomecanica WHERE tecnica_id = ?', (str(t_id),))
        reglas_rows = cursor.fetchall()
        reglas = [
            ReglaBiomecanica(
                articulacion_clave=r['articulacion_clave'],
                umbral_angular_tolerado=r['umbral_angular_tolerado'],
                descripcion_error=r['descripcion_error'] or ""
            )
            for r in reglas_rows
        ]
        return TecnicaMaestra(
            id=t_id,
            nombre=row['nombre'],
            categoria=row['categoria_tecnica'],
            posicion_origen=row['posicion_origen'],
            video_url=row['video_url'] or "",
            ventana_sakoe_chiba=row['ventana_sakoe_chiba'] or 0.15,
            reglas=reglas
        )


class AnalisisRepository:
    """Repositorio de análisis biomecánicos persistidos (Patrón Repository - Mannino)."""

    def __init__(self, db_path: Optional[Union[str, Path]] = None):
        self.db = SQLiteDB(db_path)

    def guardar(self, analisis: AnalisisBiomecanico) -> AnalisisBiomecanico:
        cursor = self.db.get_cursor()
        errores_data = [
            {
                'articulacion': e.articulacion,
                'angulo_alumno': e.angulo_alumno,
                'angulo_maestro': e.angulo_maestro,
                'diferencia': e.diferencia,
                'frame': e.frame,
                'mensaje': e.mensaje
            }
            for e in analisis.errores
        ]
        errores_json = json.dumps(errores_data)

        cursor.execute('''
            INSERT OR REPLACE INTO analisis_biomecanico
            (id_analisis, video_id, desviacion_angular_maxima, articulacion_afectada,
             puntuacion_global, cantidad_errores, estado_computo, errores_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            str(analisis.id),
            str(analisis.video_id),
            analisis.desviacion_angular_maxima,
            analisis.articulacion_afectada,
            getattr(analisis, 'puntuacion_global', 100.0),
            len(analisis.errores),
            analisis.estado_computo,
            errores_json
        ))

        if analisis.fotograma_anotado:
            f_id = str(uuid.uuid4())
            fa = analisis.fotograma_anotado
            cursor.execute('''
                INSERT OR REPLACE INTO fotograma_anotado
                (id_fotograma, analisis_id, imagen_url, coordenada_error_x, coordenada_error_y, explicacion_causa)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                f_id,
                str(analisis.id),
                fa.imagen_url,
                fa.coordenada_error_x,
                fa.coordenada_error_y,
                fa.explicacion_causa
            ))

        self.db.commit()
        return analisis

    def obtener_por_id(self, id: Union[UUID, str]) -> Optional[AnalisisBiomecanico]:
        cursor = self.db.get_cursor()
        cursor.execute('SELECT * FROM analisis_biomecanico WHERE id_analisis = ?', (str(id),))
        row = cursor.fetchone()
        if not row:
            return None
        return self._row_to_entity(row)

    def obtener_por_video(self, video_id: Union[UUID, str]) -> List[AnalisisBiomecanico]:
        cursor = self.db.get_cursor()
        cursor.execute('SELECT * FROM analisis_biomecanico WHERE video_id = ?', (str(video_id),))
        return [self._row_to_entity(row) for row in cursor.fetchall()]

    def obtener_todos(self) -> List[AnalisisBiomecanico]:
        cursor = self.db.get_cursor()
        cursor.execute('SELECT * FROM analisis_biomecanico')
        return [self._row_to_entity(row) for row in cursor.fetchall()]

    def _row_to_entity(self, row: sqlite3.Row) -> AnalisisBiomecanico:
        a_id = UUID(row['id_analisis'])
        v_id = UUID(row['video_id'])
        cursor = self.db.get_cursor()
        cursor.execute('SELECT * FROM fotograma_anotado WHERE analisis_id = ?', (str(a_id),))
        f_row = cursor.fetchone()

        fotograma = None
        if f_row:
            fotograma = FotogramaAnotado(
                imagen_url=f_row['imagen_url'],
                coordenada_error_x=f_row['coordenada_error_x'] or 0,
                coordenada_error_y=f_row['coordenada_error_y'] or 0,
                explicacion_causa=f_row['explicacion_causa'] or ""
            )

        errores = []
        if row['errores_json']:
            try:
                for e in json.loads(row['errores_json']):
                    errores.append(ErrorBiomecanico(**e))
            except Exception:
                pass

        return AnalisisBiomecanico(
            id=a_id,
            video_id=v_id,
            desviacion_angular_maxima=row['desviacion_angular_maxima'] or 0.0,
            articulacion_afectada=row['articulacion_afectada'] or "",
            puntuacion_global=row['puntuacion_global'] if 'puntuacion_global' in row.keys() and row['puntuacion_global'] is not None else 100.0,
            estado_computo=row['estado_computo'] or "completado",
            fotograma_anotado=fotograma,
            errores=errores
        )
