"""Motor asíncrono, fábrica de sesiones y dependencia de FastAPI."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from .config import ConfigurationVariables

configuration = ConfigurationVariables()
engine = create_async_engine(configuration.get_database_url, echo=configuration.log_sql_queries)
session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    """Abre una sesión por petición HTTP."""
    async with session_factory() as session:
        yield session


AsyncSQLSession = Annotated[AsyncSession, Depends(get_session)]
