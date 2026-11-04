"""Resultado de la importación del paquete demo."""

from __future__ import annotations

from ..shared.base_data_transfer import BaseDataTransfer


class ImportDemoBundleResponse(BaseDataTransfer):
    """Filas importadas por tabla."""

    is_synthetic: bool
    products: int
    users: int
    interactions: int
    recommendations: int
    experiment_results: int
