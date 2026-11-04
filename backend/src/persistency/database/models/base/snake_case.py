"""Conversión de nombres de clase a nombres de tabla."""

from __future__ import annotations

import re

_BOUNDARY = re.compile(r"(?<!^)(?=[A-Z])")


def snake_case(name: str) -> str:
    """`ExperimentResult` → `experiment_result`."""
    return _BOUNDARY.sub("_", name).lower()
