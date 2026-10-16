#!/usr/bin/env python3
"""repo-doctor: audit a GitHub repo for professionalism and score it 0-100.

Usage:
    python repo_doctor.py <owner>/<repo>

Example:
    python repo_doctor.py octocat/Hello-World

Uses only the Python standard library (urllib). No API token needed;
unauthenticated requests are subject to GitHub's public rate limit.
"""

import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

API_BASE = "https://api.github.com"
USER_AGENT = "repo-doctor/1.0 (+https://github.com/shouvikkkk/repo-doctor)"
REQUEST_TIMEOUT = 15
RECENT_DAYS = 180

# (key, label, max points)
CHECKS = [
    ("description", "Has a non-empty description", 15),
    ("readme", "Has a README", 25),
    ("license", "Has a LICENSE", 15),
    ("topics", "Has topics", 10),
    ("homepage", "Has a homepage/website set", 10),
    ("branch", "Default branch is main or master", 10),
    ("recent", "Pushed within the last 180 days", 15),
]

TOTAL_POINTS = sum(points for _, _, points in CHECKS)


class RepoDoctorError(Exception):
    """A user-facing failure (network, not found, rate limit)."""


def fetch_json(url):
    """GET a GitHub API URL and return the parsed JSON body.

    Raises RepoDoctorError with a clear message on any failure.
    """
    request = urllib.request.Request(
        url, headers={"User-Agent": USER_AGENT, "Accept": "application/vnd.github+json"}
    )
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            raise RepoDoctorError("repo not found (HTTP 404)")
        if exc.code == 403:
            remaining = exc.headers.get("X-RateLimit-Remaining")
            if remaining == "0":
                reset = exc.headers.get("X-RateLimit-Reset", "?")
                raise RepoDoctorError(
                    "GitHub API rate limit exceeded "
                    "(60 requests/hour for unauthenticated calls; "
                    "resets at unix time %s)" % reset
                )
            raise RepoDoctorError("access forbidden by GitHub (HTTP 403)")
        raise RepoDoctorError("GitHub API returned HTTP %d" % exc.code)
    except urllib.error.URLError as exc:
        raise RepoDoctorError("network error: %s" % exc.reason)


def readme_exists(owner, repo):
    """True if the repo has a README, False if the API says it does not.

    A 404 from the /readme endpoint simply means "no README"; other
    HTTP errors are raised as RepoDoctorError.
    """
    url = "%s/repos/%s/%s/readme" % (API_BASE, owner, repo)
    request = urllib.request.Request(
        url, headers={"User-Agent": USER_AGENT, "Accept": "application/vnd.github+json"}
    )
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT):
            return True
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return False
        if exc.code == 403 and exc.headers.get("X-RateLimit-Remaining") == "0":
            raise RepoDoctorError("GitHub API rate limit exceeded")
        raise RepoDoctorError("GitHub API returned HTTP %d" % exc.code)
    except urllib.error.URLError as exc:
        raise RepoDoctorError("network error: %s" % exc.reason)


def pushed_recently(pushed_at, days=RECENT_DAYS):
    """True if the ISO-8601 pushed_at timestamp is within the last `days`."""
    if not pushed_at:
        return False
    try:
        pushed = datetime.strptime(pushed_at, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc
        )
    except ValueError:
        return False
    return (datetime.now(timezone.utc) - pushed).days <= days


def run_checks(data, has_readme):
    """Evaluate every check against the repo JSON. Returns list of
    (label, passed, awarded, max_points)."""
    results = {
        "description": bool((data.get("description") or "").strip()),
        "readme": has_readme,
        "license": data.get("license") is not None,
        "topics": bool(data.get("topics")),
        "homepage": bool((data.get("homepage") or "").strip()),
        "branch": data.get("default_branch") in ("main", "master"),
        "recent": pushed_recently(data.get("pushed_at")),
    }
    report = []
    for key, label, points in CHECKS:
        passed = results[key]
        report.append((label, passed, points if passed else 0, points))
    return report


def verdict_for(score):
    if score >= 90:
        return "Excellent - this repo looks professional."
    if score >= 70:
        return "Good - a few polish items left."
    if score >= 40:
        return "Needs work - the basics are missing."
    return "Rough - this repo needs a full cleanup."


def print_report(full_name, report):
    score = sum(awarded for _, _, awarded, _ in report)
    print("repo-doctor: %s" % full_name)
    print("-" * 44)
    for label, passed, awarded, points in report:
        mark = "\u2713" if passed else "\u2717"
        print("%s %-38s (+%d)" % (mark, label, awarded))
    print("-" * 44)
    print("Score: %d/%d" % (score, TOTAL_POINTS))
    print("Verdict: %s" % verdict_for(score))


def parse_target(arg):
    parts = arg.split("/")
    if len(parts) != 2 or not all(p.strip() for p in parts):
        return None
    return parts[0].strip(), parts[1].strip()


def main(argv):
    if len(argv) != 2:
        print("Usage: python repo_doctor.py <owner>/<repo>", file=sys.stderr)
        print("Example: python repo_doctor.py octocat/Hello-World", file=sys.stderr)
        return 2
    target = parse_target(argv[1])
    if target is None:
        print(
            "Error: expected <owner>/<repo>, got %r" % argv[1], file=sys.stderr
        )
        print("Example: python repo_doctor.py octocat/Hello-World", file=sys.stderr)
        return 2
    owner, repo = target
    try:
        data = fetch_json("%s/repos/%s/%s" % (API_BASE, owner, repo))
        has_readme = readme_exists(owner, repo)
    except RepoDoctorError as exc:
        print("Error: %s" % exc, file=sys.stderr)
        return 1
    print_report("%s/%s" % (owner, repo), run_checks(data, has_readme))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
