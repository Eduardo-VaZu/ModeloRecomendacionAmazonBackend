"""Base de los casos de uso: un handler por caso, sobre una unidad de trabajo."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ...database import AsyncSQLSession
from ...persistency.unit_of_work import UnitOfWork
from .base_data_transfer import BaseDataTransfer


class BaseHandler[TRequest: BaseDataTransfer, TResponse: BaseDataTransfer](ABC):
    """Recibe la sesión de FastAPI y expone los repositorios vía `_unit_of_work`."""

    def __init__(self, session: AsyncSQLSession) -> None:
        self._unit_of_work = UnitOfWork(session)

    @abstractmethod
    async def execute(self, request: TRequest) -> TResponse:
        """Ejecuta el caso de uso."""
