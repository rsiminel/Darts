"""Tests for Darts.create_points.

These characterize the *current* behavior of the scoring map so we have a green
regression baseline before tackling the fixes in TODO.md. Where current behavior
reflects a known bug, the test says so and references the TODO item.

Geometry reference (for grid_size=200, so center=(100,100) and the squared
radius is `radius = (x-100)**2 + (y-100)**2`):

    miss          radius >  100**2          = 10000
    small bull    radius <  (12.7/340*100)**2 ~  13.95   -> 25
    outer bull    radius <  (32/340*100)**2   ~  88.58   -> 50
    triple ring   3391 < radius < 3962                   -> 3 * segment
    double ring   radius >  (162/170*100)**2  ~ 9080.9   -> 2 * segment
    single        anything else on the board            -> 1 * segment
"""

import numpy as np
import pytest

from Darts import create_points

GRID = 200

# A deliberately simple 4-segment layout makes the wedges exact 90deg quadrants:
#   dividers = [-pi, -pi/2, 0, pi/2, pi]
#   wedge 0: angle in (-pi, -pi/2) -> SQUARE[0]
#   wedge 1: angle in (-pi/2, 0)   -> SQUARE[1]
#   wedge 2: angle in (0,  pi/2)   -> SQUARE[2]
#   wedge 3: angle in (pi/2, pi)   -> SQUARE[3]
SQUARE = [1, 2, 3, 4]


@pytest.fixture(scope="module")
def square_grid():
    return create_points(GRID, SQUARE)


# --- shape / type / value-domain invariants ---------------------------------

def test_output_shape_is_square(square_grid):
    assert square_grid.shape == (GRID, GRID)


def test_output_is_float_and_non_negative(square_grid):
    assert square_grid.dtype == np.float64
    assert (square_grid >= 0).all()


def test_scores_only_come_from_the_allowed_value_set(square_grid):
    # Every pixel is a miss, a bullseye, or single/double/triple of a segment.
    allowed = {0, 25, 50}
    for v in SQUARE:
        allowed |= {v, 2 * v, 3 * v}
    assert set(np.unique(square_grid)).issubset(allowed)


def test_is_deterministic():
    assert np.array_equal(create_points(GRID, SQUARE), create_points(GRID, SQUARE))


# --- bullseyes ---------------------------------------------------------------

def test_center_is_the_inner_bull(square_grid):
    # radius 0 -> inner (small) bull, worth 50 in real darts.
    assert square_grid[100, 100] == 50


def test_just_outside_small_bull_is_outer_bull(square_grid):
    # (105,100): radius = 25 -> outer bull, worth 25 in real darts.
    assert square_grid[105, 100] == 25


def test_inner_bull_outscores_outer_bull(square_grid):
    # Real darts: inner bull (50) > outer bull (25).
    assert square_grid[100, 100] > square_grid[105, 100]


# --- misses ------------------------------------------------------------------

@pytest.mark.parametrize("x,y", [(0, 0), (0, 199), (199, 0), (199, 199), (1, 1)])
def test_corners_and_far_pixels_are_misses(square_grid, x, y):
    assert square_grid[x, y] == 0


# --- segments: single / double / triple multipliers --------------------------
# Pixels chosen on the 45deg diagonals so the angle lands cleanly inside a
# quadrant wedge, with the squared radius placed in a specific ring.

@pytest.mark.parametrize(
    "pixel,expected,zone",
    [
        # wedge 2 (angle = +pi/4), segment value SQUARE[2] = 3
        ((130, 130), 3, "single"),   # radius 1800
        ((142, 142), 9, "triple"),   # radius 3528  -> 3 * 3
        ((169, 169), 6, "double"),   # radius 9522  -> 2 * 3
        # wedge 1 (angle = -pi/4), segment value SQUARE[1] = 2
        ((130, 70), 2, "single"),    # radius 1800
        ((142, 58), 6, "triple"),    # radius 3528  -> 3 * 2
        ((169, 31), 4, "double"),    # radius 9522  -> 2 * 2
    ],
)
def test_segment_ring_multipliers(square_grid, pixel, expected, zone):
    x, y = pixel
    assert square_grid[x, y] == expected, f"{zone} pixel {pixel}"


def test_double_and_triple_are_2x_and_3x_the_single(square_grid):
    single = square_grid[130, 130]
    triple = square_grid[142, 142]
    double = square_grid[169, 169]
    assert triple == 3 * single
    assert double == 2 * single


def test_wedges_select_the_right_segment_value(square_grid):
    # Same radius (single ring), opposite diagonals -> different segments.
    assert square_grid[130, 130] == SQUARE[2]  # +pi/4
    assert square_grid[130, 70] == SQUARE[1]   # -pi/4


# --- wedge dividers / cardinal axes ------------------------------------------
# A pixel whose angle equals a divider must still be scored (not left at 0).
# Convention: the boundary belongs to the wedge it is the *lower* bound of.
# For SQUARE=[1,2,3,4] the cardinal axes coincide with dividers:
#   +x  angle  0     -> wedge 2 -> SQUARE[2] = 3
#   +y  angle  pi/2  -> wedge 3 -> SQUARE[3] = 4
#   -x  angle  pi    -> wedge 0 -> SQUARE[0] = 1   (pi wraps to -pi)
#   -y  angle -pi/2  -> wedge 1 -> SQUARE[1] = 2
@pytest.mark.parametrize(
    "pixel,expected,axis",
    [
        ((150, 100), 3, "+x"),
        ((100, 150), 4, "+y"),
        ((50, 100), 1, "-x"),
        ((100, 50), 2, "-y"),
    ],
)
def test_pixels_on_cardinal_axes_are_scored(square_grid, pixel, expected, axis):
    x, y = pixel
    assert square_grid[x, y] == expected, f"{axis} axis pixel {pixel}"


def test_no_on_board_pixel_is_an_unscored_hole(square_grid):
    # Every pixel inside the board radius must have a non-zero score; any 0 there
    # would be a divider/axis hole like the one this fix removes.
    yy, xx = np.mgrid[0:GRID, 0:GRID]
    on_board = ((xx - 100) ** 2 + (yy - 100) ** 2) < 100 ** 2
    assert (square_grid[on_board] > 0).all()


# --- sanity against the real board -------------------------------------------

def test_standard_layout_max_score_is_triple_twenty():
    grid = create_points(GRID, [1, 18, 4, 13, 6, 10, 15, 2, 17, 3, 19, 7, 16, 8, 11, 14, 9, 12, 5, 20])
    # Highest possible: triple 20 = 60. Bull values (25, 50) are lower.
    assert grid.max() == 60
    assert grid[100, 100] == 50  # center is the inner bull
