"""R10: medición del tiempo de cómputo en segundos."""

from __future__ import annotations

import time


class Timer:
    """Context manager que guarda en `seconds` el tiempo transcurrido."""

    seconds: float = 0.0

    def __enter__(self) -> Timer:
        self._start = time.perf_counter()
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.seconds = time.perf_counter() - self._start
