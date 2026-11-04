"""R1: descarga y lectura de Amazon Reviews 2023."""

from __future__ import annotations

import urllib.request
from collections.abc import Sequence
from pathlib import Path

import pandas as pd
from tqdm import tqdm

from recsys.config import DatasetConfig

_CHUNK_BYTES = 1 << 20


def raw_paths(dataset: DatasetConfig, raw_dir: Path) -> tuple[Path, Path]:
    """Rutas locales de reseñas y metadatos de la categoría configurada."""
    return (
        raw_dir / f"{dataset.category}.jsonl",
        raw_dir / f"meta_{dataset.category}.jsonl",
    )


def download_file(url: str, destination: Path) -> None:
    """Descarga `url` en `destination`; no hace nada si el archivo ya existe."""
    if destination.exists():
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_suffix(destination.suffix + ".part")
    with urllib.request.urlopen(url) as response, partial.open("wb") as file:
        total = int(response.headers.get("Content-Length", 0)) or None
        with tqdm(total=total, unit="B", unit_scale=True, desc=destination.name) as bar:
            while chunk := response.read(_CHUNK_BYTES):
                file.write(chunk)
                bar.update(len(chunk))
    partial.rename(destination)


def download_category(dataset: DatasetConfig, raw_dir: Path) -> tuple[Path, Path]:
    reviews_path, meta_path = raw_paths(dataset, raw_dir)
    download_file(dataset.reviews_url.format(category=dataset.category), reviews_path)
    download_file(dataset.meta_url.format(category=dataset.category), meta_path)
    return reviews_path, meta_path


def read_jsonl(
    path: Path, columns: Sequence[str] | None = None, chunksize: int = 200_000
) -> pd.DataFrame:
    """Lee un .jsonl por bloques conservando solo `columns` (sin inferir tipos ni fechas)."""
    chunks = pd.read_json(path, lines=True, chunksize=chunksize, dtype=False, convert_dates=False)
    frames = [chunk.reindex(columns=list(columns)) if columns else chunk for chunk in chunks]
    return pd.concat(frames, ignore_index=True)
