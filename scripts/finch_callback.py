"""
finch_callback.py
Implementación de Loss-Adaptive Learning Rate Schedule inspirado en FINCH (arXiv:2605.20005)
adaptado para el aprendizaje continuo de posturas (YOLO Pose) sin olvido catastrófico.

Principio matemático de FINCH:
El límite superior del olvido por paso de entrenamiento está acotado por:
    ||ΔW||_F <= lr * sqrt(loss)

Estrategia:
- Cuando la pérdida (loss) es alta (lotes nuevos/atípicos), el LR se reduce para evitar desestabilizar las representaciones previas.
- Cuando la pérdida converge (loss baja), el LR aumenta controladamente para acelerar la consolidación sin degradar el conocimiento canónico.
"""

import math
from ultralytics.utils import LOGGER

class FINCHScheduler:
    def __init__(self, base_lr=0.001, min_lr=1e-5, max_lr=0.01, ref_loss=2.0, alpha=0.5):
        self.base_lr = base_lr
        self.min_lr = min_lr
        self.max_lr = max_lr
        self.ref_loss = ref_loss
        self.alpha = alpha
        self.history = []

    def extract_loss(self, trainer):
        # 1. Intentar trainer.loss directo
        if hasattr(trainer, "loss") and trainer.loss is not None:
            try:
                val = float(trainer.loss.item() if hasattr(trainer.loss, "item") else trainer.loss)
                if math.isfinite(val) and val > 0:
                    return val
            except Exception:
                pass

        # 2. Intentar trainer.tloss (dict o iterable de pérdidas agregadas)
        if hasattr(trainer, "tloss") and trainer.tloss is not None:
            try:
                if isinstance(trainer.tloss, dict):
                    vals = [float(v.item() if hasattr(v, "item") else v) for v in trainer.tloss.values()]
                    return sum(v for v in vals if math.isfinite(v))
                elif isinstance(trainer.tloss, (list, tuple)):
                    vals = [float(v.item() if hasattr(v, "item") else v) for v in trainer.tloss]
                    return sum(v for v in vals if math.isfinite(v))
            except Exception:
                pass

        # 3. Intentar trainer.loss_items
        if hasattr(trainer, "loss_items") and trainer.loss_items is not None:
            try:
                if isinstance(trainer.loss_items, dict):
                    vals = [float(v.item() if hasattr(v, "item") else v) for v in trainer.loss_items.values()]
                    return sum(v for v in vals if math.isfinite(v))
                elif isinstance(trainer.loss_items, (list, tuple)):
                    vals = [float(v.item() if hasattr(v, "item") else v) for v in trainer.loss_items]
                    return sum(v for v in vals if math.isfinite(v))
            except Exception:
                pass

        return None

    def on_train_batch_end(self, trainer):
        loss = self.extract_loss(trainer)
        if loss is None or not math.isfinite(loss):
            return

        # FINCH: lr adaptativo inversamente proporcional a sqrt(loss)
        scale = math.pow(self.ref_loss / (loss + 1e-8), self.alpha)
        new_lr = self.base_lr * scale
        new_lr = max(self.min_lr, min(self.max_lr, new_lr))

        if hasattr(trainer, "optimizer") and trainer.optimizer is not None:
            for param_group in trainer.optimizer.param_groups:
                param_group['lr'] = new_lr

        epoch = getattr(trainer, "epoch", 0)
        batch = getattr(trainer, "batch_idx", len(self.history))
        self.history.append({
            "epoch": epoch,
            "loss": loss,
            "scale": scale,
            "lr": new_lr
        })

        if len(self.history) % 10 == 0:
            LOGGER.info(f"🥋 [FINCH Callback] Epoch {epoch+1} | Batch Loss: {loss:.4f} | Scale: {scale:.3f} | Adjusted LR: {new_lr:.6f}")

