"""Unit tests for configuration loading."""

import pytest
from src.costwatch.config import Config


def test_config_loads_defaults():
    """Verify that configuration loads correctly from config.yaml."""
    config = Config.load("config.yaml")
    assert config.rolling_weeks == 8
    assert config.min_history_weeks == 4
    assert config.own_threshold_pct == 8.0
    assert config.peer_threshold_pct == 10.0
    assert config.open_ended_max_weeks == 8
    assert config.magnitude_check is True
    assert config.magnitude_tolerance_pp == 10.0
    assert config.top_k == 5
    assert "shipments" in config.paths
    assert "notes" in config.paths
