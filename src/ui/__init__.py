"""
Capa de Presentación y UI/UX (Streamlit / Craig Larman).
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.ui.app import main
from src.ui.coach_view import render_coach_view
from src.ui.feedback_view import render_feedback_view
from src.ui.progression_view import render_progression_view
from src.ui.token_view import render_token_gate
from src.ui.upload_view import render_upload_view

__all__ = [
    "main",
    "render_coach_view",
    "render_token_gate",
    "render_upload_view",
    "render_feedback_view",
    "render_progression_view",
]
