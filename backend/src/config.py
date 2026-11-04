"""Configuración del backend leída desde variables de entorno."""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings


class ConfigurationVariables(BaseSettings):
    """Variables de entorno del backend (ver `.env` en la raíz del repositorio)."""

    database_url: str = Field(alias="POSTGRES_URL")
    log_sql_queries: bool = Field(default=False, alias="LOG_SQL_QUERIES")
    cors_origins: list[str] = Field(
        default=["http://localhost:5173", "http://localhost:5180"], alias="CORS_ORIGINS"
    )

    @property
    def get_database_url(self) -> str:
        """URL con el driver asíncrono `psycopg` que espera SQLAlchemy."""
        return self.database_url.replace("postgresql://", "postgresql+psycopg://", 1)
