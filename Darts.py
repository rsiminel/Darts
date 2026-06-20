#%%
from scipy.ndimage import gaussian_filter
import matplotlib.pyplot as plt
import numpy as np

grid_size = 200
worst_aim = 100

# Standard dartboard segment order, clockwise starting from "1".
STANDARD_LAYOUT = [1, 18, 4, 13, 6, 10, 15, 2, 17, 3, 19, 7, 16, 8, 11, 14, 9, 12, 5, 20]


def create_points(grid_size, points):
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
    in_double = radius > (162/170 * half)**2
    in_triple = (radius < (107/170 * half)**2) & (radius > (99/170 * half)**2)
    grid = np.where(in_double, 2*seg_value, np.where(in_triple, 3*seg_value, seg_value))

    # Overlay centre regions and misses, lowest precedence first so the loop's
    # if/elif order (miss > inner bull > outer bull > segment) is reproduced.
    grid = np.where(radius < (32/340 * half)**2, 25.0, grid)   # outer bull
    grid = np.where(radius < (12.7/340 * half)**2, 50.0, grid)  # inner bull
    grid = np.where(radius > half**2, 0.0, grid)                # missed the board
    return grid.astype(float)


#%%
def demo_isotropic(layout=STANDARD_LAYOUT):
    """Sweep a single (isotropic) aim spread; plot the optimal aim point per skill level."""
    points = create_points(grid_size, layout)
    best_shot = np.zeros([grid_size] * 2)
    for sigma in range(worst_aim):
        score = gaussian_filter(points, sigma=sigma, mode='constant', cval=0)
        for coord in np.argwhere(score == np.amax(score)):
            best_shot[coord[0], coord[1]] = sigma
    plt.imshow(points, cmap="gray")
    plt.imshow(best_shot, cmap="Wistia", alpha=1.0*(best_shot > 0))
    plt.show()
    return best_shot


#%%
def demo_anisotropic(layout=STANDARD_LAYOUT):
    """Sweep independent horizontal/vertical aim spreads; plot optimal aim points (RGB-encoded)."""
    points = create_points(grid_size, layout)
    best_shot = np.zeros([grid_size, grid_size, 4])
    for sigmaX in range(worst_aim):
        for sigmaY in range(worst_aim):
            score = gaussian_filter(points, sigma=[sigmaX, sigmaY], mode='constant', cval=0)
            for coord in np.argwhere(score == np.amax(score)):
                best_shot[coord[0], coord[1], 0] = sigmaX / worst_aim
                best_shot[coord[0], coord[1], 1] = sigmaY / worst_aim
                best_shot[coord[0], coord[1], 2] = 1.0 - (sigmaX + sigmaY) / worst_aim
                best_shot[coord[0], coord[1], 3] = 1.0
    plt.imshow(points, cmap="gray")
    plt.imshow(best_shot)
    plt.show()
    return best_shot


#%%
if __name__ == "__main__":
    demo_isotropic()
    demo_anisotropic()
