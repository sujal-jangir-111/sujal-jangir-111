#!/usr/bin/env python3
"""Draw a contribution activity graph (last N days) as an SVG.

Reads daily contribution counts from the GitHub GraphQL API, so it needs no
third-party service. Runs inside the profile workflow with GITHUB_TOKEN.

Usage: python scripts/activity_graph.py <user> <output.svg> [days]
"""

import datetime as dt
import json
import os
import sys
import urllib.request

# Tokyo Night, matching the stats cards
BG, GRID, TEXT, TITLE = "#1a1b27", "#2a2e42", "#a9b1d6", "#7aa2f7"
LINE, AREA, POINT = "#bb9af7", "#bb9af7", "#7aa2f7"

QUERY = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar { weeks { contributionDays { date contributionCount } } }
    }
  }
}"""


def fetch_counts(user: str, days: int) -> list[tuple[dt.date, int]]:
    token = os.environ["GITHUB_TOKEN"]
    today = dt.datetime.now(dt.timezone.utc).date()
    start = today - dt.timedelta(days=days - 1)
    body = json.dumps({"query": QUERY, "variables": {
        "login": user,
        "from": f"{start}T00:00:00Z",
        "to": f"{today}T23:59:59Z",
    }}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql", data=body,
        headers={"Authorization": f"bearer {token}", "User-Agent": "profile-readme"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.load(resp)
    if "errors" in data:
        sys.exit(f"GitHub API error: {data['errors']}")
    weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    by_day = {d["date"]: d["contributionCount"] for w in weeks for d in w["contributionDays"]}
    return [(start + dt.timedelta(i), by_day.get(str(start + dt.timedelta(i)), 0))
            for i in range(days)]


def render(user_label: str, series: list[tuple[dt.date, int]]) -> str:
    W, H = 1200, 320
    left, right, top, bottom = 70, 30, 70, 50
    pw, ph = W - left - right, H - top - bottom
    counts = [c for _, c in series]
    peak = max(counts)
    step = max(1, -(-peak // 4))            # 4 gridlines, nice integer steps
    ymax = step * 4
    n = len(series)

    def x(i): return left + pw * i / (n - 1)
    def y(v): return top + ph - ph * v / ymax

    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
           f'viewBox="0 0 {W} {H}" font-family="Segoe UI, Ubuntu, sans-serif">',
           f'<defs><linearGradient id="fill" x1="0" y1="0" x2="0" y2="1">'
           f'<stop offset="0" stop-color="{AREA}" stop-opacity="0.45"/>'
           f'<stop offset="1" stop-color="{AREA}" stop-opacity="0.02"/></linearGradient></defs>',
           f'<rect width="{W}" height="{H}" rx="10" fill="{BG}"/>',
           f'<text x="{W/2}" y="40" text-anchor="middle" font-size="22" font-weight="600" '
           f'fill="{TITLE}">{user_label}\'s Contribution Graph</text>']

    for k in range(5):                      # horizontal grid + y labels
        v = step * k
        out.append(f'<line x1="{left}" x2="{W-right}" y1="{y(v):.1f}" y2="{y(v):.1f}" '
                   f'stroke="{GRID}" stroke-width="1"/>')
        out.append(f'<text x="{left-12}" y="{y(v)+5:.1f}" text-anchor="end" '
                   f'font-size="13" fill="{TEXT}">{v}</text>')

    for i, (day, _) in enumerate(series):   # x labels every 5 days
        if i % 5 == 0 or i == n - 1:
            out.append(f'<text x="{x(i):.1f}" y="{H-bottom+25}" text-anchor="middle" '
                       f'font-size="12" fill="{TEXT}">{day.day} {day.strftime("%b")}</text>')

    pts = " ".join(f"{x(i):.1f},{y(c):.1f}" for i, c in enumerate(counts))
    out.append(f'<polygon points="{left},{y(0):.1f} {pts} {W-right},{y(0):.1f}" fill="url(#fill)"/>')
    out.append(f'<polyline points="{pts}" fill="none" stroke="{LINE}" stroke-width="2.5" '
               f'stroke-linejoin="round" stroke-linecap="round"/>')
    for i, c in enumerate(counts):
        out.append(f'<circle cx="{x(i):.1f}" cy="{y(c):.1f}" r="3.5" fill="{POINT}">'
                   f'<title>{series[i][0]}: {c} contributions</title></circle>')

    out.append(f'<text x="{W-right}" y="{H-8}" text-anchor="end" font-size="12" '
               f'fill="{TEXT}">Contributions · last {n} days</text>')
    out.append("</svg>")
    return "\n".join(out)


def main() -> None:
    user, out = sys.argv[1], sys.argv[2]
    days = int(sys.argv[3]) if len(sys.argv) > 3 else 60
    series = fetch_counts(user, days)
    with open(out, "w", encoding="utf-8") as f:
        f.write(render("Sujal Jangir", series))
    print(f"Wrote {out}: {sum(c for _, c in series)} contributions in {days} days")


if __name__ == "__main__":
    main()
