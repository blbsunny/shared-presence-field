"""
Stage B: the Shared Presence Field.

    S(x) = (1/N) * sum_i exp( -d_i(x)^2 / (2 * sigma^2) )

where d_i(x) is the distance from x to the NEAREST point of building i.

The sum runs over buildings, not over points. That is where "one building, one
vote" lives: collapsing a whole cloud to a single nearest distance is what stops
a densely recorded building from counting more than a sparse one. The 1/N only
rescales.

Values are unnormalised: they are not rescaled within a dataset.

-----------------------------------------------------------------------------
NOTE TO SELF BEFORE PUBLISHING
This is a reference implementation of the formula. Diff it against the script
you actually ran for the paper; if they differ, ship yours, not this one.
-----------------------------------------------------------------------------
"""

from __future__ import annotations

import numpy as np
from scipy.spatial import cKDTree


def shared_presence(query_xyz, clouds, sigma):
    """Evaluate S at `query_xyz`.

    Parameters
    ----------
    query_xyz : (M, 3) array
        Points at which to evaluate the field. In the papers these are the real
        scanned points, not a grid.
    clouds : sequence of (n_i, 3) arrays
        One array per building, already in the common frame.
    sigma : float
        How close two surfaces must lie to count as the same place, in metres.

    Returns
    -------
    (M,) array of shared presence values.
    """
    query_xyz = np.asarray(query_xyz, dtype=np.float64)
    n_buildings = len(clouds)
    if n_buildings == 0:
        raise ValueError("no buildings given")

    total = np.zeros(len(query_xyz), dtype=np.float64)
    two_sigma_sq = 2.0 * float(sigma) ** 2

    for cloud in clouds:
        # one nearest distance per building -> one contribution per building
        d, _ = cKDTree(np.asarray(cloud, dtype=np.float64)).query(query_xyz, k=1)
        total += np.exp(-(d ** 2) / two_sigma_sq)

    return total / n_buildings


def per_building_value(cloud, field_values):
    """Summarise one building by the median of S over its own points.

    Median rather than mean: per-point values are affected by scan density and
    local anomalies.
    """
    return float(np.median(field_values))


def self_term(n_buildings):
    """A building's own contribution to every point of its own cloud.

    It is exactly 1/N, identical for all buildings, so it shifts every
    per-building value by the same constant and does not affect their ordering.
    Leaving one building out gives S_-j = (N*S - 1) / (N - 1), a monotone
    transform of S.
    """
    return 1.0 / float(n_buildings)
