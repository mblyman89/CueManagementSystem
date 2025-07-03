#!/usr/bin/env python3
"""
Enhanced Setup Script for Firework Cue Management System
========================================================

This setup script provides comprehensive installation and configuration
for the Firework Cue Management System, including:

- Dependency installation and verification
- System configuration and optimization
- Hardware setup assistance
- Development environment setup
- Testing and validation tools

Author: NinjaTeach AI Team
Version: 1.0.0
License: MIT
"""

import os
import sys
import subprocess
import platform
import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import argparse


class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class SetupManager:
    """Main setup and configuration manager"""

    def __init__(self):
        self.system_info = self._get_system_info()
        self.project_root = Path(__file__).parent
        self.config_dir = self.project_root / "config"
        self.logs_dir = self.project_root / "logs"
        self.data_dir = self.project_root / "data"

    def _get_system_info(self) -> Dict:
        """Gather system information for configuration"""
        return {
            'platform': platform.system(),
            'platform_version': platform.version(),
            'architecture': platform.machine(),
            'python_version': sys.version,
            'python_executable': sys.executable,
        }

    def print_header(self, text: str):
        """Print formatted header"""
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 60}")
        print(f"{text.center(60)}")
        print(f"{'=' * 60}{Colors.ENDC}")

    def print_success(self, text: str):
        """Print success message"""
        print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")

    def print_warning(self, text: str):
        """Print warning message"""
        print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")

    def print_error(self, text: str):
        """Print error message"""
        print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")

    def print_info(self, text: str):
        """Print info message"""
        print(f"{Colors.OKBLUE}ℹ {text}{Colors.ENDC}")

    def run_command(self, command: List[str], description: str) -> Tuple[bool, str]:
        """Run a system command and return success status and output"""
        try:
            self.print_info(f"Running: {description}")
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True
            )
            return True, result.stdout
        except subprocess.CalledProcessError as e:
            return False, e.stderr
        except FileNotFoundError:
            return False, f"Command not found: {command[0]}"

    def check_python_version(self) -> bool:
        """Check if Python version meets requirements"""
        self.print_header("Python Version Check")

        version_info = sys.version_info
        required_major, required_minor = 3, 8

        if version_info.major >= required_major and version_info.minor >= required_minor:
            self.print_success(f"Python {version_info.major}.{version_info.minor}.{version_info.micro} - OK")
            return True
        else:
            self.print_error(
                f"Python {required_major}.{required_minor}+ required, found {version_info.major}.{version_info.minor}")
            return False

    def create_directories(self):
        """Create necessary project directories"""
        self.print_header("Creating Project Directories")

        directories = [
            self.logs_dir,
            self.data_dir / "shows",
            self.data_dir / "audio",
            self.data_dir / "templates",
            self.data_dir / "exports",
            Path("resources") / "icons",
            Path("resources") / "styles",
            Path("resources") / "ui",
        ]

        for directory in directories:
            try:
                directory.mkdir(parents=True, exist_ok=True)
                self.print_success(f"Created directory: {directory}")
            except Exception as e:
                self.print_error(f"Failed to create {directory}: {e}")

    def install_dependencies(self, dev_mode: bool = False) -> bool:
        """Install Python dependencies"""
        self.print_header("Installing Dependencies")

        # Check if pip is available
        success, _ = self.run_command([sys.executable, "-m", "pip", "--version"], "Checking pip")
        if not success:
            self.print_error("pip is not available")
            return False

        # Upgrade pip first
        success, output = self.run_command(
            [sys.executable, "-m", "pip", "install", "--upgrade", "pip"],
            "Upgrading pip"
        )
        if success:
            self.print_success("pip upgraded successfully")
        else:
            self.print_warning("Failed to upgrade pip, continuing anyway")

        # Install main requirements
        requirements_file = "requirements_comprehensive.txt"
        if not Path(requirements_file).exists():
            requirements_file = "requirements.txt"

        success, output = self.run_command(
            [sys.executable, "-m", "pip", "install", "-r", requirements_file],
            f"Installing requirements from {requirements_file}"
        )

        if success:
            self.print_success("Main dependencies installed successfully")
        else:
            self.print_error(f"Failed to install dependencies: {output}")
            return False

        # Install development dependencies if requested
        if dev_mode:
            dev_packages = [
                "pytest>=7.4.0",
                "pytest-qt>=4.2.0",
                "pytest-asyncio>=0.21.0",
                "black>=23.0.0",
                "flake8>=6.0.0",
                "isort>=5.12.0",
                "mypy>=1.5.0"
            ]

            for package in dev_packages:
                success, _ = self.run_command(
                    [sys.executable, "-m", "pip", "install", package],
                    f"Installing {package}"
                )
                if success:
                    self.print_success(f"Installed {package}")
                else:
                    self.print_warning(f"Failed to install {package}")

        return True

    def install_system_dependencies(self):
        """Install system-level dependencies based on platform"""
        self.print_header("System Dependencies")

        system = self.system_info['platform']

        if system == "Linux":
            self._install_linux_dependencies()
        elif system == "Darwin":  # macOS
            self._install_macos_dependencies()
        elif system == "Windows":
            self._install_windows_dependencies()
        else:
            self.print_warning(f"Unknown platform: {system}")

    def _install_linux_dependencies(self):
        """Install Linux-specific dependencies"""
        self.print_info("Detected Linux system")

        # Check for package managers
        package_managers = [
            ("apt-get", ["sudo", "apt-get", "update"]),
            ("yum", ["sudo", "yum", "update"]),
            ("pacman", ["sudo", "pacman", "-Sy"])
        ]

        pm_found = False
        for pm, update_cmd in package_managers:
            if shutil.which(pm):
                self.print_info(f"Found package manager: {pm}")
                pm_found = True

                if pm == "apt-get":
                    packages = [
                        "python3-dev", "python3-pip", "portaudio19-dev",
                        "ffmpeg", "libavcodec-extra", "mosquitto", "mosquitto-clients"
                    ]
                    install_cmd = ["sudo", "apt-get", "install", "-y"] + packages
                elif pm == "yum":
                    packages = [
                        "python3-devel", "python3-pip", "portaudio-devel",
                        "ffmpeg", "mosquitto"
                    ]
                    install_cmd = ["sudo", "yum", "install", "-y"] + packages
                elif pm == "pacman":
                    packages = [
                        "python", "python-pip", "portaudio",
                        "ffmpeg", "mosquitto"
                    ]
                    install_cmd = ["sudo", "pacman", "-S", "--noconfirm"] + packages

                success, output = self.run_command(install_cmd, f"Installing packages with {pm}")
                if success:
                    self.print_success(f"System packages installed with {pm}")
                else:
                    self.print_warning(f"Some packages may have failed to install: {output}")
                break

        if not pm_found:
            self.print_warning("No supported package manager found. Please install dependencies manually:")
            self.print_info("- Python development headers")
            self.print_info("- PortAudio development libraries")
            self.print_info("- FFmpeg")
            self.print_info("- Mosquitto MQTT broker")

    def _install_macos_dependencies(self):
        """Install macOS-specific dependencies"""
        self.print_info("Detected macOS system")

        if shutil.which("brew"):
            self.print_info("Found Homebrew package manager")
            packages = ["portaudio", "ffmpeg", "mosquitto"]

            for package in packages:
                success, _ = self.run_command(
                    ["brew", "install", package],
                    f"Installing {package} with Homebrew"
                )
                if success:
                    self.print_success(f"Installed {package}")
                else:
                    self.print_warning(f"Failed to install {package}")
        else:
            self.print_warning("Homebrew not found. Please install manually:")
            self.print_info(
                "1. Install Homebrew: /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"")
            self.print_info("2. Run: brew install portaudio ffmpeg mosquitto")

    def _install_windows_dependencies(self):
        """Install Windows-specific dependencies"""
        self.print_info("Detected Windows system")
        self.print_warning("Windows system dependencies must be installed manually:")
        self.print_info("1. Download and install FFmpeg from https://ffmpeg.org/download.html")
        self.print_info("2. Add FFmpeg to your system PATH")
        self.print_info("3. Consider installing Windows Subsystem for Linux (WSL) for better compatibility")
        self.print_info("4. For MQTT broker, consider using Docker or a cloud service")

    def create_configuration_files(self):
        """Create enhanced configuration files"""
        self.print_header("Creating Configuration Files")

        # Enhanced settings configuration
        settings_config = {
            "application": {
                "name": "Firework Cue Management System",
                "version": "1.0.0",
                "debug_mode": False,
                "log_level": "INFO"
            },
            "database": {
                "name": "firework_cues.db",
                "backup_enabled": True,
                "backup_interval_hours": 24,
                "max_backups": 7
            },
            "audio": {
                "sample_rate": 44100,
                "hop_length": 512,
                "frame_length": 2048,
                "onset_threshold": 0.3,
                "peak_threshold": 0.5,
                "min_peak_distance": 0.1,
                "supported_formats": ["mp3", "wav", "flac", "ogg", "m4a"]
            },
            "hardware": {
                "mqtt": {
                    "default_host": "localhost",
                    "default_port": 1883,
                    "keepalive": 60,
                    "qos": 2,
                    "username_required": False,
                    "password_required": False,
                    "tls_enabled": False
                },
                "gpio": {
                    "data_pin": 17,
                    "latch_pin": 27,
                    "clock_pin": 22,
                    "reset_pin": 23,
                    "enable_pin": 24
                },
                "safety": {
                    "min_cue_delay": 0.1,
                    "max_simultaneous_outputs": 16,
                    "emergency_stop_timeout": 1.0,
                    "confirmation_required": True
                }
            },
            "ui": {
                "theme": {
                    "primary_color": "#2E86AB",
                    "secondary_color": "#A23B72",
                    "accent_color": "#F18F01",
                    "background_color": "#C73E1D"
                },
                "window": {
                    "default_width": 1200,
                    "default_height": 800,
                    "min_width": 800,
                    "min_height": 600
                },
                "fonts": {
                    "default_family": "Arial",
                    "default_size": 10,
                    "header_size": 12
                }
            },
            "show_generation": {
                "max_cues": 1000,
                "default_complexity": "moderate",
                "default_style": "classical",
                "auto_save_enabled": True,
                "preview_enabled": True
            }
        }

        # Save configuration
        config_file = self.config_dir / "enhanced_settings.json"
        try:
            with open(config_file, 'w') as f:
                json.dump(settings_config, f, indent=4)
            self.print_success(f"Created enhanced configuration: {config_file}")
        except Exception as e:
            self.print_error(f"Failed to create configuration: {e}")

        # Create environment configuration
        self._create_environment_config()

        # Create logging configuration
        self._create_logging_config()

        # Create hardware templates
        self._create_hardware_templates()

    def _create_environment_config(self):
        """Create environment-specific configuration"""
        env_config = {
            "development": {
                "debug": True,
                "log_level": "DEBUG",
                "auto_reload": True,
                "mock_hardware": True,
                "test_data_enabled": True
            },
            "production": {
                "debug": False,
                "log_level": "INFO",
                "auto_reload": False,
                "mock_hardware": False,
                "test_data_enabled": False,
                "backup_enabled": True,
                "monitoring_enabled": True
            },
            "testing": {
                "debug": True,
                "log_level": "DEBUG",
                "mock_hardware": True,
                "test_data_enabled": True,
                "fast_mode": True
            }
        }

        env_file = self.config_dir / "environments.json"
        try:
            with open(env_file, 'w') as f:
                json.dump(env_config, f, indent=4)
            self.print_success(f"Created environment configuration: {env_file}")
        except Exception as e:
            self.print_error(f"Failed to create environment config: {e}")

    def _create_logging_config(self):
        """Create logging configuration"""
        logging_config = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
                },
                "detailed": {
                    "format": "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s"
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": "INFO",
                    "formatter": "standard",
                    "stream": "ext://sys.stdout"
                },
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "DEBUG",
                    "formatter": "detailed",
                    "filename": "logs/application.log",
                    "maxBytes": 10485760,
                    "backupCount": 5
                },
                "error_file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "ERROR",
                    "formatter": "detailed",
                    "filename": "logs/errors.log",
                    "maxBytes": 10485760,
                    "backupCount": 5
                }
            },
            "loggers": {
                "": {
                    "handlers": ["console", "file"],
                    "level": "DEBUG",
                    "propagate": False
                },
                "errors": {
                    "handlers": ["error_file"],
                    "level": "ERROR",
                    "propagate": False
                }
            }
        }

        logging_file = self.config_dir / "logging.json"
        try:
            with open(logging_file, 'w') as f:
                json.dump(logging_config, f, indent=4)
            self.print_success(f"Created logging configuration: {logging_file}")
        except Exception as e:
            self.print_error(f"Failed to create logging config: {e}")

    def _create_hardware_templates(self):
        """Create hardware configuration templates"""
        hardware_templates = {
            "raspberry_pi_basic": {
                "name": "Raspberry Pi Basic Setup",
                "description": "Basic 8-output setup using single shift register",
                "mqtt": {
                    "host": "raspberrypi.local",
                    "port": 1883,
                    "client_id": "cue_system_basic"
                },
                "gpio": {
                    "data_pin": 17,
                    "latch_pin": 27,
                    "clock_pin": 22,
                    "reset_pin": 23,
                    "enable_pin": 24
                },
                "outputs": {
                    "count": 8,
                    "type": "shift_register",
                    "registers": 1
                }
            },
            "raspberry_pi_extended": {
                "name": "Raspberry Pi Extended Setup",
                "description": "Extended 32-output setup using daisy-chained shift registers",
                "mqtt": {
                    "host": "raspberrypi.local",
                    "port": 1883,
                    "client_id": "cue_system_extended"
                },
                "gpio": {
                    "data_pin": 17,
                    "latch_pin": 27,
                    "clock_pin": 22,
                    "reset_pin": 23,
                    "enable_pin": 24
                },
                "outputs": {
                    "count": 32,
                    "type": "shift_register",
                    "registers": 4
                }
            },
            "simulation_mode": {
                "name": "Simulation Mode",
                "description": "Software-only simulation for testing and development",
                "mock_hardware": True,
                "outputs": {
                    "count": 16,
                    "type": "simulation"
                }
            }
        }

        templates_file = self.config_dir / "hardware_templates.json"
        try:
            with open(templates_file, 'w') as f:
                json.dump(hardware_templates, f, indent=4)
            self.print_success(f"Created hardware templates: {templates_file}")
        except Exception as e:
            self.print_error(f"Failed to create hardware templates: {e}")

    def create_startup_scripts(self):
        """Create convenient startup scripts"""
        self.print_header("Creating Startup Scripts")

        # Python startup script
        python_script = f"""#!/usr/bin/env python3
\"\"\"
Firework Cue Management System Launcher
\"\"\"
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set environment variables
os.environ['CUE_SYSTEM_ROOT'] = str(project_root)
os.environ['CUE_SYSTEM_CONFIG'] = str(project_root / 'config')
os.environ['CUE_SYSTEM_DATA'] = str(project_root / 'data')
os.environ['CUE_SYSTEM_LOGS'] = str(project_root / 'logs')

# Import and run main application
try:
    from main import main
    main()
except ImportError as e:
    print(f"Error importing main module: {{e}}")
    print("Please ensure all dependencies are installed:")
    print("pip install -r requirements_comprehensive.txt")
    sys.exit(1)
except Exception as e:
    print(f"Error starting application: {{e}}")
    sys.exit(1)
"""

        script_file = self.project_root / "start_cue_system.py"
        try:
            with open(script_file, 'w') as f:
                f.write(python_script)
            os.chmod(script_file, 0o755)
            self.print_success(f"Created startup script: {script_file}")
        except Exception as e:
            self.print_error(f"Failed to create startup script: {e}")

        # Shell script for Unix systems
        if self.system_info['platform'] in ['Linux', 'Darwin']:
            shell_script = f"""#!/bin/bash
# Firework Cue Management System Launcher

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${{BASH_SOURCE[0]}}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Check if virtual environment exists
if [ -d "cue_system_env" ]; then
    echo "Activating virtual environment..."
    source cue_system_env/bin/activate
fi

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{{print $2}}')
echo "Using Python version: $python_version"

# Start the application
echo "Starting Firework Cue Management System..."
python3 start_cue_system.py

# Deactivate virtual environment if it was activated
if [ -n "$VIRTUAL_ENV" ]; then
    deactivate
fi
"""

            shell_file = self.project_root / "start_cue_system.sh"
            try:
                with open(shell_file, 'w') as f:
                    f.write(shell_script)
                os.chmod(shell_file, 0o755)
                self.print_success(f"Created shell launcher: {shell_file}")
            except Exception as e:
                self.print_error(f"Failed to create shell launcher: {e}")

        # Batch script for Windows
        if self.system_info['platform'] == 'Windows':
            batch_script = f"""@echo off
REM Firework Cue Management System Launcher

cd /d "%~dp0"

REM Check if virtual environment exists
if exist "cue_system_env" (
    echo Activating virtual environment...
    call cue_system_env\\Scripts\\activate.bat
)

REM Check Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set python_version=%%i
echo Using Python version: %python_version%

REM Start the application
echo Starting Firework Cue Management System...
python start_cue_system.py

REM Deactivate virtual environment if it was activated
if defined VIRTUAL_ENV (
    deactivate
)

pause
"""

            batch_file = self.project_root / "start_cue_system.bat"
            try:
                with open(batch_file, 'w') as f:
                    f.write(batch_script)
                self.print_success(f"Created batch launcher: {batch_file}")
            except Exception as e:
                self.print_error(f"Failed to create batch launcher: {e}")

    def run_tests(self):
        """Run system tests to verify installation"""
        self.print_header("Running System Tests")

        # Test Python imports
        test_imports = [
            "PySide6.QtWidgets",
            "librosa",
            "numpy",
            "scipy",
            "matplotlib",
            "paho.mqtt.client"
        ]

        for module in test_imports:
            try:
                __import__(module)
                self.print_success(f"Import test passed: {module}")
            except ImportError as e:
                self.print_error(f"Import test failed: {module} - {e}")

        # Test file creation
        test_file = self.logs_dir / "test.log"
        try:
            with open(test_file, 'w') as f:
                f.write("Test log entry\n")
            test_file.unlink()  # Clean up
            self.print_success("File system test passed")
        except Exception as e:
            self.print_error(f"File system test failed: {e}")

        # Test configuration loading
        config_file = self.config_dir / "enhanced_settings.json"
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    json.load(f)
                self.print_success("Configuration loading test passed")
            except Exception as e:
                self.print_error(f"Configuration loading test failed: {e}")

    def print_summary(self):
        """Print setup summary and next steps"""
        self.print_header("Setup Complete!")

        print(f"{Colors.OKGREEN}🎆 Firework Cue Management System Setup Complete! 🎆{Colors.ENDC}")
        print()
        print(f"{Colors.BOLD}Next Steps:{Colors.ENDC}")
        print(f"{Colors.OKBLUE}1. Start the application:{Colors.ENDC}")

        if self.system_info['platform'] == 'Windows':
            print(f"   {Colors.OKCYAN}start_cue_system.bat{Colors.ENDC}")
        else:
            print(f"   {Colors.OKCYAN}./start_cue_system.sh{Colors.ENDC}")
            print(f"   {Colors.OKCYAN}# or{Colors.ENDC}")
            print(f"   {Colors.OKCYAN}python3 start_cue_system.py{Colors.ENDC}")

        print(f"{Colors.OKBLUE}2. Read the comprehensive guide:{Colors.ENDC}")
        print(f"   {Colors.OKCYAN}COMPREHENSIVE_GUIDE.md{Colors.ENDC}")

        print(f"{Colors.OKBLUE}3. Check configuration files:{Colors.ENDC}")
        print(f"   {Colors.OKCYAN}config/enhanced_settings.json{Colors.ENDC}")
        print(f"   {Colors.OKCYAN}config/hardware_templates.json{Colors.ENDC}")

        print(f"{Colors.OKBLUE}4. For hardware setup:{Colors.ENDC}")
        print(f"   {Colors.OKCYAN}hardware/README_MQTT.md{Colors.ENDC}")

        print()
        print(f"{Colors.WARNING}Remember: Always prioritize safety when working with fireworks!{Colors.ENDC}")
        print(f"{Colors.OKGREEN}Enjoy creating spectacular shows! 🎇{Colors.ENDC}")


