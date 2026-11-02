#!/usr/bin/env python3
"""Indexa los tres manuales como evidencia texto+imagen por página en rag_knowledge.

Uso (desde backend):
    python scripts/ingest_multimodal_manuals.py --reset
"""
import argparse
import io
import logging
import sys
from pathlib import Path
from urllib.parse import quote

import fitz

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))

from corpocmente.config import settings  # noqa: E402
from corpocmente.infrastructure.ai.qwen_adapter import QwenEmbeddingAdapter  # noqa: E402
from corpocmente.infrastructure.persistence.qdrant_rag_adapter import QdrantRAGAdapter  # noqa: E402

MANUALES = (
    ROOT / "Jiu-Jitsu University.pdf",
    ROOT / "manual-fundamental-arataba-de-jiu-jitsu.pdf",
    ROOT / "BJJ-GuiaCompleto.pdf",
)
PAGES_ROOT = BACKEND / "storage" / "manuales" / "paginas"


def slug_pdf(pdf: Path) -> str:
    return pdf.stem.replace(" ", "-")


def indexar_manual(
    pdf: Path,
    qwen: QwenEmbeddingAdapter,
    rag: QdrantRAGAdapter,
    max_pages: int | None,
    start_page: int = 1,
    batch_size: int = 8,
) -> tuple[int, int]:
    if not pdf.is_file():
        raise FileNotFoundError(pdf)
    doc = fitz.open(pdf)
    output_dir = PAGES_ROOT / slug_pdf(pdf)
    output_dir.mkdir(parents=True, exist_ok=True)
    last_page = min(len(doc), max_pages) if max_pages else len(doc)
    if start_page < 1 or start_page > last_page + 1:
        raise ValueError(f"Página inicial inválida {start_page} para {pdf.name} (1..{last_page + 1}).")
    total = max(0, last_page - start_page + 1)
    print(f"INDEX_START pdf={pdf.name} pages={total} start_page={start_page} output={output_dir}", flush=True)

    for b_start in range(start_page, last_page + 1, batch_size):
        b_end = min(b_start + batch_size, last_page + 1)
        batch_chunks = []
        batch_items = []
        batch_meta = []
        for page_number in range(b_start, b_end):
            page = doc.load_page(page_number - 1)
            texto = page.get_text("text").strip()
            chunk = f"===== Page {page_number} =====\n{texto}"
            image_path = output_dir / f"pagina_{page_number}.jpg"
            pix = page.get_pixmap(dpi=150, alpha=False)
            pix.save(str(image_path))
            media_url = "/api/v1/conocimiento/media/paginas/" + quote(
                f"{slug_pdf(pdf)}/{image_path.name}", safe="/"
            )
            prompt = (
                f"Manual {pdf.name}, página {page_number}. "
                f"Texto de la página: {texto[:6000]}"
            )
            batch_chunks.append(chunk)
            batch_items.append({"image": str(image_path), "text": prompt})
            batch_meta.append({
                "modalidad": "multimodal",
                "media_path": str(image_path),
                "media_url": media_url,
                "pagina": page_number,
                "fuente_referencia": f"p. {page_number}",
            })

        if hasattr(qwen, "generar_embeddings_multimodal_lote"):
            embeddings = qwen.generar_embeddings_multimodal_lote(batch_items, batch_size=batch_size)
        else:
            embeddings = [qwen.generar_embedding(it["image"], prompt=it["text"]) for it in batch_items]

        rag.ingestar_desde_respuesta(
            {"chunks": batch_chunks, "embeddings": embeddings},
            tecnica_id=None,
            fuente_tipo="manual_pdf",
            fuente_nombre=pdf.name,
            fuente_referencia=batch_meta[0]["fuente_referencia"],
            alcance="global",
            metadata_por_chunk=batch_meta,
        )
        for page_number, item in zip(range(b_start, b_end), batch_items):
            print(
                f"INDEX_PAGE pdf={pdf.name} page={page_number}/{last_page} image={item['image']}",
                flush=True,
            )

    doc.close()
    return total, total


def sincronizar_mensajes_profesor_db() -> int:
    """Sincroniza los mensajes de profesor vigentes en la base de datos con Qdrant."""
    from corpocmente.infrastructure.persistence.postgrest_client import PostgrestClient
    from corpocmente.application.services.instructor_message_ingestion import sincronizar_mensaje_profesor
    db = PostgrestClient()
    try:
        tecnicas = db.rpc("get_tecnicas_with_videos", {})
    except Exception as exc:
        print(f"No se pudieron consultar técnicas en PostgREST: {exc}", flush=True)
        return 0
    total = 0
    for t in tecnicas:
        tid = t.get("id")
        msg = t.get("mensaje_profesor")
        if tid and msg and msg.strip():
            count = sincronizar_mensaje_profesor(str(tid), msg)
            total += count
            print(f"INDEX_INSTRUCTOR_MESSAGE tecnica_id={tid} nombre='{t.get('nombre')}' chars={len(msg.strip())}", flush=True)
    return total


def preflight_multimodal(qwen: QwenEmbeddingAdapter) -> None:
    """Comprueba el embedding real antes de borrar la colección existente."""
    from PIL import Image
    primer_manual = MANUALES[0]
    if not primer_manual.is_file():
        raise FileNotFoundError(primer_manual)
    doc = fitz.open(primer_manual)
    pix = doc.load_page(0).get_pixmap(dpi=72, alpha=False)
    doc.close()
    image = Image.open(io.BytesIO(pix.tobytes("jpeg")))
    vector = qwen.generar_embedding(image, prompt="Preflight multimodal del manual.")
    print(f"QWEN_PREFLIGHT dimensions={len(vector)} status=ok", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="Borra rag_knowledge antes de indexar.")
    parser.add_argument("--max-pages", type=int, default=None, help="Límite de páginas por PDF, solo diagnóstico.")
    parser.add_argument("--resume-page", type=int, default=1, help="Reanuda Jiu-Jitsu University desde esta página (no borra Qdrant).")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
    qwen = QwenEmbeddingAdapter(
        use_local=settings.USE_LOCAL_QWEN,
        colab_url=settings.COLAB_TUNNEL_URL,
    )
    preflight_multimodal(qwen)
    rag = QdrantRAGAdapter()
    if args.reset:
        print(f"QDRANT_DELETE collection={rag.collection_name}", flush=True)
        rag.client.delete_collection(rag.collection_name)
        rag._asegurar_coleccion()
        print(f"QDRANT_READY collection={rag.collection_name}", flush=True)
    pages = images = 0
    for index, pdf in enumerate(MANUALES):
        indexed_pages, indexed_images = indexar_manual(
            pdf, qwen, rag, args.max_pages,
            start_page=args.resume_page if index == 0 else 1,
        )
        pages += indexed_pages
        images += indexed_images
    print(f"INDEX_COMPLETE pages={pages} images={images} collection={settings.QDRANT_RAG_COLLECTION}", flush=True)
    instructor_messages = sincronizar_mensajes_profesor_db()
    print(f"INDEX_INSTRUCTOR_COMPLETE count={instructor_messages}", flush=True)


if __name__ == "__main__":
    main()
