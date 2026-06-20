#%%
from scipy.ndimage import gaussian_filter, rotate
import matplotlib.pyplot as plt
import numpy as np
import argparse
from pathlib import Path

grid_size = 200
worst_aim = 100

# Standard dartboard segment order, clockwise starting from "1".
STANDARD_LAYOUT = [1, 18, 4, 13, 6, 10, 15, 2, 17, 3, 19, 7, 16, 8, 11, 14, 9, 12, 5, 20]

# Ring radii as fractions of the board radius, derived from real board geometry.
# (Bull fractions are relative to the 340 mm board diameter; the double/triple
# fractions are relative to the 170 mm board radius.)
INNER_BULL_FRAC = 12.7 / 340   # inside this -> inner bull
OUTER_BULL_FRAC = 32 / 340     # inside this -> outer bull
DOUBLE_INNER_FRAC = 162 / 170  # beyond this -> double ring
TRIPLE_OUTER_FRAC = 107 / 170  # triple ring outer edge
TRIPLE_INNER_FRAC = 99 / 170   # triple ring inner edge

INNER_BULL_SCORE = 50
OUTER_BULL_SCORE = 25


def create_points(grid_size, points):
    """Render a dartboard score map.

    Returns a ``(grid_size, grid_size)`` float array where each pixel holds the
    score for a dart landing there: 0 off the board, ``INNER_BULL_SCORE`` /
    ``OUTER_BULL_SCORE`` in the two bullseyes, and 1x/2x/3x a segment value in
    the single/double/triple rings. ``points`` is the segment value for each
    wedge, given clockwise (e.g. :data:`STANDARD_LAYOUT`); its length sets the
    number of wedges.
    """
    points = np.asarray(points)
    num_points = len(points)
    half = grid_size / 2
    dividers = np.pi * (2*np.arange(num_points + 1)/num_points - 1)

    # radius[x, y] is the squared distance from the board centre; angle is the
    # polar angle. indexing='ij' keeps the [x, y] orientation of the old loop.
    x, y = np.meshgrid(np.arange(grid_size), np.arange(grid_size), indexing='ij')
    radius = (x - half)**2 + (y - half)**2
    angle = np.arctan2(y - half, x - half)
    # arctan2 returns pi on the negative-x axis; wrap to -pi so it lands in the
    # first wedge rather than past the last divider.
    angle = np.where(angle == np.pi, -np.pi, angle)

    # Wedge index per pixel: the p with dividers[p] <= angle < dividers[p+1].
    # searchsorted(side='right') counts dividers <= angle; minus one gives p.
    seg_idx = np.clip(np.searchsorted(dividers, angle, side='right') - 1, 0, num_points - 1)
    seg_value = points[seg_idx]

    # Ring multipliers (matched precedence: double, then triple, else single).
    in_double = radius > (DOUBLE_INNER_FRAC * half)**2
    in_triple = (radius < (TRIPLE_OUTER_FRAC * half)**2) & (radius > (TRIPLE_INNER_FRAC * half)**2)
    grid = np.where(in_double, 2*seg_value, np.where(in_triple, 3*seg_value, seg_value))

    # Overlay centre regions and misses, lowest precedence first so the loop's
    # if/elif order (miss > inner bull > outer bull > segment) is reproduced.
    grid = np.where(radius < (OUTER_BULL_FRAC * half)**2, OUTER_BULL_SCORE, grid)
    grid = np.where(radius < (INNER_BULL_FRAC * half)**2, INNER_BULL_SCORE, grid)
    grid = np.where(radius > half**2, 0.0, grid)  # missed the board
    return grid.astype(float)


#%%
def expected_score(points, sigma_x, sigma_y=None, theta_deg=0.0):
    """Expected score for aiming at each pixel, given a Gaussian aim spread.

    Blurring the score map by the dart-scatter distribution gives the expected
    score at every aim point. ``sigma_x``/``sigma_y`` are the spread along the
    two axes (``sigma_y`` defaults to ``sigma_x`` for isotropic aim) and
    ``theta_deg`` rotates that spread, modelling correlated/tilted scatter.
    """
    if sigma_y is None:
        sigma_y = sigma_x
    if sigma_x == 0 and sigma_y == 0:
        return points.astype(float)
    if theta_deg % 360 == 0:
        return gaussian_filter(points, sigma=[sigma_x, sigma_y], mode='constant', cval=0)
    # Rotate into the spread's frame, blur along its axes, rotate back. Reuses
    # the efficient separable filter for any orientation.
    rot = rotate(points, -theta_deg, reshape=False, mode='constant', cval=0, order=1)
    blurred = gaussian_filter(rot, sigma=[sigma_x, sigma_y], mode='constant', cval=0)
    return rotate(blurred, theta_deg, reshape=False, mode='constant', cval=0, order=1)


def optimal_aim(score):
    """Return the (x, y) of the highest-scoring aim point (first, in row order)."""
    coord = np.argwhere(score == np.amax(score))[0]
    return int(coord[0]), int(coord[1])


