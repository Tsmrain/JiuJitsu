# Technical Memo: Transition-3D — Biomechanical Pose Normalization in DTW

- **Date:** 2026-10-31
- **Iteration:** Transition-3D (Agile Unified Process - Craig Larman)
- **Status:** APPROVED / PRODUCTION READY 🥋
- **Scope:** Full Integration of Canonical Biomechanical Normalization (`pose_normalizer.py`) into Multi-Dimensional Dynamic Time Warping (`dtw_comparator.py`).

---

## 1. Executive Summary & Problem Root Cause

In prior iterations, the biomechanical comparison between student and instructor sequences was performed over **raw screen pixel coordinates** (133 dimensions, where the first 51 dims correspond to `[x, y, conf]` of 17 COCO keypoints in absolute screen space).

### The "Pixel vs. Movement" Flaw:
When evaluating the same technical execution recorded from a different camera distance, athlete height, or frame position:
1. **Translation Drift:** A practitioner centered at $(x=250, y=550)$ compared against an instructor at $(x=450, y=320)$ incurred a Euclidean coordinate distance of hundreds of pixels per joint.
2. **Anthropometric Scale:** Athletes with different limb lengths or torso heights suffered artificial penalties.
3. **DTW Distortion:** The raw DTW distance reached **$16,806.60$ pixels**, suppressing frame-level similarities to $\approx 1.9\% - 25.7\%$, even when the physical execution of the open guard was technically correct.

The platform had an unintegrated domain module [`backend/corpocmente/domain/biomechanics/pose_normalizer.py`](file:///Users/santiago/Desktop/JiuJitsu-main/backend/corpocmente/domain/biomechanics/pose_normalizer.py) specifically engineered to project 2D skeletons into an invariant canonical reference frame.

---

## 2. Mathematical Solution & Architecture

The integration in [`backend/corpocmente/domain/biomechanics/dtw_comparator.py`](file:///Users/santiago/Desktop/JiuJitsu-main/backend/corpocmente/domain/biomechanics/dtw_comparator.py) enforces a 4-step canonical projection on every frame prior to DTW alignment:

$$\mathbf{p}_{\text{norm}} = \mathbf{R}(-\theta) \cdot \left( \frac{\mathbf{p} - \mathbf{p}_{\text{hip\_mid}}}{\|\mathbf{p}_{\text{shoulder\_mid}} - \mathbf{p}_{\text{hip\_mid}}\|} \right)$$

1. **Hip-Centered Translation:** Origin shifted to the midpoint between left and right hip $(\mathbf{p}_{\text{L\_HIP}} + \mathbf{p}_{\text{R\_HIP}}) / 2$.
2. **Torso-Length Invariant Scale:** Divided by torso Euclidean norm $\|\mathbf{p}_{\text{shoulder\_mid}} - \mathbf{p}_{\text{hip\_mid}}\|$.
3. **Vertical Torso Alignment:** Rotated by angle $\theta = \text{atan2}(t_x, t_y)$ to align the torso vector with the canonical $+Y$ body axis.
4. **Invariant Joint Angles:** Extraction of 12 invariant joint angles in degrees $[0^\circ, 180^\circ]$ (elbows, shoulders, hips, knees, neck, trunk, pelvis, spine).
5. **Unified 46-D Feature Vector:** 34 normalized canonical coordinate positions $+$ 12 normalized angles $\frac{\theta - 90^\circ}{90^\circ}$.

---

## 3. Empirical Verification Results (Prueba de Fuego)

Evaluated via isolated execution of [`backend/scripts/10_test_normalized_dtw.py`](file:///Users/santiago/Desktop/JiuJitsu-main/backend/scripts/10_test_normalized_dtw.py):

| Evaluation Metric | Raw Pixel Method (Pre-3D) | Biomechanical Normalized DTW (3D) | Impact / Delta |
| :--- | :---: | :---: | :---: |
| **DTW Distance (`Alumno.mp4`)** | **16,806.60 px** | **212.95 units** | **$-98.7\%$ distance drop** |
| **DTW Normalized / frame** | 21.4644 | 0.2720 | Realistic biomechanical alignment |
| **Biomechanical Similarity (`Alumno.mp4`)** | **25.72%** (raw pixel) | **50.51%** | **$+24.79\%$ increase (approved)** |
| **Negative Control (`control_bailarinas.mp4`)** | N/A | **18.67%** | **Zero False Positives (< 35%)** |
| **Self-Comparison (`Maestro` vs `Maestro`)** | 0.0 px (100.0%) | 0.0 units (100.0%) | Deterministic sanity preserved |
| **Cropped Comparison (`Maestro[20:-20]`)** | > 90.0% | **99.55%** | Robust temporal warp |
| **Critical Biomechanical Joints Detected** | Collapsed by pixels | **[13, 9, 8]** (knee, wrist, elbow) | Real anatomical diagnostic |

---

## 4. Regression & Quality Gates

- **Unit & Integration Suite:** `cd backend && ./venv/bin/pytest tests/ -q`
  - **Result:** `79 passed, 6 skipped, 1 warning in 6.89s`.
  - Zero broken test contracts.
  - Backward compatibility preserved for synthetic tests and raw/normalized input formats.

