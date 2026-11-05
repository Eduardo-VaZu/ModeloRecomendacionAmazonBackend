"""Carga y validación de `configs/config.yaml`."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "configs" / "config.yaml"

MIN_INTERACTIONS = 5  # R2: exigencia de la tesis


@dataclass(frozen=True)
class PathsConfig:
    raw: Path
    interim: Path
    processed: Path
    reports: Path
    artifacts: Path


@dataclass(frozen=True)
class DatasetConfig:
    name: str
    category: str
    reviews_url: str
    meta_url: str


@dataclass(frozen=True)
class QualityConfig:
    min_completeness: float
    meta_completeness_fields: tuple[str, ...]


@dataclass(frozen=True)
class FilteringConfig:
    k_core: int

    def __post_init__(self) -> None:
        if self.k_core < MIN_INTERACTIONS:
            raise ValueError(
                f"La tesis exige k_core >= {MIN_INTERACTIONS}, se recibió {self.k_core}"
            )


@dataclass(frozen=True)
class SplitConfig:
    val_ratio: float
    test_ratio: float

    def __post_init__(self) -> None:
        if not 0 < self.val_ratio + self.test_ratio < 1:
            raise ValueError("val_ratio + test_ratio debe estar entre 0 y 1")


@dataclass(frozen=True)
class EvaluationConfig:
    k_values: tuple[int, ...]
    relevance_threshold: float
    batch_size: int


@dataclass(frozen=True)
class ContentConfig:
    max_features: int
    ngram_range: tuple[int, int]
    min_df: int
    n_candidates: int


@dataclass(frozen=True)
class ALSConfig:
    factors: int
    regularization: float
    iterations: int
    alpha: float


@dataclass(frozen=True)
class HybridConfig:
    blend_weight: float


@dataclass(frozen=True)
class TuningConfig:
    """Grillas que `04_tune` recorre sobre validación; `metric` decide la mejor combinación."""

    metric: str
    als_factors: tuple[int, ...]
    als_regularization: tuple[float, ...]
    als_alpha: tuple[float, ...]
    n_candidates: tuple[int, ...]
    blend_weights: tuple[float, ...]


@dataclass(frozen=True)
class DemoConfig:
    n_users: int
    top_k: int


@dataclass(frozen=True)
class Config:
    seed: int
    paths: PathsConfig
    dataset: DatasetConfig
    quality: QualityConfig
    filtering: FilteringConfig
    split: SplitConfig
    evaluation: EvaluationConfig
    content: ContentConfig
    als: ALSConfig
    hybrid: HybridConfig
    tuning: TuningConfig
    demo: DemoConfig


def load_config(path: Path = DEFAULT_CONFIG_PATH) -> Config:
    raw: dict[str, Any] = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    quality, evaluation, content = raw["quality"], raw["evaluation"], raw["content"]
    return Config(
        seed=raw["seed"],
        paths=PathsConfig(**{key: PROJECT_ROOT / value for key, value in raw["paths"].items()}),
        dataset=DatasetConfig(**raw["dataset"]),
        quality=QualityConfig(
            min_completeness=quality["min_completeness"],
            meta_completeness_fields=tuple(quality["meta_completeness_fields"]),
        ),
        filtering=FilteringConfig(**raw["filtering"]),
        split=SplitConfig(**raw["split"]),
        evaluation=EvaluationConfig(
            k_values=tuple(evaluation["k_values"]),
            relevance_threshold=evaluation["relevance_threshold"],
            batch_size=evaluation["batch_size"],
        ),
        content=ContentConfig(**{**content, "ngram_range": tuple(content["ngram_range"])}),
        als=ALSConfig(**raw["als"]),
        hybrid=HybridConfig(**raw["hybrid"]),
        tuning=TuningConfig(
            **{key: tuple(v) if isinstance(v, list) else v for key, v in raw["tuning"].items()}
        ),
        demo=DemoConfig(**raw["demo"]),
    )
