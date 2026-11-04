"""Errores de dominio que la capa HTTP traduce a códigos de estado."""


class NotFoundError(Exception):
    """El recurso solicitado no existe (HTTP 404)."""
