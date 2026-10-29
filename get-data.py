import json
from pathlib import Path
from urllib.request import Request, urlopen

# RUN API: https://www.speedrun.com/api/v1/runs?game=v1p527d8&max=200
# USER API: https://www.speedrun.com/api/v1/users/{id}

API_URL = "https://www.speedrun.com/api/v1"
GAME_ID = "v1p527d8"
PAGE_SIZE = 200 # the maximum (speedrun.com's limit)
OUTPUT_DIR = Path(__file__).resolve().parent
RUNS_FILE = OUTPUT_DIR / "level-runs.json"
USERS_FILE = OUTPUT_DIR / "users.json"


def get_json(url):
    request = Request(url, headers={"User-Agent": "5b-level-runs-downloader"})
    with urlopen(request, timeout=30) as response:
        return json.load(response)


def fetch_level_runs():
    # fetch every run first
    next_url = f"{API_URL}/runs?game={GAME_ID}&max={PAGE_SIZE}"
    runs = []
    user_ids = []
    seen_user_ids = set()
    seen_urls = set()

    while next_url:
        if next_url in seen_urls:
            raise RuntimeError(f"URL already seen: {next_url}")
        seen_urls.add(next_url)

        page = get_json(next_url)
        for run in page["data"]:
            # this line filters out all non-IL's; if your focus is on full-game runs, you want to pass (continue) if run.get("level") is NOT None
            if run.get("level") is None:
                continue
            # filter out rejected/pending runs
            if run.get("status", {}).get("status") != "verified":
                continue

            runs.append(run)
            players = run.get("players", [])
            player_id = players[0].get("id") if players else None
            if player_id and player_id not in seen_user_ids:
                seen_user_ids.add(player_id)
                user_ids.append(player_id)

        # because we can only pull 200 runs at a time, we have to update the URL to pull the next series of runs until we read all of them
        next_url = next(
            (
                link["uri"]
                for link in page["pagination"]["links"]
                if link.get("rel") == "next"
            ),
            None,
        )

    return runs, user_ids


def fetch_users(user_ids):
    users = {}
    # fetching the users in chronological order is important so that when a new user comes in, they will be appended to the bottom rather than being inserted and shifting the entire alignment
    for index, user_id in enumerate(user_ids, start=1):
        user = get_json(f"{API_URL}/users/{user_id}")["data"]
        users[user_id] = user["names"]["international"]
        print(f"Fetched user {index}/{len(user_ids)}: {user_id}")
    return users


def write_json(path, data):
    with path.open("w", encoding="utf-8") as output:
        json.dump(data, output, indent=2, ensure_ascii=False)
        output.write("\n")


def main():
    runs, user_ids = fetch_level_runs()
    write_json(RUNS_FILE, runs)
    print(f"Saved {len(runs)} level runs to {RUNS_FILE}")

    # list of users is stored separately
    users = fetch_users(user_ids)
    write_json(USERS_FILE, users)
    print(f"Saved {len(users)} user names to {USERS_FILE}")


if __name__ == "__main__":
    main()