#%%
def demo_isotropic(layout=STANDARD_LAYOUT, grid_size=grid_size, worst_aim=worst_aim,
                   save_path=None, show=True):
    """Sweep a single (isotropic) aim spread; plot the optimal aim point per skill level."""
    points = create_points(grid_size, layout)
    best_shot = np.zeros([grid_size] * 2)
    for sigma in range(worst_aim):
        score = expected_score(points, sigma)
        x, y = optimal_aim(score)
        best_shot[x, y] = sigma
    fig, ax = plt.subplots()
    ax.imshow(points, cmap="gray")
    ax.imshow(best_shot, cmap="Wistia", alpha=1.0 * (best_shot > 0))
    ax.set_title("Optimal aim point vs. isotropic aim spread")
    _finish(fig, save_path, show)
    return best_shot


#%%
def demo_anisotropic(layout=STANDARD_LAYOUT, grid_size=grid_size, worst_aim=worst_aim,
                     save_path=None, show=True):
    """Sweep independent horizontal/vertical aim spreads; plot optimal aim points (RGB-encoded)."""
    points = create_points(grid_size, layout)
    best_shot = np.zeros([grid_size, grid_size, 4])
    for sigmaX in range(worst_aim):
        for sigmaY in range(worst_aim):
            score = expected_score(points, sigmaX, sigmaY)
            x, y = optimal_aim(score)
            best_shot[x, y, 0] = sigmaX / worst_aim
            best_shot[x, y, 1] = sigmaY / worst_aim
            best_shot[x, y, 2] = 1.0 - (sigmaX + sigmaY) / worst_aim
            best_shot[x, y, 3] = 1.0
    fig, ax = plt.subplots()
    ax.imshow(points, cmap="gray")
    ax.imshow(np.clip(best_shot, 0, 1))  # blue channel can go negative; clip for imshow
    ax.set_title("Optimal aim point vs. anisotropic aim spread (RGB = sigmaX, sigmaY)")
    _finish(fig, save_path, show)
    return best_shot


#%%
def demo_correlated(layout=STANDARD_LAYOUT, grid_size=grid_size,
                    sigma_major=18.0, sigma_minor=6.0, theta_deg=30.0,
                    save_path=None, show=True):
    """Plot the expected-score field for a correlated (tilted, elongated) aim spread.

    Marks the optimal aim point for a scatter ellipse with the given major/minor
    spread rotated by ``theta_deg``.
    """
    points = create_points(grid_size, layout)
    score = expected_score(points, sigma_major, sigma_minor, theta_deg)
    x, y = optimal_aim(score)
    fig, ax = plt.subplots()
    im = ax.imshow(score, cmap="inferno")
    ax.plot(y, x, "c+", markersize=14, markeredgewidth=2)
    ax.set_title(f"Expected score (sigma={sigma_major}/{sigma_minor}, theta={theta_deg} deg)\n"
                 f"optimal aim x={x}, y={y}")
    fig.colorbar(im, ax=ax, label="expected score")
    _finish(fig, save_path, show)
    return score


def _finish(fig, save_path, show):
    """Save and/or show a figure, then release it."""
    if save_path is not None:
        fig.savefig(save_path, bbox_inches="tight", dpi=120)
        print(f"wrote {save_path}")
    if show:
        plt.show()
    plt.close(fig)


#%%
def _resolve_layout(spec):
    if spec == "standard":
        return STANDARD_LAYOUT
    return [int(v) for v in spec.split(",")]


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Find where to aim on a dartboard given how bad your aim is.")
    parser.add_argument("--demo", choices=["isotropic", "anisotropic", "correlated", "all"],
                        default="all", help="which visualization(s) to run")
    parser.add_argument("--layout", default="standard",
                        help="'standard' or a comma-separated list of segment values")
    parser.add_argument("--grid-size", type=int, default=grid_size)
    parser.add_argument("--worst-aim", type=int, default=worst_aim,
                        help="largest aim spread (sigma) to sweep")
    parser.add_argument("--save-dir", type=Path, default=None,
                        help="write PNGs to this directory instead of only showing them")
    parser.add_argument("--no-show", action="store_true",
                        help="don't open interactive windows (useful with --save-dir)")
    args = parser.parse_args(argv)

    layout = _resolve_layout(args.layout)
    show = not args.no_show
    save_dir = args.save_dir
    if save_dir is not None:
        save_dir.mkdir(parents=True, exist_ok=True)

    def path_for(name):
        return None if save_dir is None else save_dir / f"{name}.png"

    if args.demo in ("isotropic", "all"):
        demo_isotropic(layout, args.grid_size, args.worst_aim, path_for("isotropic"), show)
    if args.demo in ("anisotropic", "all"):
        demo_anisotropic(layout, args.grid_size, args.worst_aim, path_for("anisotropic"), show)
    if args.demo in ("correlated", "all"):
        demo_correlated(layout, args.grid_size, save_path=path_for("correlated"), show=show)


#%%
if __name__ == "__main__":
    main()
