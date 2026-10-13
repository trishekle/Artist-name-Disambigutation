"""Artist profiles, always keyed by Spotify artist ID."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import sparse

from .features import FeatureSet


@dataclass
class ArtistProfile:
    artist_id: str
    artist_name: str
    track_count: int
    indices: np.ndarray
    numeric_centroid: np.ndarray
    album_centroid: np.ndarray
    text_centroid: sparse.csr_matrix
    collaborator_centroid: sparse.csr_matrix
    statistics: dict


def build_artist_profiles(features: FeatureSet) -> dict[str, ArtistProfile]:
    profiles = {}
    for artist_id, group in features.frame.groupby("artist_id", sort=False):
        indices = group.index.to_numpy()
        raw = group
        profile = ArtistProfile(
            artist_id=str(artist_id),
            artist_name=str(raw["artist_name"].iloc[0]),
            track_count=len(indices), indices=indices,
            numeric_centroid=np.asarray(features.numeric[indices].mean(axis=0)).ravel(),
            album_centroid=np.asarray(features.album[indices].mean(axis=0)).ravel(),
            text_centroid=sparse.csr_matrix(features.text[indices].mean(axis=0)),
            collaborator_centroid=sparse.csr_matrix(features.collaborators[indices].mean(axis=0)),
            statistics={
                "mean_duration": raw["duration_ms"].mean(), "median_duration": raw["duration_ms"].median(),
                "duration_std": raw["duration_ms"].std(), "explicit_rate": raw["explicit"].astype(bool).mean(),
                "mean_track_number": raw["track_number"].mean(), "mean_album_size": raw["album_total_tracks"].mean(),
                "release_year_mean": raw["release_year"].mean(), "release_year_std": raw["release_year"].std(),
                "album_type_distribution": raw["album_type"].fillna("unknown").value_counts(normalize=True).to_dict(),
                "common_collaborators": raw["credited_artist_ids"].fillna("").str.split("|").explode().replace("", np.nan).value_counts().head(10).to_dict(),
            },
        )
        profiles[profile.artist_id] = profile
    if len(profiles) < 2:
        raise ValueError("A same-name comparison requires at least two distinct artist_id values.")
    return profiles
