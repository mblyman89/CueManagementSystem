"""
Enhanced Settings Configuration for Firework Cue Management System
================================================================

This module provides comprehensive configuration management with:
- Environment-specific settings
- Hardware configuration templates
- Safety and security parameters
- Performance optimization settings
- User interface customization
- Logging and monitoring configuration

Author: NinjaTeach AI Team
Version: 1.0.0
License: MIT
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum


class Environment(Enum):
    """Application environment types"""
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TESTING = "testing"


class LogLevel(Enum):
    """Logging levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class ApplicationConfig:
    """Core application configuration"""
    name: str = "Firework Cue Management System"
    version: str = "1.0.0"
    environment: Environment = Environment.DEVELOPMENT
    debug_mode: bool = False
    log_level: LogLevel = LogLevel.INFO
    auto_save_interval: int = 300  # seconds
    backup_enabled: bool = True
    performance_monitoring: bool = False


@dataclass
class DatabaseConfig:
    """Database configuration settings"""
    name: str = "firework_cues.db"
    backup_enabled: bool = True
    backup_interval_hours: int = 24
    max_backups: int = 7
    vacuum_on_startup: bool = True
    connection_timeout: int = 30
    max_connections: int = 10


@dataclass
class AudioConfig:
    """Audio processing configuration"""
    sample_rate: int = 44100
    hop_length: int = 512
    frame_length: int = 2048
    onset_threshold: float = 0.3
    peak_threshold: float = 0.5
    min_peak_distance: float = 0.1
    max_file_size_mb: int = 500
    supported_formats: List[str] = field(default_factory=lambda: [
        "mp3", "wav", "flac", "ogg", "m4a", "aac", "wma"
    ])
    cache_analysis: bool = True
    parallel_processing: bool = True
    max_processing_threads: int = 4


@dataclass
class MQTTConfig:
    """MQTT communication configuration"""
    default_host: str = "localhost"
    default_port: int = 1883
    keepalive: int = 60
    qos: int = 2  # Exactly once delivery
    username_required: bool = False
    password_required: bool = False
    tls_enabled: bool = False
    cert_file: Optional[str] = None
    key_file: Optional[str] = None
    ca_file: Optional[str] = None
    reconnect_delay_min: int = 1
    reconnect_delay_max: int = 60
    message_timeout: int = 10
    max_queued_messages: int = 1000


@dataclass
class GPIOConfig:
    """GPIO pin configuration for Raspberry Pi"""
    data_pin: int = 17
    latch_pin: int = 27
    clock_pin: int = 22
    reset_pin: int = 23
    enable_pin: int = 24
    emergency_stop_pin: int = 25
    status_led_pin: int = 26
    buzzer_pin: int = 19
    pull_up_resistors: bool = True
    debounce_time: float = 0.05


@dataclass
class SafetyConfig:
    """Safety and security configuration"""
    min_cue_delay: float = 0.1  # Minimum delay between cues (seconds)
    max_simultaneous_outputs: int = 16
    emergency_stop_timeout: float = 1.0
    confirmation_required: bool = True
    two_person_rule: bool = False  # Require two operators for execution
    safety_interlock_enabled: bool = True
    max_show_duration: int = 3600  # Maximum show duration in seconds
    auto_stop_on_error: bool = True
    hardware_watchdog_timeout: float = 5.0
    command_verification_required: bool = True


@dataclass
class UIThemeConfig:
    """User interface theme configuration"""
    primary_color: str = "#2E86AB"
    secondary_color: str = "#A23B72"
    accent_color: str = "#F18F01"
    background_color: str = "#FFFFFF"
    text_color: str = "#333333"
    success_color: str = "#28A745"
    warning_color: str = "#FFC107"
    error_color: str = "#DC3545"
    info_color: str = "#17A2B8"


@dataclass
class UIWindowConfig:
    """Window and layout configuration"""
    default_width: int = 1200
    default_height: int = 800
    min_width: int = 800
    min_height: int = 600
    max_width: int = 1920
    max_height: int = 1080
    remember_size: bool = True
    remember_position: bool = True
    fullscreen_available: bool = True
    always_on_top: bool = False


@dataclass
class UIFontConfig:
    """Font configuration"""
    default_family: str = "Arial"
    default_size: int = 10
    header_size: int = 12
    button_size: int = 10
    table_size: int = 9
    monospace_family: str = "Courier New"
    bold_headers: bool = True


@dataclass
class ShowGenerationConfig:
    """Show generation algorithm configuration"""
    max_cues: int = 1000
    default_complexity: str = "moderate"
    default_style: str = "classical"
    auto_save_enabled: bool = True
    preview_enabled: bool = True
    beat_sensitivity: float = 0.7
    rhythm_analysis_enabled: bool = True
    spectral_analysis_enabled: bool = True
    machine_learning_enabled: bool = True
    template_matching_enabled: bool = True


