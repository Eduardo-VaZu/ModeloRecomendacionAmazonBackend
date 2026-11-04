"""Petición de importación del paquete demo."""

from __future__ import annotations

from ..shared.base_data_transfer import BaseDataTransfer


class ImportDemoBundleRequest(BaseDataTransfer):
    """Carpeta con los `.jsonl` y `summary.json` generados por `scripts/06_export_demo.py`."""

    directory: str
