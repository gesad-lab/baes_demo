import os
import shutil
from pathlib import Path

import pytest
from dotenv import load_dotenv

from baes.core.managed_system_manager import ManagedSystemManager
from config import Config

load_dotenv(override=True)


@pytest.mark.unit
class TestConfigurationIntegrity:
    """Validate that generated managed system uses centralized configuration values."""

    TESTS_TEMP_DIR = Path(__file__).parent.parent / ".temp"

    def setup_method(self):
        # Ensure temp directory root exists
        self.TESTS_TEMP_DIR.mkdir(exist_ok=True, parents=True)

        # Create unique temp dir
        self.temp_dir = self.TESTS_TEMP_DIR / f"config_integrity_{os.getpid()}_{id(self)}"
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
        self.temp_dir.mkdir(parents=True)

        # Override MANAGED_SYSTEM_PATH for the manager
        self.original_managed_path = os.environ.get("MANAGED_SYSTEM_PATH")
        os.environ["MANAGED_SYSTEM_PATH"] = str(self.temp_dir / "managed_system")

        # Instantiate manager and scaffold structure
        self.manager = ManagedSystemManager()
        assert self.manager.ensure_managed_system_structure() is True

    def teardown_method(self):
        if self.original_managed_path is not None:
            os.environ["MANAGED_SYSTEM_PATH"] = self.original_managed_path
        else:
            os.environ.pop("MANAGED_SYSTEM_PATH", None)

        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    # ------------------------------------------------------------------
    # Actual tests
    # ------------------------------------------------------------------

    def test_env_file_ports_match_centralized_config(self):
        """Managed system .env should reflect the centralized Config values."""
        env_path = self.manager.managed_system_path / ".env"
        assert env_path.exists(), ".env file not generated"

        # Parse simple KEY=VALUE pairs (ignore comments / blank lines)
        env_values = {}
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            env_values[key.strip()] = value.strip()

        assert env_values.get("API_PORT") == str(Config.API_PORT), "API_PORT mismatch in .env"
        assert env_values.get("UI_PORT") == str(Config.UI_PORT), "UI_PORT mismatch in .env"
        assert env_values.get("API_HOST") == Config.API_HOST, "API_HOST mismatch in .env"
        assert env_values.get("UI_HOST") == Config.UI_HOST, "UI_HOST mismatch in .env"

    def test_copied_config_files_exist(self):
        """config.py should be copied to app/ and ui/ directories for import safety."""
        root_copy = self.manager.managed_system_path / "config.py"
        app_copy = self.manager.managed_system_path / "app" / "config.py"
        ui_copy = self.manager.managed_system_path / "ui" / "config.py"

        for path in (root_copy, app_copy, ui_copy):
            assert path.exists(), f"Missing copied config at {path}"

    def test_start_script_uses_centralized_ports(self):
        """start_servers.sh script should reference Config-driven ports, not hardcoded defaults."""
        start_script = self.manager.managed_system_path / "start_servers.sh"
        assert start_script.exists(), "start_servers.sh not generated"
        content = start_script.read_text()
        assert str(Config.API_PORT) in content, "API_PORT not reflected in start_servers.sh"
        assert str(Config.UI_PORT) in content, "UI_PORT not reflected in start_servers.sh"
