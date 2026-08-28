import uuid
from datetime import datetime, date
from sqlalchemy import (
    String, Numeric, Integer, Date, DateTime, Text, 
    ForeignKey, UniqueConstraint, CheckConstraint, func
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    """Base declarativa para todos los modelos ORM del sistema."""
    pass

# =============================================================================
# 1. ENTIDAD RAÍZ: ESCUELA
# =============================================================================
class EscuelaBJJ(Base):
    __tablename__ = 'escuela_bjj'
    
    id_escuela: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    sede: Mapped[str] = mapped_column(String(100), nullable=False)
    ciudad: Mapped[str] = mapped_column(String(50), nullable=False)
    comunidad_whatsapp: Mapped[str | None] = mapped_column(String(150), nullable=True)

    # Relaciones
    usuarios = relationship("UsuarioAcademia", back_populates="escuela")


# =============================================================================
# 2. SUPERCLASE ABSTRACTA: USUARIO (Herencia Table-per-Subclass de Mannino)
# =============================================================================
class UsuarioAcademia(Base):
    __tablename__ = 'usuario_academia'
    
    id_usuario: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    escuela_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('escuela_bjj.id_escuela', ondelete='RESTRICT'), nullable=False)
    nombre_completo: Mapped[str] = mapped_column(String(150), nullable=False)
    telefono_whatsapp: Mapped[str] = mapped_column(String(25), nullable=False)
    correo_electronico: Mapped[str] = mapped_column(String(120), nullable=False, unique=True) # UQ
    fecha_registro: Mapped[date] = mapped_column(Date, nullable=False, server_default=func.current_date())
    
    # NOTA DE ARQUITECTURA ORM: 
    # Se añade 'tipo_usuario' como discriminador polimórfico. Aunque el DDL 
    # estricto de la tesis no la incluye, SQLAlchemy la requiere para resolver 
    # la herencia de forma eficiente en memoria sin hacer JOINs innecesarios.
    tipo_usuario: Mapped[str] = mapped_column(String(20), nullable=False, server_default='usuario')

    escuela = relationship("EscuelaBJJ", back_populates="usuarios")
    
    __mapper_args__ = {
        "polymorphic_on": "tipo_usuario",
        "polymorphic_identity": "usuario",
    }


# =============================================================================
# 3 y 4. SUBCLASES: HEAD COACH Y ESTUDIANTE
# =============================================================================
class HeadCoach(UsuarioAcademia):
    __tablename__ = 'head_coach'
    
    id_usuario: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('usuario_academia.id_usuario', ondelete='CASCADE'), primary_key=True)
    grado_cinturon: Mapped[str] = mapped_column(String(30), nullable=False)
    licencia_federativa: Mapped[str | None] = mapped_column(String(50), nullable=True)

    codigos_emitidos = relationship("CodigoActivacion", back_populates="coach_emisor")
    tecnicas_homologadas = relationship("TecnicaMaestra", back_populates="coach")
    
    __mapper_args__ = {
        "polymorphic_identity": "head_coach",
    }

class Estudiante(UsuarioAcademia):
    __tablename__ = 'estudiante'
    
    id_usuario: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('usuario_academia.id_usuario', ondelete='CASCADE'), primary_key=True)
    grado_cinturon: Mapped[str] = mapped_column(String(30), nullable=False)
    peso_kg: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    estado_membresia: Mapped[str] = mapped_column(String(20), nullable=False, server_default='activa')

    __table_args__ = (
        CheckConstraint('peso_kg > 20.0 AND peso_kg < 250.0', name='chk_estudiante_peso'),
        CheckConstraint("estado_membresia IN ('activa', 'inactiva', 'suspendida')", name='chk_estudiante_membresia'),
    )

    codigos_asignados = relationship("CodigoActivacion", back_populates="estudiante")
    videos = relationship("VideoEjecucion", back_populates="estudiante")
    historial = relationship("HistorialProgresion", back_populates="estudiante", uselist=False)
    
    __mapper_args__ = {
        "polymorphic_identity": "estudiante",
    }


# =============================================================================
# 5. TOKEN DE MEMBRESÍA (RF-09)
# =============================================================================
class CodigoActivacion(Base):
    __tablename__ = 'codigo_activacion'
    
    id_codigo: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    coach_emisor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('head_coach.id_usuario', ondelete='RESTRICT'), nullable=False)
    estudiante_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey('estudiante.id_usuario', ondelete='SET NULL'), nullable=True)
    token: Mapped[str] = mapped_column(String(64), nullable=False, unique=True) # UQ
    fecha_emision: Mapped[date] = mapped_column(Date, nullable=False, server_default=func.current_date())
    fecha_expiracion: Mapped[date] = mapped_column(Date, nullable=False)
    estado: Mapped[str] = mapped_column(String(15), nullable=False, server_default='vigente')

    __table_args__ = (
        CheckConstraint('fecha_expiracion >= fecha_emision', name='chk_codigo_fechas'),
        CheckConstraint("estado IN ('vigente', 'expirado', 'revocado')", name='chk_codigo_estado'),
    )

    coach_emisor = relationship("HeadCoach", back_populates="codigos_emitidos")
    estudiante = relationship("Estudiante", back_populates="codigos_asignados")


