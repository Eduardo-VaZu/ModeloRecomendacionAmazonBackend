"""Paso 5: evalúa los modelos sobre test y guarda la tabla de resultados.

Por ahora mide O1 (modelos no personalizados). En la Fase 6 se añaden contenido, ALS, el híbrido
(O2) y la tabla pre/post (R12).
"""

import pandas as pd

from recsys.config import load_config
from recsys.data.storage import load_splits
from recsys.evaluation.evaluator import evaluate
from recsys.models.baselines import ItemMeanRecommender, PopularityRecommender
from recsys.utils.logging import get_logger
from recsys.utils.seed import set_seed

logger = get_logger("05_evaluate")


def main() -> None:
    config = load_config()
    set_seed(config.seed)
    splits = load_splits(config.paths.processed)

    results = []
    for model in (PopularityRecommender(), ItemMeanRecommender()):
        model.fit(splits["train"])
        results.append(evaluate(model, splits["test"], config.evaluation))
        logger.info("%s: %s", model.name, results[-1])

    output = config.paths.reports / "tables" / "results.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(results).to_csv(output, index=False)
    logger.info("Resultados en %s", output)


if __name__ == "__main__":
    main()
