# Technical Memo: Transition-3 — Full Local Migration & Technical Debt Elimination

- **Date:** 2026-10-30
- **Iteration:** Transition-3 (Agile Unified Process - Craig Larman)
- **Status:** APPROVED / 100% LOCAL
- **Scope:** Complete Elimination of Gemini Technical Debt, Local ViCoS Anti-Spam Filter Validation, and Standalone MLX Inference

---

## 1. Executive Summary

Iteration Transition-3 completes the architectural migration of the Corpo e Mente system to a **100% autonomous local architecture**. All external cloud dependencies for inference and validation (Google Gemini API) have been fully excised from the codebase. The platform now operates entirely offline and on-device (Apple Silicon M-series via MLX and MPS).

The pipeline now utilizes:
1. **Pose Extraction & Biomechanical Tracking:** YOLO-pose (`yolo26n-pose.pt` / `yolo26s` finetuned).
2. **Anti-Spam Video Gate:** Local ViCoS MLP classifier (`position_classifier_grouped.pkl`) evaluating multi-person grappling interactions.
3. **Multimodal RAG & Knowledge Retrieval:** Qwen3-VL-Embedding-2B (MLX 8-bit, 2048 dims) indexed into Qdrant.
4. **Pedagogical Qualitative Feedback:** Qwen3-VL-4B-Instruct (MLX 4-bit) generating structured JSON corrections (`summary`, `correction`) based on critical frame and multimodal evidence.

---

## 2. Gemini Technical Debt Elimination

### 2.1 Removed Components
- **Class `GeminiApiAdapter` & `GeminiRateLimitError`:** Completely removed from `backend/corpocmente/infrastructure/ai/adapters.py`.
- **Legacy Test Suite:** Deleted `backend/tests/infrastructure/test_gemini_adapter.py`.
- **Dependencies:** Removed `google-genai==0.2.1` from `backend/requirements.txt` and `GEMINI_API_KEY` from configuration files (`.env.example`, `README.md`).
- **Domain Decoupling:** Updated `IntelligenceAnalysisFacade` and regression test suites (`test_intelligence_facade.py`, `test_threshold_prompt_regression.py`, `test_pipeline_biomecanico.py`) to reference `LocalVLMAdapter` directly.

### 2.2 Raw Verification Evidence
Executing strict reference checks confirms zero occurrences of Gemini across the application source code and test suite:

```bash
cd backend
grep -rn "GeminiApiAdapter\|google.genai" corpocmente/ tests/
# Output: 0 results (exit code 1)

grep -rn "Gemini" corpocmente/ tests/ --include="*.py"
# Output: 0 results (exit code 1)
```

Suite regression status: **79 passed, 6 skipped, 0 failed** in 6.17s.

---

## 3. Local Anti-Spam Classification (ViCoS Position Classifier)

### 3.1 Model Architecture & Anti-Leakage Training
- **Dataset:** ViCoS Brazilian Jiu-Jitsu dataset (17-keypoint paired poses annotated by ground/standing position).
- **Leakage Prevention:** To avoid data leakage across consecutive video frames, samples were partitioned using `GroupShuffleSplit` across temporal blocks of 30 frames (`BLOQUE = 30`).
- **Classifier:** Multi-Layer Perceptron (`MLPClassifier`, hidden layers `(128, 64)`, ReLU, early stopping).
- **Validation Metrics:**
  - **Overall Accuracy:** `90.19%` (`0.901855`)
  - **Macro F1-Score:** `88.18%` (`0.881817`)
  - **Decision Threshold:** Minimum BJJ frame ratio = `0.60` over sampled frames with at least 5 frames showing 2 interacting persons.

---

## 4. Anti-Spam Smoke Test Metrics & Edge Cases

The anti-spam filter (`LocalSpamFilter`) was validated against student execution videos, reference pattern videos (exempt), and negative non-BJJ controls:

```
INFO:corpocmente.infrastructure.ai.local_spam_filter:LocalSpamFilter cargado: accuracy=0.901855, f1=0.881817, min_bjj_ratio=0.60, min_interaction_frames=5

=== VIDEOS PROFESOR (Patrón de referencia — Exentos de filtro anti-spam) ===
  Maestro.mp4: [EXENTO DEL FILTRO - Flujo Maestro] (✓ Existe)
  Escape de 100 kilos brazo por debajo.mp4: [EXENTO DEL FILTRO - Flujo Maestro] (✓ Existe)
  Profesor dill pasaje de guardia abierta.mp4: [EXENTO DEL FILTRO - Flujo Maestro] (✓ Existe)
  profesor salida de Guardia Parandose.mp4: [EXENTO DEL FILTRO - Flujo Maestro] (✓ Existe)
  Profesor ensena 1 escape de guardia cerrada.mp4: [EXENTO DEL FILTRO - Flujo Maestro] (✓ Existe)

=== VIDEOS ALUMNO (Evaluación técnica — SÍ pasan por el filtro, esperado: True) ===
  Alumno.mp4:          6/7 frames BJJ (ratio=0.86, umbral=0.60) -> True  [PASS ✅]
  Alumno_Gaetamo.mp4:  5/5 frames BJJ (ratio=1.00, umbral=0.60) -> True  [PASS ✅]

=== NO-BJJ / CONTROLES NEGATIVOS (esperado: False) ===
  control_bailarinas.mp4: 4/13 frames BJJ (ratio=0.31, umbral=0.60) -> False [REJECTED ✅]
  control_boxeo.mp4:      0 frames con 2 personas (min 5)           -> False [REJECTED ✅]
  control_yoga.mp4:       11/11 frames BJJ (ratio=1.00, umbral=0.60)-> True  [FALSE POSITIVE ⚠️]
```

### 4.1 False Positive Analysis: Partner AcroYoga (`control_yoga.mp4`)
- **Finding:** `control_yoga.mp4` triggered a False Positive (ratio = 1.00).
- **Root Cause:** AcroYoga partner poses feature two bodies closely entangled in horizontal and inverted ground positions. Geometrically and kinematically, the normalized relative distance and joint orientations closely mimic Jiu-Jitsu guard positions (e.g. open guard, butterfly guard).
- **Architectural Safeguard:** This finding was reported without code alteration, preserving existing classifier boundaries until fine-tuned pose models (`yolo26s_bjj_pose`) and domain-specific temporal heuristics (e.g. dynamic motion energy vs static holding) are integrated.

---

## 5. Local VLM Integration & End-to-End Latency

- **Model:** `mlx-community/Qwen3-VL-4B-Instruct-4bit` running natively on Apple Silicon GPU/Unified Memory.
- **Role:** Replaces remote API calls for pedagogical evaluation, interpreting the marked critical frame along with top-3 visual RAG evidences.
- **Latency Performance:**
  - Full End-to-End execution (`04_e2e_vlm_evaluacion.py` covering auth, technique query, first-frame upload, person selection, background pose extraction, DTW alignment, Qdrant search, and local VLM inference):
  - **Total Latency:** `< 30 seconds` (well within SLA limits for asynchronous background evaluation).

