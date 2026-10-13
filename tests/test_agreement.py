"""Task 4: agreement metric and review-candidate ranking."""

from __future__ import annotations

import networkx as nx

from src.analysis.features import load_features
from src.analysis.graph import (
    ARTIST_NODE,
    TRACK_NODE,
    agreement_report,
    artist_node_id,
    build_bipartite_graph,
    track_node_id,
)
from src.analysis.profiles import build_artist_profiles
from tests.fixtures import two_artist_frame


def _synthetic_graph(flip: bool) -> nx.Graph:
    """Two artists, three tracks each credited correctly. If flip, one track's
    weights favor the wrong artist."""
    g = nx.Graph()
    for a in ("A", "B"):
        g.add_node(artist_node_id(a), type=ARTIST_NODE, artist_id=a, artist_name=a, track_count=3)
    specs = [
        ("t1", "A", {"A": 0.9, "B": 0.1}),
        ("t2", "A", {"A": 0.8, "B": 0.2}),
        ("t3", "A", {"A": 0.7, "B": 0.3}),
        ("t4", "B", {"A": 0.2, "B": 0.9}),
        ("t5", "B", {"A": 0.1, "B": 0.8}),
        ("t6", "B", {"A": 0.3, "B": 0.7}),
    ]
    if flip:
        # t3 is credited to A but now scores much higher for B.
        specs[2] = ("t3", "A", {"A": 0.2, "B": 0.95})
    for tid, credited, w in specs:
        tnode = track_node_id(tid)
        g.add_node(tnode, type=TRACK_NODE, track_id=tid, track_name=tid, credited_artist_id=credited)
        for artist_id, weight in w.items():
            g.add_edge(tnode, artist_node_id(artist_id), weight=weight)
    return g


def test_all_match_is_full_agreement():
    report = agreement_report(_synthetic_graph(flip=False))
    assert report["total_tracks"] == 6
    assert report["agree_count"] == 6
    assert report["agreement_rate"] == 1.0
    assert report["disagreements"] == []


def test_single_flip_is_sole_disagreement():
    report = agreement_report(_synthetic_graph(flip=True))
    assert report["agreement_rate"] == 5 / 6
    assert len(report["disagreements"]) == 1
    d = report["disagreements"][0]
    assert d["track_id"] == "t3"
    assert d["credited_artist_id"] == "A"
    assert d["best_fit_artist_id"] == "B"
    assert d["gap"] > 0


def test_real_group_report_runs(tmp_path):
    csv = tmp_path / "group.csv"
    two_artist_frame().to_csv(csv, index=False)
    features = load_features(csv)
    profiles = build_artist_profiles(features)
    report = agreement_report(build_bipartite_graph(features, profiles))
    assert report["total_tracks"] == len(features.frame)
    assert 0.0 <= report["agreement_rate"] <= 1.0
    # The fixture's two artists are cleanly separated, so agreement should be high.
    assert report["agreement_rate"] >= 0.8
