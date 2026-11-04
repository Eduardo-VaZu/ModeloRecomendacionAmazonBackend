"""Genera un paquete demo SINTÉTICO para desarrollar el prototipo sin el dataset real.

Los datos son aleatorios y van marcados con `is_synthetic=True`; el frontend muestra un aviso.
Nunca deben usarse como resultados de la tesis.

    python scripts/dev_synthetic_demo.py
"""

import numpy as np
import pandas as pd

from recsys.config import load_config
from recsys.export.demo_bundle import DatasetSummary, DemoBundle
from recsys.utils.logging import get_logger

logger = get_logger("dev_synthetic_demo")

N_PRODUCTS, N_USERS, TOP_K, N_CANDIDATES = 300, 60, 20, 300
CATEGORIES = ["Accesorios", "Juegos", "Consolas", "Audio", "Coleccionables"]
DAY_MS = 86_400_000


def _products(rng: np.random.Generator) -> pd.DataFrame:
    categories = rng.choice(CATEGORIES, size=N_PRODUCTS)
    return pd.DataFrame(
        {
            "product_id": [f"SYN{i:05d}" for i in range(N_PRODUCTS)],
            "title": [f"{cat} sintético #{i}" for i, cat in enumerate(categories)],
            "category": categories,
            "store": rng.choice(["Tienda A", "Tienda B", "Tienda C"], size=N_PRODUCTS),
        }
    )


def _interactions(rng: np.random.Generator, product_ids: np.ndarray) -> pd.DataFrame:
    popularity = rng.zipf(1.6, size=len(product_ids)).astype(float)
    popularity /= popularity.sum()
    rows = []
    for u in range(N_USERS):
        n = int(rng.integers(6, 16))
        items = rng.choice(product_ids, size=n, replace=False, p=popularity)
        start = int(rng.integers(1_600_000_000_000, 1_650_000_000_000))
        n_test, n_val = max(1, n // 5), max(1, n // 5)
        for position, item in enumerate(items):
            from_end = n - 1 - position
            split = "test" if from_end < n_test else "val" if from_end < n_test + n_val else "train"
            rows.append(
                (
                    f"SYNUSER{u:04d}",
                    item,
                    float(rng.integers(1, 6)),
                    start + position * DAY_MS,
                    split,
                )
            )
    return pd.DataFrame(rows, columns=["user_id", "product_id", "rating", "timestamp", "split"])


def _recommendations(
    rng: np.random.Generator, interactions: pd.DataFrame, product_ids: np.ndarray
) -> pd.DataFrame:
    popular = interactions["product_id"].value_counts().index.to_numpy()
    rows = []
    for user_id, history in interactions.groupby("user_id"):
        train = history[history["split"] == "train"]["product_id"].to_numpy()
        test = set(history[(history["split"] == "test") & (history["rating"] >= 4)]["product_id"])
        unseen = np.setdiff1d(product_ids, train)

        top_popular = [p for p in popular if p not in set(train)][:TOP_K]
        for rank, product in enumerate(top_popular, start=1):
            rows.append(
                (user_id, "popularity", rank, product, None, None, 1 / rank, product in test, None)
            )

        candidates = rng.choice(unseen, size=TOP_K * 2, replace=False)
        if test and rng.random() < 0.6:
            candidates[rng.integers(TOP_K)] = next(iter(test))
        content = np.sort(rng.uniform(0.3, 0.9, size=len(candidates)))[::-1]
        als = np.clip(content * rng.uniform(0.6, 1.3, size=len(candidates)), 0, 1)
        is_test = np.array([c in test for c in candidates])
        als[is_test] = np.maximum(als[is_test], 0.95)
        final = 0.7 * als + 0.3 * content
        reasons = rng.choice(train, size=len(candidates))

        for rank, i in enumerate(range(TOP_K), start=1):
            rows.append(
                (
                    user_id,
                    "content_based",
                    rank,
                    candidates[i],
                    content[i],
                    None,
                    content[i],
                    bool(is_test[i]),
                    reasons[i],
                )
            )
        for rank, i in enumerate(np.argsort(-final)[:TOP_K], start=1):
            rows.append(
                (
                    user_id,
                    "hybrid",
                    rank,
                    candidates[i],
                    content[i],
                    als[i],
                    final[i],
                    bool(is_test[i]),
                    reasons[i],
                )
            )
    columns = [
        "user_id",
        "model",
        "rank",
        "product_id",
        "content_score",
        "als_score",
        "final_score",
        "is_hit",
        "reason_product_id",
    ]
    return pd.DataFrame(rows, columns=columns)


def _experiment_results() -> pd.DataFrame:
    values = {
        "popularity": {
            "rmse": 1.21,
            "mae": 0.96,
            "precision": 0.012,
            "recall": 0.031,
            "f1": 0.017,
            "coverage": 0.002,
            "train_time_s": 0.2,
        },
        "item_mean": {
            "rmse": 1.08,
            "mae": 0.84,
            "precision": 0.004,
            "recall": 0.010,
            "f1": 0.006,
            "coverage": 0.004,
            "train_time_s": 0.3,
        },
        "content_based": {
            "rmse": 1.02,
            "mae": 0.80,
            "precision": 0.021,
            "recall": 0.052,
            "f1": 0.030,
            "coverage": 0.310,
            "train_time_s": 12.4,
        },
        "als": {
            "rmse": 0.99,
            "mae": 0.77,
            "precision": 0.027,
            "recall": 0.066,
            "f1": 0.038,
            "coverage": 0.180,
            "train_time_s": 41.7,
        },
        "hybrid": {
            "rmse": 0.95,
            "mae": 0.74,
            "precision": 0.034,
            "recall": 0.081,
            "f1": 0.048,
            "coverage": 0.230,
            "train_time_s": 54.1,
        },
    }
    ranking = {"precision", "recall", "f1", "coverage"}
    rows = [
        (model, metric, k, value * (1 + 0.15 * (k / 10 - 1)) if metric in ranking else value)
        for model, metrics in values.items()
        for metric, value in metrics.items()
        for k in ((5, 10, 20) if metric in ranking else (None,))
    ]
    frame = pd.DataFrame(rows, columns=["model", "metric", "k", "value"])
    return frame.assign(k=frame["k"].astype("Int64"))


def main() -> None:
    config = load_config()
    rng = np.random.default_rng(config.seed)
    products = _products(rng)
    interactions = _interactions(rng, products["product_id"].to_numpy())
    recommendations = _recommendations(rng, interactions, products["product_id"].to_numpy())

    bundle = DemoBundle(
        summary=DatasetSummary(
            source="Datos sintéticos de desarrollo",
            category=config.dataset.category,
            is_synthetic=True,
            n_users=N_USERS,
            n_items=N_PRODUCTS,
            n_interactions=len(interactions),
            n_candidates=N_CANDIDATES,
        ),
        products=products,
        users=interactions.groupby("user_id").size().rename("n_interactions").reset_index(),
        interactions=interactions,
        recommendations=recommendations,
        experiment_results=_experiment_results(),
    )
    output = config.paths.artifacts / "demo"
    bundle.write(output)
    logger.info("Paquete SINTÉTICO escrito en %s", output)


if __name__ == "__main__":
    main()