@dataclass
class PerformanceConfig:
    """Performance optimization settings"""
    max_memory_usage_mb: int = 2048
    cpu_usage_limit_percent: int = 80
    disk_cache_size_mb: int = 512
    network_timeout: int = 30
    ui_refresh_rate: int = 60  # FPS
    audio_buffer_size: int = 1024
    parallel_processing_enabled: bool = True
    hardware_acceleration_enabled: bool = True


@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: LogLevel = LogLevel.INFO
    file_enabled: bool = True
    console_enabled: bool = True
    max_file_size_mb: int = 10
    max_backup_files: int = 5
    log_format: str = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"
    performance_logging: bool = False
    security_logging: bool = True


class EnhancedSettings:
    """Enhanced settings manager with environment support"""

    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or Path(__file__).parent
        self.environment = self._detect_environment()
        self._load_configuration()

    def _detect_environment(self) -> Environment:
        """Detect current environment from environment variables"""
        env_name = os.getenv("CUE_SYSTEM_ENV", "development").lower()
        try:
            return Environment(env_name)
        except ValueError:
            return Environment.DEVELOPMENT

    def _load_configuration(self):
        """Load configuration based on environment"""
        # Load base configuration
        self.application = ApplicationConfig()
        self.database = DatabaseConfig()
        self.audio = AudioConfig()
        self.mqtt = MQTTConfig()
        self.gpio = GPIOConfig()
        self.safety = SafetyConfig()
        self.ui_theme = UIThemeConfig()
        self.ui_window = UIWindowConfig()
        self.ui_font = UIFontConfig()
        self.show_generation = ShowGenerationConfig()
        self.performance = PerformanceConfig()
        self.logging = LoggingConfig()

        # Apply environment-specific overrides
        self._apply_environment_overrides()

        # Load user customizations if available
        self._load_user_customizations()

    def _apply_environment_overrides(self):
        """Apply environment-specific configuration overrides"""
        if self.environment == Environment.DEVELOPMENT:
            self.application.debug_mode = True
            self.application.log_level = LogLevel.DEBUG
            self.logging.level = LogLevel.DEBUG
            self.logging.performance_logging = True
            self.safety.confirmation_required = False
            self.performance.parallel_processing_enabled = False

        elif self.environment == Environment.PRODUCTION:
            self.application.debug_mode = False
            self.application.log_level = LogLevel.INFO
            self.application.backup_enabled = True
            self.application.performance_monitoring = True
            self.logging.level = LogLevel.INFO
            self.logging.security_logging = True
            self.safety.confirmation_required = True
            self.safety.two_person_rule = True
            self.safety.safety_interlock_enabled = True
            self.mqtt.tls_enabled = True
            self.mqtt.username_required = True
            self.mqtt.password_required = True

        elif self.environment == Environment.TESTING:
            self.application.debug_mode = True
            self.application.log_level = LogLevel.DEBUG
            self.logging.level = LogLevel.DEBUG
            self.safety.confirmation_required = False
            self.performance.parallel_processing_enabled = False
            self.show_generation.max_cues = 100  # Smaller for testing

    def _load_user_customizations(self):
        """Load user-specific customizations from JSON files"""
        customization_files = [
            "user_settings.json",
            "hardware_config.json",
            "ui_preferences.json"
        ]

        for filename in customization_files:
            file_path = self.config_dir / filename
            if file_path.exists():
                try:
                    with open(file_path, 'r') as f:
                        customizations = json.load(f)
                    self._apply_customizations(customizations)
                except Exception as e:
                    print(f"Warning: Failed to load {filename}: {e}")

    def _apply_customizations(self, customizations: Dict[str, Any]):
        """Apply user customizations to configuration"""
        for section, settings in customizations.items():
            if hasattr(self, section):
                config_obj = getattr(self, section)
                for key, value in settings.items():
                    if hasattr(config_obj, key):
                        setattr(config_obj, key, value)

    def save_user_preferences(self, preferences: Dict[str, Any]):
        """Save user preferences to file"""
        prefs_file = self.config_dir / "user_settings.json"
        try:
            with open(prefs_file, 'w') as f:
                json.dump(preferences, f, indent=4)
        except Exception as e:
            print(f"Error saving user preferences: {e}")

    def get_hardware_template(self, template_name: str) -> Optional[Dict[str, Any]]:
        """Get hardware configuration template"""
        templates_file = self.config_dir / "hardware_templates.json"
        if templates_file.exists():
            try:
                with open(templates_file, 'r') as f:
                    templates = json.load(f)
                return templates.get(template_name)
            except Exception as e:
                print(f"Error loading hardware template: {e}")
        return None

    def get_show_template(self, template_name: str) -> Optional[Dict[str, Any]]:
        """Get show configuration template"""
        templates_file = self.config_dir / "show_templates.json"
        if templates_file.exists():
            try:
                with open(templates_file, 'r') as f:
                    templates = json.load(f)
                return templates.get(template_name)
            except Exception as e:
                print(f"Error loading show template: {e}")
        return None

    def validate_configuration(self) -> List[str]:
        """Validate current configuration and return list of issues"""
        issues = []

        # Validate safety settings
        if self.safety.min_cue_delay < 0.05:
            issues.append("Minimum cue delay is too small (< 0.05s)")

        if self.safety.max_simultaneous_outputs > 64:
            issues.append("Maximum simultaneous outputs exceeds safe limit (64)")

        # Validate audio settings
        if self.audio.sample_rate not in [22050, 44100, 48000, 96000]:
            issues.append("Unusual sample rate may cause compatibility issues")

        # Validate performance settings
        if self.performance.max_memory_usage_mb < 512:
            issues.append("Memory limit may be too low for proper operation")

        # Validate MQTT settings
        if self.environment == Environment.PRODUCTION:
            if not self.mqtt.tls_enabled:
                issues.append("TLS should be enabled in production environment")
            if not self.mqtt.username_required:
                issues.append("Authentication should be required in production")

        return issues

    def export_configuration(self) -> Dict[str, Any]:
        """Export current configuration to dictionary"""
        return {
            "environment": self.environment.value,
            "application": self.application.__dict__,
            "database": self.database.__dict__,
            "audio": self.audio.__dict__,
            "mqtt": self.mqtt.__dict__,
            "gpio": self.gpio.__dict__,
            "safety": self.safety.__dict__,
            "ui_theme": self.ui_theme.__dict__,
            "ui_window": self.ui_window.__dict__,
            "ui_font": self.ui_font.__dict__,
            "show_generation": self.show_generation.__dict__,
            "performance": self.performance.__dict__,
            "logging": self.logging.__dict__
        }


