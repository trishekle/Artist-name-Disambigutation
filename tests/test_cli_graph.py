"""Task 5: the CLI graph mode runs end-to-end and reports agreement + candidates."""

from __future__ import annotations

import argparse

from src.analysis import outliers
from src.analysis.features import load_features
from src.analysis.profiles import build_artist_profiles
from tests.fixtures import two_artist_frame


def _args(**kw):
    base = dict(threshold=0.40, gap_threshold=0.20, compare=False)
    base.update(kw)
    return argparse.Namespace(**base)


def test_graph_mode_runs_and_reports(tmp_path, capsys):
    csv = tmp_path / "group.csv"
    two_artist_frame().to_csv(csv, index=False)
    features = load_features(csv)
    profiles = build_artist_profiles(features)

    outliers.run_graph_mode(features, profiles, _args())
    out = capsys.readouterr().out

    assert "graph mode" in out
    assert "Graph summary" in out
    assert "Agreement:" in out
    assert "Review candidates" in out


def test_threshold_mode_still_works(tmp_path, capsys):
    csv = tmp_path / "group.csv"
    two_artist_frame().to_csv(csv, index=False)
    features = load_features(csv)
    profiles = build_artist_profiles(features)

    outliers.run_threshold_mode(features, profiles, _args())
    out = capsys.readouterr().out
    assert "Same-name group" in out
    assert "potential anomalies" in out


def test_compare_flag_adds_threshold_section(tmp_path, capsys):
    csv = tmp_path / "group.csv"
    two_artist_frame().to_csv(csv, index=False)
    features = load_features(csv)
    profiles = build_artist_profiles(features)

    outliers.run_graph_mode(features, profiles, _args(compare=True))
    out = capsys.readouterr().out
    assert "[compare]" in out
