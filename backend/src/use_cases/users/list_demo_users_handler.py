"""Caso de uso: listar y buscar usuarios de la muestra."""

from __future__ import annotations

from ..shared.base_handler import BaseHandler
from .user_requests import ListDemoUsersRequest
from .user_responses import DemoUserPageResponse, DemoUserResponse


class ListDemoUsersHandler(BaseHandler[ListDemoUsersRequest, DemoUserPageResponse]):
    """Devuelve una página de usuarios ordenada por actividad."""

    async def execute(self, request: ListDemoUsersRequest) -> DemoUserPageResponse:
        users, total = await self._unit_of_work.demo_users.search(
            request.search, request.limit, request.offset
        )
        return DemoUserPageResponse(
            items=[DemoUserResponse.model_validate(user) for user in users], total=total
        )
