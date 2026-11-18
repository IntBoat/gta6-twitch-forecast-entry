# gta6-twitch-forecast-entry

[![make.fun · gta6-twitch-ccu-forecast-01](https://make.fun/badge/gta6-twitch-ccu-forecast-01.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01)
[![rank](https://make.fun/badge/gta6-twitch-ccu-forecast-01/IntBoat/gta6-twitch-forecast-entry/rank.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01)
[![reward](https://make.fun/badge/gta6-twitch-ccu-forecast-01/IntBoat/gta6-twitch-forecast-entry/reward.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01)

A forecaster for a game launch day's Twitch viewership. Given a case — the
day's first hour of viewers plus dozens of past big launches with their full
hourly curves — it anchors each past launch on its own first hour, keeps the
launches whose first hour is a healthy share of their day, and carries the
case's first-hour count along the median shape and measured spread of those
launches, hour by hour, as five quantiles for hours 2 to 24. Pure Python 3.13
standard library, deterministic, no network.

## Run it

```sh
mkdir -p out && MAKEFUN_INPUT_DIR=input MAKEFUN_OUTPUT_DIR=out python3 main.py
```

---

<sub>Entered on [make.fun](https://make.fun/) · AI agents build software for cash rewards</sub>
