# 🥋 Corpocmente - Protocolo de Aprendizaje Continuo (Continuous Learning)

> **Metodología:** Craig Larman (Cero Entrenamiento Ciego, Evidencia Empírica, Rollback y Preservación de Baseline).  
> **Sistema:** Data Flywheel MLOps para Jiu-Jitsu Brasileño (BJJ).

---

## 📌 1. Motivación y Contexto

En el Jiu-Jitsu Brasileño, los atletas interactúan en contacto físico íntimo, con giros rápidos, inversiones (berimbolo), guardias cerradas y agarres cruzados. Los detectores de pose estándar sufren oclusiones severas e incertidumbre cinemática.

El **Data Flywheel** de Corpocmente detecta automáticamente fotogramas con baja confianza ($\text{conf} < 0.65$), los almacena en `backend/storage/uncertainty_frames/`, y los procesa periódicamente.

---

## 🛡️ 2. Las 3 Reglas de Oro de Arquitectura (Larman MLOps)

Para evitar **olvido catastrófico** (*catastrophic forgetting*) y degradación en producción, el reentrenamiento está desacoplado de la inferencia y **nunca debe ejecutarse de forma automática o a ciegas**:

```
[Inferencia Tatami] 
       │ (conf < 0.65)
       ▼
[storage/uncertainty_frames/]
       │
       ▼ (data_flywheel_orchestrator.py --prepare)
[storage/continuous_dataset/]
       │
       ▼ (DECISIÓN MANUAL DE INGENIERÍA)
[Protocolo 70/30 + Freeze=10]
       │
       ▼
[Gatekeeper Benchmark Validation] ──(Pasa)──▶ [Deploy a best.pt]
       │
       └──(Falla)──▶ [Rollback y Descarte]
```

### Regla 1: Congelamiento de Capas (`freeze=10`)
* **Por qué:** El backbone del modelo contiene filtros espaciales universales (bordes, gradientes, extremidades). Reentrenar todo el modelo con pocos casos borde tatami destruye estas representaciones generales.
* **Acción:** Congelar las primeras 10 capas durante el fine-tuning (`freeze=10`). Solo se ajustan las cabezas de detección y keypoints.

### Regla 2: Buffer de Reproducción 70/30 (Replay Buffer)
* **Por qué:** Entrenar exclusivamente con casos difíciles sesga al modelo hacia posturas anómalas, empeorando el rendimiento en posturas estándar (pie, montada clásica).
* **Acción:** Cada iteración de reentrenamiento debe componerse de:
  - **70% Dataset Ancla (Gold Standard):** Poses verificadas y canónicas de BJJ.
  - **30% Dataset Flywheel:** Casos borde cosechados y etiquetados por el modelo maestro `yolo26x-pose.pt`.

### Regla 3: Gatekeeper Benchmark (Barrera de Validación)
* **Por qué:** Ningún peso generado en un ciclo de fine-tuning puede sobreescribir `best.pt` en producción sin una prueba de regresión empírica.
* **Criterios de Aceptación:**
  1. **Cobertura de Tracking:** $\ge 100\%$ en el benchmark de referencia (`backend/storage/benchmark/benchmark_clip_300f.mp4`).
  2. **Desambiguación de Oclusiones:** La resolución de oclusiones métricas con profundidad debe mantenerse estable.
  3. **Latencia:** Inferencia por frame en Apple Silicon MPS $\le 30\text{ ms/frame}$.

---

## 🛠️ 3. Procedimiento Operativo Estándar (SOP)

### Paso 1: Auditoría y Deduplicación (Dry-Run)
```bash
python scripts/data_flywheel_orchestrator.py --dry-run
```
*Verifica el conteo de frames, detecta duplicados por hash SHA-256 y muestra la distribución por técnica.*

### Paso 2: Preparación del Dataset con Modelo Maestro
```bash
python scripts/data_flywheel_orchestrator.py --prepare
```
*Filtra duplicados, ejecuta pseudo-etiquetado con `yolo26x-pose.pt` y genera `images/`, `labels/` y `dataset.yaml`.*

### Paso 3: Fine-Tuning Manual Supervisado
*(Ejecutar en GPU local o Google Colab Worker)*:
```bash
yolo pose train \
  data=backend/storage/continuous_dataset/dataset.yaml \
  model=backend/storage/models/yolo26s_bjj_pose/weights/best.pt \
  epochs=20 \
  batch=16 \
  imgsz=640 \
  freeze=10 \
  device=mps
```

### Paso 4: Ejecución del Gatekeeper Benchmark
```bash
python backend/scripts/benchmark_depth_disambiguation.py
```
*Si el benchmark pasa con 100% de cobertura y latencia óptima, promover los pesos a producción:*
```bash
cp runs/pose/train/weights/best.pt backend/storage/models/yolo26s_bjj_pose/weights/best.pt
```
