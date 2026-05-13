#!/usr/bin/env python3
"""
Build AI-friendly index files for all exported X lists.

Outputs:
  data/exports/ai_lists_index.json
  data/exports/ai_all_lists.json
  data/exports/lists/x_list_<list_id>/ai_context.json
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
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


def build_context(list_id: str, list_dir: Path, config: dict[str, Any], generated_at: str) -> dict[str, Any]:
    handles = load_json(list_dir / "recommended_members.json", [])
    full = load_json(list_dir / "members_full.json", {})
    full_members = full.get("members", []) if isinstance(full, dict) else []
    members = [
        {
            "uid": str(member.get("id") or ""),
            "handle": f"@{member.get('screen_name')}" if member.get("screen_name") else "",
            "url": member.get("url") or "",
        }
        for member in full_members
        if isinstance(member, dict) and member.get("id")
    ]
    member_uids = [member["uid"] for member in members]
    source_url = config.get("source_url") or f"https://x.com/i/lists/{list_id}"

    return {
        "schema_version": "1.0",
        "generated_at": generated_at,
        "list": {
            "list_id": list_id,
            "name": config.get("name") or f"x_list_{list_id}",
            "ai_output_heading": config.get("ai_output_heading") or config.get("name") or f"x_list_{list_id}",
            "category": config.get("category") or "uncategorized",
            "tags": config.get("tags") or [],
            "description": config.get("description") or "",
            "source_url": source_url,
            "github_dir": f"x_list_members/data/exports/lists/x_list_{list_id}",
        },
        "outputs": {
            "recommended_members": f"data/exports/lists/x_list_{list_id}/recommended_members.json",
            "members_full": f"data/exports/lists/x_list_{list_id}/members_full.json",
            "members_handles": f"data/exports/lists/x_list_{list_id}/members_handles.json",
        },
        "member_count": len(handles),
        "member_uids": member_uids,
        "handles": handles,
        "members": members,
    }


def main() -> int:
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    configs = load_list_config()
    contexts = []

    for list_id, list_dir in discover_list_dirs():
        context = build_context(list_id, list_dir, configs.get(list_id, {}), generated_at)
        write_json(list_dir / "ai_context.json", context)
        contexts.append(context)

    index = {
        "schema_version": "1.0",
        "generated_at": generated_at,
        "purpose": "AI-readable index of exported X list member datasets.",
        "how_to_use": "Read lists[].ai_context_json first. Use list.ai_output_heading as the top-level heading when reporting results. For classification/statistics, use member_uids or members[].uid. Read members_full_json only when profile details are explicitly needed.",
        "lists": [
            {
                "list_id": context["list"]["list_id"],
                "name": context["list"]["name"],
                "ai_output_heading": context["list"]["ai_output_heading"],
                "category": context["list"]["category"],
                "tags": context["list"]["tags"],
                "description": context["list"]["description"],
                "source_url": context["list"]["source_url"],
                "member_count": context["member_count"],
                "ai_context_json": f"data/exports/lists/x_list_{context['list']['list_id']}/ai_context.json",
                "recommended_members_json": f"data/exports/lists/x_list_{context['list']['list_id']}/recommended_members.json",
                "members_full_json": f"data/exports/lists/x_list_{context['list']['list_id']}/members_full.json",
            }
            for context in contexts
        ],
    }

    all_lists = {
        "schema_version": "1.0",
        "generated_at": generated_at,
        "reporting_rule": "When giving results, group by list.ai_output_heading as the top-level title. Do not merge accounts from different list_id values.",
        "lists": contexts,
    }

    write_json(EXPORT_DIR / "ai_lists_index.json", index)
    write_json(EXPORT_DIR / "ai_all_lists.json", all_lists)
    print(f"Indexed {len(contexts)} lists")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
