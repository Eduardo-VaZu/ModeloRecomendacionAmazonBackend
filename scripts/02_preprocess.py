"""Paso 2: calidad (R13) → k-core (R2) → codificación → partición temporal."""

import json

from recsys.config import load_config
from recsys.data.loader import raw_paths, read_jsonl
from recsys.data.preprocessing import encode_ids, k_core_filter
from recsys.data.quality import apply_quality_rules
from recsys.data.splitting import temporal_user_split
from recsys.data.storage import save_processed
from recsys.schema import ITEM_ID, ITEM_IDX, META_COLUMNS, REVIEW_COLUMNS
from recsys.utils.logging import get_logger

logger = get_logger("02_preprocess")


def main() -> None:
    config = load_config()
    reviews_path, meta_path = raw_paths(config.dataset, config.paths.raw)

    reviews = read_jsonl(reviews_path, REVIEW_COLUMNS)
    meta = read_jsonl(meta_path, META_COLUMNS)
    logger.info("Leídos: %d reseñas, %d productos", len(reviews), len(meta))

    reviews, meta, report = apply_quality_rules(
        reviews, meta, config.quality.meta_completeness_fields, config.quality.min_completeness
    )
    logger.info("Reglas de calidad: %s", report)

    active = k_core_filter(reviews, config.filtering.k_core)
    logger.info("k-core=%d: %d interacciones", config.filtering.k_core, len(active))

    encoded, users, items = encode_ids(active)
    item_table = (
        meta.set_index(ITEM_ID).loc[items].reset_index().assign(**{ITEM_IDX: range(len(items))})
    )
    train, val, test = temporal_user_split(
        encoded, config.split.val_ratio, config.split.test_ratio
    )
    logger.info("Usuarios=%d, productos=%d", len(users), len(items))
    logger.info("train=%d, val=%d, test=%d", len(train), len(val), len(test))

    processed = config.paths.processed
    save_processed({"train": train, "val": val, "test": test}, item_table, len(users), processed)
    (processed / "quality_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    logger.info("Guardado en %s", processed)


if __name__ == "__main__":
    main()
