#!/usr/bin/env python3
"""Scrape a user's public contribution calendar into JSON.

Reads the contribution grid off the public profile page, so it needs no token
and no third-party stats service. Falls back to the GraphQL API when a token
is present in GITHUB_TOKEN, which is more reliable but requires auth.

    python3 scripts/fetch_contributions.py --user Ner04 --output data/contributions.json
"""

import argparse
import json
import os
import sys
from datetime import date, datetime, timedelta, timezone

import requests
from bs4 import BeautifulSoup

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) profile-readme-builder"


def fetch_html(user, year_from, year_to):
    """Pull the contribution grid from the public profile page."""
    days = {}
    session = requests.Session()
    session.headers.update({"User-Agent": UA,
                            "X-Requested-With": "XMLHttpRequest"})

    for year in range(year_from, year_to + 1):
        url = (f"https://github.com/users/{user}/contributions"
               f"?from={year}-01-01&to={year}-12-31")
        resp = session.get(url, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Current markup keeps the count in a sibling <tool-tip for="cell-id">
        # rather than on the cell itself, so index those by target id first.
        tooltips = {t.get("for"): t.get_text(" ", strip=True)
                    for t in soup.select("tool-tip") if t.get("for")}

        for cell in soup.select("td.ContributionCalendar-day"):
            day = cell.get("data-date")
            if not day:
                continue

            count = cell.get("data-count")  # older markup
            if count is None:
                text = tooltips.get(cell.get("id"), "")
                first = text.split(" ", 1)[0].replace(",", "")
                # "No contributions on ..." vs "12 contributions on ..."
                count = first if first.isdigit() else 0

            days[day] = int(count or 0)

    return days


def fetch_graphql(user, token, year_from, year_to):
    """Authenticated path - exact counts, no scraping."""
    query = """
    query($login:String!, $from:DateTime!, $to:DateTime!) {
      user(login:$login) {
        contributionsCollection(from:$from, to:$to) {
          contributionCalendar {
            weeks { contributionDays { date contributionCount } }
          }
        }
      }
    }"""
    days = {}
    for year in range(year_from, year_to + 1):
        resp = requests.post(
            "https://api.github.com/graphql",
            headers={"Authorization": f"bearer {token}"},
            json={"query": query, "variables": {
                "login": user,
                "from": f"{year}-01-01T00:00:00Z",
                "to": f"{year}-12-31T23:59:59Z"}},
            timeout=30,
        )
        resp.raise_for_status()
        payload = resp.json()
        if "errors" in payload:
            raise RuntimeError(f"GraphQL error: {payload['errors']}")
        calendar = (payload["data"]["user"]["contributionsCollection"]
                    ["contributionCalendar"])
        for week in calendar["weeks"]:
            for d in week["contributionDays"]:
                days[d["date"]] = d["contributionCount"]
    return days


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--user", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--weeks", type=int, default=53,
                   help="how many trailing weeks to keep (default: 53)")
    p.add_argument("--force-scrape", action="store_true",
                   help="ignore GITHUB_TOKEN and scrape the public page")
    args = p.parse_args()

    today = date.today()
    start = today - timedelta(weeks=args.weeks)
    token = None if args.force_scrape else os.environ.get("GITHUB_TOKEN")

    days, source = None, None
    if token:
        try:
            days = fetch_graphql(args.user, token, start.year, today.year)
            source = "graphql"
        except Exception as exc:
            # A bad or under-scoped token should not break the daily refresh;
            # the public page carries the same data.
            print(f"GraphQL failed ({exc}) - falling back to scrape",
                  file=sys.stderr)

    if days is None:
        days = fetch_html(args.user, start.year, today.year)
        source = "scrape"

    # Keep only the trailing window, and align the grid to start on a Sunday
    # so columns line up as weeks the way GitHub renders them.
    grid_start = start - timedelta(days=(start.weekday() + 1) % 7)
    series = []
    cursor = grid_start
    while cursor <= today:
        key = cursor.isoformat()
        series.append({"date": key, "count": days.get(key, 0)})
        cursor += timedelta(days=1)

    total = sum(d["count"] for d in series)
    payload = {
        "user": args.user,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": source,
        "start": series[0]["date"],
        "end": series[-1]["date"],
        "total": total,
        "days": series,
    }

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(payload, f, indent=1)

    active = sum(1 for d in series if d["count"])
    print(f"wrote {args.output}: {len(series)} days via {source}, "
          f"{total} contributions across {active} active days")
    if total == 0:
        print("warning: zero contributions found - the scrape may have missed "
              "the grid markup", file=sys.stderr)


if __name__ == "__main__":
    main()
