"""Texto de cada producto y su vectorización TF-IDF (scikit-learn) para la Etapa 1."""

from __future__ import annotations

import pandas as pd
import scipy.sparse as sp
from sklearn.feature_extraction.text import TfidfVectorizer

from recsys.config import ContentConfig

TEXT_FIELDS = ["title", "features", "description", "categories", "store"]


def _flatten(value: object) -> str:
    if isinstance(value, (list, tuple)):
        return " ".join(_flatten(part) for part in value)
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return str(value)


def build_item_text(meta: pd.DataFrame) -> pd.Series:
    """Concatena los campos descriptivos de cada producto en un solo texto.

    Los campos faltantes se imputan con texto vacío (tratamiento de R13 para los campos con
    completitud menor al umbral).
    """
    return meta[TEXT_FIELDS].map(_flatten).agg(" ".join, axis=1).str.lower()


def fit_tfidf(texts: pd.Series, config: ContentConfig) -> tuple[TfidfVectorizer, sp.csr_matrix]:
    vectorizer = TfidfVectorizer(
        max_features=config.max_features,
        ngram_range=config.ngram_range,
        min_df=config.min_df,
        sublinear_tf=True,
    )
    return vectorizer, vectorizer.fit_transform(texts)
