"""Task 2: the data-source seam must match direct load_features, and list groups."""

from __future__ import annotations

import numpy as np

from src.analysis import data_source
from src.analysis.features import load_features
from tests.fixtures import two_artist_frame


def test_load_group_matches_direct_load(tmp_path):
    csv = tmp_path / "spotify_tracks_Twins.csv"
    two_artist_frame().to_csv(csv, index=False)

    via_seam = data_source.load_group(csv)
    direct = load_features(csv)

    assert via_seam.frame.equals(direct.frame)
    assert via_seam.numeric.shape == direct.numeric.shape
    np.testing.assert_allclose(via_seam.numeric.toarray(), direct.numeric.toarray())
    assert via_seam.text.shape == direct.text.shape


def test_available_groups_filters_single_id(tmp_path, monkeypatch):
    # One analyzable (2 IDs) and one single-ID group.
    two = two_artist_frame()
    two.to_csv(tmp_path / "spotify_tracks_Twins.csv", index=False)
    solo = two[two["artist_id"] == two["artist_id"].iloc[0]]
    solo.to_csv(tmp_path / "spotify_tracks_Solo.csv", index=False)

    monkeypatch.setattr(data_source, "DATA_DIR", tmp_path)
    groups = data_source.available_groups()
    assert "Twins" in groups
    assert "Solo" not in groups


def test_available_groups_on_real_data():
    # Known from the repo's shipped CSVs: Funhouse and WITCH are analyzable.
    groups = data_source.available_groups()
    assert "Funhouse" in groups
    assert "WITCH" in groups
    assert "Dio" not in groups  # single artist_id in its CSV
