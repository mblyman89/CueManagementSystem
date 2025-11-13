"""
Configuration Manager for CuePi
Handles persistent storage of user preferences and settings
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any


class ConfigManager:
    """Manages application configuration"""

    def __init__(self):
        self.config_dir = Path.home() / "Library" / "Application Support" / "CuePi"
        self.config_file = self.config_dir / "config.json"
        self._ensure_config_dir()
        self._config = self._load_config()

    def _ensure_config_dir(self):
        """Create config directory if it doesn't exist"""
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading config: {e}")
                return self._default_config()
        return self._default_config()

    def _default_config(self) -> Dict[str, Any]:
        """Return default configuration"""
        return {
            "spleeter_python_path": None,
            "first_launch": True,
            "last_spleeter_check": None,
            "app_version": "1.0.0",
            "spleeter_model": "5stems",
            "auto_select_drums": True,
            "save_stems": False,
            "cache_separations": True,
            "max_cache_size_mb": 1000,
            "temp_cleanup": True
        }

    def save(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self._config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self._config.get(key, default)

    def set(self, key: str, value: Any):
        """Set configuration value"""
        self._config[key] = value
        self.save()

    def get_spleeter_path(self) -> Optional[str]:
        """Get Spleeter Python path"""
        return self._config.get("spleeter_python_path")

    def set_spleeter_path(self, path: str):
        """Set Spleeter Python path"""
        self._config["spleeter_python_path"] = path
        self._config["first_launch"] = False
        self.save()

    def is_first_launch(self) -> bool:
        """Check if this is the first launch"""
        return self._config.get("first_launch", True)

    def mark_launched(self):
        """Mark that the app has been launched"""
        self._config["first_launch"] = False
        self.save()


# Global config instance
_config_manager = None


def get_config_manager() -> ConfigManager:
    """Get global config manager instance"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager