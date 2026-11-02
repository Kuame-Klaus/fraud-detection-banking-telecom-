"""SYNTHETIC Ghana cell site locations for the telecom maps (Klaus Konsults).
The generator gives T9 only a location code, so each cell_id gets a made up latitude and longitude near a real
Ghana town, seeded and deterministic. These are NOT real cell sites. Replace them with the client's site list."""
from __future__ import annotations

import numpy as np
import pandas as pd

# (town, latitude, longitude, weight): weights roughly follow population, an ASSUMPTION
TOWNS = [("Accra", 5.6037, -0.1870, 6), ("Kumasi", 6.6885, -1.6244, 4), ("Tamale", 9.4008, -0.8393, 2),
         ("Sekondi Takoradi", 4.9016, -1.7831, 2), ("Cape Coast", 5.1053, -1.2466, 1), ("Ho", 6.6008, 0.4713, 1),
         ("Sunyani", 7.3399, -2.3268, 1), ("Koforidua", 6.0940, -0.2591, 1), ("Bolgatanga", 10.7856, -0.8514, 1),
         ("Wa", 10.0601, -2.5099, 1), ("Tema", 5.6698, -0.0166, 2), ("Techiman", 7.5900, -1.9390, 1)]


def cell_sites(cell_ids, seed: int = 42) -> pd.DataFrame:
    ids = sorted(set(map(str, cell_ids)))
    rng = np.random.default_rng(seed + 700)
    w = np.array([t[3] for t in TOWNS], dtype=float); w /= w.sum()
    town = rng.choice(len(TOWNS), size=len(ids), p=w)
    lat = np.array([TOWNS[i][1] for i in town]) + rng.normal(0, 0.05, len(ids))
    lon = np.array([TOWNS[i][2] for i in town]) + rng.normal(0, 0.05, len(ids))
    return pd.DataFrame({"cell_id": ids, "town": [TOWNS[i][0] for i in town], "latitude": lat.round(5), "longitude": lon.round(5)})
