"""Paso 6 (CRISP-DM, Fase 06): exporta el paquete del prototipo visual a `artifacts/demo/`.

Toma una muestra de usuarios de test, su historial y el Top-K de cada modelo entrenado en
03_train. Para el híbrido guarda el puntaje de cada etapa (contenido, ALS y final) y, para todo
modelo personalizado, el ítem del historial más parecido por contenido como "motivo" de la
recomendación (los modelos no personalizados no llevan motivo).
"""

import numpy as np
import pandas as pd
import scipy.sparse as sp

from recsys.config import Config, load_config
from recsys.export.demo_bundle import DatasetSummary, DemoBundle, results_to_long
from recsys.models.base import Recommender
from recsys.models.hybrid import HybridRecommender
from recsys.pipeline import load_models, load_processed
from recsys.schema import ITEM_ID, ITEM_IDX, RATING, TIMESTAMP, USER_ID, USER_IDX
from recsys.utils.logging import get_logger
from recsys.utils.seed import set_seed

logger = get_logger("06_export_demo")

PERSONALIZED = ("content_based", "als", "hybrid")  # usan el historial del usuario


def _sample_users(test: pd.DataFrame, n_users: int, seed: int) -> np.ndarray:
    users = test[USER_IDX].unique()
    rng = np.random.default_rng(seed)
    return np.sort(rng.choice(users, size=min(n_users, len(users)), replace=False))


def _history(frames: dict[str, pd.DataFrame], users: np.ndarray) -> pd.DataFrame:
    parts = [
        frame[frame[USER_IDX].isin(users)].assign(split=name) for name, frame in frames.items()
    ]
    return pd.concat(parts, ignore_index=True).sort_values([USER_IDX, TIMESTAMP])


def _top_k(model: Recommender, users: np.ndarray, k: int) -> pd.DataFrame:
    """Top-K con puntajes; para el híbrido, también el detalle de las dos etapas."""
    if isinstance(model, HybridRecommender):
        candidates, content_part, als_part, final_part = model.stage_scores(users)
        order = np.argsort(-final_part, axis=1, kind="stable")[:, :k]

        def take(values: np.ndarray) -> np.ndarray:
            return np.take_along_axis(values, order, axis=1).ravel().astype(float)

        items = np.take_along_axis(candidates, order, axis=1)
        content, als, final = take(content_part), take(als_part), take(final_part)
    else:
        items, scores = model.recommend_with_scores(users, k)
        final = scores.ravel().astype(float)
        content = final if model.name == "content_based" else np.full(final.shape, np.nan)
        als = final if model.name == "als" else np.full(final.shape, np.nan)
    n_users, width = items.shape
    return pd.DataFrame(
        {
            USER_IDX: np.repeat(users, width),
            ITEM_IDX: items.ravel(),
            "rank": np.tile(np.arange(1, width + 1), n_users),
            "content_score": content,
            "als_score": als,
            "final_score": final,
            "model": model.name,
        }
    )


def _reasons(recs: pd.DataFrame, train: pd.DataFrame, vectors: sp.csr_matrix) -> np.ndarray:
    """Ítem de entrenamiento del usuario más similar (coseno TF-IDF) a cada recomendado."""
    history = train.groupby(USER_IDX)[ITEM_IDX].agg(np.array)
    reasons = np.empty(len(recs), dtype=np.int64)
    for user, rows in recs.groupby(USER_IDX).indices.items():
        seen = history[user]
        similarity = (vectors[recs[ITEM_IDX].to_numpy()[rows]] @ vectors[seen].T).toarray()
        reasons[rows] = seen[similarity.argmax(axis=1)]
    return reasons


def _experiment_results(config: Config) -> pd.DataFrame:
    path = config.paths.tables / "results.csv"
    if not path.exists():
        logger.warning("No existe %s; el paquete irá sin resultados", path)
        return pd.DataFrame(columns=["model", "metric", "k", "value"])
    return results_to_long(pd.read_csv(path))


