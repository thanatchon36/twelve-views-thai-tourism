"""Read a dataset: the real file if present, otherwise its synthetic stand-in, with a warning.

A real file is ``data/raw/<name>.csv`` with the columns listed in ``data/raw/synthetic_manifest.json``.
Without it the loader reads ``data/raw/synthetic_<name>.csv`` and warns once per dataset and run, so a synthetic
number can never pass silently for a real one.
"""
from __future__ import annotations

import sys

import pandas as pd

from .config import RAW

_warned: set[str] = set()


def path(name: str):
    real = RAW / f"{name}.csv"
    return real if real.exists() else RAW / f"synthetic_{name}.csv"


def is_synthetic(name: str) -> bool:
    return not (RAW / f"{name}.csv").exists()


def load(name: str) -> pd.DataFrame:
    p = path(name)
    if is_synthetic(name) and name not in _warned:
        _warned.add(name)
        print(f"WARNING: data/raw/{name}.csv not found; using SYNTHETIC data/raw/{p.name}", file=sys.stderr)
    return pd.read_csv(p)
