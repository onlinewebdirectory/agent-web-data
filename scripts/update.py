"""Fetch the Online Web Directory export, validate it, and record what changed.

Standard library only. Run by .github/workflows/update.yml once a day:
    python scripts/update.py
Writes data/sites.csv and, when anything changed, changes/YYYY/YYYY-MM-DD.csv.
Refuses (exit 1, nothing written) when the export looks broken, so a bad
night can never wipe the history.
"""
import csv
import datetime
import io
import os
import re
import sys
import urllib.request

EXPORT_URL = "https://onlinewebdirectory.net/exports/sites.csv"
COLUMNS = ["host", "access_posture", "challenge_vendor", "js_required", "robots_posture",
           "machine_interface", "machine_interface_path", "checked_at"]
FACT_FIELDS = COLUMNS[1:-1]  # checked_at moving on its own is not a change
HOST = re.compile(r"^[a-z0-9-]+(\.[a-z0-9-]+)*\.[a-z0-9-]{2,}$")
MIN_ROWS = 1000
MIN_SHARE = 0.9


class Invalid(Exception):
    pass


def parse(text):
    reader = csv.reader(io.StringIO(text))
    header = next(reader, None)
    if header != COLUMNS:
        raise Invalid(f"unexpected header: {header}")
    rows = {}
    for row in reader:
        if not row:
            continue
        if len(row) != len(COLUMNS) or not HOST.match(row[0]):
            raise Invalid(f"bad row: {row[:2]}")
        rows[row[0]] = dict(zip(COLUMNS, row))
    return rows


def apply(text, snapshot_path, changes_dir, day, min_rows=MIN_ROWS):
    new = parse(text)
    if len(new) < min_rows:
        raise Invalid(f"only {len(new)} sites (need at least {min_rows})")
    old = parse(open(snapshot_path).read()) if os.path.exists(snapshot_path) else {}
    if old and len(new) < MIN_SHARE * len(old):
        raise Invalid(f"{len(new)} sites is under {int(MIN_SHARE * 100)}% of the previous {len(old)}")

    changes = []
    for host in sorted(new):
        before = old.get(host, {})
        for field in FACT_FIELDS:
            was, now = before.get(field, ""), new[host][field]
            if was != now and (before or now):
                changes.append([host, field, was, now])

    os.makedirs(os.path.dirname(snapshot_path), exist_ok=True)
    with open(snapshot_path, "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(COLUMNS)
        for host in sorted(new):
            w.writerow([new[host][c] for c in COLUMNS])

    if changes:
        path = os.path.join(changes_dir, day[:4], f"{day}.csv")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", newline="") as f:
            w = csv.writer(f, lineterminator="\n")
            w.writerow(["host", "field", "old", "new"])
            w.writerows(changes)
    return {"sites": len(new), "changes": len(changes)}


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    req = urllib.request.Request(EXPORT_URL, headers={"User-Agent": "agent-web-data-updater"})
    with urllib.request.urlopen(req, timeout=60) as res:
        text = res.read().decode("utf-8")
    day = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    try:
        result = apply(text, os.path.join(root, "data", "sites.csv"), os.path.join(root, "changes"), day)
    except Invalid as e:
        print(f"refused: {e}", file=sys.stderr)
        sys.exit(1)
    print(f"{day}: {result['sites']} sites, {result['changes']} changes")
    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a") as f:
            f.write(f"day={day}\nsites={result['sites']}\nchanges={result['changes']}\n")


if __name__ == "__main__":
    main()
