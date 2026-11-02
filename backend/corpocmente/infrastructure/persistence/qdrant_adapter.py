import logging
import numpy as np
from typing import List, Dict, Optional, Any
from uuid import UUID
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue

from corpocmente.config import settings

import os
from corpocmente.infrastructure.ai.adapters import COCO_JOINT_NAMES

logger = logging.getLogger(__name__)
RAG_VECTOR_DIM = 2048

class VectorSearchResultDTO:
    def __init__(
        self,
        score: float,
        frame_path: str,
        discrepancias: List[str],
        frame_alumno_idx: Optional[int] = None,
        frame_referencia_idx: Optional[int] = None,
        articulaciones_criticas: Optional[List[int]] = None,
        keypoints_alumno: Optional[List[float]] = None,
        keypoints_referencia: Optional[List[float]] = None,
    ):
        self.score = score
        self.frame_path = frame_path
        self.discrepancias = discrepancias
        self.frame_alumno_idx = frame_alumno_idx
        self.frame_referencia_idx = frame_referencia_idx
        self.articulaciones_criticas = articulaciones_criticas or []
        self.keypoints_alumno = keypoints_alumno or []
        self.keypoints_referencia = keypoints_referencia or []

class QdrantVectorAdapter:
    """
    Adaptador (GoF Adapter) para encapsular las búsquedas por similitud vectorial (HNSW + Coseno)
    en Qdrant DB, aislando el dominio del cliente nativo de Qdrant.
    """

    def __init__(self, 
                 host: Optional[str] = None, 
                 port: Optional[int] = None, 
                 collection_name: Optional[str] = None,
                 client: Optional[QdrantClient] = None):
        self.host = host or settings.QDRANT_HOST
        self.port = port or settings.QDRANT_PORT
        self.pose_collection_name = collection_name or settings.QDRANT_COLLECTION
        self.rag_collection_name = settings.QDRANT_RAG_COLLECTION
        if self.pose_collection_name == self.rag_collection_name:
            raise ValueError("La colección biomecánica y la colección RAG deben ser distintas.")
        self._client = client

    @property
    def collection_name(self) -> str:
        """Alias retrocompatible para la colección biomecánica de keypoints (133 dims)."""
        return self.pose_collection_name

    @property
    def rag_collection(self) -> str:
        """Alias retrocompatible de la colección RAG multimodal (2048 dims)."""
        return self.rag_collection_name

    @property
    def client(self) -> QdrantClient:
        if self._client is None:
            self._client = QdrantClient(host=self.host, port=self.port)
        return self._client

    def asegurar_coleccion(self, vector_size: int = 133) -> None:
        """Crea la colección en Qdrant con métrica de Coseno si no existe previamente."""
        collections = [c.name for c in self.client.get_collections().collections]
        if self.pose_collection_name not in collections:
            self.client.create_collection(
                collection_name=self.pose_collection_name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
            )
            logger.info(f"Colección biomecánica '{self.pose_collection_name}' creada con dimensión {vector_size}.")

    def insertar_vector(self, vector_id: UUID, vector: List[float], payload: Dict) -> None:
        """Inserta o actualiza un vector biomecánico con sus metadatos (payload)."""
        point = PointStruct(
            id=str(vector_id),
            vector=vector,
            payload=payload
        )
        self.client.upsert(
            collection_name=self.pose_collection_name,
            points=[point]
        )

    def guardar_patron_secuencia(
        self,
        tecnica_id: UUID,
        patron_id: UUID,
        profesor_id: UUID,
        secuencia_kpts: List[List[float]],
        keypoint_schema_version: str = "coco17_v1"
    ) -> int:
        """
        Guarda en Qdrant los vectores crudos de 133 dimensiones correspondientes a cada
        frame de la secuencia del profesor, con sus metadatos de técnica, patrón y frame_idx.
        """
        self.asegurar_coleccion(vector_size=133)
        points = []
        import uuid
        for frame_idx, kpts in enumerate(secuencia_kpts):
            vec = list(kpts)
            if len(vec) < 133:
                vec.extend([0.0] * (133 - len(vec)))
            else:
                vec = vec[:133]

            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{patron_id}_{frame_idx}"))
            points.append(PointStruct(
                id=point_id,
                vector=vec,
                payload={
                    "tecnica_id": str(tecnica_id),
                    "patron_id": str(patron_id),
                    "profesor_id": str(profesor_id),
                    "frame_idx": int(frame_idx),
                    "keypoints_raw": vec,
                    "keypoint_schema_version": keypoint_schema_version,
                    "activo": True
                }
            ))

        batch_size = 100
        total_puntos = len(points)
        for i in range(0, total_puntos, batch_size):
            batch = points[i:i + batch_size]
            self.client.upsert(
                collection_name=self.pose_collection_name,
                points=batch
            )
        logger.info(f"Guardados {total_puntos} vectores en Qdrant para patrón {patron_id} (técnica {tecnica_id}).")
        return total_puntos

    def _get_patron_activo_db(self, tecnica_id: UUID) -> Optional[UUID]:
        try:
            from corpocmente.infrastructure.persistence.postgrest_client import PostgrestClient
            db = PostgrestClient()
            res = db.rpc("get_patron_activo", {"p_tecnica_id": str(tecnica_id)})
            if res:
                if isinstance(res, list) and len(res) > 0:
                    val = res[0]
                    if isinstance(val, dict):
                        val = val.get("patron_activo_id")
                elif isinstance(res, dict):
                    val = res.get("patron_activo_id")
                else:
                    val = res
                if val:
                    return UUID(str(val))
        except Exception as e:
            logger.debug(f"Error consultando get_patron_activo via PostgREST: {e}")

        # Fallback a psycopg2
        try:
            import psycopg2
            from corpocmente.config import settings
            db_url = getattr(settings, "DATABASE_URL", "postgres://postgres:postgres@localhost:5432/corpocmente")
            conn = psycopg2.connect(db_url)
            cur = conn.cursor()
            cur.execute("SELECT patron_activo_id FROM tecnicas WHERE id = %s", (str(tecnica_id),))
            row = cur.fetchone()
            cur.close()
            conn.close()
            if row and row[0]:
                return UUID(str(row[0]))
        except Exception as e_sql:
            logger.error(f"Error en fallback SQL get_patron_activo: {e_sql}")
        return None

    def obtener_secuencia_referencia(
        self,
        tecnica_id: UUID,
        patron_id: Optional[UUID] = None
    ) -> List[List[float]]:
        """
        Recupera de Qdrant la secuencia completa de vectores de referencia (133 dims),
        paginando con scroll, validando el esquema coco17_v1 y ordenando por frame_idx ascendente.
        Si patron_id es None, consulta PostgreSQL para obtener el patron_activo_id.
        """
        self.asegurar_coleccion(vector_size=133)
        if patron_id is None:
            patron_id = self._get_patron_activo_db(tecnica_id)
            if not patron_id:
                logger.warning(f"No hay patrón activo en PostgreSQL para técnica {tecnica_id}")
                return []

        filtro = Filter(must=[
            FieldCondition(key="tecnica_id", match=MatchValue(value=str(tecnica_id))),
            FieldCondition(key="patron_id", match=MatchValue(value=str(patron_id))),
        ])

        puntos_totales = []
        next_offset = None
        while True:
            records, next_offset = self.client.scroll(
                collection_name=self.pose_collection_name,
                scroll_filter=filtro,
                limit=100,
                offset=next_offset,
                with_vectors=True,
                with_payload=True,
            )
            puntos_totales.extend(records)
            if next_offset is None:
                break

        if not puntos_totales:
            return []

        puntos_validos = []
        for p in puntos_totales:
            payload = p.payload or {}
            schema = payload.get("keypoint_schema_version", "coco17_v1")
            if schema != "coco17_v1":
                logger.warning(f"Vector {p.id} tiene esquema incompatible: {schema}")
                continue
            frame_idx = payload.get("frame_idx", 0)
            raw_vec = payload.get("keypoints_raw")
            if raw_vec is not None and isinstance(raw_vec, list) and len(raw_vec) == 133:
                vec = raw_vec
            else:
                vec = p.vector
            puntos_validos.append((frame_idx, vec))

        puntos_validos.sort(key=lambda x: x[0])
        return [vec for _, vec in puntos_validos]

    def eliminar_patron(self, patron_id: UUID) -> int:
        """
        Elimina de Qdrant todos los puntos asociados a un patron_id específico.
        """
        filtro = Filter(must=[
            FieldCondition(key="patron_id", match=MatchValue(value=str(patron_id)))
        ])
        try:
            self.client.delete(
                collection_name=self.pose_collection_name,
                points_selector=filtro
            )
            logger.info(f"Patrón {patron_id} eliminado de Qdrant.")
            return 1
        except Exception as e:
            logger.warning(f"Error al eliminar patrón {patron_id} de Qdrant: {e}")
            return 0


    def buscar_similitud_pose(self, vector_alumno: List[float], tecnica_id: UUID) -> VectorSearchResultDTO:
        """
        Busca el fotograma de referencia más similar en Qdrant filtrando por la técnica.
        Retorna el score de similitud, la ruta de la imagen patrón y sus discrepancias técnicas.
        """
        filtro_tecnica = Filter(
            must=[
                FieldCondition(
                    key="tecnica_id",
                    match=MatchValue(value=str(tecnica_id))
                )
            ]
        )

        resultados = self.client.search(
            collection_name=self.pose_collection_name,
            query_vector=vector_alumno,
            query_filter=filtro_tecnica,
            limit=1
        )

        if not resultados:
            raise ValueError(f"No se encontraron vectores de referencia para la técnica ID {tecnica_id}")

        mejor_coincidencia = resultados[0]
        payload = mejor_coincidencia.payload or {}

        # Mapeo a DTO desacoplado
        return VectorSearchResultDTO(
            score=round(float(mejor_coincidencia.score) * 100, 2),  # Porcentaje de similitud
            frame_path=payload.get("frame_path", ""),
            discrepancias=payload.get("discrepancias", [])
        )

    def buscar_maxima_diferencia(
        self,
        esqueletos_alumno: List['EsqueletoBiomecanico'],
        tecnica_id: UUID
    ) -> VectorSearchResultDTO:
        """
        Descarga UNA VEZ todos los vectores de referencia de la técnica desde Qdrant
        y compara cada frame del alumno contra ellos mediante similitud coseno local
        con numpy. Para cada frame del alumno identifica su mejor coincidencia en la
        secuencia del profesor y determina el fotograma crítico con MENOR similitud
        (mayor error de ejecución), extrayendo las articulaciones divergentes.
        """
        if not esqueletos_alumno:
            raise ValueError("La lista de esqueletos del alumno está vacía.")

        # 1. Descargar TODAS las referencias con scroll (no search)
        filtro = Filter(must=[
            FieldCondition(key="tecnica_id", match=MatchValue(value=str(tecnica_id)))
        ])
        referencias, _ = self.client.scroll(
            collection_name=self.pose_collection_name,
            scroll_filter=filtro,
            limit=10000,
            with_vectors=True,
            with_payload=True,
        )
        if not referencias:
            raise ValueError(
                f"No hay vectores de referencia en Qdrant para la técnica {tecnica_id}. "
                f"Ejecutar scripts/ingest_reference_video.py primero."
            )

        ref_vectors = np.array([p.vector for p in referencias], dtype=np.float32)
        ref_norms = np.linalg.norm(ref_vectors, axis=1, keepdims=True) + 1e-9
        ref_normed = ref_vectors / ref_norms

        # 2. Iterar frames del alumno localmente
        peor_similitud = 1.0
        peor_payload = None
        peor_frame_alumno = 0
        peor_ref_idx = 0

        for idx, esqueleto in enumerate(esqueletos_alumno):
            vec = np.array(esqueleto.to_vector_array(), dtype=np.float32)
            vec_n = vec / (np.linalg.norm(vec) + 1e-9)
            sims = ref_normed @ vec_n                 # coseno contra todas las refs
            j = int(np.argmax(sims))
            sim_frame = float(sims[j])
            if sim_frame < peor_similitud or idx == 0:
                peor_similitud = sim_frame
                peor_frame_alumno = idx
                peor_ref_idx = j
                peor_payload = referencias[j].payload or {}

        logger.info(
            f"Peor frame alumno: #{peor_frame_alumno} (similitud coseno = {peor_similitud:.4f}) vs ref #{peor_ref_idx}"
        )

        # 3. Análisis articular detallado en el fotograma crítico
        articulaciones_criticas = []
        payload_discrepancias = list(peor_payload.get("discrepancias", []))
        kp_alumno = esqueletos_alumno[peor_frame_alumno].to_vector_array()

        ref_pt = referencias[peor_ref_idx]
        kp_ref = ref_pt.vector if hasattr(ref_pt, "vector") and isinstance(ref_pt.vector, list) else ref_vectors[peor_ref_idx].tolist()

        if len(kp_alumno) >= 51 and len(kp_ref) >= 51:
            distancias = []
            for art_i in range(17):
                xs, ys = kp_alumno[art_i * 3], kp_alumno[art_i * 3 + 1]
                xr, yr = kp_ref[art_i * 3], kp_ref[art_i * 3 + 1]
                dist = float(np.sqrt((xs - xr) ** 2 + (ys - yr) ** 2))
                peso = 1.0 if art_i >= 5 else 0.4
                distancias.append((dist * peso, art_i))

            distancias.sort(key=lambda x: x[0], reverse=True)
            articulaciones_criticas = [d[1] for d in distancias[:2]]

        if payload_discrepancias:
            discrepancias_detectadas = payload_discrepancias
        else:
            discrepancias_detectadas = [
                f"Desviación biomecánica en {COCO_JOINT_NAMES[art_idx] if art_idx < len(COCO_JOINT_NAMES) else f'Articulación #{art_idx}'}: posición divergente del patrón del profesor."
                for art_idx in articulaciones_criticas
            ]

        return VectorSearchResultDTO(
            score=round(peor_similitud * 100, 2),      # escala 0–100
            frame_path=peor_payload.get("frame_path", ""),
            discrepancias=discrepancias_detectadas,
            frame_alumno_idx=peor_frame_alumno,
            frame_referencia_idx=peor_ref_idx,
            articulaciones_criticas=articulaciones_criticas,
            keypoints_alumno=kp_alumno,
            keypoints_referencia=kp_ref,
        )

    def asegurar_poses_referencia(
        self,
        tecnica_id: UUID,
        video_referencia_path: str,
        yolo_adapter,
        tecnica_nombre: str = "",
        every_n: int = 5
    ) -> int:
        """
        Verifica si la técnica ya cuenta con vectores de referencia en Qdrant.
        Si no existen y el archivo de video existe localmente, extrae los keypoints con YOLO,
        extrae los frames JPG de muestra y los indexa automáticamente en Qdrant.
        """
        if not video_referencia_path or not os.path.exists(video_referencia_path):
            return 0

        self.asegurar_coleccion(vector_size=133)

        filtro = Filter(must=[
            FieldCondition(key="tecnica_id", match=MatchValue(value=str(tecnica_id)))
        ])
        existentes, _ = self.client.scroll(
            collection_name=self.pose_collection_name,
            scroll_filter=filtro,
            limit=1,
            with_vectors=False,
            with_payload=False
        )
        if existentes:
            logger.info(f"Vectores de referencia para técnica {tecnica_id} ya indexados.")
            return len(existentes)

        logger.info(f"Auto-ingestando video de referencia del profesor: {video_referencia_path}")

        import cv2
        import uuid
        ref_frames_dir = f"/tmp/corpocmente_reference_frames/{tecnica_id}"
        os.makedirs(ref_frames_dir, exist_ok=True)

        frame_map = {}
        cap = cv2.VideoCapture(video_referencia_path)
        if cap.isOpened():
            idx = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                if idx % every_n == 0:
                    jpg_path = os.path.join(ref_frames_dir, f"ref_{idx:05d}.jpg")
                    cv2.imwrite(jpg_path, frame)
                    frame_map[idx] = jpg_path
                idx += 1
            cap.release()

        esqueletos = yolo_adapter.extraer_keypoints(video_referencia_path)
        if not esqueletos:
            logger.warning("YOLO no detectó poses en el video de referencia.")
            return 0

        points = []
        for esk in esqueletos:
            kp = esk.to_vector_array() if hasattr(esk, "to_vector_array") else esk.keypoints133
            if len(kp) != 133:
                continue

            frame_idx = getattr(esk, "frame_idx", 0)
            frame_path = frame_map.get(frame_idx, "")

            points.append(PointStruct(
                id=str(uuid.uuid4()),
                vector=kp,
                payload={
                    "tecnica_id": str(tecnica_id),
                    "tecnica_nombre": tecnica_nombre,
                    "frame_idx": frame_idx,
                    "frame_path": frame_path,
                    "discrepancias": [],
                }
            ))

        if points:
            self.client.upsert(collection_name=self.pose_collection_name, points=points)
            logger.info(f"Auto-ingesta completada: {len(points)} poses indexadas para técnica {tecnica_id}.")
            return len(points)

        return 0

    def recuperar_contexto_rag(self, vector_multimodal: List[float], tecnica_id: UUID) -> str:
        """
        Busca en la colección RAG (vectores de 2048 dims generados por Qwen) la teoría
        de libros o manuales más relevante para la query textual del análisis.

        Retorna los top-3 chunks concatenados con separador '---' para dar contexto
        enriquecido al VLM. Retorna cadena vacía si no hay resultados o si falla.
        """
        if len(vector_multimodal) != RAG_VECTOR_DIM:
            raise ValueError(f"Embedding RAG inválido: se esperaban {RAG_VECTOR_DIM} dimensiones.")
        try:
            filtro = Filter(should=[
                Filter(must=[FieldCondition(key="tecnica_id", match=MatchValue(value=str(tecnica_id)))]),
                Filter(must=[FieldCondition(key="alcance", match=MatchValue(value="global"))]),
            ])
            hits = self.client.search(
                collection_name=self.rag_collection_name,
                query_vector=("dense", vector_multimodal),
                query_filter=filtro,
                limit=3,
                with_payload=True,
            )
            chunks = []
            for hit in hits:
                payload = hit.payload or {}
                txt = self._formatear_evidencia_rag(payload)
                if txt:
                    chunks.append(txt)
            return "\n\n---\n\n".join(chunks)
        except Exception as e:
            logger.warning("No se pudo recuperar contexto RAG: %s", e)
            return ""

    @staticmethod
    def _formatear_evidencia_rag(evidencia: Dict) -> str:
        payload = evidencia.get("payload", evidencia)
        fuente = [
            valor for valor in (
                payload.get("fuente_nombre") or payload.get("fuente_tipo"),
                payload.get("fuente_referencia"),
                f"página {payload['pagina']}" if payload.get("pagina") else None,
                (
                    f"minuto {int(float(payload['timestamp_seconds']) // 60)}:"
                    f"{int(float(payload['timestamp_seconds']) % 60):02d}"
                ) if payload.get("timestamp_seconds") is not None else None,
            ) if valor
        ]
        atribucion = f"Fuente: {' — '.join(fuente)}\n" if fuente else ""
        texto_asociado = payload.get("texto_asociado")
        contenido = payload.get("contenido_texto") or ""
        if texto_asociado:
            contenido = f"{contenido}\n{texto_asociado}"
        return f"{atribucion}{contenido}".strip()

    def recuperar_evidencias_rag(
        self,
        vectores_consulta: List[List[float]],
        tecnica_id: Optional[UUID] = None,
        limit: int = 5,
        video_referencia_path: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Alias compatible para recuperar_evidencias_rag_multimodal."""
        return self.recuperar_evidencias_rag_multimodal(
            vectores_consulta=vectores_consulta,
            tecnica_id=tecnica_id,
            limit=limit,
            video_referencia_path=video_referencia_path,
        )

    def recuperar_evidencias_rag_multimodal(
        self,
        vectores_consulta: List[List[float]],
        tecnica_id: Optional[UUID] = None,
        limit: int = 5,
        video_referencia_path: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Busca evidencias RAG usando uno o varios vectores de consulta.

        Puede recibir:
        - vector de imagen del frame crítico del alumno
        - vector textual de técnica + discrepancias

        Devuelve resultados priorizando payloads con media_path.
        """
        if not vectores_consulta:
            return self.obtener_mensaje_profesor_rag(tecnica_id)[:limit] if tecnica_id else []
        for index, vector in enumerate(vectores_consulta):
            if len(vector) != RAG_VECTOR_DIM:
                raise ValueError(
                    f"Embedding de consulta RAG {index} inválido: se esperaban {RAG_VECTOR_DIM} dimensiones."
                )

        should_conditions = []

        if tecnica_id is not None:
            should_conditions.append(
                Filter(
                    must=[
                        FieldCondition(
                            key="tecnica_id",
                            match=MatchValue(value=str(tecnica_id)),
                        )
                    ]
                )
            )

        should_conditions.append(
            Filter(
                must=[
                    FieldCondition(
                        key="alcance",
                        match=MatchValue(value="global"),
                    )
                ]
            )
        )

        query_filter = Filter(should=should_conditions)
        col_name = self.rag_collection_name

        resultados_unicos: Dict[str, Any] = {}

        for vector in vectores_consulta:
            hits = self.client.search(
                collection_name=col_name,
                query_vector=("dense", vector),
                query_filter=query_filter,
                limit=limit,
                with_payload=True,
            )

            for hit in hits:
                key = str(hit.id)
                actual = resultados_unicos.get(key)
                if actual is None or hit.score > actual.score:
                    resultados_unicos[key] = hit

        ordenados = sorted(
            resultados_unicos.values(),
            key=lambda x: x.score,
            reverse=True,
        )

        def payload_de(hit):
            return hit.payload or {}

        def es_visual(hit):
            return bool(payload_de(hit).get("media_path"))

        visuales = [h for h in ordenados if es_visual(h)]
        no_visuales = [h for h in ordenados if not es_visual(h)]

        if video_referencia_path:
            visuales.sort(
                key=lambda h: (
                    0 if payload_de(h).get("video_path") == video_referencia_path else 1,
                    -h.score,
                )
            )

        seleccionados = (visuales + no_visuales)[:limit]

        evidencias = []

        for hit in seleccionados:
            payload = payload_de(hit)

            evidencias.append(
                {
                    "id": str(hit.id),
                    "score": float(hit.score),
                    "contenido_texto": payload.get("contenido_texto", ""),
                    "texto_asociado": payload.get("texto_asociado", ""),
                    "modalidad": payload.get("modalidad", "texto"),
                    "media_path": payload.get("media_path"),
                    "media_url": payload.get("media_url"),
                    "video_path": payload.get("video_path"),
                    "timestamp_seconds": payload.get("timestamp_seconds"),
                    "frame_idx": payload.get("frame_idx"),
                    "tecnica_id": payload.get("tecnica_id"),
                    "alcance": payload.get("alcance"),
                    "fuente_tipo": payload.get("fuente_tipo"),
                    "fuente_nombre": payload.get("fuente_nombre"),
                    "fuente_referencia": payload.get("fuente_referencia"),
                    "fuente_url": payload.get("fuente_url"),
                    "pagina": payload.get("pagina"),
                }
            )

        # El mensaje vigente del instructor es contexto obligatorio de la evaluación,
        # incluso si su similitud densa no quedó entre los top-k.
        if tecnica_id is not None:
            mensaje = self.obtener_mensaje_profesor_rag(tecnica_id)
            if mensaje and not any(e["id"] == mensaje[0]["id"] for e in evidencias):
                evidencias = ([mensaje[0]] + evidencias)[:limit]
        return evidencias

    def obtener_mensaje_profesor_rag(self, tecnica_id: Optional[UUID]) -> List[Dict[str, Any]]:
        """Obtiene la instrucción exacta del profesor, sin búsqueda semántica."""
        if tecnica_id is None:
            return []
        try:
            filtro = Filter(must=[
                FieldCondition(key="tecnica_id", match=MatchValue(value=str(tecnica_id))),
                FieldCondition(key="fuente_tipo", match=MatchValue(value="instructor_message")),
            ])
            puntos, _ = self.client.scroll(
                collection_name=self.rag_collection_name,
                scroll_filter=filtro,
                limit=1,
                with_payload=True,
                with_vectors=False,
            )
            if not puntos:
                return []
            punto = puntos[0]
            payload = punto.payload or {}
            return [{
                "id": str(punto.id), "score": 1.0,
                "contenido_texto": payload.get("contenido_texto", ""),
                "texto_asociado": payload.get("texto_asociado", ""),
                "modalidad": payload.get("modalidad", "texto"),
                "media_path": None, "media_url": None,
                "tecnica_id": payload.get("tecnica_id"), "alcance": payload.get("alcance"),
                "fuente_tipo": "instructor_message", "fuente_nombre": payload.get("fuente_nombre"),
                "fuente_referencia": payload.get("fuente_referencia"), "fuente_url": payload.get("fuente_url"),
                "pagina": None,
            }]
        except Exception as exc:
            logger.warning("No se pudo recuperar mensaje del profesor: %s", exc)
            return []
