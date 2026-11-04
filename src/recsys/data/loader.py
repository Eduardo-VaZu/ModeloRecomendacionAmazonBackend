"""R1: descarga y lectura de Amazon Reviews 2023."""

from __future__ import annotations

import http.client
import time
import urllib.error
import urllib.request
from collections.abc import Sequence
from pathlib import Path

import pandas as pd
from tqdm import tqdm

from recsys.config import DatasetConfig
from recsys.utils.logging import get_logger

logger = get_logger(__name__)

_CHUNK_BYTES = 1 << 20
_TIMEOUT_S = 60
_RETRIES = 20
_RETRY_WAIT_S = 10


def raw_paths(dataset: DatasetConfig, raw_dir: Path) -> tuple[Path, Path]:
    """Rutas locales de reseñas y metadatos de la categoría configurada."""
    return (
        raw_dir / f"{dataset.category}.jsonl",
        raw_dir / f"meta_{dataset.category}.jsonl",
    )


def _resume_download(url: str, partial: Path, desc: str) -> None:
    """Continúa la descarga en `partial` desde su tamaño actual (HTTP Range)."""
    offset = partial.stat().st_size if partial.exists() else 0
    request = urllib.request.Request(url, headers={"Range": f"bytes={offset}-"})
    try:
        response = urllib.request.urlopen(request, timeout=_TIMEOUT_S)
    except urllib.error.HTTPError as error:
        if error.code == 416:  # el rango pedido empieza en el final: ya estaba completo
            return
        raise
    with response:
        if response.status != 206:  # el servidor ignoró el rango: se empieza de cero
            offset = 0
        total = offset + int(response.headers.get("Content-Length", 0))
        mode = "ab" if offset else "wb"
        with (
            partial.open(mode) as file,
            tqdm(total=total, initial=offset, unit="B", unit_scale=True, desc=desc) as bar,
        ):
            while chunk := response.read(_CHUNK_BYTES):
                file.write(chunk)
                bar.update(len(chunk))
    if partial.stat().st_size != total:
        raise ConnectionError(f"Descarga incompleta: {partial.stat().st_size} de {total} bytes")


def download_file(url: str, destination: Path) -> None:
    """Descarga `url` en `destination`; no hace nada si el archivo ya existe.

    Si la conexión se corta, reintenta continuando desde lo ya descargado en el `.part`.
    """
    if destination.exists():
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_suffix(destination.suffix + ".part")
    for attempt in range(1, _RETRIES + 1):
        try:
            _resume_download(url, partial, destination.name)
            break
        except (OSError, http.client.HTTPException) as error:
            if attempt == _RETRIES:
                raise
            logger.warning("Falló la descarga (%s); reintento %d de %d", error, attempt, _RETRIES)
            time.sleep(_RETRY_WAIT_S)
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
