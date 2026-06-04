from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
import sys

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from aco_path_planning.config import DEFAULT_OUTPUT_ROOT


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize saved experiment outputs.")
    parser.add_argument("--input-dir", default=str(DEFAULT_OUTPUT_ROOT))
    parser.add_argument("--output-file", default=str(DEFAULT_OUTPUT_ROOT / "summary.csv"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_dir = Path(args.input_dir)
    output_file = Path(args.output_file)
    rows = collect_results(input_dir)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    write_summary(output_file, rows)
    print(output_file)
    return 0


def collect_results(input_dir: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for result_file in sorted(input_dir.rglob("result.json")):
        payload = json.loads(result_file.read_text(encoding="utf-8"))
        params = payload.get("params", {})
        rows.append(
            {
                "surface": payload.get("surface"),
                "map_name": payload.get("map_name"),
                "found": payload.get("found"),
                "path_length": payload.get("path_length"),
                "best_iteration": payload.get("best_iteration"),
                "runtime_seconds": payload.get("runtime_seconds"),
                "total_successful_paths": payload.get("total_successful_paths"),
                "avg_success_count": _mean(payload.get("history_success_count", [])),
                "best_length_curve_final": _last_finite(payload.get("history_best_length", [])),
                "iteration_best_curve_final": _last_finite(
                    payload.get("history_iteration_best_length", [])
                ),
                "iteration_mean_curve_final": _last_finite(
                    payload.get("history_iteration_mean_length", [])
                ),
                "alpha": params.get("alpha"),
                "beta": params.get("beta"),
                "evaporation_rate": params.get("evaporation_rate"),
                "local_evaporation_rate": params.get("local_evaporation_rate"),
                "elite_enabled": params.get("elite_enabled"),
                "elite_weight": params.get("elite_weight"),
                "random_seed": params.get("random_seed"),
                "result_dir": str(result_file.parent),
            }
        )
    return rows


def write_summary(path: Path, rows: list[dict[str, object]]) -> None:
    fieldnames = [
        "surface",
        "map_name",
        "found",
        "path_length",
        "best_iteration",
        "runtime_seconds",
        "total_successful_paths",
        "avg_success_count",
        "best_length_curve_final",
        "iteration_best_curve_final",
        "iteration_mean_curve_final",
        "alpha",
        "beta",
        "evaporation_rate",
        "local_evaporation_rate",
        "elite_enabled",
        "elite_weight",
        "random_seed",
        "result_dir",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _mean(values: list[float | int]) -> float:
    if not values:
        return 0.0
    return float(sum(values) / len(values))


def _last_finite(values: list[float | int]) -> float | None:
    for value in reversed(values):
        if value != float("inf"):
            return float(value)
    return None


if __name__ == "__main__":
    raise SystemExit(main())
