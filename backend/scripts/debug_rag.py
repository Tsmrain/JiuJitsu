#!/usr/bin/env python3
"""
Diagnóstico empírico del RAG (FASE 1):
1. Consulta Qdrant directamente con el vector de "llave de brazo como se hace"
   y con el vector cognitivo/expandido usado por /conocimiento/biblioteca/buscar.
2. Imprime los top-3 chunks reales devueltos por Qdrant.
3. Muestra el prompt exacto que LocalVLMAdapter.generar_respuesta_rag_chat envía a Qwen3-VL.
"""

import inspect
import os
import sys
from pathlib import Path

ROOT_BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_BACKEND))
os.environ.setdefault("USE_LOCAL_QWEN", "true")

from dotenv import load_dotenv

load_dotenv(ROOT_BACKEND / ".env")

from corpocmente.domain.glossary.glossary_service import expandir_query_con_glosario
from corpocmente.infrastructure.ai.local_vlm_adapter import LocalVLMAdapter
from corpocmente.infrastructure.ai.qwen_adapter import QwenEmbeddingAdapter
from corpocmente.infrastructure.persistence.qdrant_rag_adapter import QdrantRAGAdapter


def main() -> None:
    query = "llave de brazo como se hace"
    qwen = QwenEmbeddingAdapter()
    rag = QdrantRAGAdapter()
    vlm = LocalVLMAdapter()

    print("=== 1. VECTOR DIRECTO DE LA QUERY ===")
    vec_direct = qwen.generar_embedding_texto(query)
    hits_direct = rag.buscar_biblioteca(vec_direct, limit=5)
    for idx, item in enumerate(hits_direct[:3], start=1):
        print(f"\n[Directo #{idx}] id={item.get('id')} score={item.get('score'):.4f}")
        print(f"  fuente_nombre={item.get('fuente_nombre')!r} pagina={item.get('pagina')!r} cita={item.get('cita')!r}")
        print(f"  media_url={item.get('media_url')!r}")
        print(f"  fuente_url={item.get('fuente_url')!r}")
        print(f"  contenido_texto:\n{item.get('contenido_texto', '')}")

    print("\n=== 2. PIPELINE COGNITIVO + GLOSARIO (COMO EN /biblioteca/buscar) ===")
    query_cog = vlm.reescribir_query_cognitiva(query)
    query_exp = expandir_query_con_glosario(query_cog or query)
    print(f"query_original : {query!r}")
    print(f"query_cognitiva: {query_cog!r}")
    print(f"query_expandida: {query_exp!r}")

    vec_pipe = qwen.generar_embedding_texto(query_exp or query_cog or query)
    hits_pipe = rag.buscar_biblioteca(vec_pipe, limit=5)
    for idx, item in enumerate(hits_pipe[:3], start=1):
        print(f"\n[Pipeline #{idx}] id={item.get('id')} score={item.get('score'):.4f}")
        print(f"  fuente_nombre={item.get('fuente_nombre')!r} pagina={item.get('pagina')!r} cita={item.get('cita')!r}")
        print(f"  media_url={item.get('media_url')!r}")
        print(f"  fuente_url={item.get('fuente_url')!r}")
        print(f"  contenido_texto:\n{item.get('contenido_texto', '')}")

    print("\n=== 3. CÓDIGO ACTUAL DE generar_respuesta_rag_chat (PROMPT A QWEN3-VL) ===")
    print(inspect.getsource(LocalVLMAdapter.generar_respuesta_rag_chat))


if __name__ == "__main__":
    main()
