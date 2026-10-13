"""Task 3: the bipartite graph must mirror the score matrix exactly."""

from __future__ import annotations

from src.analysis.features import load_features
from src.analysis.graph import (
    ARTIST_NODE,
    TRACK_NODE,
    artist_node_id,
    build_bipartite_graph,
    graph_summary,
    track_node_id,
)
from src.analysis.profiles import build_artist_profiles
from src.analysis.scoring import compute_score_matrix
from tests.fixtures import two_artist_frame


def _build(tmp_path):
    csv = tmp_path / "group.csv"
    two_artist_frame().to_csv(csv, index=False)
    features = load_features(csv)
    profiles = build_artist_profiles(features)
    return features, profiles, build_bipartite_graph(features, profiles)


def test_node_counts_match(tmp_path):
    features, profiles, graph = _build(tmp_path)
    summary = graph_summary(graph)
    assert summary["track_nodes"] == len(features.frame)
    assert summary["artist_nodes"] == len(profiles)
    assert summary["edges"] == len(features.frame) * len(profiles)


def test_every_edge_crosses_track_and_artist(tmp_path):
    _, _, graph = _build(tmp_path)
    for u, v in graph.edges():
        types = {graph.nodes[u]["type"], graph.nodes[v]["type"]}
        assert types == {TRACK_NODE, ARTIST_NODE}


def test_edge_weights_match_matrix(tmp_path):
    features, profiles, graph = _build(tmp_path)
    matrix, artist_ids = compute_score_matrix(features, profiles)
    track_ids = features.frame["track_id"].astype(str).to_numpy()
    for row, track_id in enumerate(track_ids):
        for col, artist_id in enumerate(artist_ids):
            w = graph[track_node_id(track_id)][artist_node_id(artist_id)]["weight"]
            assert abs(w - matrix[row, col]) < 1e-9
