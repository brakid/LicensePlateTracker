"""Configuration loading."""
from dataclasses import dataclass
from pathlib import Path
import yaml


@dataclass
class Config:
    entry_camera_url: str
    exit_camera_url: str
    max_stay_minutes: float
    confidence_threshold: float
    frame_sample_every_n: int
    entry_debounce_seconds: int
    db_path: str


def load_config(path: str = "config.yaml") -> Config:
    with open(path) as f:
        raw = yaml.safe_load(f)
    return Config(
        entry_camera_url=raw["entry_camera_url"],
        exit_camera_url=raw["exit_camera_url"],
        max_stay_minutes=raw["max_stay_minutes"],
        confidence_threshold=raw["confidence_threshold"],
        frame_sample_every_n=raw["frame_sample_every_n"],
        entry_debounce_seconds=raw["entry_debounce_seconds"],
        db_path=raw["db_path"],
    )