def main():
    """Main setup function"""
    parser = argparse.ArgumentParser(description="Enhanced setup for Firework Cue Management System")
    parser.add_argument("--dev", action="store_true", help="Install development dependencies")
    parser.add_argument("--no-system", action="store_true", help="Skip system dependency installation")
    parser.add_argument("--test-only", action="store_true", help="Run tests only")

    args = parser.parse_args()

    setup = SetupManager()

    if args.test_only:
        setup.run_tests()
        return

    # Welcome message
    setup.print_header("Firework Cue Management System Setup")
    print(f"{Colors.OKGREEN}Welcome to the enhanced setup process!{Colors.ENDC}")
    print(f"{Colors.OKBLUE}This will configure your system for optimal performance.{Colors.ENDC}")

    # System information
    setup.print_header("System Information")
    for key, value in setup.system_info.items():
        setup.print_info(f"{key}: {value}")

    # Setup steps
    success = True

    # Check Python version
    if not setup.check_python_version():
        setup.print_error("Python version check failed. Please upgrade Python.")
        return

    # Create directories
    setup.create_directories()

    # Install system dependencies
    if not args.no_system:
        setup.install_system_dependencies()

    # Install Python dependencies
    if not setup.install_dependencies(dev_mode=args.dev):
        setup.print_error("Dependency installation failed.")
        success = False

    # Create configuration files
    setup.create_configuration_files()

    # Create startup scripts
    setup.create_startup_scripts()

    # Run tests
    setup.run_tests()

    # Print summary
    if success:
        setup.print_summary()
    else:
        setup.print_error("Setup completed with errors. Please review the output above.")


if __name__ == "__main__":
    main()