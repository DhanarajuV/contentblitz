import yaml
import os


def load_config(env: str = "development") -> dict:
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    path = os.path.join(root, "config", f"{env}.yaml")
    with open(path) as f:
        return yaml.safe_load(f)


config = load_config()