"""Paso 1: descarga reseñas y metadatos de la categoría configurada (R1)."""

from recsys.config import load_config
from recsys.data.loader import download_category
from recsys.utils.logging import get_logger

logger = get_logger("01_download")


def main() -> None:
    config = load_config()
    reviews_path, meta_path = download_category(config.dataset, config.paths.raw)
    logger.info("Reseñas: %s", reviews_path)
    logger.info("Metadatos: %s", meta_path)


if __name__ == "__main__":
    main()
