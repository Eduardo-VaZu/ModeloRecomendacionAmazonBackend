"""Acceso a las pruebas de hipótesis (HE1-HE3)."""

from __future__ import annotations

from ..database.models import HypothesisTest
from .base_repository import BaseRepository


class HypothesisTestRepository(BaseRepository[HypothesisTest]):
    """Repositorio de `HypothesisTest`."""

    _entity_class = HypothesisTest
