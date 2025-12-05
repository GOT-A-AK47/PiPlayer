"""
Config Loader Module
Handles loading and managing configuration settings.
"""

import json
import logging
import os


class Config:
    """Configuration manager for PiPlayer"""

    def __init__(self, config_file='config.json'):
        self.config_file = config_file
        self.config = {}
        self.logger = logging.getLogger(__name__)
        self.load()

    def load(self):
        """Load configuration from JSON file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
                self.logger.info(f"Configuration loaded from {self.config_file}")
            else:
                self.logger.warning(f"Config file {self.config_file} not found, using defaults")
                self.config = self._get_defaults()
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing config file: {e}")
            self.config = self._get_defaults()
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")
            self.config = self._get_defaults()

    def save(self):
        """Save current configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            self.logger.info(f"Configuration saved to {self.config_file}")
        except Exception as e:
            self.logger.error(f"Error saving config: {e}")

    def get(self, key, default=None):
        """Get configuration value using dot notation"""
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key, value):
        """Set configuration value using dot notation"""
        keys = key.split('.')
        config = self.config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    def _get_defaults(self):
        """Return default configuration"""
        return {
            "application": {
                "name": "PiPlayer",
                "version": "1.0.0"
            },
            "log_level": "INFO",
            "log_file": "logs/piplayer.log",
            "music": {
                "directory": "music",
                "playlist_directory": "playlists",
                "supported_formats": [".mp3", ".ogg", ".wav", ".flac"]
            },
            "audio": {
                "sample_rate": 44100,
                "bit_depth": -16,
                "channels": 2,
                "buffer_size": 4096
            },
            "player": {
                "auto_start": False,
                "default_volume": 0.7,
                "repeat_mode": "all",
                "shuffle": False,
                "last_playlist": None
            },
            "display": {
                "enabled": True,
                "driver": "st7789",
                "width": 240,
                "height": 240,
                "rotation": 0,
                "backlight_pin": 13
            },
            "buttons": {
                "enabled": True,
                "debounce_time": 0.02,
                "button_a": 5,
                "button_b": 6,
                "button_x": 16,
                "button_y": 24
            },
            "web": {
                "enabled": False,
                "host": "0.0.0.0",
                "port": 5000
            }
        }

    def __getitem__(self, key):
        """Allow dict-like access"""
        return self.get(key)

    def __setitem__(self, key, value):
        """Allow dict-like assignment"""
        self.set(key, value)
