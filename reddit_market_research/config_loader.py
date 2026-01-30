"""
Configuration Loader and Output Manager

Provides centralized configuration loading and output directory management
for the Reddit Market Research toolchain.
"""

import os
import yaml
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


class Config:
    """Configuration manager that loads settings from config.yaml."""

    _instance: Optional['Config'] = None
    _config: Dict[str, Any] = {}

    def __new__(cls) -> 'Config':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self) -> None:
        """Load configuration from config.yaml."""
        config_path = Path(__file__).parent / "config.yaml"
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f) or {}
        else:
            self._config = {}

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value using dot notation."""
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
            if value is None:
                return default
        return value

    @property
    def product_mappings(self) -> Dict[str, str]:
        """Get community to product name mappings."""
        return self._config.get('product_mappings', {})

    @property
    def output_config(self) -> Dict[str, Any]:
        """Get output configuration."""
        return self._config.get('output', {})

    @property
    def visualization_config(self) -> Dict[str, Any]:
        """Get visualization configuration."""
        return self._config.get('visualization', {})

    @property
    def text_analysis_config(self) -> Dict[str, Any]:
        """Get text analysis configuration."""
        return self._config.get('text_analysis', {})

    @property
    def data_processing_config(self) -> Dict[str, Any]:
        """Get data processing configuration."""
        return self._config.get('data_processing', {})


def get_output_dir(base_name: str) -> Path:
    """
    Get the output directory for a processing stage.
    
    Args:
        base_name: The name of the stage (e.g., 'setup_and_validation', 'data_preparation')
    
    Returns:
        Path to the output directory
    """
    config = Config()
    output_config = config.output_config
    
    base_dir = output_config.get('base_dir', 'output')
    use_timestamp = output_config.get('use_timestamp', True)
    timestamp_format = output_config.get('timestamp_format', '%Y_%m_%d_%H%M')
    
    if use_timestamp:
        timestamp = datetime.now().strftime(timestamp_format)
        output_path = Path(base_dir) / f"{timestamp}_{base_name}"
    else:
        output_path = Path(base_dir) / base_name
    
    output_path.mkdir(parents=True, exist_ok=True)
    return output_path


def get_product_name(community_name: str) -> str:
    """
    Get the product name for a community.
    
    Args:
        community_name: The community name (e.g., 'r/boltnewbuilders')
    
    Returns:
        The product display name
    """
    config = Config()
    mappings = config.product_mappings
    return mappings.get(community_name, community_name.replace('r/', '').title())


def get_visualization_colors() -> Dict[str, Any]:
    """Get visualization color configuration."""
    config = Config()
    return config.visualization_config.get('colors', {})


def is_visualization_enabled(chart_type: str) -> bool:
    """
    Check if a specific visualization is enabled.
    
    Args:
        chart_type: The type of chart (e.g., 'sentiment_bar_chart')
    
    Returns:
        True if the visualization is enabled
    """
    config = Config()
    charts = config.visualization_config.get('charts', {})
    return charts.get(chart_type, True)


def get_product_mapping_path() -> Path:
    """
    Get the path to the product mapping file.
    
    Returns:
        Path to the product mapping JSON file
    """
    config = Config()
    mappings = config.product_mappings
    # Return the path where mappings would be stored
    output_config = config.output_config
    base_dir = output_config.get('base_dir', 'output')
    return Path(base_dir) / "product_mapping.json"
