import os

# Use a non-interactive backend so importing Darts (which imports pyplot)
# never tries to open a window during tests.
os.environ.setdefault("MPLBACKEND", "Agg")
