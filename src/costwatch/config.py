"""Configuration loader for CostWatch parameters."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict
import yaml


@dataclass(frozen=True)
class Config:
    """Immutable application configuration."""
    rolling_weeks: int
    min_history_weeks: int
    own_threshold_pct: float
    peer_threshold_pct: float
    open_ended_max_weeks: int
    magnitude_check: bool
    magnitude_tolerance_pp: float
    top_k: int
    embedding_model: str
    model_name: str
    temperature: float
    paths: Dict[str, str]

    @classmethod
    def load(cls, config_path: str = "config.yaml") -> "Config":
        """Load configuration from a YAML file."""
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        with open(path, "r", encoding="utf-8") as f:
            data: Dict[str, Any] = yaml.safe_load(f)
        return cls(
            rolling_weeks=int(data["rolling_weeks"]),
            min_history_weeks=int(data["min_history_weeks"]),
            own_threshold_pct=float(data["own_threshold_pct"]),
            peer_threshold_pct=float(data["peer_threshold_pct"]),
            open_ended_max_weeks=int(data["open_ended_max_weeks"]),
            magnitude_check=bool(data["magnitude_check"]),
            magnitude_tolerance_pp=float(data["magnitude_tolerance_pp"]),
            top_k=int(data["top_k"]),
            embedding_model=str(data["embedding_model"]),
            model_name=str(data["model_name"]),
            temperature=float(data["temperature"]),
            paths=dict(data.get("paths", {})),
        )
