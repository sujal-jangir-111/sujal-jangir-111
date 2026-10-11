#!/usr/bin/env python3
"""Download the contribution activity graph and tidy its x-axis.

The hosted graph prints a date under every day, which crowds the axis for a
90-day window, so only every Nth label is kept.

Usage: python scripts/activity_graph.py <output.svg> [label_step]
"""

import re
import sys
import urllib.request
from urllib.parse import urlencode

USERNAME = "sujal-jangir-111"

PARAMS = {
    "username": USERNAME,
    "bg_color": "1a1b27",   # Tokyo Night, matches the stats cards
    "color": "7aa2f7",
    "line": "bb9af7",
    "point": "7aa2f7",
    "area": "true",
    "area_color": "bb9af7",
    "hide_border": "true",
    "days": "90",
    "height": "280",
}
GRAPH_URL = "https://github-readme-activity-graph.vercel.app/graph?" + urlencode(PARAMS)

X_LABEL = re.compile(r'(<text[^>]*class="ct-label ct-horizontal ct-end"[^>]*>)[^<]*(</text>)')


def thin_labels(svg: str, step: int) -> str:
    count = 0

    def keep_every_nth(match: re.Match) -> str:
        nonlocal count
        keep = count % step == 0
        count += 1
        return match.group(0) if keep else match.group(1) + match.group(2)

    return X_LABEL.sub(keep_every_nth, svg)


def main() -> None:
    out = sys.argv[1] if len(sys.argv) > 1 else "github-activity-graph.svg"
    step = int(sys.argv[2]) if len(sys.argv) > 2 else 5

    req = urllib.request.Request(GRAPH_URL, headers={"User-Agent": "profile-readme"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        svg = resp.read().decode("utf-8")

    if "<svg" not in svg:
        sys.exit("Activity graph service did not return an SVG")

    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(thin_labels(svg, step))
    print(f"Wrote {out} (x-axis label every {step} days)")


if __name__ == "__main__":
    main()
