# Technical Memo: Patch local a mlx-embeddings (Qwen3-VL)

**Fecha:** 2026-10-28
**Iteración:** Transition-2A.1
**Autor:** Antigravity
**Estado:** activo

## Issue

El paquete `mlx-embeddings` (versión 0.1.0) falla al
vectorizar secuencias mixtas texto+imagen con Qwen3-VL-Embedding-2B porque:

1. `language_model._position_ids` y `_rope_deltas` no se resetean entre
   llamadas consecutivas con y sin `pixel_values`, causando `pos shape`
   incompatible con `get_rope_index`.
2. El cache de `_position_ids` se reutiliza aunque su longitud sea
   menor a `input_ids.shape[-1]`.
3. El `attention_mask` de una secuencia text-only después de una
   multimodal tiene `shape[-1] != input_ids.shape[-1]`, lo cual
   rompe `get_rope_index`.

## Solución

Se aplicó un patch local al archivo:
`backend/venv/lib/python3.12/site-packages/mlx_embeddings/models/qwen3_vl/model.py`

**SHA256 del archivo parchado:**
28fb69f1d6e2e8702f928789544481bc0ecfa0d3cc28a37cf26272c69f6b7067

**Copia de referencia del archivo parchado:**
`backend/vendor/mlx_embeddings_qwen3_vl_model.py.patched`

**Cambios aplicados:**

1. En `compute_qwen3_vl_hidden_states`, tras obtener `language_model`:
   ```python
   if pixel_values is not None:
       language_model._rope_deltas = None
       language_model._position_ids = None
   ```
   Fuerza recálculo de RoPE al entrar una nueva secuencia visual.

2. En el bloque de reuso de `position_ids`:
   ```python
   if (
       language_model._position_ids is not None
       and language_model._position_ids.shape[-1] >= input_ids.shape[-1]
   ):
       position_ids = language_model._position_ids[..., : input_ids.shape[-1]]
   else:
       position_ids, rope_deltas = language_model.get_rope_index(...)
   ```
   Evita reutilizar cache de longitud insuficiente.

3. En el manejo del `attention_mask`:
   ```python
   rope_mask = attention_mask
   ...
   if attention_mask is not None and attention_mask.shape[-1] != input_ids.shape[-1]:
       rope_mask = None
   ```
   Desactiva RoPE multimodal cuando la máscara no coincide con la
   longitud del texto (secuencias text-only post-multimodal).

## Verificación

- Benchmark: `scripts/benchmark_qwen_local.py` pasa.
- Test: `backend/tests/infrastructure/test_qwen_adapter.py` 6/6.
- E2E: ingesta del PDF "Jiu-Jitsu University" (600p) completada en
  817.52 segundos (13.6 minutos) con 630 chunks (ver Task 2).

## Alternativas consideradas y descartadas

- **Reemplazar por llama.cpp**: descartado por menor integración con
  el resto del stack Python.
- **Esperar fix upstream**: descartado por bloqueo de la iteración.
- **Fork completo de mlx-embeddings**: descartado por sobrecosto de
  mantenimiento.

## Deuda técnica registrada

- Reportar el bug a `ml-explore/mlx-embeddings` con PR.
- Cuando se libere la versión 0.2.0, re-evaluar
  si el patch sigue siendo necesario.
- Añadir un check automatizado al `start.sh` que verifique que el
  SHA256 del archivo parchado coincida con el documentado; si no
  coincide (reinstalación), abortar con mensaje claro.

## Script de re-aplicación

`scripts/reapply_mlx_patch.sh` (a crear en Task 5).
