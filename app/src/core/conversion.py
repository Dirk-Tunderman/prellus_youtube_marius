#!/usr/bin/env python3
"""
Centralized Character/Time Conversion Module

This module provides a single source of truth for all character and time conversion
constants used throughout the application. All conversion rates can be modified
in the config.yaml file without code changes.

Usage:
    from src.core.conversion import ConversionConfig
    
    conversion = ConversionConfig()
    target_chars = conversion.minutes_to_chars(duration_minutes, speed_factor)
    target_minutes = conversion.chars_to_minutes(char_count)
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class ConversionConfig:
    """
    Centralized conversion configuration that loads constants from config.yaml
    and provides methods for consistent character/time conversions throughout the app.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the conversion configuration.
        
        Args:
            config_path: Optional path to config.yaml. If not provided, will search
                        for it in standard locations.
        """
        self._config = None
        self._config_path = config_path
        self._load_config()
    
    def _find_config_path(self) -> str:
        """Find the config.yaml file in standard locations."""
        # Get the project root directory
        current_file = Path(__file__)
        project_root = current_file.parent.parent.parent.parent  # Go up 4 levels to reach project root
        
        # Try different possible locations
        possible_paths = [
            self._config_path,  # Provided path
            os.path.join(project_root, "app/config/config.yaml"),
            os.path.join(project_root, "config/config.yaml"),
            "app/config/config.yaml",
            "config/config.yaml"
        ]
        
        for path in possible_paths:
            if path and os.path.exists(path):
                return path
        
        # Default fallback
        return os.path.join(project_root, "app/config/config.yaml")
    
    def _load_config(self):
        """Load configuration from YAML file."""
        config_path = self._find_config_path()
        
        try:
            with open(config_path, 'r') as f:
                self._config = yaml.safe_load(f)
            logger.debug(f"Loaded conversion config from {config_path}")
        except Exception as e:
            logger.warning(f"Error loading config from {config_path}: {e}")
            logger.warning("Using default conversion values")
            self._config = {}
    
    def reload_config(self):
        """Force reload configuration from file to pick up any changes."""
        logger.info("🔄 Reloading conversion configuration from file...")
        self._load_config()
        logger.info(f"✅ Reloaded: {self.chars_per_minute} chars/minute")
    
    def _get_conversion_config(self) -> Dict[str, Any]:
        """Get the character_conversion section from config."""
        if not self._config:
            return {}
        return self._config.get('character_conversion', {})
    
    @property
    def words_per_minute(self) -> int:
        """Base TTS reading speed in words per minute."""
        return self._get_conversion_config().get('words_per_minute', 200)
    
    @property
    def chars_per_word(self) -> int:
        """Average characters per word including space."""
        return self._get_conversion_config().get('chars_per_word', 5)
    
    @property
    def chars_per_minute(self) -> int:
        """Calculated characters per minute (WPM * chars per word)."""
        return self._get_conversion_config().get('chars_per_minute', 1000)
    
    @property
    def gpt5_chars_per_response(self) -> int:
        """GPT-5 observed maximum characters per response."""
        return self._get_conversion_config().get('gpt5_chars_per_response', 60000)
    
    @property
    def claude_chars_per_response(self) -> int:
        """Claude observed maximum characters per response."""
        return self._get_conversion_config().get('claude_chars_per_response', 60000)
    
    def minutes_to_chars(self, minutes: float, speed_factor: float = 1.0) -> int:
        """
        Convert duration in minutes to target character count.
        
        Args:
            minutes: Duration in minutes
            speed_factor: Playback speed factor (e.g., 0.8 for 0.8x speed)
        
        Returns:
            Target character count
        """
        if minutes <= 0:
            return 0
        
        # Use the configured chars_per_minute directly (more accurate than WPM × chars/word)
        # Adjust for speed factor: slower speed = fewer characters needed for same time
        # At 0.8x speed, content plays 25% slower, so we need 25% fewer characters
        effective_chars_per_minute = self.chars_per_minute / speed_factor
        
        target_chars = int(minutes * effective_chars_per_minute)
        
        logger.debug(f"Conversion: {minutes}min @ {speed_factor}x speed -> {target_chars:,} chars")
        logger.debug(f"  Base chars/min: {self.chars_per_minute}, Effective chars/min: {effective_chars_per_minute:.1f}")
        
        return target_chars
    
    def chars_to_minutes(self, char_count: int, speed_factor: float = 1.0) -> float:
        """
        Convert character count to estimated duration in minutes.
        
        Args:
            char_count: Number of characters
            speed_factor: Playback speed factor (e.g., 0.8 for 0.8x speed)
        
        Returns:
            Estimated duration in minutes
        """
        if char_count <= 0:
            return 0.0
        
        # Calculate base duration
        base_minutes = char_count / self.chars_per_minute
        
        # Adjust for speed factor: slower speed = longer duration
        actual_minutes = base_minutes * speed_factor
        
        logger.debug(f"Conversion: {char_count:,} chars @ {speed_factor}x speed -> {actual_minutes:.2f}min")
        
        return actual_minutes
    
    def get_model_chars_per_response(self, model: str) -> int:
        """
        Get the maximum characters per response for a given model.
        
        Args:
            model: Model name (e.g., "gpt-5", "claude-3-sonnet")
        
        Returns:
            Maximum characters per response for the model
        """
        if model.startswith("gpt-5"):
            return self.gpt5_chars_per_response
        elif model.startswith("claude"):
            return self.claude_chars_per_response
        
        # Default for other models - can be extended in config.yaml if needed
        return 100000  # Conservative default for other models
    
    def log_conversion_summary(self):
        """Log a summary of current conversion settings."""
        logger.info("🧮 CONVERSION SETTINGS SUMMARY:")
        logger.info(f"   📚 Words per minute: {self.words_per_minute} WPM")
        logger.info(f"   🔤 Characters per word: {self.chars_per_word}")
        logger.info(f"   ⚡ Characters per minute: {self.chars_per_minute}")
        logger.info(f"   🤖 GPT-5 chars per response: {self.gpt5_chars_per_response:,}")
        logger.info(f"   🧠 Claude chars per response: {self.claude_chars_per_response:,}")


# Global instance for easy access
_global_conversion_config = None


def get_conversion_config() -> ConversionConfig:
    """
    Get the global conversion configuration instance.
    
    Returns:
        ConversionConfig instance
    """
    global _global_conversion_config
    if _global_conversion_config is None:
        _global_conversion_config = ConversionConfig()
    return _global_conversion_config


# Convenience functions for common conversions
def minutes_to_chars(minutes: float, speed_factor: float = 1.0) -> int:
    """Convert minutes to characters using global config."""
    return get_conversion_config().minutes_to_chars(minutes, speed_factor)


def chars_to_minutes(char_count: int, speed_factor: float = 1.0) -> float:
    """Convert characters to minutes using global config."""
    return get_conversion_config().chars_to_minutes(char_count, speed_factor)


def get_model_chars_per_response(model: str) -> int:
    """Get max characters per response for model using global config."""
    return get_conversion_config().get_model_chars_per_response(model)


def reload_conversion_config():
    """Force reload the global conversion configuration from file."""
    global _global_conversion_config
    if _global_conversion_config is not None:
        _global_conversion_config.reload_config()
    else:
        # If no global instance exists, getting it will create a new one with fresh config
        get_conversion_config()