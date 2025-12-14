from pathlib import Path
from typing import Any, Dict

import yaml


class Config:
    """Configuration manager for loading and accessing YAML configuration."""

    def __init__(self, config_path: str | None = None):
        """
        Initialize the configuration manager.

        Args:
            config_path: Path to the YAML configuration file.
                        If None, looks for config.yaml in the project root.
        """
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config.yaml"
        else:
            config_path = Path(config_path)

        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        self._config = self._load_yaml(config_path)

    @staticmethod
    def _load_yaml(path: Path) -> Dict[str, Any]:
        """Load YAML configuration from file."""
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation.

        Args:
            key: Configuration key (supports nested keys with dots, e.g., "email.username")
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        keys = key.split(".")
        value = self._config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default

        return value

    @property
    def email_username(self) -> str:
        """Get email username."""
        return self.get("email.username", "")

    @property
    def email_password(self) -> str:
        """Get email password."""
        return self.get("email.password", "")

    @property
    def email_allowed_subjects(self) -> list[str]:
        """Get allowed email subjects."""
        return self.get("email.allowed_subjects", [])

    @property
    def zen_money_api_key(self) -> str:
        """Get ZenMoney API key."""
        return self.get("zen_money.api_key", "")

    @property
    def zen_money_user_id(self) -> int:
        """Get ZenMoney user ID."""
        return self.get("zen_money.user_id", 0)

    @property
    def currency_config(self) -> Dict[str, Any]:
        """Get currency configuration."""
        return self.get("currency_config", {})

    @property
    def category_config(self) -> Dict[str, str]:
        """Get category configuration."""
        return self.get("category_config", {})

    def __getitem__(self, key: str) -> Any:
        """Allow dictionary-style access."""
        return self.get(key)


# Global config instance
_config_instance: Config | None = None


def get_config(config_path: str | None = None) -> Config:
    """
    Get or create the global config instance.

    Args:
        config_path: Path to YAML config file (only used on first call)

    Returns:
        Config instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config(config_path)
    return _config_instance
