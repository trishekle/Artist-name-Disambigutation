"""Task 6: headless smoke test of the Streamlit app's data-prep layer."""

from __future__ import annotations

import pytest

from src import app_core
from src.analysis import data_source
from tests.fixtures import two_artist_frame


@pytest.fixture()
def group_dir(tmp_path, monkeypatch):
    two_artist_frame().to_csv(tmp_path / "spotify_tracks_Twins.csv", index=False)
    monkeypatch.setattr(data_source, "DATA_DIR", tmp_path)
    return tmp_path


def test_list_groups_sees_fixture(group_dir):
    assert "Twins" in app_core.list_groups()


def test_prepare_group_builds_view(group_dir):
    view = app_core.prepare_group("Twins")
    assert view.summary["track_nodes"] == 6
    assert view.summary["artist_nodes"] == 2
    assert 0.0 <= view.report["agreement_rate"] <= 1.0


def test_candidates_and_track_options(group_dir):
    view = app_core.prepare_group("Twins")

    all_tracks = app_core.candidates_frame(view, only_disagreements=False)
    assert len(all_tracks) == 6

    options = app_core.track_options(view)
    assert len(options) == 6


def test_inspect_track_lists_all_artists(group_dir):
    view = app_core.prepare_group("Twins")
    # Pick any track id from the view.
    track_id = view.report["rows"][0]["track_id"]
    detail = app_core.inspect_track(view, track_id)
    assert len(detail) == 2  # scored against both artists
    assert detail["credited"].sum() == 1  # exactly one credited artist marked
    # Scores are sorted descending.
    assert list(detail["score"]) == sorted(detail["score"], reverse=True)


def test_pyvis_html_renders(group_dir):
    view = app_core.prepare_group("Twins")
    html = app_core.pyvis_html(view)
    assert isinstance(html, str)
    assert "vis-network" in html or "vis.js" in html or "<html" in html.lower()
