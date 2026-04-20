"""Camada de compatibilidade para imports legados.

O modelo de identidade foi movido para o app usuarios.
"""

from usuarios.models import Usuario

__all__ = ["Usuario"]