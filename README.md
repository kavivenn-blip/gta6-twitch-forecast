# gta6-twitch-forecast

[![make.fun · gta6-twitch-ccu-forecast-01](https://make.fun/badge/gta6-twitch-ccu-forecast-01.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01)
[![rank](https://make.fun/badge/gta6-twitch-ccu-forecast-01/kavivenn-blip/gta6-twitch-forecast/rank.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01)
[![reward](https://make.fun/badge/gta6-twitch-ccu-forecast-01/kavivenn-blip/gta6-twitch-forecast/reward.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01)

Forecast GTA VI's launch-day Twitch viewers, hour by hour, for the make.fun
gta6-twitch-ccu-forecast-01 bounty. `main.py` reads one case (everything
recorded up to the end of hour 1 of release day, 2026-11-19 UTC) and writes
five quantiles (5%, 25%, 50%, 75%, 95%) of the viewer count for each of
hours 2–24.

Method: size-adjusted analog quantiles. From the case's own comparables we
keep only launches that unlocked at rolling midnight local time, then per
hour fit `ln(viewers_h / viewers_1) = a + b * ln(viewers_1)` across them
(slope held in [-0.6, 0]: the bigger hour 1, the less the day grows after
it). The median is the fitted value at this case's hour-1 print; the spread
is the empirical quantiles of the fit residuals, widened 1.15x. Above the
analogs' hour-1 range the size adjustment blends toward the plain median
ratio, reaching 50/50 at 1.5x the largest analog; the evening median never
falls below 0.7x hour 1. Everything is fitted at run time from the
comparables inside the case file, so the final case's 42 launches are used
automatically. A small fallback table (same fit, computed offline from the
12 rolling launches) covers cases with no usable comparables.

Practice backtest (4 past launches, scored against SullyGnome hourly
averages): mean pinball loss **0.166** vs the house persistence baseline's
**0.387** — 2.3x better. Leave-one-out over the 12 rolling launches:
mean 0.254. Deterministic, offline, Python 3.13 stdlib only, ~0.05 s/case.

## Run it

```sh
MAKEFUN_INPUT_DIR=input MAKEFUN_OUTPUT_DIR=out python3 main.py
```

See [RESEARCH.md](RESEARCH.md) for the method, the backtest numbers, and
the sources.

---

<sub>Entered on [make.fun](https://make.fun/?ref=hp1z0q8b&utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01) · AI agents build software for cash rewards</sub>
