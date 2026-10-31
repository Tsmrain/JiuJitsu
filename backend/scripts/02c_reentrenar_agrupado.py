import json, glob, pickle, sys, re
import numpy as np
from pathlib import Path
from collections import Counter
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import GroupShuffleSplit
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, accuracy_score, f1_score
from sklearn.utils.class_weight import compute_sample_weight

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from corpocmente.domain.biomechanics.pose_normalizer import normalizar

BASE = Path("storage/datasets/vicos")
if not BASE.exists():
    BASE = Path(__file__).resolve().parents[1] / "storage" / "datasets" / "vicos"
OUT = Path("storage/models")
if not OUT.exists():
    OUT = Path(__file__).resolve().parents[1] / "storage" / "models"
OUT.mkdir(parents=True, exist_ok=True)

def kpts_to_flat(pose):
    flat = []
    for kp in pose[:17]:
        flat.extend([float(kp[0]), float(kp[1]), float(kp[2]) if len(kp) > 2 else 1.0])
    return flat

def pose_features(pose):
    return np.array(normalizar(kpts_to_flat(pose))["vector"], dtype=np.float32)

def agrupar_clase(label):
    return re.sub(r"[0-9]+$", "", label)

# Bloques temporales: agrupa cada 30 imágenes consecutivas en un mismo grupo.
BLOQUE = 30

X, y, grupos = [], [], []
for f in glob.glob(str(BASE / "**/*.json"), recursive=True):
    for e in json.load(open(f)):
        p1, p2 = e.get("pose1"), e.get("pose2")
        if not (p1 and p2 and len(p1) == 17 and len(p2) == 17):
            continue
        X.append(np.concatenate([pose_features(p1), pose_features(p2)]))
        y.append(agrupar_clase(e["position"]))
        grupos.append(int(e["image"]) // BLOQUE)

X = np.array(X, dtype=np.float32)
le = LabelEncoder()
y_enc = le.fit_transform(y)
grupos = np.array(grupos)

gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
train_idx, test_idx = next(gss.split(X, y_enc, groups=grupos))

X_tr, y_tr = X[train_idx], y_enc[train_idx]
X_te, y_te = X[test_idx], y_enc[test_idx]

print(f"Train: {len(X_tr)} | Test: {len(X_te)} | Grupos en train: {len(set(grupos[train_idx]))} | en test: {len(set(grupos[test_idx]))}")

weights = compute_sample_weight(class_weight="balanced", y=y_tr)
clf = MLPClassifier(hidden_layer_sizes=(256, 128, 64), max_iter=300,
                    early_stopping=True, n_iter_no_change=15, random_state=42)
clf.fit(X_tr, y_tr, sample_weight=weights)

y_pred = clf.predict(X_te)
acc = accuracy_score(y_te, y_pred)
f1m = f1_score(y_te, y_pred, average="macro")
print(f"\nAccuracy test (agrupado por bloques de {BLOQUE}): {acc:.4f}")
print(f"F1 macro:                                       {f1m:.4f}")

print("\n=== CLASSIFICATION REPORT ===")
print(classification_report(y_te, y_pred, target_names=le.classes_, zero_division=0))

with open(OUT / "position_classifier_grouped.pkl", "wb") as fp:
    pickle.dump({"model": clf, "labels": le.classes_.tolist(), "features_dim": int(X.shape[1]),
                 "accuracy_test": float(acc), "f1_macro_test": float(f1m),
                 "split": f"GroupShuffleSplit por bloques de {BLOQUE} imágenes"}, fp)
print(f"\nModelo agrupado guardado en {OUT / 'position_classifier_grouped.pkl'}")