# =============================================================================
# 6 y 7. CATÁLOGO CURRICULAR Y REGLAS DETERMINISTAS (RF-01, RF-10)
# =============================================================================
class TecnicaMaestra(Base):
    __tablename__ = 'tecnica_maestra'
    
    id_tecnica: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    coach_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('head_coach.id_usuario', ondelete='RESTRICT'), nullable=False)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    categoria_tecnica: Mapped[str] = mapped_column(String(60), nullable=False)
    posicion_origen: Mapped[str] = mapped_column(String(60), nullable=False)
    ventana_sakoe_chiba: Mapped[float] = mapped_column(Numeric(3, 2), nullable=False, server_default='0.15')
    video_url: Mapped[str] = mapped_column(String(255), nullable=False)
    fecha_carga: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        UniqueConstraint('categoria_tecnica', 'posicion_origen', name='uq_tecnica_origen'),
        CheckConstraint('ventana_sakoe_chiba >= 0.05 AND ventana_sakoe_chiba <= 0.30', name='chk_tecnica_ventana'),
    )

    coach = relationship("HeadCoach", back_populates="tecnicas_homologadas")
    reglas = relationship("ReglaBiomecanica", back_populates="tecnica", cascade="all, delete-orphan")
    videos = relationship("VideoEjecucion", back_populates="tecnica")

class ReglaBiomecanica(Base):
    __tablename__ = 'regla_biomecanica'
    
    id_regla: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tecnica_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('tecnica_maestra.id_tecnica', ondelete='CASCADE'), nullable=False)
    articulacion_clave: Mapped[str] = mapped_column(String(50), nullable=False)
    umbral_angular_tolerado: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    descripcion_error: Mapped[str] = mapped_column(Text, nullable=False)

    __table_args__ = (
        CheckConstraint('umbral_angular_tolerado >= 0.0', name='chk_regla_umbral'),
    )

    tecnica = relationship("TecnicaMaestra", back_populates="reglas")


# =============================================================================
# 8, 9 y 10. EJECUCIÓN, ANÁLISIS Y FOTOGRAMA (RF-11 Zero-Persistence)
# =============================================================================
class VideoEjecucion(Base):
    __tablename__ = 'video_ejecucion'
    
    id_video: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    estudiante_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('estudiante.id_usuario', ondelete='CASCADE'), nullable=False)
    tecnica_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('tecnica_maestra.id_tecnica', ondelete='RESTRICT'), nullable=False)
    fecha_captura: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    duracion_segundos: Mapped[float] = mapped_column(Numeric(4, 2), nullable=False)
    peso_mb: Mapped[float] = mapped_column(Numeric(4, 2), nullable=False)
    video_url: Mapped[str] = mapped_column(String(255), nullable=False)

    __table_args__ = (
        CheckConstraint('duracion_segundos <= 6.0', name='chk_video_duracion'),
        CheckConstraint('peso_mb <= 5.0', name='chk_video_peso'),
    )

    estudiante = relationship("Estudiante", back_populates="videos")
    tecnica = relationship("TecnicaMaestra", back_populates="videos")
    analisis = relationship("AnalisisBiomecanico", back_populates="video", uselist=False, cascade="all, delete-orphan")

class AnalisisBiomecanico(Base):
    __tablename__ = 'analisis_biomecanico'
    
    id_analisis: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('video_ejecucion.id_video', ondelete='CASCADE'), nullable=False)
    fecha_procesamiento: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    desviacion_angular_maxima: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    articulacion_afectada: Mapped[str] = mapped_column(String(50), nullable=False)
    estado_computo: Mapped[str] = mapped_column(String(20), nullable=False, server_default='completado')

    __table_args__ = (
        CheckConstraint("estado_computo IN ('completado', 'fallo_tecnico')", name='chk_analisis_estado'),
    )

    video = relationship("VideoEjecucion", back_populates="analisis")
    fotograma = relationship("FotogramaAnotado", back_populates="analisis", uselist=False, cascade="all, delete-orphan")

class FotogramaAnotado(Base):
    __tablename__ = 'fotograma_anotado'
    
    id_fotograma: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analisis_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('analisis_biomecanico.id_analisis', ondelete='CASCADE'), nullable=False, unique=True) # UQ 1:0..1
    imagen_url: Mapped[str] = mapped_column(String(255), nullable=False)
    coordenada_error_x: Mapped[int] = mapped_column(Integer, nullable=False)
    coordenada_error_y: Mapped[int] = mapped_column(Integer, nullable=False)
    explicacion_causa: Mapped[str] = mapped_column(Text, nullable=False)

    analisis = relationship("AnalisisBiomecanico", back_populates="fotograma")


# =============================================================================
# 11. HISTORIAL LONGITUDINAL (RF-12)
# =============================================================================
class HistorialProgresion(Base):
    __tablename__ = 'historial_progresion'
    
    id_historial: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    estudiante_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('estudiante.id_usuario', ondelete='CASCADE'), nullable=False, unique=True) # UQ 1:1
    puntuacion_global: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, server_default='100.0')
    cantidad_errores: Mapped[int] = mapped_column(Integer, nullable=False, server_default='0')
    fecha_ultima_evaluacion: Mapped[date] = mapped_column(Date, nullable=False, server_default=func.current_date())

    __table_args__ = (
        CheckConstraint('puntuacion_global >= 0.0 AND puntuacion_global <= 100.0', name='chk_historial_puntuacion'),
        CheckConstraint('cantidad_errores >= 0', name='chk_historial_errores'),
    )

    estudiante = relationship("Estudiante", back_populates="historial")