# Global settings instance
settings = EnhancedSettings()

# Legacy compatibility - maintain original settings structure
APP_NAME = settings.application.name
APP_VERSION = settings.application.version
DATABASE_NAME = settings.database.name
MAX_CUES = settings.show_generation.max_cues

# Table settings
TABLE_COLUMNS = [
    "CUE #",
    "TYPE",
    "# OF OUTPUTS",
    "OUTPUTS",
    "DELAY",
    "DURATION",
    "EXECUTE TIME"
]

# Button settings
BUTTON_NAMES = [
    "EXECUTE CUE",
    "EXECUTE ALL",
    "STOP",
    "PAUSE",
    "RESUME",
    "MODE",
    "CREATE CUE",
    "EDIT CUE",
    "DELETE CUE",
    "DELETE ALL",
    "MUSIC",
    "GENERATE SHOW",
    "EXPORT SHOW",
    "SAVE SHOW",
    "EXIT"
]

# Hardware settings for backward compatibility
MQTT_DEFAULT_HOST = settings.mqtt.default_host
MQTT_DEFAULT_PORT = settings.mqtt.default_port
GPIO_DATA_PIN = settings.gpio.data_pin
GPIO_LATCH_PIN = settings.gpio.latch_pin
GPIO_CLOCK_PIN = settings.gpio.clock_pin

# Safety settings
MIN_CUE_DELAY = settings.safety.min_cue_delay
MAX_SIMULTANEOUS_OUTPUTS = settings.safety.max_simultaneous_outputs
EMERGENCY_STOP_TIMEOUT = settings.safety.emergency_stop_timeout

# Audio settings
SAMPLE_RATE = settings.audio.sample_rate
HOP_LENGTH = settings.audio.hop_length
ONSET_THRESHOLD = settings.audio.onset_threshold


def get_settings() -> EnhancedSettings:
    """Get the global settings instance"""
    return settings


def reload_settings():
    """Reload settings from configuration files"""
    global settings
    settings = EnhancedSettings()


def set_environment(env: Environment):
    """Set the application environment"""
    os.environ["CUE_SYSTEM_ENV"] = env.value
    reload_settings()


# Configuration validation on import
if __name__ == "__main__":
    # Validate configuration when run directly
    issues = settings.validate_configuration()
    if issues:
        print("Configuration Issues Found:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("Configuration validation passed!")

    # Print current configuration summary
    print(f"\nCurrent Configuration:")
    print(f"  Environment: {settings.environment.value}")
    print(f"  Debug Mode: {settings.application.debug_mode}")
    print(f"  Log Level: {settings.logging.level.value}")
    print(f"  MQTT Host: {settings.mqtt.default_host}")
    print(f"  Safety Confirmation: {settings.safety.confirmation_required}")