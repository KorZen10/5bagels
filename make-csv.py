import csv
import json
from pathlib import Path


DATA_DIR = Path(__file__).resolve().parent
RUNS_FILE = DATA_DIR / "level-runs.json"
LEVELS_FILE = DATA_DIR / "5b-levels.json"
USERS_FILE = DATA_DIR / "users.json"

# These are specifically the category ID's for finish% and complete%
CATEGORIES = {
    "ndxp80v2": "finish",
    "w201z5ok": "complete",
}


def load_json(path):
    with path.open("r", encoding="utf-8") as source:
        return json.load(source)

# not gonna lie, this whole thing was written by Copilot lol
# the weblink stuff is the URL for the video, since 5blazers also has fields for that
def build_csv_rows(category, runs, levels, users):
    level_ids = [level["id"] for level in levels]
    level_names = [level["name"] for level in levels]
    user_names = users.items()

    best_runs = {}
    for run in runs:
        if run.get("level") is None or run.get("category") != category:
            continue

        players = run.get("players", [])
        player_id = players[0].get("id") if players else None
        primary_time = run.get("times", {}).get("primary_t")
        if player_id is None or primary_time is None:
            continue
        if player_id not in users:
            raise ValueError(f"Run {run.get('id')} has unknown user ID {player_id}")

        key = (player_id, run["level"])
        current = best_runs.get(key)
        if current is None or primary_time < current["time"]:
            best_runs[key] = {
                "time": primary_time,
                "weblink": run.get("weblink", ""),
            }

    minimum_times = {}
    for (player_id, level_id), run in best_runs.items():
        current_minimum = minimum_times.get(level_id)
        if current_minimum is None or run["time"] < current_minimum:
            minimum_times[level_id] = run["time"]

    rows = [
        ["MIN:"]
        + [minimum_times.get(level_id, "") for level_id in level_ids]
        + [""] * len(level_ids),
        [""] + level_names + level_names,
    ]

    for player_id, player_name in user_names:
        rows.append(
            [player_name]
            + [
                best_runs.get((player_id, level_id), {}).get("time", "")
                for level_id in level_ids
            ]
            + [
                best_runs.get((player_id, level_id), {}).get("weblink", "")
                for level_id in level_ids
            ]
        )

    return rows


def main():
    runs = load_json(RUNS_FILE)
    levels = load_json(LEVELS_FILE)
    users = load_json(USERS_FILE)

    for category_id, category_name in CATEGORIES.items():
        rows = build_csv_rows(category_id, runs, levels, users)
        output_file = DATA_DIR / f"times-{category_name}.csv"
        with output_file.open("w", newline="", encoding="utf-8") as output:
            csv.writer(output).writerows(rows)

        print(f"Saved {len(rows) - 2} users to {output_file}")


if __name__ == "__main__":
    main()