"""Forecast a launch day's Twitch viewers, hour by hour, from past launches.

Written for make.fun's gta6-twitch-ccu-forecast-01. The program reads one case
file: a game's release day (UTC) whose first hour's viewer count is known, plus
dozens of past big launches with their full hourly curves. It forecasts hours
2..24 as five quantiles each, scored by pinball loss on the log scale.

Method: anchor every comparable launch on its own first hour, but keep only the
launches whose first hour is a healthy share of their day (at least 15% of the
day's peak). The rest have a first hour that predates any real unlock in UTC
terms, so their ratios to it explode and say nothing about a normal launch.
From the kept launches, each hour's log-ratio to hour 1 gives a median shape
and a spread; the forecast is the case's own first-hour count carried along
that shape, with normal quantiles at the measured spread.

Runs as `python3 -P -s /bot/main.py`, standard library only, no network, and
deterministic: the same case always yields the same bytes.
"""

import json
import math
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

INPUT_DIR = Path(os.environ.get("MAKEFUN_INPUT_DIR", "/input"))
OUTPUT_DIR = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))

LEVELS = [0.05, 0.25, 0.5, 0.75, 0.95]
Z = [-1.645, -0.674, 0.0, 0.674, 1.645]

# A comparable counts only if its release day is well sampled and its first
# hour is at least this share of its own day peak (a real anchor).
MIN_DAY_HOURS = 20
MIN_ANCHOR_SHARE = 0.15
# An hour needs at least this many comparable ratios before its own median
# and spread are trusted; below that, the pooled shape fills in.
MIN_HOUR_SAMPLES = 8
# The spread used for an hour's quantiles is kept inside these bounds: a
# thinner one understates how far a launch day can wander, a fatter one is
# usually a few broken anchors rather than real uncertainty.
SIGMA_FLOOR = 0.18
SIGMA_CAP = 0.90


def parse(ts):
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def median(xs):
    xs = sorted(xs)
    n = len(xs)
    return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2.0


def day_hours(comp):
    """hour (1..24) -> viewers on the comparable's release day."""
    ds = parse(comp["day_start"])
    out = {}
    for pt in comp["hourly"]:
        t = parse(pt["from"])
        if ds <= t < ds + timedelta(hours=24):
            h = int((t - ds).total_seconds() // 3600) + 1
            if pt["viewers"]:
                out[h] = float(pt["viewers"])
    return out


def comparable_pool(case):
    """Release-day curves of the comparables with a trustworthy hour 1."""
    pool = []
    for comp in case["comparables"]:
        if comp["name"] == case["game"]["name"]:
            continue
        dh = day_hours(comp)
        if 1 not in dh or len(dh) < MIN_DAY_HOURS:
            continue
        if dh[1] < MIN_ANCHOR_SHARE * max(dh.values()):
            continue
        pool.append(dh)
    return pool


def shape_and_spread(pool):
    """Per forecast hour: (median log-ratio to hour 1, its spread)."""
    shape = {}
    for h in range(2, 25):
        xs = [math.log(dh[h] / dh[1]) for dh in pool if h in dh]
        if len(xs) >= MIN_HOUR_SAMPLES:
            m = median(xs)
            var = sum((x - m) ** 2 for x in xs) / len(xs)
            sd = math.sqrt(var)
            # Cross-check with the interquartile range: if the middle half of
            # the launches spans wider than the standard deviation suggests,
            # trust the wider reading; then bound the result.
            xs_sorted = sorted(xs)
            iqr = xs_sorted[3 * len(xs) // 4] - xs_sorted[len(xs) // 4]
            sd = max(sd, 0.85 * iqr / 1.349)
            shape[h] = (m, min(max(sd, SIGMA_FLOOR), SIGMA_CAP))
    # Fill any thin hour from its neighbours so every hour has a forecast.
    for h in range(2, 25):
        if h not in shape:
            near = [shape[k] for k in (h - 1, h + 1, h - 2, h + 2) if k in shape]
            if near:
                shape[h] = (sum(s for s, _ in near) / len(near),
                            sum(s for _, s in near) / len(near))
    return shape


def baseline_quantiles(p1, h):
    """The house persistence shape, used only if no comparable is usable."""
    return [p1 * math.exp(z * 0.15 * math.sqrt(h - 1)) for z in Z]


def forecast_case(case, name):
    if case["levels"] != LEVELS:
        raise ValueError(f"{name} asks for levels {case['levels']}, not {LEVELS}")
    first = next((k for k in case["known"] if k["hour"] == 1), None)
    if first is None:
        raise ValueError(f"{name} has no hour-1 print")
    p1 = max(1.0, float(first["viewers"]))
    pool = comparable_pool(case)
    shape = shape_and_spread(pool) if pool else {}
    rows = []
    for row in case["forecast"]:
        h = row["hour"]
        if h in shape:
            m, sd = shape[h]
            qs = [p1 * math.exp(m + z * sd) for z in Z]
        else:
            qs = baseline_quantiles(p1, h)
        qs = [round(min(max(q, 0.01), 1e9), 2) for q in qs]
        qs = [int(q) if float(q).is_integer() else q for q in qs]
        rows.append({"hour": h, "q": qs})
    return {"hours": rows}


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for path in sorted(INPUT_DIR.glob("*.in")):
        case = json.loads(path.read_text(encoding="utf-8"))
        forecast = forecast_case(case, path.name)
        (OUTPUT_DIR / f"{path.stem}.out").write_text(
            json.dumps(forecast, separators=(",", ":")) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
