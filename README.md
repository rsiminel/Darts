# Darts — Where Should You Actually Aim?

A small experiment that answers a counterintuitive question:

> **Given how bad your aim is, where on a dartboard should you aim to maximize your expected score?**

The famous result is that the optimal target is *not* the triple-20 — only sharpshooters
should aim there. As your aim gets shakier, the best place to aim drifts toward more
forgiving regions of the board. This script reproduces that result visually.

## The idea

A player with imperfect aim doesn't reliably hit where they aim — their darts scatter
around the intended target. We model that scatter as a **Gaussian blur** applied to the
board's score map:

1. Build a 2D image of the dartboard where each pixel's value is the score for hitting it
   (singles, doubles, triples, and the two bullseyes), using the standard board layout.
2. Blur that image with a Gaussian of width `sigma`. A larger `sigma` means a shakier
   hand. The blurred image gives the **expected score** for aiming at each pixel.
3. The brightest pixel in the blurred image is the **optimal place to aim** for that skill
   level.

Sweeping `sigma` from sharp to terrible shows how the optimal aim point migrates across
the board.

## What's in the script

`Darts.py` is laid out as Jupyter-style cells (`#%%` markers); run it in an interactive
window or as a plain script.

- **`create_points(grid_size, points)`** — renders the dartboard score map. Wedge values
  are taken from the `points` list (the default is the real-world board order). Ring radii
  are scaled from actual board proportions; doubles score `2×`, triples `3×`.
- **Cell 1 (isotropic aim)** — sweeps a single `sigma` and overlays the optimal aim point
  for each skill level on the board, colored by `sigma`.
- **Cell 2 (anisotropic aim)** — sweeps independent horizontal and vertical spreads
  (`sigmaX`, `sigmaY`) for players who scatter more in one direction than the other, and
  encodes the two spreads into RGB.

## Running it

```bash
pip install numpy scipy matplotlib
python Darts.py
```

## Notes

- Scores are simplified point values, not the official 50/25 bull scoring, but the board
  geometry and segment order are real.
- `grid_size` controls resolution; `worst_aim` controls how shaky the worst modeled player
  is. Both trade off against runtime — the anisotropic cell is `O(worst_aim²)`.
