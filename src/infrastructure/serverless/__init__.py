"""Módulo serverless para Huawei Cloud FunctionGraph."""

from src.infrastructure.serverless.container_app import app
from src.infrastructure.serverless.functiongraph_handler import handler

__all__ = ["app", "handler"]

