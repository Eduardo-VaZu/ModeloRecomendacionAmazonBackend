"""Punto de entrada ASGI: registra los routers de cada funcionalidad."""

from .bootstrap import app
from .routers.experiments_router import experiments_router
from .routers.users_router import users_router

app.include_router(users_router)
app.include_router(experiments_router)
