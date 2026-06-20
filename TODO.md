# TODO / Roadmap

Tracked avenues of improvement for the dartboard aim optimizer. Roughly ordered
within each section by value-for-effort.

## Correctness & fidelity
- [x] Fix inverted bullseye scores: inner bull now 50, outer bull 25 (`Darts.py:24-31`).
- [x] Use `break` instead of `continue` in the wedge loop once a segment matches.
- [x] Remove the redundant `x == grid_size/2` special case; `np.arctan2(y, 0)`
      already returns ±π/2.
- [x] Include wedge-divider boundaries (`>=` lower bound) so pixels on a divider —
      notably the cardinal axes — are scored instead of left as 0 holes (`Darts.py`).

## Performance
- [x] Vectorize `create_points` with NumPy meshgrids — dropped the pure-Python double
      loop over `grid_size²` (~10-50x faster; 500x500 in ~27 ms).
- [ ] Vectorize / cache the `O(worst_aim²)` anisotropic sweep.

## Features
- [ ] Expected-score-vs-`sigma` plot comparing fixed targets (triple-20, bull, optimal)
      — makes the "don't aim at the triple-20" result explicit.
- [ ] Support correlated/rotated scatter (full 2D covariance, not just axis-aligned
      `sigmaX`/`sigmaY`).
- [ ] Animate the optimal aim point migrating as `sigma` increases (export a GIF).
- [ ] Parameterize via CLI args / config instead of editing source; option to save
      figures to disk.

## Project hygiene
- [ ] Add a docstring to `create_points`.
- [ ] Extract magic geometry ratios (`12.7/340`, `32/340`, `162/170`, `107/170`,
      `99/170`) into named constants.
- [x] Add sanity tests (known pixel coordinate → expected score). See `tests/`.
- [ ] Add an `assets/` folder with a rendered output image, embedded in the README.
