"""Synthetic enriched-metadata frames for tests.

These build a tiny two-artist same-name group that satisfies
``features.REQUIRED_COLUMNS`` so the analysis pipeline can run offline.
"""

from __future__ import annotations

import pandas as pd

ARTIST_A = "AAAAAAAAAAAAAAAAAAAAAA"
ARTIST_B = "BBBBBBBBBBBBBBBBBBBBBB"


def _row(track_id, name, artist_id, album_id, album_name, duration, year, number):
    return {
        "track_id": track_id,
        "track_name": name,
        "artist_id": artist_id,
        "artist_name": "Twins",
        "album_id": album_id,
        "album_name": album_name,
        "duration_ms": duration,
        "explicit": False,
        "track_number": number,
        "disc_number": 1,
        "album_type": "album",
        "album_release_date": f"{year}-01-01",
        "album_total_tracks": 10,
        "credited_artist_ids": artist_id,
        "credited_artist_names": "Twins",
    }


def two_artist_frame() -> pd.DataFrame:
    """Two clearly separated artists: short/old metal vs. long/new ambient."""
    rows = [
        _row("tA1", "Iron Thunder", ARTIST_A, "albA", "Steel Nights", 180000, 1985, 1),
        _row("tA2", "Blood Steel", ARTIST_A, "albA", "Steel Nights", 190000, 1985, 2),
        _row("tA3", "War Hymn", ARTIST_A, "albA", "Steel Nights", 200000, 1986, 3),
        _row("tB1", "Soft Clouds Drifting", ARTIST_B, "albB", "Calm Horizons", 420000, 2020, 1),
        _row("tB2", "Gentle Rain Falling", ARTIST_B, "albB", "Calm Horizons", 440000, 2021, 2),
        _row("tB3", "Quiet Ocean Deep", ARTIST_B, "albB", "Calm Horizons", 410000, 2021, 3),
    ]
    return pd.DataFrame(rows)
