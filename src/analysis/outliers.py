"""CLI for cautious, metadata-only potential-anomaly review.

Two modes:
  * default   - threshold rules on compatibility scores (original behavior).
  * --graph   - reframe scoring as a bipartite track<->artist graph and report an
                agreement metric plus review candidates (Tier 1).
Both are review signals, not proof of misattribution.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from .data_source import load_group
from .graph import agreement_report, build_bipartite_graph, graph_summary
from .profiles import build_artist_profiles
from .scoring import score_tracks

OUTLIER_THRESHOLD = 0.40
MIN_SCORE_GAP = 0.20


def find_outliers(scores, threshold=OUTLIER_THRESHOLD, gap_threshold=MIN_SCORE_GAP):
    result = scores.copy()
    result["is_outlier"] = ((result["assigned_score"] < threshold) &
                            (result["score_gap"] > gap_threshold))
    return result.sort_values(["is_outlier", "score_gap"], ascending=[False, False])


def _print_profiles(profiles) -> None:
    print("Artist profiles:")
    for profile in profiles.values():
        print(f"- {profile.artist_id}: {profile.track_count} tracks")


def run_threshold_mode(features, profiles, args) -> None:
    scores = find_outliers(score_tracks(features, profiles), args.threshold, args.gap_threshold)
    group_name = features.frame["artist_name"].iloc[0]
    print(f"=== Same-name group: {group_name} ===\n")
    _print_profiles(profiles)
    print("\nTop potential anomalies (metadata signals; not proof of misattribution):")
    columns = ["track_name", "artist_id", "assigned_score", "best_other_artist_id",
               "best_other_score", "score_gap", "is_outlier"]
    print(scores[columns].head(20).to_string(index=False))


def run_graph_mode(features, profiles, args) -> None:
    graph = build_bipartite_graph(features, profiles)
    summary = graph_summary(graph)
    report = agreement_report(graph)
    group_name = features.frame["artist_name"].iloc[0]

    print(f"=== Same-name group: {group_name} (graph mode) ===\n")
    _print_profiles(profiles)
    print(
        f"\nGraph summary:\n  track nodes: {summary['track_nodes']} | "
        f"artist nodes: {summary['artist_nodes']} | edges: {summary['edges']}"
    )
    print(
        f"\nAgreement: {report['agree_count']}/{report['total_tracks']} tracks "
        f"({report['agreement_rate']:.1%}) match their credited artist"
    )

    disagreements = report["disagreements"]
    print(
        "\nReview candidates (credited artist disagrees with best-fit artist; "
        "signal, not proof):"
    )
    if not disagreements:
        print("  none - every track's best-fit artist is the one it is credited to.")
    else:
        table = pd.DataFrame(disagreements)[
            ["track_name", "credited_artist_id", "best_fit_artist_id",
             "credited_score", "best_fit_score", "gap"]
        ]
        print(table.head(20).to_string(index=False))

    if args.compare:
        scores = find_outliers(score_tracks(features, profiles), args.threshold, args.gap_threshold)
        flagged = scores[scores["is_outlier"]]
        print(f"\n[compare] threshold-mode flagged {len(flagged)} track(s) "
              f"(assigned<{args.threshold}, gap>{args.gap_threshold}):")
        if flagged.empty:
            print("  none.")
        else:
            print(flagged[["track_name", "artist_id", "assigned_score", "score_gap"]]
                  .head(20).to_string(index=False))


def main() -> None:
    parser = argparse.ArgumentParser(description="Find metadata-only potential same-name artist anomalies.")
    parser.add_argument("csv_path", type=Path, help="group CSV path or group name")
    parser.add_argument("--graph", action="store_true", help="use the bipartite-graph agreement mode")
    parser.add_argument("--compare", action="store_true",
                        help="in graph mode, also print the threshold-mode flags for comparison")
    parser.add_argument("--threshold", type=float, default=OUTLIER_THRESHOLD)
    parser.add_argument("--gap-threshold", type=float, default=MIN_SCORE_GAP, dest="gap_threshold")
    args = parser.parse_args()

    features = load_group(args.csv_path)
    profiles = build_artist_profiles(features)
    if args.graph:
        run_graph_mode(features, profiles, args)
    else:
        run_threshold_mode(features, profiles, args)


if __name__ == "__main__":
    main()
