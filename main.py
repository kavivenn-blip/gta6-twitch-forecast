"""Forecast GTA VI's launch-day Twitch viewers, hour by hour.

Entry for make.fun gta6-twitch-ccu-forecast-01 (program/v1, Python 3.13 stdlib only).

Method: size-adjusted analog quantiles.
  A launch day on Twitch has a shape, and that shape depends on how big the
  launch already is in its first hour. From the case's own comparables we keep
  only the launches that unlocked at rolling midnight local time (no
  simultaneous global unlock, no early-access contamination), then, per hour
  h = 2..24, we fit a line through those launches in log space:

      ln(viewers_h / viewers_1) = a_h + b_h * ln(viewers_1)

  with the slope held inside [-0.6, 0]: the bigger hour 1, the smaller the
  later hours grow relative to it. The median forecast is the fitted value at
  this case's hour-1 print; the spread is the empirical quantiles of the
  fit's residuals, widened by 1.15 because the analog set is small.

  Two guards keep the fit honest when hour 1 lands outside the data.
  Above the analogs' hour-1 range the size adjustment is an extrapolation
  with nothing behind it, so it is blended toward the plain (unadjusted)
  median ratio, the blend weight ramping from 0 at the range edge to 50/50
  once hour 1 reaches 1.5x the largest analog. Below the range the
  adjustment is kept whole: small launches really do grow more (Wolverine
  peaked 9.09x its hour 1), and a hard 50/50 switch there cost 0.09 loss
  on the practice set. The evening median ratio (hours 14-21) never falls
  below 0.7x hour 1.

  Everything is fitted at run time from the comparables inside the case
  file, so the final case's 42 launches are used automatically. FALLBACK
  below holds the same per-hour fit constants, computed offline from the
  12 rolling-midnight launches known at build time, and is used only when
  the case carries no usable comparables.

  Deterministic: analogs are processed in name order, no randomness, no
  network, no clock. Two runs on the same case write identical bytes.
"""

import json
import math
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

INPUT_DIR = Path(os.environ.get("MAKEFUN_INPUT_DIR", "/input"))
OUTPUT_DIR = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))

LEVELS = [0.05, 0.25, 0.5, 0.75, 0.95]
# Standard normal quantiles, used only by the persistence fallback.
Z = [-1.645, -0.674, 0, 0.674, 1.645]
SIGMA = 0.15

WIDEN = 1.15          # residual spread is widened: few analogs, honest bands
SLOPE_LO = -0.6       # winsorized slope of log-ratio on log hour-1
SLOPE_HI = 0.0
MIN_FIT = 3           # analogs needed to fit one hour
MIN_HOURS = 12        # hours a launch must have to count as an analog
NIGHT = range(14, 22)  # evening peak hours
NIGHT_FLOOR = 0.7     # evening median ratio never below this

