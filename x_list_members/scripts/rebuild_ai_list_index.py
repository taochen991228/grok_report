#!/usr/bin/env python3
"""
Build compact AI-friendly list files.

Outputs:
  data/exports/ai_all_lists.json
  data/exports/lists/x_list_<list_id>/ai_context.json
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


EXPORT_DIR = Path("data/exports")
LISTS_DIR = EXPORT_DIR / "lists"
LIST_CONFIG = Path("config/lists.json")
LIST_DIR_PATTERN = re.compile(r"^x_list_(\d+)$")


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {path}")


def load_list_config() -> dict[str, dict[str, Any]]:
    data = load_json(LIST_CONFIG, {"lists": []})
    result: dict[str, dict[str, Any]] = {}
    for item in data.get("lists", []):
        if not isinstance(item, dict):
            continue
        list_id = str(item.get("list_id") or "")
        if list_id:
            result[list_id] = item
    return result


def discover_list_dirs() -> list[tuple[str, Path]]:
    if not LISTS_DIR.exists():
        return []

    list_dirs: list[tuple[str, Path]] = []
    for path in LISTS_DIR.iterdir():
        if not path.is_dir():
            continue
        match = LIST_DIR_PATTERN.match(path.name)
        if match:
            list_dirs.append((match.group(1), path))
    return sorted(list_dirs)


def build_context(list_id: str, list_dir: Path, config: dict[str, Any]) -> dict[str, Any]:
    handles = load_json(list_dir / "recommended_members.json", [])

    return {
        "list_id": list_id,
        "name": config.get("name") or f"x_list_{list_id}",
        "handles": handles,
    }


def main() -> int:
    configs = load_list_config()
    contexts = []

    for list_id, list_dir in discover_list_dirs():
        context = build_context(list_id, list_dir, configs.get(list_id, {}))
        write_json(list_dir / "ai_context.json", context)
        contexts.append(context)

    all_lists = {
        "lists": contexts,
    }

    write_json(EXPORT_DIR / "ai_lists_index.json", all_lists)
    write_json(EXPORT_DIR / "ai_all_lists.json", all_lists)
    print(f"Indexed {len(contexts)} lists")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
