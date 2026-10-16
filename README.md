# repo-doctor

A CLI that audits any GitHub repo for professionalism and scores it 0-100.

## Install

No dependencies. Python 3 only — it uses `urllib` from the standard library.

```bash
git clone https://github.com/shouvikkkk/repo-doctor.git
cd repo-doctor
```

## Usage

```bash
python repo_doctor.py <owner>/<repo>
```

Real example:

```bash
$ python repo_doctor.py octocat/Hello-World
repo-doctor: octocat/Hello-World
--------------------------------------------
✓ Has a non-empty description            (+15)
✓ Has a README                           (+25)
✗ Has a LICENSE                          (+0)
✗ Has topics                             (+0)
✗ Has a homepage/website set             (+0)
✓ Default branch is main or master       (+10)
✗ Pushed within the last 180 days        (+0)
--------------------------------------------
Score: 50/100
Verdict: Needs work - the basics are missing.
```

## What it checks

| Check | Points |
|---|---|
| Has a non-empty description | 15 |
| Has a README | 25 |
| Has a LICENSE | 15 |
| Has topics | 10 |
| Has a homepage/website set | 10 |
| Default branch is `main` or `master` | 10 |
| Pushed within the last 180 days | 15 |
| **Total** | **100** |

Verdicts: 90+ Excellent · 70–89 Good · 40–69 Needs work · 0–39 Rough.

Errors are reported plainly: a missing repo prints `Error: repo not found (HTTP 404)`, network failures print the cause, and a hit API rate limit tells you when it resets. No API token is required (60 requests/hour unauthenticated).

## License

MIT — see [LICENSE](LICENSE).
