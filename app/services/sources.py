from pathlib import Path
import yaml


def load_sources(path: Path) -> list[dict]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    return payload.get("sources", [])
