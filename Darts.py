#%%
from scipy.ndimage import gaussian_filter
import matplotlib.pyplot as plt
import numpy as np

grid_size = 200
worst_aim = 100

# Standard dartboard segment order, clockwise starting from "1".
STANDARD_LAYOUT = [1, 18, 4, 13, 6, 10, 15, 2, 17, 3, 19, 7, 16, 8, 11, 14, 9, 12, 5, 20]


def create_points(grid_size, points):
    num_points = len(points)
    grid = np.zeros([grid_size] * 2)
    dividers = np.pi * (2*np.arange(num_points + 1)/num_points - 1)
    for x in range(grid_size):
        for y in range(grid_size):
            radius = (x - grid_size/2)**2 + (y - grid_size/2)**2
            # Missed the board
            if radius > (grid_size/2)**2:
                grid[x, y] = 0
                continue
            # Inner (small) Bullseye
            elif radius < (12.7/340 * grid_size/2)**2:
                grid[x, y] = 50
                continue
            # Outer Bullseye
            elif radius < (32/340 * grid_size/2)**2:
                grid[x, y] = 25
                continue
            # Segments
            elif x == grid_size/2:
                    if y > grid_size/2: angle = np.pi/2
                    else: angle = - np.pi/2
            else:
                angle = np.arctan2((y - grid_size/2), (x - grid_size/2))
            # arctan2 returns pi for the negative-x axis; wrap it to -pi so it
            # falls into the first wedge instead of past the last divider.
            if angle == np.pi:
                angle = -np.pi
            for point in range(num_points):
                # Lower bound inclusive so a pixel exactly on a divider (e.g. the
                # cardinal axes) is still scored rather than left as a 0 hole.
                if (angle >= dividers[point] and angle < dividers[point + 1]):
                    if radius > (162/170 * grid_size/2)**2:
                        grid[x, y] = 2*points[point]
                    elif radius < (107/170 * grid_size/2)**2 and radius > (99/170 * grid_size/2)**2:
                        grid[x, y] = 3*points[point]
                    else:
                        grid[x, y] = points[point]
                    continue
    return grid


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
