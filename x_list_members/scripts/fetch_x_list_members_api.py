#!/usr/bin/env python3
"""
Fetch X/Twitter list members with the official X API v2.

Requires an X Developer App Bearer Token. This does not use browser cookies.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from extract_x_list_members import get_handles, render_handles_md, render_handles_txt, render_md, render_txt


LIST_ID_PATTERN = re.compile(r"(?:x\.com|twitter\.com)/i/lists/(\d+)|^(\d+)$")
DEFAULT_USER_FIELDS = ",".join(
    [
        "created_at",
        "description",
        "entities",
        "id",
        "location",
        "name",
        "profile_image_url",
        "protected",
        "public_metrics",
        "url",
        "username",
        "verified",
        "verified_type",
    ]
)


def parse_list_id(value: str) -> str:
    match = LIST_ID_PATTERN.search(value.strip())
    if not match:
        raise ValueError(f"could not parse list id from: {value}")
    return next(group for group in match.groups() if group)


def normalize_bearer_token(token: str) -> str:
    token = token.strip()
    if not token:
        raise ValueError("missing bearer token. Set X_API_BEARER_TOKEN or pass --bearer-token")
    if token.lower().startswith("bearer "):
        return token
    return f"Bearer {token}"


def build_url(list_id: str, max_results: int, user_fields: str, pagination_token: str | None) -> str:
    query: dict[str, Any] = {
        "max_results": max_results,
        "user.fields": user_fields,
    }
    if pagination_token:
        query["pagination_token"] = pagination_token
    return f"https://api.x.com/2/lists/{list_id}/members?{urlencode(query)}"


def fetch_json(url: str, bearer_token: str, timeout: int) -> dict[str, Any]:
    request = Request(
        url,
        headers={
            "Authorization": normalize_bearer_token(bearer_token),
            "User-Agent": "grok-report-list-member-fetcher/1.0",
        },
        method="GET",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8")
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {detail[:1000]}") from exc
    except URLError as exc:
        raise RuntimeError(f"network error: {exc}") from exc

    data = json.loads(body)
    if isinstance(data, dict) and data.get("errors") and not data.get("data"):
        raise RuntimeError(json.dumps(data["errors"], ensure_ascii=False, indent=2))
    if not isinstance(data, dict):
        raise RuntimeError("unexpected response: not a JSON object")
    return data


def convert_user(user: dict[str, Any]) -> dict[str, Any]:
    metrics = user.get("public_metrics") if isinstance(user.get("public_metrics"), dict) else {}
    username = user.get("username") or ""
    return {
        "id": str(user.get("id") or ""),
        "name": user.get("name") or "",
        "screen_name": username,
        "url": f"https://x.com/{username}" if username else "",
        "description": user.get("description") or "",
        "followers_count": metrics.get("followers_count"),
        "friends_count": metrics.get("following_count"),
        "statuses_count": metrics.get("tweet_count"),
        "listed_count": metrics.get("listed_count"),
        "created_at": user.get("created_at"),
        "verified": bool(user.get("verified")),
        "blue_verified": user.get("verified_type") == "blue",
        "protected": bool(user.get("protected")),
        "profile_image_url": user.get("profile_image_url"),
        "location": user.get("location") or "",
        "verified_type": user.get("verified_type"),
    }


def dedupe_members(existing: list[dict[str, Any]], new_members: list[dict[str, Any]]) -> int:
    seen = {member["id"] for member in existing if member.get("id")}
    added = 0
    for member in new_members:
        member_id = member.get("id")
        if not member_id or member_id in seen:
            continue
        existing.append(member)
        seen.add(member_id)
        added += 1
    return added


def archive_existing_outputs(list_id: str, export_dir: Path, raw_dir: Path) -> Path | None:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_dir = Path("data/archive") / timestamp / f"x_list_{list_id}"
    paths = [
        export_dir / "recommended_members.json",
        export_dir / f"x_list_{list_id}_members_handles.json",
        export_dir / f"x_list_{list_id}_members_handles.txt",
        export_dir / f"x_list_{list_id}_members_handles.md",
        export_dir / f"x_list_{list_id}_members_full.json",
        export_dir / f"x_list_{list_id}_members_full.txt",
        export_dir / f"x_list_{list_id}_members_full.md",
        raw_dir / f"x_list_{list_id}_members_api_pages.json",
    ]
    existing_paths = [path for path in paths if path.exists()]
    if not existing_paths:
        return None

    archive_dir.mkdir(parents=True, exist_ok=True)
    for path in existing_paths:
        shutil.copy2(path, archive_dir / path.name)
    return archive_dir


def write_outputs(list_id: str, members: list[dict[str, Any]], pages: list[dict[str, Any]], last_meta: dict[str, Any], archive: bool) -> None:
    raw_dir = Path("data/raw")
    export_dir = Path("data/exports")
    list_export_dir = export_dir / "lists" / f"x_list_{list_id}"
    raw_dir.mkdir(parents=True, exist_ok=True)
    export_dir.mkdir(parents=True, exist_ok=True)
    list_export_dir.mkdir(parents=True, exist_ok=True)

    prefix = f"x_list_{list_id}_members"
    handles_json = json.dumps(get_handles(members), ensure_ascii=False, indent=2) + "\n"
    full_json = json.dumps({"count": len(members), "members": members, "meta": last_meta}, ensure_ascii=False, indent=2) + "\n"
    archive_dir = archive_existing_outputs(list_id, export_dir, raw_dir) if archive else None
    if archive_dir:
        print(f"Archived previous outputs to {archive_dir}")

    (raw_dir / f"{prefix}_api_pages.json").write_text(json.dumps({"pages": pages}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (export_dir / "recommended_members.json").write_text(handles_json, encoding="utf-8")
    (export_dir / f"{prefix}_handles.json").write_text(handles_json, encoding="utf-8")
    (export_dir / f"{prefix}_handles.txt").write_text(render_handles_txt(members), encoding="utf-8")
    (export_dir / f"{prefix}_handles.md").write_text(render_handles_md(members), encoding="utf-8")
    (export_dir / f"{prefix}_full.json").write_text(full_json, encoding="utf-8")
    (export_dir / f"{prefix}_full.txt").write_text(render_txt(members), encoding="utf-8")
    (export_dir / f"{prefix}_full.md").write_text(render_md(members), encoding="utf-8")
    (list_export_dir / "recommended_members.json").write_text(handles_json, encoding="utf-8")
    (list_export_dir / "members_handles.json").write_text(handles_json, encoding="utf-8")
    (list_export_dir / "members_handles.txt").write_text(render_handles_txt(members), encoding="utf-8")
    (list_export_dir / "members_handles.md").write_text(render_handles_md(members), encoding="utf-8")
    (list_export_dir / "members_full.json").write_text(full_json, encoding="utf-8")
    (list_export_dir / "members_full.txt").write_text(render_txt(members), encoding="utf-8")
    (list_export_dir / "members_full.md").write_text(render_md(members), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch members from an X/Twitter list with the official X API.")
    parser.add_argument("list", help="X list id or URL, for example: https://x.com/i/lists/2053756758662033590")
    parser.add_argument("--bearer-token", default=os.getenv("X_API_BEARER_TOKEN", ""), help="Official X API Bearer Token. Defaults to X_API_BEARER_TOKEN env var")
    parser.add_argument("--max-results", type=int, default=100, help="Members per request, 1-100")
    parser.add_argument("--max-pages", type=int, default=50, help="Safety limit for pagination")
    parser.add_argument("--sleep", type=float, default=1.0, help="Seconds to sleep between pages")
    parser.add_argument("--timeout", type=int, default=30, help="HTTP timeout seconds")
    parser.add_argument("--user-fields", default=DEFAULT_USER_FIELDS, help="Comma-separated X API user.fields")
    parser.add_argument("--no-archive", action="store_true", help="Do not archive old outputs before replacing them")
    args = parser.parse_args()

    list_id = parse_list_id(args.list)
    bearer_token = normalize_bearer_token(args.bearer_token)
    all_members: list[dict[str, Any]] = []
    pages: list[dict[str, Any]] = []
    next_token: str | None = None
    last_meta: dict[str, Any] = {}

    for page_number in range(1, args.max_pages + 1):
        url = build_url(list_id, args.max_results, args.user_fields, next_token)
        print(f"Fetching API page {page_number}...")
        page = fetch_json(url, bearer_token, args.timeout)
        pages.append(page)

        users = page.get("data") if isinstance(page.get("data"), list) else []
        page_members = [convert_user(user) for user in users if isinstance(user, dict)]
        added = dedupe_members(all_members, page_members)
        last_meta = page.get("meta") if isinstance(page.get("meta"), dict) else {}
        next_token = last_meta.get("next_token")
        print(f"  page members: {len(page_members)}, new: {added}, total: {len(all_members)}")

        if not next_token or added == 0:
            break
        time.sleep(args.sleep)

    write_outputs(list_id, all_members, pages, last_meta, archive=not args.no_archive)
    print(f"Done. Exported {len(all_members)} members to data/exports")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
