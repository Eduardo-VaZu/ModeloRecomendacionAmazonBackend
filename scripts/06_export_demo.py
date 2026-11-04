"""Paso 6: exporta el paquete de datos del prototipo visual a `artifacts/demo/`.

Toma una muestra de usuarios de test, su historial y las recomendaciones de cada modelo. Por ahora
exporta los modelos no personalizados (O1); en la Fase 5 se añaden contenido e híbrido (O2) con
sus puntajes por etapa.
"""

import numpy as np
import pandas as pd

from recsys.config import Config, load_config
from recsys.data.storage import load_items, load_splits
from recsys.export.demo_bundle import DatasetSummary, DemoBundle, results_to_long
from recsys.models.base import Recommender
from recsys.models.baselines import ItemMeanRecommender, PopularityRecommender
from recsys.schema import ITEM_ID, ITEM_IDX, RATING, TIMESTAMP, USER_ID, USER_IDX
from recsys.utils.logging import get_logger
from recsys.utils.seed import set_seed

logger = get_logger("06_export_demo")


def _sample_users(test: pd.DataFrame, n_users: int, seed: int) -> np.ndarray:
    users = test[USER_IDX].unique()
    rng = np.random.default_rng(seed)
    return np.sort(rng.choice(users, size=min(n_users, len(users)), replace=False))


def _history(frames: dict[str, pd.DataFrame], users: np.ndarray) -> pd.DataFrame:
    parts = [
        frame[frame[USER_IDX].isin(users)].assign(split=name) for name, frame in frames.items()
    ]
    return pd.concat(parts, ignore_index=True).sort_values([USER_IDX, TIMESTAMP])


def _recommendations(
    model: Recommender, users: np.ndarray, top_k: int, relevant: set[tuple[int, int]]
) -> pd.DataFrame:
    items, scores = model.recommend_with_scores(users, top_k)
    n_users, k = items.shape
    frame = pd.DataFrame(
        {
            USER_IDX: np.repeat(users, k),
            ITEM_IDX: items.ravel(),
            "rank": np.tile(np.arange(1, k + 1), n_users),
            "final_score": scores.ravel().astype(float),
        }
    )
    pairs = zip(frame[USER_IDX], frame[ITEM_IDX], strict=True)
    return frame.assign(
        model=model.name,
        content_score=None,
        als_score=None,
        reason_product_id=None,
        is_hit=[pair in relevant for pair in pairs],
    )


def _experiment_results(config: Config) -> pd.DataFrame:
    path = config.paths.reports / "tables" / "results.csv"
    if not path.exists():
        logger.warning("No existe %s; el paquete irá sin resultados", path)
        return pd.DataFrame(columns=["model", "metric", "k", "value"])
    return results_to_long(pd.read_csv(path))


def main() -> None:
    config = load_config()
    set_seed(config.seed)
    splits = load_splits(config.paths.processed)
    items = load_items(config.paths.processed)

    frames = {name: data.frame for name, data in splits.items()}
    users = _sample_users(frames["test"], config.demo.n_users, config.seed)
    test = frames["test"]
    relevant_test = test[test[RATING] >= config.evaluation.relevance_threshold]
    relevant = set(zip(relevant_test[USER_IDX], relevant_test[ITEM_IDX], strict=True))

    models: list[Recommender] = [PopularityRecommender(), ItemMeanRecommender()]
    recommendations = []
    for model in models:
        model.fit(splits["train"])
        recommendations.append(_recommendations(model, users, config.demo.top_k, relevant))
    recs = pd.concat(recommendations, ignore_index=True)

    history = _history(frames, users)
    user_ids = history.drop_duplicates(USER_IDX).set_index(USER_IDX)[USER_ID]
    item_ids = items.set_index(ITEM_IDX)[ITEM_ID]
    recs = recs.assign(
        user_id=recs[USER_IDX].map(user_ids), product_id=recs[ITEM_IDX].map(item_ids)
    )

    used_items = set(history[ITEM_ID]) | set(recs["product_id"])
    products = items[items[ITEM_ID].isin(used_items)]

    bundle = DemoBundle(
        summary=DatasetSummary(
            source=config.dataset.name,
            category=config.dataset.category,
            is_synthetic=False,
            n_users=splits["train"].n_users,
            n_items=splits["train"].n_items,
            n_interactions=sum(len(frame) for frame in frames.values()),
            n_candidates=config.content.n_candidates,
        ),
        products=pd.DataFrame(
            {
                "product_id": products[ITEM_ID],
                "title": products["title"],
                "category": products["categories"].map(lambda c: c[-1] if len(c) else ""),
                "store": products["store"],
            }
        ),
        users=history.groupby(USER_ID).size().rename("n_interactions").reset_index(),
        interactions=history.rename(columns={ITEM_ID: "product_id"}),
        recommendations=recs,
        experiment_results=_experiment_results(config),
    )
    output = config.paths.artifacts / "demo"
    bundle.write(output)
    logger.info("Paquete demo con %d usuarios en %s", len(users), output)


if __name__ == "__main__":
    main()
