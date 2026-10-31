import json
from pathlib import Path
from collections import Counter

json_path = Path("storage/datasets/vicos/annotations.json")
if not json_path.exists():
    json_path = Path("backend/storage/datasets/vicos/annotations.json")

with open(json_path) as f:
    data = json.load(f)

print(f"Tipo: {type(data)}")
print(f"Total entradas: {len(data) if isinstance(data, list) else 'no es lista'}")

if isinstance(data, list):
    print(f"\nPrimera entrada (claves): {list(data[0].keys())}")
    print(f"\n¿Tiene pose1?: {'pose1' in data[0]}")
    print(f"¿Tiene pose2?: {'pose2' in data[0]}")
    
    # Contar cuántas tienen pose1 vs pose2 vs ambos
    con_pose1 = sum(1 for e in data if "pose1" in e)
    con_pose2 = sum(1 for e in data if "pose2" in e)
    con_ambos = sum(1 for e in data if "pose1" in e and "pose2" in e)
    print(f"\nEntradas con pose1: {con_pose1}")
    print(f"Entradas con pose2: {con_pose2}")
    print(f"Entradas con ambos: {con_ambos}")
    
    # Clases
    print(f"\nClases: {dict(Counter(e.get('position') for e in data))}")
    
    # Estructura del ejemplo
    print(f"\nEjemplo de pose2 (primeros 2): {data[0]['pose2'][:2] if 'pose2' in data[0] else 'N/A'}")
    print(f"Ejemplo de pose1 (primeros 2): {data[0]['pose1'][:2] if 'pose1' in data[0] else 'N/A'}")
