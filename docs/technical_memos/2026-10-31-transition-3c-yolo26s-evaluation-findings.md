# Technical Memo: Transition-3C — Empirical Evaluation of YOLO26s Fine-Tuning & Domain Degradation Analysis

- **Date:** 2026-10-31
- **Author:** Equipo de Ingeniería / Proyecto de Grado Corpo e Mente
- **Status:** CONCLUDED / MODEL REJECTED / BASELINE RETAINED
- **Scope:** Empirical Verification of `best.pt` (YOLO26s fine-tuned on ViCoS dataset) vs Base Model (`yolo26n-pose.pt`).

---

## 1. Context & Objective

In iteration Transition-3C, fine-tuning of `yolo26s-pose.pt` (11.8M parameters) was completed on Google Colab (51 epochs on NVIDIA A100 GPU over 6.13 hours) using the ViCoS dataset (20,775 annotations of Brazilian Jiu-Jitsu ground interactions).

The objective was to evaluate whether the specialized weights `storage/models/yolo26n_bjj_pose/weights/best.pt` could improve keypoint detection and biomechanical tracking on production videos of students and professors (`Alumno.mp4`, `Alumno_Gaetamo.mp4`, `Maestro.mp4`).

---

## 2. Experimental Phases & Hypotheses

### 2.1 Iteración 3C.1 — Integración Directa
- **Hypothesis:** `best.pt` should detect both practitioners with higher pose precision in grappling encounters.
- **Result:** **REJECTED.** On `Alumno.mp4` and `Alumno_Gaetamo.mp4`, the model failed to detect 2 persons simultaneously across all sampled frames (`0 frames con 2 personas`), triggering False Negatives in the `LocalSpamFilter`.
- **Action:** Rollback to `iter-3c-antes`.

### 2.2 Iteración 3C.2 — Calibración Aislada de Confianza (`conf=0.15`, `conf=0.20`)
- **Hypothesis:** The fine-tuned model might have lower bounding-box output logits; lowering `conf` conditionally from 0.30 to 0.15/0.20 could recover detection.
- **Result:** **REJECTED.** 
  - In `Alumno.mp4` (276 frames), only 15 frames had $\ge 2$ bounding boxes, and only 1 frame had $\ge 2$ valid poses ($\ge 8$ keypoints $> 0.15$).
  - Mean visible keypoint confidence was 0.3669, but interaction detection remained at 0 frames in sampled checks.
- **Action:** Rollback to `iter-3c2-antes`.

### 2.3 Iteración 3C.3 — Rescate por Hiperparámetros de Aspect Ratio (`imgsz=1280`, `rect=True`)
- **Hypothesis:** `Alumno_Gaetamo.mp4` is a vertical smartphone video (464x832). Padding to 640x640 letterbox might shrink subjects excessively. Using `imgsz=1280` and `rect=True` should provide higher resolution without letterboxing.
- **Result:** **REJECTED.** Even at double resolution and rectangular aspect ratio, detections remained at 0 boxes on `Alumno_Gaetamo.mp4`.

### 2.4 Iteración 3C.4 — Prueba de Fuego: Zoom Test en Primer Plano (`/tmp/alumno_zoom.mp4`)
- **Hypothesis:** If the model only recognizes close-ups where subjects fill 80% of the screen (similar to ViCoS crop images), cropping the center 440x400 of `Alumno_Gaetamo.mp4` so the two fighters occupy the entire screen should allow detection.
- **Experiment:** Generated `/tmp/alumno_zoom.mp4` (401 frames, 440x400) tightly focused on the two fighters in open guard.
- **Results:**
  ```text
  --- DETECCIÓN EN FRAMES MUESTREADOS (conf=0.15) ---
  Frame   0: best.pt -> boxes=0 [], poses=0 | base -> boxes=2 [0.71, 0.61]
  Frame  14: best.pt -> boxes=0 [], poses=0 | base -> boxes=2 [0.75, 0.70]
  Frame  28: best.pt -> boxes=0 [], poses=0 | base -> boxes=2 [0.79, 0.68]
  Frame  56: best.pt -> boxes=0 [], poses=0 | base -> boxes=2 [0.81, 0.60]
  Frame  84: best.pt -> boxes=0 [], poses=0 | base -> boxes=2 [0.76, 0.58]
  Frame 140: best.pt -> boxes=0 [], poses=0 | base -> boxes=2 [0.65, 0.59]
  ...
  --- EVALUACIÓN COMPLETA (401 frames) ---
  conf=0.30 -> >=2 cajas:   0/401 ( 0.0%) | >=2 poses válidas: 0/401 (0.0%)
  conf=0.20 -> >=2 cajas:   0/401 ( 0.0%) | >=2 poses válidas: 0/401 (0.0%)
  conf=0.15 -> >=2 cajas:   0/401 ( 0.0%) | >=2 poses válidas: 0/401 (0.0%)
  conf=0.10 -> >=2 cajas:   0/401 ( 0.0%) | >=2 poses válidas: 0/401 (0.0%)
  conf=0.05 -> >=2 cajas:   4/401 ( 1.0%) | >=2 poses válidas: 0/401 (0.0%)
  ```

