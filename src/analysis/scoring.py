"""Transparent track-to-artist metadata compatibility scoring."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

from .features import FeatureSet
from .profiles import ArtistProfile

WEIGHTS = {"text": 0.30, "duration": 0.25, "release": 0.15, "collaboration": 0.30}


def _bounded_distance(values: np.ndarray, centroid: np.ndarray, columns: slice) -> np.ndarray:
    distance = np.mean(np.abs(values[:, columns] - centroid[columns]), axis=1)
    return 1.0 / (1.0 + distance)


def compute_score_matrix(
    features: FeatureSet, profiles: dict[str, ArtistProfile], weights: dict | None = None
) -> tuple[np.ndarray, list[str]]:
    """Return the full per-track x per-artist compatibility matrix and its artist-ID columns.

    ``matrix[i, j]`` is the compatibility of track ``i`` with the artist whose ID is
    ``artist_ids[j]``. Row order matches ``features.frame``; column order matches the
    insertion order of ``profiles``. This is the raw material behind both the summary
    returned by :func:`score_tracks` and the bipartite graph's track->artist edge weights.
    """
    weights = weights or WEIGHTS
    if set(weights) != set(WEIGHTS) or not np.isclose(sum(weights.values()), 1.0):
        raise ValueError("weights must contain text, duration, release, collaboration and sum to 1.")
    numeric = features.numeric.toarray()
    artist_ids = list(profiles)
    scores = np.empty((len(features.frame), len(artist_ids)))
    for column, artist_id in enumerate(artist_ids):
        profile = profiles[artist_id]
        text = cosine_similarity(features.text, profile.text_centroid).ravel()
        collaborators = (
            cosine_similarity(features.collaborators, profile.collaborator_centroid).ravel()
            if features.collaborators.shape[1] else np.zeros(len(features.frame))
        )
        duration = _bounded_distance(numeric, profile.numeric_centroid, slice(0, 1))
        # Track position, disc, album length, release year, explicit flag, and album type.
        release_numeric = _bounded_distance(numeric, profile.numeric_centroid, slice(1, None))
        album = cosine_similarity(features.album, profile.album_centroid.reshape(1, -1)).ravel()
        release = (release_numeric + album) / 2
        scores[:, column] = (weights["text"] * text + weights["duration"] * duration +
                             weights["release"] * release + weights["collaboration"] * collaborators)
    return scores, artist_ids


def score_tracks(features: FeatureSet, profiles: dict[str, ArtistProfile], weights: dict | None = None) -> pd.DataFrame:
    """Return every track's assigned versus best alternative compatibility."""
    scores, artist_ids = compute_score_matrix(features, profiles, weights)
    assigned_ids = features.frame["artist_id"].astype(str).to_numpy()
    assigned_indices = np.array([artist_ids.index(value) for value in assigned_ids])
    assigned = scores[np.arange(len(scores)), assigned_indices]
    masked = scores.copy()
    masked[np.arange(len(scores)), assigned_indices] = -np.inf
    best_indices = masked.argmax(axis=1)
    best_other = masked[np.arange(len(scores)), best_indices]
    result = features.frame[["track_id", "track_name", "artist_id", "artist_name"]].copy()
    result["assigned_score"] = assigned
    result["best_other_score"] = best_other
    result["best_other_artist_id"] = [artist_ids[index] for index in best_indices]
    result["score_gap"] = best_other - assigned
    return result
