"""Headless data-prep for the Streamlit app.

All non-UI logic lives here so it can be unit-tested without a browser. The
Streamlit shell (``app.py``) only arranges widgets and calls these functions.
Everything loads through the ``data_source`` seam, so a future Postgres backend
reaches the UI with no changes here.
"""

from __future__ import annotations

from dataclasses import dataclass

import networkx as nx
import pandas as pd

from .analysis import data_source
from .analysis.graph import (
    ARTIST_NODE,
    TRACK_NODE,
    agreement_report,
    build_bipartite_graph,
    track_node_id,
    track_scores,
)
from .analysis.profiles import build_artist_profiles


@dataclass
class GroupView:
    """Everything the UI needs for one same-name group."""

    name: str
    graph: nx.Graph
    report: dict
    profiles: dict
    summary: dict


def list_groups() -> list[str]:
    """Analyzable group names (>= 2 artist IDs), via the data-source seam."""
    return data_source.available_groups()


def prepare_group(name: str) -> GroupView:
    """Load one group and run the full Tier 1 pipeline into a UI-ready view."""
    features = data_source.load_group(name)
    profiles = build_artist_profiles(features)
    graph = build_bipartite_graph(features, profiles)
    report = agreement_report(graph)
    from .analysis.graph import graph_summary

    return GroupView(
        name=name,
        graph=graph,
        report=report,
        profiles=profiles,
        summary=graph_summary(graph),
    )


def candidates_frame(view: GroupView, only_disagreements: bool) -> pd.DataFrame:
    """Table of tracks, optionally filtered to review candidates, ranked by gap."""
    rows = view.report["disagreements"] if only_disagreements else view.report["rows"]
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    columns = ["track_name", "credited_artist_id", "best_fit_artist_id",
               "credited_score", "best_fit_score", "gap", "agrees"]
    present = [c for c in columns if c in frame.columns]
    return frame[present].sort_values("gap", ascending=False).reset_index(drop=True)


def track_options(view: GroupView) -> dict[str, str]:
    """Map a human label -> track_id for the inspector select box."""
    options = {}
    for row in view.report["rows"]:
        flag = "  (review)" if not row["agrees"] else ""
        options[f"{row['track_name']}{flag}"] = row["track_id"]
    return options


def inspect_track(view: GroupView, track_id: str) -> pd.DataFrame:
    """Per-artist scores for one track, with the credited artist marked."""
    scores = track_scores(view.graph, track_id)
    credited = view.graph.nodes[track_node_id(track_id)]["credited_artist_id"]
    rows = [
        {
            "artist_id": artist_id,
            "artist_name": view.profiles[artist_id].artist_name if artist_id in view.profiles else artist_id,
            "score": score,
            "credited": artist_id == credited,
        }
        for artist_id, score in scores.items()
    ]
    return pd.DataFrame(rows).sort_values("score", ascending=False).reset_index(drop=True)


def pyvis_html(view: GroupView, only_disagreements: bool = False, height: str = "600px") -> str:
    """Render the bipartite graph to standalone interactive HTML via pyvis.

    Artist nodes are large and blue; track nodes that agree are green, review
    candidates are red and slightly larger so they stand out. Edge width scales
    with compatibility score. Returns the HTML string for ``components.html``.
    """
    from pyvis.network import Network

    net = Network(height=height, width="100%", bgcolor="#ffffff", font_color="#222222", notebook=False)
    net.barnes_hut()

    disagree_ids = {r["track_id"] for r in view.report["disagreements"]}
    graph = view.graph

    for node, data in graph.nodes(data=True):
        if data.get("type") == ARTIST_NODE:
            net.add_node(
                node,
                label=data["artist_name"],
                title=f"Artist {data['artist_id']}\n{data['track_count']} tracks",
                color="#1f77b4",
                shape="dot",
                size=30,
            )
        else:
            tid = data["track_id"]
            is_candidate = tid in disagree_ids
            if only_disagreements and not is_candidate:
                continue
            net.add_node(
                node,
                label=data["track_name"],
                title=f"{data['track_name']}\ncredited: {data['credited_artist_id']}",
                color="#d62728" if is_candidate else "#2ca02c",
                shape="dot",
                size=16 if is_candidate else 10,
            )

    present = set(net.get_nodes())
    for u, v, edata in graph.edges(data=True):
        if u in present and v in present:
            weight = edata["weight"]
            net.add_edge(u, v, value=weight, title=f"score {weight:.3f}")

    net.set_options(
        '{"physics": {"stabilization": {"iterations": 150}}, '
        '"interaction": {"hover": true, "navigationButtons": true, "tooltipDelay": 100}}'
    )
    return net.generate_html(notebook=False)
