"""Task 1: the exposed score matrix must agree with score_tracks' summary."""

from __future__ import annotations

import numpy as np

from src.analysis.features import load_features
from src.analysis.profiles import build_artist_profiles
from src.analysis.scoring import compute_score_matrix, score_tracks
from tests.fixtures import two_artist_frame


def _load(tmp_path):
    csv = tmp_path / "group.csv"
    two_artist_frame().to_csv(csv, index=False)
    features = load_features(csv)
    return features, build_artist_profiles(features)


def test_matrix_shape_matches_tracks_by_artists(tmp_path):
    features, profiles = _load(tmp_path)
    matrix, artist_ids = compute_score_matrix(features, profiles)
    assert matrix.shape == (len(features.frame), len(profiles))
    assert artist_ids == list(profiles)


def test_assigned_column_matches_summary(tmp_path):
    features, profiles = _load(tmp_path)
    matrix, artist_ids = compute_score_matrix(features, profiles)
    summary = score_tracks(features, profiles)

    assigned_ids = features.frame["artist_id"].astype(str).to_numpy()
    assigned_cols = np.array([artist_ids.index(a) for a in assigned_ids])
    assigned_from_matrix = matrix[np.arange(len(matrix)), assigned_cols]
    np.testing.assert_allclose(assigned_from_matrix, summary["assigned_score"].to_numpy())


def test_row_max_matches_best_overall_score(tmp_path):
    features, profiles = _load(tmp_path)
    matrix, _ = compute_score_matrix(features, profiles)
    summary = score_tracks(features, profiles)
    # The best score available to any track is max(assigned, best_other).
    best_overall = np.maximum(summary["assigned_score"], summary["best_other_score"]).to_numpy()
    np.testing.assert_allclose(matrix.max(axis=1), best_overall)
