import os
import shutil
from pathlib import Path
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance

QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))

def clean_directory_contents(dir_path: str):
    p = Path(dir_path)
    if not p.exists():
        p.mkdir(parents=True, exist_ok=True)
        print(f"📁 Directorio creado: {dir_path}")
        return

    count = 0
    for item in p.iterdir():
        if item.is_dir():
            shutil.rmtree(item)
            count += 1
        else:
            item.unlink()
            count += 1
    print(f"🧹 Vaciado {dir_path} ({count} elementos eliminados).")

def reset_qdrant():
    print("=" * 60)
    print("1. RESET DE COLECCIONES EN QDRANT")
    print("=" * 60)
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    collections = [c.name for c in client.get_collections().collections]
    print(f"Colecciones actuales en Qdrant: {collections}")

    # Recrear rag_knowledge vacía
    if "rag_knowledge" in collections:
        print("Eliminando colección 'rag_knowledge'...")
        client.delete_collection("rag_knowledge")

    print("Creando colección 'rag_knowledge' vacía (dim=2048, Cosine, named vector 'dense')...")
    client.create_collection(
        collection_name="rag_knowledge",
        vectors_config={"dense": VectorParams(size=2048, distance=Distance.COSINE)}
    )
    rag_count = client.count("rag_knowledge").count
    print(f"✅ Colección 'rag_knowledge' recreada exitosamente. Total puntos: {rag_count}")
    assert rag_count == 0, f"Error: Se esperaban 0 puntos, hay {rag_count}"

    # Eliminar colecciones temporales o de test si existen
    for c in client.get_collections().collections:
        if c.name.startswith("test_") or "temp" in c.name:
            print(f"Eliminando colección temporal: {c.name}")
            client.delete_collection(c.name)

def reset_local_storage():
    print("\n" + "=" * 60)
    print("2. LIMPIEZA FÍSICA DE ALMACENAMIENTO LOCAL Y TEMPORALES")
    print("=" * 60)
    dirs_to_clean = [
        "backend/storage/manuales/paginas",
        "backend/storage/uncertainty_frames",
        "/tmp/corpocmente_frames",
        "/tmp/corpocmente_videos",
    ]
    for d in dirs_to_clean:
        clean_directory_contents(d)

if __name__ == "__main__":
    reset_qdrant()
    reset_local_storage()
    print("\n✅ FASE 3 COMPLETADA EXITOSAMENTE: Qdrant y Almacenamiento Local en estado limpio.")

