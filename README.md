# Artist Name Disambiguation

Metadata-only tooling to spot likely **misattributed tracks** among same-name
Spotify artists. Different artists sometimes share an exact name (two "WITCH",
three "Funhouse"), and tracks occasionally get credited to the wrong one. This
project scores how well each track fits each same-name artist, reframes those
scores as a bipartite **track ↔ artist graph**, and flags tracks whose best-fit
artist is not the one they are credited to as **review candidates**.

> The output is a **review signal, not proof**. There is no ground-truth labeling
> yet, so a flagged track only means "worth a human look," not "confirmed wrong."
> Analysis uses **metadata only** (names, durations, albums, collaborators) — never
> audio.

## Demo

![Interactive graph demo](docs/Demo_v1.gif)


## Data and credentials (read first)

- **No catalog data is included in this repo.** The `data/` directory is
  git-ignored. You regenerate it yourself from the Spotify Web API.
- Spotify API credentials live in a git-ignored `.env` file and are never
  committed. Create one in the project's parent directory:

  ```
  SPOTIFY_CLIENT_ID=your_client_id
  SPOTIFY_CLIENT_SECRET=your_client_secret
  ```

- Only Spotify **metadata** is stored, for identity/catalog analysis. Do not add
  audio to this project. Keeping catalog data out of version control respects
  Spotify's API terms on storing and redistributing their data.

## Setup

```bash
pip install -r requirements.txt
```

Requires Python 3.10+.

## Generate data (ingestion)

Ingestion is keyed on verified Spotify **artist IDs**, since display names are
not unique. Produces one CSV per same-name group at `data/spotify_tracks_<name>.csv`.

```bash
# Discover the exact-name artist IDs for a name (no ingestion)
python -m src.ingestion.ingestion --discover "WITCH"

# Ingest every exact-name artist returned for a display name
python -m src.ingestion.ingestion --artist-name "WITCH"

# Or ingest from the manually verified list in data/same_name_artists.json
python -m src.ingestion.ingestion --use-verified-config
```

A group is **analyzable only if its CSV has ≥ 2 distinct artist IDs** (a single
artist has nothing to compare against).

## Run the analysis

### Interactive app (recommended)

```bash
streamlit run app.py
```

Opens in your browser. Pick a same-name group, see the **agreement rate**,
explore the interactive graph (pan / zoom / hover), filter to **review
candidates**, and click a track to inspect its per-artist scores. Big dots are
artists; small dots are tracks (red = review candidate, green = agrees).

### Command line

```bash
# Graph-based agreement report + review candidates
python -m src.analysis.outliers data/spotify_tracks_WITCH.csv --graph

# Also print the original threshold-based flags for comparison
python -m src.analysis.outliers data/spotify_tracks_WITCH.csv --graph --compare

# Original threshold mode (default, no --graph)
python -m src.analysis.outliers data/spotify_tracks_WITCH.csv
```

## How it works

| Stage | File | What it does |
|-------|------|--------------|
| Ingestion | `src/ingestion/ingestion.py` | Pull catalog metadata from Spotify, keyed by artist ID |
| Data seam | `src/analysis/data_source.py` | Single load point (CSV today, swappable for a database later) |
| Features | `src/analysis/features.py` | Interpretable metadata blocks (numeric, album, text, collaborators), leakage-aware |
| Profiles | `src/analysis/profiles.py` | Per-artist centroids and summary stats |
| Scoring | `src/analysis/scoring.py` | Track-vs-artist compatibility; full score matrix |
| Graph | `src/analysis/graph.py` | Bipartite track↔artist graph + agreement metric |
| CLI | `src/analysis/outliers.py` | Threshold mode (default) and `--graph` mode |
| App | `app.py`, `src/app_core.py` | Interactive Streamlit UI |

**Agreement metric:** a track "agrees" if its highest-scoring artist is the one
it is credited to; disagreements are review candidates, ranked by how much a
rival artist fit better (the score gap).

## Tests

```bash
python -m pytest tests -q -p no:importnb
```

(The `-p no:importnb` flag disables an unrelated third-party pytest plugin that
otherwise crashes collection in this environment.)

## Status and next steps

Tier 1 (bipartite graph + agreement metric + interactive UI) is complete. Known
limitations and planned work:

- **No ground truth.** The agreement metric is a consistency signal. The highest-
  value next step is a small hand-labeled set (correct / misattributed / unsure)
  to measure precision and recall.
- **Small catalogs.** Ingestion samples a few albums per artist; flagged gaps are
  often borderline.
- **Tier 2 (planned):** add track↔track edges (shared album / collaborators) and
  community detection for richer structure.

## License

Released under the [MIT License](LICENSE). This covers the project's code only,
not Spotify's data or API terms.
