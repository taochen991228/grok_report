#!/usr/bin/env python3
"""
Extract X/Twitter list members from a ListMembers GraphQL JSON response.

Examples:
  python scripts/extract_x_list_members.py --format handles-json
  python scripts/extract_x_list_members.py --format handles-txt
  python scripts/extract_x_list_members.py --format all
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


LIST_ID = "2053756758662033590"
DEFAULT_INPUT = f"data/raw/x_list_{LIST_ID}_members_response.json"
DEFAULT_EXPORT_DIR = "data/exports"


def walk_values(value: Any):
    """Yield every nested dict/list value in a JSON-like object."""
    yield value
    if isinstance(value, dict):
        for child in value.values():
            yield from walk_values(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_values(child)


def get_user_result(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None

    if value.get("__typename") == "User" and value.get("rest_id"):
        return value

    user_results = value.get("user_results")
    if isinstance(user_results, dict):
        result = user_results.get("result")
        if isinstance(result, dict) and result.get("__typename") == "User":
            return result

    return None


def extract_members(data: Any) -> list[dict[str, Any]]:
    members: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    for node in walk_values(data):
        user = get_user_result(node)
        if not user:
            continue

        rest_id = str(user.get("rest_id") or "")
        if not rest_id or rest_id in seen_ids:
            continue
        seen_ids.add(rest_id)

        core = user.get("core") if isinstance(user.get("core"), dict) else {}
        legacy = user.get("legacy") if isinstance(user.get("legacy"), dict) else {}
        verification = user.get("verification") if isinstance(user.get("verification"), dict) else {}
        avatar = user.get("avatar") if isinstance(user.get("avatar"), dict) else {}

        screen_name = core.get("screen_name") or legacy.get("screen_name") or ""
        name = core.get("name") or legacy.get("name") or ""
        description = legacy.get("description") or ""

        members.append(
            {
                "id": rest_id,
                "name": name,
                "screen_name": screen_name,
                "url": f"https://x.com/{screen_name}" if screen_name else "",
                "description": description,
                "followers_count": legacy.get("followers_count"),
                "friends_count": legacy.get("friends_count"),
                "statuses_count": legacy.get("statuses_count"),
                "listed_count": legacy.get("listed_count"),
                "created_at": core.get("created_at") or legacy.get("created_at"),
                "verified": bool(verification.get("verified") or legacy.get("verified")),
                "blue_verified": bool(user.get("is_blue_verified")),
                "protected": bool((user.get("privacy") or {}).get("protected", legacy.get("protected", False))),
                "profile_image_url": avatar.get("image_url") or legacy.get("profile_image_url_https"),
            }
        )

    return members


def extract_cursors(data: Any) -> dict[str, str]:
    cursors: dict[str, str] = {}
    for node in walk_values(data):
        if not isinstance(node, dict):
            continue
        if node.get("__typename") != "TimelineTimelineCursor":
            continue
        cursor_type = node.get("cursorType")
        value = node.get("value")
        if cursor_type and value:
            cursors[str(cursor_type).lower()] = str(value)
    return cursors


def render_txt(members: list[dict[str, Any]]) -> str:
    lines = []
    for index, member in enumerate(members, 1):
        handle = f"@{member['screen_name']}" if member["screen_name"] else "(no handle)"
        name = member["name"] or ""
        url = member["url"] or ""
        lines.append(f"{index}. {handle}\t{name}\t{url}")
    return "\n".join(lines) + "\n"


def get_handles(members: list[dict[str, Any]]) -> list[str]:
    return [f"@{member['screen_name']}" for member in members if member.get("screen_name")]


def render_handles_txt(members: list[dict[str, Any]]) -> str:
    return "\n".join(get_handles(members)) + "\n"


def render_handles_md(members: list[dict[str, Any]]) -> str:
    lines = ["# X List Members", ""]
    lines.extend(f"- {handle}" for handle in get_handles(members))
    return "\n".join(lines) + "\n"


def render_md(members: list[dict[str, Any]]) -> str:
    lines = [
        "| # | Handle | Name | Followers | Following | Verified | URL |",
        "|---:|---|---|---:|---:|---|---|",
    ]
    for index, member in enumerate(members, 1):
        handle = f"@{member['screen_name']}" if member["screen_name"] else ""
        name = str(member["name"] or "").replace("|", "\\|").replace("\n", " ")
        followers = member["followers_count"] if member["followers_count"] is not None else ""
        following = member["friends_count"] if member["friends_count"] is not None else ""
        verified = "yes" if member["verified"] or member["blue_verified"] else ""
        url = member["url"]
        handle_cell = f"[{handle}]({url})" if handle and url else handle
        lines.append(f"| {index} | {handle_cell} | {name} | {followers} | {following} | {verified} | {url} |")
    return "\n".join(lines) + "\n"


def write_output(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    print(f"Wrote {path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract members from an X/Twitter ListMembers GraphQL response.")
    parser.add_argument("input", nargs="?", default=DEFAULT_INPUT, help=f"Input JSON file, default: {DEFAULT_INPUT}")
    parser.add_argument(
        "--format",
        choices=("handles-json", "handles-txt", "handles-md", "full-json", "full-txt", "full-md", "all"),
        default="handles-json",
        help="Output format. handles-json is the recommended copy/paste format.",
    )
    parser.add_argument("--output", help="Output file path. Not used with --format all unless omitted.")
    parser.add_argument("--include-cursors", action="store_true", help="Include top/bottom cursors in JSON output")
    args = parser.parse_args()

    input_path = Path(args.input)
    data = json.loads(input_path.read_text(encoding="utf-8-sig"))
    members = extract_members(data)
    cursors = extract_cursors(data)

    export_dir = Path(DEFAULT_EXPORT_DIR)
    output_prefix = f"x_list_{LIST_ID}_members"

    if args.format == "all":
        write_output(
            export_dir / f"{output_prefix}_handles.json",
            json.dumps(get_handles(members), ensure_ascii=False, indent=2) + "\n",
        )
        write_output(export_dir / f"{output_prefix}_handles.txt", render_handles_txt(members))
        write_output(export_dir / f"{output_prefix}_handles.md", render_handles_md(members))
        write_output(
            export_dir / f"{output_prefix}_full.json",
            json.dumps({"count": len(members), "members": members, "cursors": cursors}, ensure_ascii=False, indent=2) + "\n",
        )
        write_output(export_dir / f"{output_prefix}_full.txt", render_txt(members))
        write_output(export_dir / f"{output_prefix}_full.md", render_md(members))
        return

    if args.format == "handles-json":
        text = json.dumps(get_handles(members), ensure_ascii=False, indent=2) + "\n"
        default_output = export_dir / f"{output_prefix}_handles.json"
    elif args.format == "handles-txt":
        text = render_handles_txt(members)
        default_output = export_dir / f"{output_prefix}_handles.txt"
    elif args.format == "handles-md":
        text = render_handles_md(members)
        default_output = export_dir / f"{output_prefix}_handles.md"
    elif args.format == "full-json":
        payload: Any = {"count": len(members), "members": members}
        if args.include_cursors:
            payload["cursors"] = cursors
        text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
        default_output = export_dir / f"{output_prefix}_full.json"
    elif args.format == "full-txt":
        text = render_txt(members)
        default_output = export_dir / f"{output_prefix}_full.txt"
    else:
        text = render_md(members)
        default_output = export_dir / f"{output_prefix}_full.md"

    output_path = Path(args.output) if args.output else default_output
    write_output(output_path, text)


if __name__ == "__main__":
    main()
