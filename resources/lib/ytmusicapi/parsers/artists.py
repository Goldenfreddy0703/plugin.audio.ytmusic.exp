from ytmusicapi.navigation import *
from typing import List, Dict, Any


def parse_artists_runs(runs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Returns artist names and IDs. Skips every other run to avoid separators."""
    artists = []
    for j in range(int(len(runs) / 2) + 1):
        artists.append({"name": runs[j * 2]["text"], "id": nav(runs[j * 2], NAVIGATION_BROWSE_ID, True)})
    return artists