### 2.5 Iteración 3C.5 — Evaluación Aislada en Video Externo Horizontal / Toma Media (`2026-10-31 09-41-31.mov`)
- **Hypothesis:** To definitively eliminate the hypothesis of camera angle, smartphone resolution, and open gym perspective, a high-definition (1920x1080 @ 60fps) medium-shot YouTube recording of Brazilian Jiu-Jitsu sparring was evaluated.
- **Script:** `backend/scripts/09_test_best_pt_custom.py` evaluating `best.pt` (`conf=0.15, imgsz=1280, rect=True`) vs `yolo26n-pose.pt` (`conf=0.30, imgsz=640`).
- **Results (24 sampled frames across 24.17s):**
  - **best.pt (Fine-tuned):**
    - Frames con $\ge 2$ personas: **2/24 (8.3%)**
    - Frames con 1 persona: **16/24 (66.7%)**
    - Frames con 0 personas: **6/24 (25.0%)**
    - Confianza media de cajas: **0.5414**
  - **yolo26n-pose.pt (Base Original):**
    - Frames con $\ge 2$ personas: **14/24 (58.3%)**
    - Frames con 1 persona: **10/24 (41.7%)**
    - Frames con 0 personas: **0/24 (0.0%)**
    - Confianza media de cajas: **0.6877**
- **Veredicto:** **ESCENARIO B (CONFIRMADO).** `best.pt` sigue fallando sistemáticamente incluso en tomas medias HD horizontales. El modelo está sobreajustado de manera crítica al dominio ViCoS y es incapaz de generalizar fuera de ese dataset.

---

## 3. Causa Raíz Científica: Catastrophic Forgetting & Domain Shift

1. **Sobreajuste al Dataset ViCoS:**
   - On native ViCoS dataset images (`storage/datasets/vicos_images/*.jpg`), `best.pt` yields high confidence (`0.85 – 0.89`).
   - However, ViCoS images share identical indoor lighting, a distinct blue/red tatami texture, fixed camera sensor noise, and tight manual keypoint labels.
2. **Bounding Box Collapse (Falta de Padding):**
   - In `06_convertir_vicos_a_yolo_pose.py`, bounding boxes were calculated as `[min_x, min_y, max_x, max_y]` of annotated keypoints with **0% padding**.
   - During ground grappling, body parts overlap tightly, creating collapsed bounding boxes that penalize normal human proportions.
3. **Catastrophic Forgetting:**
   - Training 51 epochs with `lr0=0.01` without mixed COCO-person data overwrote the general human feature representations of the base model.
   - The model ceased to identify human beings outside the narrow distribution of ViCoS cameras.

---

## 4. Architectural Decision & Defense Recommendations

1. **Locked Production Backbone:** The system retains `yolo26n-pose.pt` as its official pose estimator. It consistently achieves 86%–100% sensitivity on student videos and 0 false negatives.
2. **Thesis Discussion Value:** This series of 4 empirical iterations provides textbook evidence for the thesis report:
   - Illustrates the *precision-recall tradeoff* and domain shift in sports computer vision.
   - Demonstrates rigorous engineering discipline: automated regression test gates, strict rollback upon false negatives, and empirical hypothesis testing before committing changes.