# Offline fit constants (hour -> a, b, resid q05, q25, q75, q95, raw median
# log-ratio, min ln hour-1, max ln hour-1, n analogs), fitted 2026-11-17 on
# the 12 rolling-midnight launches known at build time (8 comparables plus
# the 4 practice launches). Used only if a case has no usable comparables.
FALLBACK = {
    2: (0.079765, -0.022272, -0.253728, -0.064011, 0.088000, 0.200257, -0.164137, 10.058652, 12.807705, 12),
    3: (-0.182680, -0.018903, -0.696517, -0.219174, 0.276194, 0.338254, -0.255499, 10.058652, 12.807705, 12),
    4: (0.769449, -0.104115, -0.562007, -0.159539, 0.208948, 0.306456, -0.304826, 10.058652, 12.807705, 12),
    5: (2.020031, -0.183003, -0.385729, -0.257566, 0.294385, 0.476463, -0.160015, 10.058652, 12.807705, 12),
    6: (2.340561, -0.184252, -0.527999, -0.299284, 0.146440, 0.730145, 0.158917, 10.058652, 12.807705, 12),
    7: (2.839485, -0.225983, -0.543608, -0.396790, 0.101991, 0.993307, 0.079900, 10.058652, 12.807705, 12),
    8: (2.819481, -0.228430, -0.503212, -0.381464, 0.108369, 1.044750, 0.145911, 10.058652, 12.807705, 12),
    9: (3.988510, -0.335107, -0.512089, -0.356778, 0.103240, 1.052256, 0.114700, 10.058652, 12.807705, 12),
    10: (3.879592, -0.329900, -0.511490, -0.368541, 0.077287, 1.109962, 0.055700, 10.058652, 12.807705, 12),
    11: (4.205424, -0.358014, -0.575570, -0.362081, 0.082459, 1.108242, 0.055153, 10.058652, 12.807705, 12),
    12: (4.948419, -0.423154, -0.787233, -0.302905, 0.181000, 1.151183, 0.084608, 10.058652, 12.807705, 12),
    13: (5.188101, -0.429455, -0.660798, -0.267367, 0.118326, 1.076926, 0.195927, 10.058652, 12.807705, 12),
    14: (5.526309, -0.444500, -0.583230, -0.279668, 0.059960, 1.006476, 0.335382, 10.058652, 12.807705, 12),
    15: (5.743450, -0.449696, -0.537643, -0.321702, 0.054245, 0.912690, 0.463131, 10.058652, 12.807705, 12),
    16: (5.850203, -0.449772, -0.579969, -0.314102, 0.126674, 0.893821, 0.610784, 10.058652, 12.807705, 12),
    17: (6.087484, -0.461854, -0.692545, -0.398657, 0.361530, 0.795121, 0.692880, 10.058652, 12.807705, 12),
    18: (6.980645, -0.529314, -0.789683, -0.380967, 0.323122, 0.799843, 0.775825, 10.058652, 12.807705, 12),
    19: (6.895790, -0.518053, -0.760453, -0.381401, 0.232035, 0.789267, 0.905206, 10.058652, 12.807705, 12),
    20: (7.446530, -0.563467, -0.631975, -0.468280, 0.196447, 0.826224, 0.871709, 10.058652, 12.807705, 12),
    21: (7.767015, -0.590899, -0.556324, -0.463812, 0.158006, 0.771448, 0.859303, 10.058652, 12.807705, 12),
    22: (7.586241, -0.577420, -0.551211, -0.380233, 0.205350, 0.700929, 0.821558, 10.058652, 12.807705, 12),
    23: (6.843610, -0.519185, -0.543080, -0.315875, 0.209405, 0.663404, 0.778197, 10.058652, 12.807705, 12),
    24: (6.721324, -0.515652, -0.593493, -0.257268, 0.232498, 0.687858, 0.666000, 10.058652, 12.807705, 12),
}


def _parse_time(text):
    return datetime.fromisoformat(str(text).replace("Z", "+00:00"))


