"""Interactive Streamlit app for graph-based same-name artist disambiguation.

Run with:  streamlit run app.py

Pick a same-name group, see the agreement rate, explore the bipartite
track<->artist graph (pan/zoom/hover), filter to review candidates, and click a
track in the inspector to read its per-artist compatibility scores.

The agreement metric is a REVIEW SIGNAL, not proof of misattribution: there is no
ground truth, so a flagged track only means "worth a human look."
"""

from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components

from src.app_core import (
    candidates_frame,
    inspect_track,
    list_groups,
    prepare_group,
    pyvis_html,
    track_options,
)

st.set_page_config(page_title="Artist Disambiguation", layout="wide")


@st.cache_data(show_spinner=False)
def _groups():
    return list_groups()


@st.cache_resource(show_spinner="Building graph...")
def _view(name: str):
    return prepare_group(name)


st.title("Same-name artist disambiguation")
st.caption(
    "Bipartite track<->artist graph. Red track = review candidate (its best-fit "
    "artist is not the one it's credited to). A signal, not proof."
)

groups = _groups()
if not groups:
    st.error("No analyzable groups found in data/ (need >= 2 artist IDs per group).")
    st.stop()

with st.sidebar:
    st.header("Controls")
    group = st.selectbox("Same-name group", groups)
    only_candidates = st.toggle("Show only review candidates in graph", value=False)

view = _view(group)
report = view.report

col1, col2, col3 = st.columns(3)
col1.metric("Agreement rate", f"{report['agreement_rate']:.1%}")
col2.metric("Tracks", report["total_tracks"])
col3.metric("Review candidates", len(report["disagreements"]))

st.subheader("Interactive graph")
html = pyvis_html(view, only_disagreements=only_candidates)
components.html(html, height=640, scrolling=True)

left, right = st.columns([3, 2])

with left:
    st.subheader("Review candidates" if only_candidates else "All tracks")
    table = candidates_frame(view, only_disagreements=only_candidates)
    if table.empty:
        st.info("No review candidates - every track's best-fit artist is the credited one.")
    else:
        st.dataframe(table, use_container_width=True, hide_index=True)

with right:
    st.subheader("Inspect a track")
    options = track_options(view)
    if options:
        label = st.selectbox("Track", list(options.keys()))
        track_id = options[label]
        st.dataframe(
            inspect_track(view, track_id),
            use_container_width=True,
            hide_index=True,
        )
