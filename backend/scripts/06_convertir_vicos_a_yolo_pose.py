import json
import cv2
import numpy as np
from pathlib import Path
from collections import defaultdict

ANNOTATIONS = Path("storage/datasets/vicos/annotations.json")
IMAGES_DIR = Path("storage/datasets/vicos_images")
OUTPUT_DIR = Path("storage/datasets/bjj_pose_yolo")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CONF_THRESHOLD = 0.3
MIN_VALID_KPTS = 4

def kpts_to_bbox(kpts):
    pts = np.array(kpts, dtype=np.float32)
    mask = (pts[:, 2] > CONF_THRESHOLD) & (pts[:, 0] > 0) & (pts[:, 1] > 0)
    if int(mask.sum()) < MIN_VALID_KPTS:
        return None
    valid = pts[mask, :2]
    return float(valid[:, 0].min()), float(valid[:, 1].min()), float(valid[:, 0].max()), float(valid[:, 1].max())

def write_yolo_label(poses, out_label_path, img_w, img_h):
    rows = []
    for pose in poses:
        bbox = kpts_to_bbox(pose)
        if bbox is None:
            continue
        x1, y1, x2, y2 = bbox
        bw, bh = x2 - x1, y2 - y1
        if bw < 5 or bh < 5:
            continue
        xc, yc = (x1 + x2) / 2 / img_w, (y1 + y2) / 2 / img_h
        bw_n, bh_n = bw / img_w, bh / img_h
        kp_flat = []
        for kp in pose:
            x, y, c = float(kp[0]), float(kp[1]), float(kp[2])
            vis = 2 if c > CONF_THRESHOLD else 0
            kp_flat.extend([x / img_w, y / img_h, vis])
        row = f"0 {xc:.6f} {yc:.6f} {bw_n:.6f} {bh_n:.6f} " + " ".join(f"{v:.6f}" for v in kp_flat)
        rows.append(row)
    if rows:
        out_label_path.write_text("\n".join(rows))
        return True
    return False

def main():
    data = json.load(open(ANNOTATIONS))
    by_image = defaultdict(list)
    for entry in data:
        img_name = entry["image"]
        poses = []
        if "pose1" in entry and len(entry["pose1"]) == 17:
            poses.append(entry["pose1"])
        if "pose2" in entry and len(entry["pose2"]) == 17:
            poses.append(entry["pose2"])
        if poses:
            by_image[img_name].extend(poses)

    all_images = sorted(by_image.keys())
    print(f"Imágenes con al menos una pose: {len(all_images)}")

    sequences = sorted(set(img[:2] for img in all_images))
    print(f"Secuencias detectadas (primeros 2 dígitos): {sequences}")

    if len(sequences) < 3:
        print("ADVERTENCIA: menos de 3 secuencias. El split por secuencia puede fallar.")
        print("Verificar estructura de nombres de imagen.")
        return

    n_val = max(1, int(len(sequences) * 0.2))
    val_seqs = set(sequences[-n_val:])
    train_seqs = set(sequences[:-n_val])
    print(f"Secuencias en train: {sorted(train_seqs)}")
    print(f"Secuencias en val:   {sorted(val_seqs)}")

    splits = {"train": [], "val": []}
    for img_name in all_images:
        seq = img_name[:2]
        splits["val" if seq in val_seqs else "train"].append(img_name)

    stats = {}
    for split_name, img_names in splits.items():
        split_dir = OUTPUT_DIR / split_name
        img_out = split_dir / "images"
        lbl_out = split_dir / "labels"
        img_out.mkdir(parents=True, exist_ok=True)
        lbl_out.mkdir(parents=True, exist_ok=True)

        count_img = 0
        count_lbl = 0
        for img_name in img_names:
            src = IMAGES_DIR / f"{img_name}.jpg"
            if not src.exists():
                continue
            img = cv2.imread(str(src))
            if img is None:
                continue
            h, w = img.shape[:2]

            dst_img = img_out / f"{img_name}.jpg"
            if not dst_img.exists():
                cv2.imwrite(str(dst_img), img)

            lbl_path = lbl_out / f"{img_name}.txt"
            if write_yolo_label(by_image[img_name], lbl_path, w, h):
                count_lbl += 1
            count_img += 1

        stats[split_name] = (count_img, count_lbl)
        print(f"  {split_name}: {count_img} imágenes, {count_lbl} labels válidas")

    yaml_content = f"""path: {OUTPUT_DIR.resolve()}
train: train/images
val: val/images

kpt_shape: [17, 3]
flip_idx: [0, 2, 1, 4, 3, 6, 5, 8, 7, 10, 9, 12, 11, 14, 13, 16, 15]

names:
  0: person
"""
    (OUTPUT_DIR / "data.yaml").write_text(yaml_content)
    print(f"\nDataset YOLO-pose listo en: {OUTPUT_DIR}")

    print("\n=== VERIFICACIÓN FINAL ===")
    train_imgs = len(list((OUTPUT_DIR / "train" / "images").glob("*.jpg")))
    train_lbls = len(list((OUTPUT_DIR / "train" / "labels").glob("*.txt")))
    val_imgs = len(list((OUTPUT_DIR / "val" / "images").glob("*.jpg")))
    val_lbls = len(list((OUTPUT_DIR / "val" / "labels").glob("*.txt")))
    print(f"train: {train_imgs} imgs, {train_lbls} labels")
    print(f"val:   {val_imgs} imgs, {val_lbls} labels")

    if abs(train_imgs - train_lbls) > train_imgs * 0.05:
        print("ADVERTENCIA: más del 5% de imágenes sin label en train.")
    if abs(val_imgs - val_lbls) > val_imgs * 0.05:
        print("ADVERTENCIA: más del 5% de imágenes sin label en val.")

if __name__ == "__main__":
    main()

