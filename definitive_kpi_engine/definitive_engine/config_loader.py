"""Configuration loading helpers."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def load_cpt_taxonomy(config_folder: str | Path) -> pd.DataFrame:
    return _load_config_csv(Path(config_folder) / "cpt_ep_taxonomy.csv")


def load_drg_taxonomy(config_folder: str | Path) -> pd.DataFrame:
    return _load_config_csv(Path(config_folder) / "drg_ep_taxonomy.csv")


def load_taxonomies(config_folder: str | Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    return load_cpt_taxonomy(config_folder), load_drg_taxonomy(config_folder)


def load_metric_definitions(config_folder: str | Path) -> pd.DataFrame:
    return _load_config_csv(Path(config_folder) / "metric_definitions.csv")


def _load_config_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing config file: {path}")
    return pd.read_csv(path, dtype=str, keep_default_na=False)
