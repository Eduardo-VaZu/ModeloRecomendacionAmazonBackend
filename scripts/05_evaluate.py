"""Paso 5: evalúa los modelos sobre test y guarda la tabla de resultados.

Cada modelo se reentrena con train + validación antes de medirse en test, para que use la
información más reciente de cada usuario. Mide O1 (modelos no personalizados) y la Etapa 1 de
contenido. En la Fase 6 se añaden ALS, el híbrido (O2) y la tabla pre/post (R12).
"""

import pandas as pd

from recsys.config import load_config
from recsys.data.storage import load_items, load_splits, train_with_validation
from recsys.evaluation.evaluator import evaluate
from recsys.models.baselines import ItemMeanRecommender, PopularityRecommender
from recsys.models.content_based import ContentBasedRecommender
from recsys.utils.logging import get_logger
from recsys.utils.seed import set_seed

logger = get_logger("05_evaluate")


def main() -> None:
    config = load_config()
    set_seed(config.seed)
    splits = load_splits(config.paths.processed)
    items = load_items(config.paths.processed)

    models = (
        PopularityRecommender(),
        ItemMeanRecommender(),
        ContentBasedRecommender(config.content, items),
    )
    train = train_with_validation(splits)
    results = []
    for model in models:
        model.fit(train)
        results.append(evaluate(model, splits["test"], config.evaluation))
        logger.info("%s: %s", model.name, results[-1])

    output = config.paths.reports / "tables" / "results.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(results).to_csv(output, index=False)
    logger.info("Resultados en %s", output)


if __name__ == "__main__":
    main()
