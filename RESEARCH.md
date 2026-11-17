# RESEARCH.md — gta6-twitch-ccu-forecast-01

Entry: `gta6-twitch-forecast` (v1). Forecast GTA VI's launch-day Twitch
viewers (category 1867279146), hours 2–24 of 2026-11-19 UTC, as five
quantiles per hour. Scored by mean pinball loss on the log scale; a prize
needs a loss strictly below the best house entry (baseline ~0.387 on
practice; the house model forecast's loss is unknown).

## Sources

- Case files in the bounty kit (`input/p00.in`–`p03.in`): 38 comparables
  each (SullyGnome hourly Twitch category averages, 14 days before to
  3 days after each launch's release day). The program reads these at
  run time; nothing is downloaded at run time.
- Practice answers: the same public SullyGnome endpoint documented in the
  kit's `input/NOTICE.txt`, fetched once for the 4 practice launches
  (4 small requests, as NOTICE asks — no bulk download).
- Public context (scale priors only, not model inputs): GTA VI Trailer 1
  (93M views/24h), Trailer 2 (475M views/24h cross-platform), Extended
  Look premiere 2026-08-27 (1.4M peak category viewers); previous
  single-player launch peaks: Hogwarts Legacy 1.27M, Cyberpunk 1.14M,
  Elden Ring 910k. Twitch diurnal peak ~15:00 EST = 19:00 UTC.

## What the data says

**Launch-day shape (rolling-midnight launches).** Hours 2–4 dip to
0.75–0.88x hour 1, the US unlock lifts hours 5–6, a plateau follows, and
the evening (hours 14–21, peak 19–21) is the day's top — consistent with
Twitch's global diurnal peak (12:00–19:00 EST = 16:00–23:00 UTC) and EU
prime time (20:00–24:00 CET).

**The size effect (the key finding).** The peak/hour-1 ratio shrinks
strongly as hour 1 grows: across the 12 rolling launches, corr(log hour-1,
log ratio) is −0.47 (hour 5) to −0.76 (hour 21), slopes −0.18 to −0.59.
Median evening ratio: ~3.6–3.9x at hour-1 50k, ~1.0–1.1x at 500k. The two
biggest launches (Elden Ring 875k, Cyberpunk 852k — both simultaneous
global) peak in hour 1–2. Explanation: viewers ≠ players — US viewers can
already watch UK streamers in hour 1 (19:00 ET), so the bigger the launch,
the larger the share of the audience already standing by in hour 1.

**GTA VI's unlock (midnight local, rolling).** NZ 2026-11-18T11:00Z, CET
23:00Z, UK 00:00Z, US East 05:00Z (= hour 6), US West 08:00Z (= hour 9).
Hour 1 (00:00–01:00 UTC) is UK/EU/NZ/AU only; the big US unlocks land in
hours 6 and 9. Hour-1 print is unknown until 19 Nov 01:00 UTC; the model
must work for any hour 1 from ~50k to ~1.5M.

## Method

Per hour h = 2..24, from the rolling-midnight analogs in the case:

1. `r = ln(viewers_h / viewers_1)` per analog.
2. OLS `r = a_h + b_h * ln(viewers_1)`, slope winsorized to [−0.6, 0].
3. Median `q50_h = p1 * exp(a_h + b_h * ln(p1))`.
4. Spread from the empirical quantiles of the OLS residuals (levels
   0.05/0.25/0.75/0.95), widened ×1.15 (n is small: 8–12 analogs).
5. `q_tau = p1 * exp(median_log + resid_q_tau)`, non-decreasing, > 0.

Analog filter: drop the case's own game (GTA VI pre-release history);
drop unlocks containing `simultaneous` or tier `early-access-contaminated`
/ `weak`; keep unlocks containing `midnight local` / `rolling`. This
leaves 8 analogs in each practice case (Resident Evil Requiem, Ghost of
Yōtei, Monster Hunter Wilds, CoD Black Ops 6, CoD MW III, CoD MW4,
Final Fantasy VII Rebirth, The Last of Us Part II) and 12 in the final
(plus the 4 practice launches).

Extrapolation guards: above the analogs' hour-1 range (max 365k) the
size adjustment blends toward the plain median ratio, weight ramping
0 → 50% as hour 1 goes from the range edge to 1.5x the largest analog;
evening median ratio (hours 14–21) floored at 0.7x hour 1. The blend is
high-side only (see "Decisions" below). A fallback table with the same
per-hour fit constants, computed offline from the 12 rolling launches,
is embedded and used only if a case carries no usable comparables.

Why this and not the alternatives: pinball loss is a proper scoring rule
for quantiles, so reporting the believed quantiles is the right answer in
theory. ARIMA/ETS/Prophet do not fit — there is one anchor point (hour 1)
plus pre-release history at 100–1000x smaller scale, no launch-day series
to extrapolate. Gradient boosting is impossible (n = 12, no meaningful
training features, offline, stdlib only). A median-only forecast scores
far worse than one with an honest spread (0.388 vs 0.249 on the same
8-analog quantiles).

## Backtest (practice, SullyGnome answers)

| Model | p00 Wolverine | p01 RDR2 | p02 GoW | p03 SM2 | Mean |
|---|---|---|---|---|---|
| A. House baseline (persistence) | 0.744 | 0.287 | 0.215 | 0.303 | **0.387** |
| B. Empirical quantiles, all 37 comps | 0.407 | 0.288 | 0.286 | 0.314 | 0.324 |
| C. Empirical quantiles, 8 rolling | 0.395 | 0.123 | 0.232 | 0.246 | 0.249 |
| **E. Size-adjusted (this entry)** | **0.191** | **0.127** | **0.121** | **0.224** | **0.166** |
| C median-only (no spread) | 0.667 | 0.165 | 0.369 | 0.349 | 0.388 |

Model E is honestly out-of-sample (fit sees only the 8 comparables, never
the practice launches) and beats the baseline 2.3x. The starter was run
locally on the 4 practice cases and reproduced the house's 0.387 exactly,
which verifies the scorer, the answers, and the I/O plumbing.

Leave-one-out over the 12 rolling launches (fit on the other 11, score
the held-out launch): mean **0.254**, 11 of 12 cases ≤ 0.333. The one
exception is Resident Evil Requiem (0.842): its hour 1 was only 46k while
its evening peaked 12.14x hour 1 — no model could foresee that from the
other 11 launches. Excluding it, LOO mean is 0.200.

p1 sensitivity (median evening ratio): 50k → x3.57, 100k → x2.51,
300k → x1.48, 500k → x1.56, 1M → x1.46, 1.5M → x1.33. Smooth, no jumps
(max adjacent-hour log change 0.41, the US-unlock step at hour 6).

Fallback-only path (comparables stripped, table fit on the 12 rolling
launches): practice mean 0.134 — in-sample for the practice launches,
so not comparable to the 0.166, but it proves the fallback table is
functional and sane (hour-20 median 402k vs baseline 270k at p1 270k).

## Decisions (what was tried and dropped)

- **Hard 50/50 blend on both sides of the fit range: rejected.** It
  scored practice 0.187 (vs 0.166 with no blend) and LOO 0.264 (vs
  0.254), and it creates a discontinuity at the range edge (hour-20
  ratio jumps 1.35x at 365k to 1.76x at 400k). The low-side blend is
  the damage: at hour-1 23k the size adjustment is genuinely
  informative (Wolverine peaked 9.09x), and diluting it cost 0.09
  loss on p00 alone. The shipped version blends only above the range,
  with the weight ramping in — same guard for the final's likely
  500k–1.5M hour 1 (peak evening ratio 1.46x at 1M vs 0.84x at hour 20
  for the raw extrapolation), no discontinuity, no practice cost.
- **Spread widening 1.0 / 1.15 / 1.3:** practice 0.161 / 0.166 / 0.172,
  LOO 0.257 / 0.254 / 0.252. Kept 1.15 — the middle, and the small-n
  honest choice.
- **EG-style table / second model:** not applicable; the model is the fit.
- **Including simultaneous-global launches (Elden Ring, Cyberpunk) as
  analogs:** rejected — their hour 1 already holds the global surge, so
  their shape (peak in hour 1–2) does not describe a rolling launch.
- **Streams / categories_hourly / history signals:** read but not used
  for the forecast — top-streamer counts and pre-release history (scale
  ~10³ vs launch ~10⁶) are too weak to move the quantiles, and the
  comparables already carry the shape.

## Run

```sh
MAKEFUN_INPUT_DIR=input MAKEFUN_OUTPUT_DIR=out python3 main.py
```

Python 3.13 stdlib only, offline, deterministic (two runs byte-identical),
~0.05 s/case (limit 8 s). Output: `/output/<id>.out`, exactly 23 rows
(hours 2–24), five non-decreasing quantiles each, ≤ 65,536 bytes.
