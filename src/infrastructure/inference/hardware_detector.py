"""
Detector de hardware para ejecución de modelos de aprendizaje profundo e inferencia.

Determina automáticamente si el entorno dispone de aceleración por GPU (CUDA)
o si debe utilizar CPU, aplicando el principio de tolerancia a fallos ante la
ausencia del framework PyTorch.
"""


def get_device() -> str:
    """
    Verifica la disponibilidad de aceleración GPU mediante PyTorch.

    Returns:
        'cuda:0' si PyTorch y CUDA están disponibles; 'cpu' en caso contrario
        o si PyTorch no se encuentra instalado en el entorno.
    """
    try:
        import torch
        if torch.cuda.is_available():
            return "cuda:0"
        return "cpu"
    except (ImportError, ModuleNotFoundError, Exception):
        return "cpu"
