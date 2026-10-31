import json, glob
from pathlib import Path
from collections import Counter

BASE = Path("storage/datasets/vicos")
if not BASE.exists():
    BASE = Path(__file__).resolve().parents[1] / "storage" / "datasets" / "vicos"

entries = []
for f in glob.glob(str(BASE / "**/*.json"), recursive=True):
    for e in json.load(open(f)):
        p1, p2 = e.get("pose1"), e.get("pose2")
        if p1 and p2 and len(p1) == 17 and len(p2) == 17:
            entries.append(e)

imgs = [e["image"] for e in entries]
frames = [e["frame"] for e in entries]

print(f"Entradas con ambos atletas: {len(entries)}")
print(f"Imágenes únicas: {len(set(imgs))}")
print(f"Frames únicos: {len(set(frames))}")
print(f"Entradas por imagen (top 5): {Counter(imgs).most_common(5)}")
print(f"Entradas por frame (top 5):  {Counter(frames).most_common(5)}")

# Chequeo de continuidad: ¿image es un contador secuencial?
imgs_int = sorted(int(i) for i in set(imgs))
diffs = [b - a for a, b in zip(imgs_int, imgs_int[1:])]
print(f"Rango image: {imgs_int[0]} -> {imgs_int[-1]}")
print(f"Pasos entre images consecutivas (top 5): {Counter(diffs).most_common(5)}")
print(f"¿Hay huecos en la secuencia de image?: {max(diffs) > 1}")

