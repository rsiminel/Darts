"""Tests for the scatter model (expected_score / optimal_aim) and the CLI."""

import numpy as np
import pytest
from scipy.ndimage import gaussian_filter

import Darts
from Darts import create_points, expected_score, optimal_aim, main, STANDARD_LAYOUT

GRID = 120
BOARD = create_points(GRID, STANDARD_LAYOUT)


# --- expected_score ----------------------------------------------------------

def test_zero_spread_returns_the_board_unchanged():
    assert np.array_equal(expected_score(BOARD, 0, 0), BOARD.astype(float))


def test_axis_aligned_matches_plain_gaussian_filter():
    # theta == 0 must take the fast path and be identical to a direct blur.
    got = expected_score(BOARD, 5, 3, theta_deg=0)
    want = gaussian_filter(BOARD, sigma=[5, 3], mode="constant", cval=0)
    assert np.array_equal(got, want)


def test_default_sigma_y_is_isotropic():
    assert np.array_equal(expected_score(BOARD, 4), expected_score(BOARD, 4, 4))


def test_isotropic_spread_is_rotation_invariant():
    # A circular Gaussian is rotation-invariant, so tilting it should barely
    # change the field (only `rotate`'s interpolation differs).
    upright = expected_score(BOARD, 8, 8, theta_deg=0)
    tilted = expected_score(BOARD, 8, 8, theta_deg=45)
    assert np.mean(np.abs(upright - tilted)) < 0.5
    ax, ay = optimal_aim(upright)
    bx, by = optimal_aim(tilted)
    assert abs(ax - bx) <= 4 and abs(ay - by) <= 4


def test_correlated_spread_changes_the_field():
    # A genuinely elongated/tilted spread should differ from the isotropic one.
    iso = expected_score(BOARD, 12, 12, theta_deg=0)
    tilted = expected_score(BOARD, 20, 4, theta_deg=30)
    assert not np.allclose(iso, tilted)
    assert tilted.shape == BOARD.shape


# --- optimal_aim -------------------------------------------------------------

def test_optimal_aim_points_at_the_maximum():
    field = np.zeros((10, 10))
    field[3, 7] = 5.0
    assert optimal_aim(field) == (3, 7)


# --- CLI ---------------------------------------------------------------------

def test_cli_writes_one_png_per_demo(tmp_path):
    # Tiny grid / sweep so the O(worst_aim^2) anisotropic demo stays fast.
    main([
        "--demo", "all",
        "--layout", "1,2,3,4",
        "--grid-size", "40",
        "--worst-aim", "3",
        "--save-dir", str(tmp_path),
        "--no-show",
    ])
    for name in ("isotropic", "anisotropic", "correlated"):
        out = tmp_path / f"{name}.png"
        assert out.exists() and out.stat().st_size > 0, name


def test_cli_custom_layout_is_parsed(tmp_path):
    main(["--demo", "correlated", "--layout", "10,20,30",
          "--grid-size", "40", "--save-dir", str(tmp_path), "--no-show"])
    assert (tmp_path / "correlated.png").exists()


@pytest.mark.parametrize("spec,expected", [("standard", STANDARD_LAYOUT), ("5,10,15", [5, 10, 15])])
def test_resolve_layout(spec, expected):
    assert Darts._resolve_layout(spec) == expected
