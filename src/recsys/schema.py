"""Nombres de columnas compartidos por todo el proyecto."""

# Columnas originales de Amazon Reviews 2023
USER_ID = "user_id"
ITEM_ID = "parent_asin"
RATING = "rating"
TIMESTAMP = "timestamp"

# Índices enteros asignados tras el preprocesamiento
USER_IDX = "user_idx"
ITEM_IDX = "item_idx"

REVIEW_COLUMNS = [USER_ID, ITEM_ID, RATING, TIMESTAMP, "verified_purchase", "helpful_vote"]
META_COLUMNS = [ITEM_ID, "title", "features", "description", "categories", "store"]
