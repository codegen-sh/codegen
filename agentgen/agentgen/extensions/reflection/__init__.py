"""
Reflection extension for agentgen.

This module provides reflection capabilities for agents, allowing them to
evaluate their own outputs and improve them based on feedback.
"""

from .reflector import Reflector, ReflectionResult

__all__ = ["Reflector", "ReflectionResult"]