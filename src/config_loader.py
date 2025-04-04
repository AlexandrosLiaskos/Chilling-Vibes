import yaml
from pathlib import Path

class ConfigLoader:
    """
    Loads YAML configuration for the automation.
    """
    def __init__(self, config_path="config.yaml"):
        self.config_path = Path(config_path)
        self.data = self.load_config()
        self._normalize_paths()

    def load_config(self):
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        with open(self.config_path, "r") as f:
            return yaml.safe_load(f)

    def _normalize_paths(self):
        """
        Normalize all template paths to absolute OS-correct paths.
        """
        templates = self.data.get("templates", {})
        for key, path_str in templates.items():
            try:
                norm_path = str(Path(path_str).resolve())
                templates[key] = norm_path
            except Exception:
                # Leave as-is if any error
                pass

    def get(self, *keys, default=None):
        """
        Access nested config values with fallback default.
        """
        d = self.data
        for key in keys:
            if isinstance(d, dict) and key in d:
                d = d[key]
            else:
                return default
        return d