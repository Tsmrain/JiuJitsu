# Technical Memo: YOLO26 local — MLX vs MPS

**Fecha:** 2026-10-28
**Iteración:** Transition-2B
**Estado:** activo

## Issue

Necesitamos YOLO26-pose corriendo localmente en Apple Silicon M5 (24 GB) para el pipeline de análisis biomecánico, sin depender del worker remoto de Google Colab ni de Google Drive polling.

## Opciones evaluadas

| Opción | Pros | Cons | Decisión |
|---|---|---|---|
| **yolo-mlx (thewebAI)** | Inferencia nativa MLX, sin PyTorch | Requiere `mlx>=0.30.3,<0.31` por bug en buffer de comandos GPU en MLX 0.31.x; colisiona con `mlx-embeddings` (requiere `mlx>=0.31.1`, instalado `0.32.4`). | Descartada para proteger el pipeline de Qwen3-VL local |
| **ultralytics + MPS** | Compatible con Metal (`torch.backends.mps`), interoperable con `mlx 0.32.4`, 63.5 FPS en M5 | Utiliza PyTorch sobre Metal en vez de MLX nativo | **Adoptada (Ruta B)** |
| **ultralytics CPU** | Sin aceleración Metal | Lento (~10 FPS), no viable para latencia interactiva | Descartada |

## Solución adoptada

Se adoptó la **Ruta B** (`ultralytics` con backend Apple MPS sobre Metal):

- **Modelo:** `yolo26n-pose.pt` (7.5 MB) con fallback local a `yolo11n-pose.pt` (6.0 MB).
- **Backend de aceleración:** PyTorch Metal Performance Shaders (`device="mps"`).
- **FPS medido:** 63.5 FPS en `Maestro.mp4` (783 fotogramas procesados en 12.32s). Cobertura cinemática: 94.25%.
- **Dimensión de keypoints:** 133 dimensiones por frame (17 keypoints corporales COCO normalizados + tracking espacial continuo).

## Gestión de recursos

- **Qwen 3-VL 2B (MLX):** ~2.5 GB RAM bajo demanda, gestionado por MLX.
- **YOLO26-pose (MPS):** cargado bajo demanda, liberado en bloque `finally` con `gc.collect()` y `torch.mps.empty_cache()`.
- **Guard de memoria:** comprobación previa `psutil.virtual_memory().available < 2 GB` lanzando `RuntimeError` preventivo si la RAM es insuficiente.
- **Instrumentación:** `log_ram_usage(tag)` registrando en logs uso, total y disponible.
- **Memoria RAM disponible post-E2E:** 11.3 GB (> 10 GB requerido).
- **Memoria RAM de procesos Python:** ~164 MB en reposo.

## Verificación

- **Test unitario de inferencia cinemática:**
  ```bash
  frames=783 con_persona=738 cobertura=0.9425 tiempo=12.32s fps=63.5
  primer_frame_keys=133
  ```
- **Test E2E completo:**
  - Registro de patrón `Maestro.mp4`: 783 frames, cobertura 94.25%, `patron_id`: `e4264a95-594c-4e61-9b28-864748304e01`.
  - Evaluación `Alumno.mp4`: `DURACION_SEG = 70.77s`, estado = `completado`, similitud = 25.72%.
  - Feedback generado por Gemini 3.5 Flash-Lite en inglés citando el libro:
    > *"Your elbows are flaring outward and losing connection to your hips, which allows the opponent to collapse your frame. Keep your elbows tightly glued to your ribs as recommended in Jiu-Jitsu University (p."*
  - Fotograma crítico anotado en disco: `/tmp/corpocmente_frames/critico_b5a01854-3f66-47f4-b415-4e11da4d41a1.jpg` (81 KB, 464x832 JPEG).

## Alternativas consideradas y descartadas

1. **Downgrade de MLX a `<0.31` para compilar `yolo-mlx`:**
   Descartado porque `mlx-embeddings` (empleado para Qwen3-VL local) requiere `mlx>=0.31.1`. Degradar la versión rompería la ingesta y recuperación RAG validada en Transition-2A.1.
2. **Inferencia en Colab:**
   Eliminada completamente. Todo el pipeline biomecánico (YOLO pose) y RAG (Qwen3-VL) corre 100% en local en el Mac M5.

## Deuda residual

- Evaluar adopción de `thewebAI/yolo-mlx` una vez que la biblioteca sea actualizada para soportar `mlx>=0.32` sin el conflicto de buffer GPU.
- Internacionalización completa de mensajes secundarios en frontend (el flujo principal E2E ya cuenta con soporte `en` default).