def _hypothesis_tests(config: Config) -> pd.DataFrame | None:
    """Pruebas HE1-HE3 de 05_evaluate; los valores no numéricos (NaN) se exportan como null."""
    path = config.paths.tables / "hypothesis_tests.csv"
    if not path.exists():
        logger.warning("No existe %s; el paquete irá sin pruebas de hipótesis", path)
        return None
    tests = pd.read_csv(path)
    return tests.astype({"effect_size_name": str, "effect_magnitude": str}).replace("nan", "")


def _vi_indicators(config: Config) -> pd.DataFrame | None:
    """I1-I5 de 03_train (vi_parameters.csv) e I6 por K de 05_evaluate."""
    parameters = config.paths.tables / "vi_parameters.csv"
    rate = config.paths.tables / "hybridization_rate.csv"
    if not parameters.exists() or not rate.exists():
        logger.warning("Faltan las tablas de la VI; el paquete irá sin I1-I6")
        return None
    vi = pd.read_csv(parameters)
    vi = vi[vi["indicator"].str.match(r"^I\d+$")]
    rows = vi[["dimension", "indicator", "name", "value"]].assign(k=pd.NA)
    i6 = pd.read_csv(rate).assign(
        dimension="D3", name="Tasa de hibridación del ranking"
    ).rename(columns={"hybridization_rate": "value"})
    frame = pd.concat([rows, i6[["dimension", "indicator", "name", "value", "k"]]])
    return frame.assign(k=frame["k"].astype("Int64")).reset_index(drop=True)


def main() -> None:
    config = load_config()
    set_seed(config.seed)
    data = load_processed(config)
    models = load_models(config.paths.models)
    vectors = models["hybrid"].content.item_vectors

    frames = {"train": data.train.frame, "test": data.test.frame}
    users = _sample_users(frames["test"], config.demo.n_users, config.seed)
    test = frames["test"]
    relevant_test = test[test[RATING] >= config.evaluation.relevance_threshold]
    relevant = set(zip(relevant_test[USER_IDX], relevant_test[ITEM_IDX], strict=True))

    recs = pd.concat(
        [_top_k(model, users, config.demo.top_k) for model in models.values()], ignore_index=True
    )
    pairs = zip(recs[USER_IDX], recs[ITEM_IDX], strict=True)
    recs["is_hit"] = [pair in relevant for pair in pairs]

    history = _history(frames, users)
    user_ids = history.drop_duplicates(USER_IDX).set_index(USER_IDX)[USER_ID]
    item_ids = data.items.set_index(ITEM_IDX)[ITEM_ID]
    recs = recs.assign(
        user_id=recs[USER_IDX].map(user_ids),
        product_id=recs[ITEM_IDX].map(item_ids),
        reason_product_id=pd.Series(_reasons(recs, frames["train"], vectors)).map(item_ids),
    )
    # Los modelos no personalizados no usan el historial: mostrar un "motivo" sería engañoso.
    recs.loc[~recs["model"].isin(PERSONALIZED), "reason_product_id"] = None

    reasons = set(recs["reason_product_id"].dropna())
    used_items = set(history[ITEM_ID]) | set(recs["product_id"]) | reasons
    products = data.items[data.items[ITEM_ID].isin(used_items)]

    bundle = DemoBundle(
        summary=DatasetSummary(
            source=config.dataset.name,
            category=config.dataset.category,
            is_synthetic=False,
            n_users=data.train.n_users,
            n_items=data.train.n_items,
            n_interactions=sum(len(frame) for frame in frames.values()),
            n_candidates=config.content.n_candidates,
        ),
        products=pd.DataFrame(
            {
                "product_id": products[ITEM_ID],
                "title": products["title"],
                "category": products["categories"].map(
                    lambda c: c[-1] if c is not None and len(c) else ""
                ),
                "store": products["store"],
            }
        ),
        users=history.groupby(USER_ID).size().rename("n_interactions").reset_index(),
        interactions=history.rename(columns={ITEM_ID: "product_id"}),
        recommendations=recs,
        experiment_results=_experiment_results(config),
        hypothesis_tests=_hypothesis_tests(config),
        vi_indicators=_vi_indicators(config),
    )
    output = config.paths.artifacts / "demo"
    bundle.write(output)
    logger.info("Paquete demo con %d usuarios en %s", len(users), output)


if __name__ == "__main__":
    main()