def _hour_of(day_start, at):
    return int((_parse_time(at) - _parse_time(day_start)).total_seconds() // 3600) + 1


def _curve(comp):
    """Release-day hourly viewers {hour: viewers} for hours 1..24."""
    out = {}
    day_start = comp.get("day_start")
    if not day_start:
        return out
    for pt in comp.get("hourly") or []:
        try:
            h = _hour_of(day_start, pt.get("from", ""))
            v = pt.get("viewers")
        except (TypeError, ValueError):
            continue
        if 1 <= h <= 24 and isinstance(v, (int, float)) and v > 0:
            out[h] = float(v)
    return out


def _is_analog(comp, case_name):
    """True for a rolling-midnight launch usable as an analog of GTA VI."""
    name = comp.get("name") or ""
    if not name or name == case_name or "Grand Theft Auto VI" in name:
        return False
    unlock = (comp.get("unlock") or "").lower()
    if "simultaneous" in unlock:
        return False
    tier = unlock.split("tier:")[-1][:40] if "tier:" in unlock else unlock[:40]
    if "early-access-contaminated" in unlock or "weak" in tier or "early access" in tier:
        return False
    return "midnight local" in unlock or "rolling" in unlock


def _quantile(sorted_vals, p):
    """Linear-interpolation quantile of an already sorted list."""
    if not sorted_vals:
        return 0.0
    i = p * (len(sorted_vals) - 1)
    lo = int(i)
    hi = min(lo + 1, len(sorted_vals) - 1)
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (i - lo)


def _ols(pairs):
    """Least squares y = a + b*x; slope winsorized to [SLOPE_LO, SLOPE_HI]."""
    n = len(pairs)
    mx = sum(x for x, _ in pairs) / n
    my = sum(y for _, y in pairs) / n
    sxx = sum((x - mx) ** 2 for x, _ in pairs)
    if sxx <= 0:
        return my, 0.0
    sxy = sum((x - mx) * (y - my) for x, y in pairs)
    b = max(SLOPE_LO, min(SLOPE_HI, sxy / sxx))
    return my - b * mx, b


def _fit_hour(curves, h):
    """Fit hour h from analog curves {name: {hour: viewers}}.

    Returns (a, b, rq05, rq25, rq75, rq95, raw_median, lo, hi, n) where lo/hi
    are the min/max ln hour-1 among the analogs used, or None when too few
    analogs have both hour 1 and hour h.
    """
    pairs = []
    raw = []
    for name in sorted(curves):
        c = curves[name]
        if 1 in c and h in c:
            pairs.append((math.log(c[1]), math.log(c[h] / c[1])))
            raw.append(math.log(c[h] / c[1]))
    if len(pairs) < MIN_FIT:
        return None
    a, b = _ols(pairs)
    res = sorted(y - (a + b * x) for x, y in pairs)
    rq = [_quantile(res, p) * WIDEN for p in (0.05, 0.25, 0.75, 0.95)]
    return (a, b, rq[0], rq[1], rq[2], rq[3], _quantile(sorted(raw), 0.5),
            min(x for x, _ in pairs), max(x for x, _ in pairs), len(pairs))


def _round2(x):
    """Round to 2 decimals, half up (whole numbers come back as int)."""
    s = x * 100
    w = math.floor(s)
    if s - w >= 0.5:
        w += 1
    v = w / 100
    return int(v) if float(v).is_integer() else v


def _clean(vals):
    """Clamp to (0, 1e9], round, and keep non-decreasing."""
    out = []
    prev = 0.01
    for v in vals:
        v = _round2(min(1e9, max(0.01, v)))
        if v < prev:
            v = prev
        out.append(v)
        prev = v
    return out


def _quantiles_from_fit(p1, h, fit):
    """Five quantiles for hour h from a per-hour fit tuple."""
    a, b, rq05, rq25, rq75, rq95, raw_med, lo, hi, _n = fit
    lp = math.log(p1)
    med = a + b * lp
    if lp > hi:
        # Hour 1 far above the data: the size adjustment is an extrapolation
        # with nothing behind it, so trust it less the further out we go --
        # blending toward the plain median ratio, reaching 50/50 once hour 1
        # is 1.5x the largest analog. Below the data the adjustment is kept
        # whole: small launches really do grow more (Wolverine x9.09), and a
        # hard 50/50 switch there cost 0.09 loss on the practice set.
        w = 0.5 * min(1.0, (lp - hi) / math.log(1.5))
        med = (1.0 - w) * med + w * raw_med
    if h in NIGHT and med < math.log(NIGHT_FLOOR):
        med = math.log(NIGHT_FLOOR)
    return _clean([p1 * math.exp(med + r) for r in (rq05, rq25, 0.0, rq75, rq95)])


def _baseline(p1, hours):
    """Persistence forecast: every hour stays at hour 1, widening spread."""
    return {"hours": [{"hour": h, "q": _clean(
        [p1 * math.exp(z * SIGMA * math.sqrt(h - 1)) for z in Z])} for h in hours]}


def forecast_case(case):
    """Forecast one case dict -> {"hours": [{"hour": h, "q": [...]}, ...]}."""
    hours = [row["hour"] for row in case.get("forecast") or []]
    if not hours:
        hours = list(range(2, 25))
    first = next((k for k in case.get("known") or [] if k.get("hour") == 1), None)
    if first is None or not isinstance(first.get("viewers"), (int, float)):
        return _baseline(1, hours)
    p1 = max(1.0, float(first["viewers"]))
    case_name = (case.get("game") or {}).get("name") or ""
    curves = {}
    for comp in case.get("comparables") or []:
        if _is_analog(comp, case_name):
            c = _curve(comp)
            if 1 in c and len(c) >= MIN_HOURS:
                curves[comp["name"]] = c
    rows = []
    for h in hours:
        fit = _fit_hour(curves, h) if len(curves) >= MIN_FIT else None
        if fit is None:
            fit = FALLBACK.get(h)
        if fit is None:
            q = _baseline(p1, [h])["hours"][0]["q"]
        else:
            q = _quantiles_from_fit(p1, h, fit)
        rows.append({"hour": h, "q": q})
    return {"hours": rows}


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for path in sorted(INPUT_DIR.glob("*.in")):
        case = json.loads(path.read_text(encoding="utf-8"))
        out = forecast_case(case)
        (OUTPUT_DIR / (path.stem + ".out")).write_text(
            json.dumps(out, separators=(",", ":")) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
