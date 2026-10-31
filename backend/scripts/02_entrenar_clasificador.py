import json, glob, pickle, sys, re
import numpy as np
from pathlib import Path
from collections import Counter
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, accuracy_score, f1_score
from sklearn.utils.class_weight import compute_sample_weight

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from corpocmente.domain.biomechanics.pose_normalizer import normalizar

BASE = Path("storage/datasets/vicos")
if not BASE.exists():
    BASE = Path(__file__).resolve().parents[1] / "storage" / "datasets" / "vicos"
OUT = BASE.parent.parent / "models"
OUT.mkdir(parents=True, exist_ok=True)

def kpts_to_flat(pose):
    flat = []
    for kp in pose[:17]:
        flat.extend([float(kp[0]), float(kp[1]), float(kp[2]) if len(kp) > 2 else 1.0])
    return flat

def pose_features(pose):
    return np.array(normalizar(kpts_to_flat(pose))["vector"], dtype=np.float32)

def agrupar_clase(label):
    """mount1, mount2, mount3 -> mount. standing -> standing."""
    return re.sub(r"[0-9]+$", "", label)

X, y = [], []
skipped_single, skipped_err = 0, 0

for f in glob.glob(str(BASE / "**/*.json"), recursive=True):
    for e in json.load(open(f)):
        p1 = e.get("pose1")
        p2 = e.get("pose2")
        if not (p1 and p2 and len(p1) == 17 and len(p2) == 17):
            skipped_single += 1
            continue
        try:
            feat = np.concatenate([pose_features(p1), pose_features(p2)])  # 92 dims
            X.append(feat)
            y.append(agrupar_clase(e["position"]))
        except Exception as exc:
            skipped_err += 1

X = np.array(X, dtype=np.float32)
le = LabelEncoder()
y_enc = le.fit_transform(y)

print(f"Entradas usadas: {len(X)}")
print(f"Saltadas (1 atleta): {skipped_single}")
print(f"Saltadas (error): {skipped_err}")
print(f"Features: {X.shape}")
print(f"Clases ({len(le.classes_)}): {dict(Counter(y))}")

X_tr, X_te, y_tr, y_te = train_test_split(
    X, y_enc, test_size=0.2, stratify=y_enc, random_state=42
)

weights = compute_sample_weight(class_weight="balanced", y=y_tr)

clf = MLPClassifier(
    hidden_layer_sizes=(256, 128, 64),
    max_iter=300,
    early_stopping=True,
    n_iter_no_change=15,
    random_state=42,
    verbose=False,
)
clf.fit(X_tr, y_tr, sample_weight=weights)

y_pred = clf.predict(X_te)
acc = accuracy_score(y_te, y_pred)
f1m = f1_score(y_te, y_pred, average="macro")

print(f"\nAccuracy test: {acc:.4f}")
print(f"F1 macro:     {f1m:.4f}")

if acc < 0.85 or f1m < 0.80:
    print("\n=== CLASSIFICATION REPORT (para diagnóstico) ===")
    print(classification_report(y_te, y_pred, target_names=le.classes_, zero_division=0))
    print(f"\nFALLO: no cumple criterio (acc>=0.85, f1>=0.80). NO continuar.")
    sys.exit(1)

print("\n=== CLASSIFICATION REPORT ===")
print(classification_report(y_te, y_pred, target_names=le.classes_, zero_division=0))

with open(OUT / "position_classifier.pkl", "wb") as fp:
    pickle.dump({
        "model": clf,
        "labels": le.classes_.tolist(),
        "features_dim": int(X.shape[1]),
        "accuracy_test": float(acc),
        "f1_macro_test": float(f1m),
    }, fp)

print(f"\nModelo guardado en {OUT / 'position_classifier.pkl'}")

