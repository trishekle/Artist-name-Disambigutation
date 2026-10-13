"""Single data-access seam for the analysis pipeline.

Everything downstream (graph, metric, CLI, UI) loads catalogs through
:func:`load_group`. Today that reads the per-group CSVs under ``data/``. To move
to Postgres later, replace the body of ``_read_group_frame`` with a query that
returns the same enriched columns (see ``features.REQUIRED_COLUMNS``); no graph,
metric, CLI, or UI code needs to change.
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from .features import FeatureSet, load_features

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
_FILENAME_PREFIX = "spotify_tracks_"


def _group_csv_path(name: str) -> Path:
    """Map a group display name (e.g. ``"Funhouse"``) to its CSV path."""
    safe = re.sub(r"[^\w.-]+", "_", name, flags=re.UNICODE).strip("._")
    return DATA_DIR / f"{_FILENAME_PREFIX}{safe}.csv"


def _resolve(name_or_path: str | Path) -> Path:
    """Accept either a group name or a direct path to a group CSV."""
    candidate = Path(name_or_path)
    if candidate.suffix.lower() == ".csv" or candidate.exists():
        return candidate
    return _group_csv_path(str(name_or_path))


def available_groups(min_artist_ids: int = 2) -> list[str]:
    """List group names that are analyzable (>= ``min_artist_ids`` distinct IDs).

    A same-name comparison needs at least two artist IDs, so single-ID catalogs
    are filtered out here rather than failing later in profile building.
    """
    groups = []
    for path in sorted(DATA_DIR.glob(f"{_FILENAME_PREFIX}*.csv")):
        name = path.stem[len(_FILENAME_PREFIX):]
        try:
            distinct = pd.read_csv(path, usecols=["artist_id"])["artist_id"].astype(str).nunique()
        except (ValueError, KeyError):
            continue
        if distinct >= min_artist_ids:
            groups.append(name)
    return groups


def load_group(name_or_path: str | Path) -> FeatureSet:
    """Load one same-name group as a :class:`FeatureSet`.

    This is the one seam the rest of the project depends on for catalog data.
    """
    return load_features(_resolve(name_or_path))
