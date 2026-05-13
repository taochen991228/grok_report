#!/usr/bin/env python3
"""
Fetch X/Twitter list members automatically and export handles/full data.

Credentials are read from environment variables or a local JSON headers file.
Do not commit your cookie/token file to GitHub.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from extract_x_list_members import extract_cursors, extract_members, get_handles, render_handles_md, render_handles_txt, render_md, render_txt


DEFAULT_OPERATION_ID = "oIetCo19avgStX4mOnGsPg"
DEFAULT_OPERATION_NAME = "ListMembers"
DEFAULT_BEARER = (
    "Bearer AAAAAAAAAAAAAAAAAAAAA"
    "NRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1"
    "Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA"
)

FEATURES = {
    "rweb_video_screen_enabled": False,
    "rweb_cashtags_enabled": True,
    "profile_label_improvements_pcf_label_in_post_enabled": True,
    "responsive_web_profile_redirect_enabled": False,
    "rweb_tipjar_consumption_enabled": False,
    "verified_phone_label_enabled": False,
    "creator_subscriptions_tweet_preview_api_enabled": True,
    "responsive_web_graphql_timeline_navigation_enabled": True,
    "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
    "premium_content_api_read_enabled": False,
    "communities_web_enable_tweet_community_results_fetch": True,
    "c9s_tweet_anatomy_moderator_badge_enabled": True,
    "responsive_web_grok_analyze_button_fetch_trends_enabled": False,
    "responsive_web_grok_analyze_post_followups_enabled": True,
    "rweb_cashtags_composer_attachment_enabled": True,
    "responsive_web_jetfuel_frame": True,
    "responsive_web_grok_share_attachment_enabled": True,
    "responsive_web_grok_annotations_enabled": True,
    "articles_preview_enabled": True,
    "responsive_web_edit_tweet_api_enabled": True,
    "rweb_conversational_replies_downvote_enabled": False,
    "graphql_is_translatable_rweb_tweet_is_translatable_enabled": True,
    "view_counts_everywhere_api_enabled": True,
    "longform_notetweets_consumption_enabled": True,
    "responsive_web_twitter_article_tweet_consumption_enabled": True,
    "content_disclosure_indicator_enabled": True,
    "content_disclosure_ai_generated_indicator_enabled": True,
    "responsive_web_grok_show_grok_translated_post": True,
    "responsive_web_grok_analysis_button_from_backend": True,
    "post_ctas_fetch_enabled": True,
    "freedom_of_speech_not_reach_fetch_enabled": True,
    "standardized_nudges_misinfo": True,
    "tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled": True,
    "longform_notetweets_rich_text_read_enabled": True,
    "longform_notetweets_inline_media_enabled": False,
    "responsive_web_grok_image_annotation_enabled": True,
    "responsive_web_grok_imagine_annotation_enabled": True,
    "responsive_web_grok_community_note_auto_translation_is_enabled": True,
    "responsive_web_enhance_cards_enabled": False,
}


def load_headers_file(path: str | None) -> dict[str, str]:
    if not path:
        return {}
    headers_path = Path(path)
    if not headers_path.exists():
        raise FileNotFoundError(f"headers file not found: {headers_path}")
    data = json.loads(headers_path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError("headers file must be a JSON object")
    return {str(key).lower(): str(value) for key, value in data.items() if value is not None}


def parse_cookie_value(cookie: str, key: str) -> str:
    for part in cookie.split(";"):
        if "=" not in part:
            continue
        name, value = part.strip().split("=", 1)
        if name == key:
            return value
    return ""


def build_headers(args: argparse.Namespace) -> dict[str, str]:
    file_headers = load_headers_file(args.headers_file)
    cookie = args.cookie or os.getenv("X_COOKIE") or file_headers.get("cookie", "")
    authorization = args.authorization or os.getenv("X_AUTHORIZATION") or file_headers.get("authorization", DEFAULT_BEARER)
    csrf_token = args.csrf_token or os.getenv("X_CSRF_TOKEN") or file_headers.get("x-csrf-token", "")

    if not csrf_token and cookie:
        csrf_token = parse_cookie_value(cookie, "ct0")

    if not cookie:
        raise ValueError("missing X cookie. Set X_COOKIE or use --headers-file config/x_headers.json")
    if not csrf_token:
        raise ValueError("missing csrf token. Set X_CSRF_TOKEN or include ct0 in your cookie")

    headers = {
        "accept": "*/*",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
        "authorization": authorization,
        "content-type": "application/json",
        "cookie": cookie,
        "referer": f"https://x.com/i/lists/{args.list_id}/members",
        "user-agent": args.user_agent,
        "x-csrf-token": csrf_token,
        "x-twitter-active-user": "yes",
        "x-twitter-auth-type": "OAuth2Session",
        "x-twitter-client-language": "en",
    }
    headers.update({key: value for key, value in file_headers.items() if key not in {"cookie", "authorization", "x-csrf-token"}})
    return headers


def build_url(list_id: str, count: int, cursor: str | None, operation_id: str) -> str:
    variables: dict[str, Any] = {"listId": list_id, "count": count}
    if cursor:
        variables["cursor"] = cursor

    query = urlencode(
        {
            "variables": json.dumps(variables, separators=(",", ":")),
            "features": json.dumps(FEATURES, separators=(",", ":")),
        }
    )
    return f"https://x.com/i/api/graphql/{operation_id}/{DEFAULT_OPERATION_NAME}?{query}"


def fetch_json(url: str, headers: dict[str, str], timeout: int) -> dict[str, Any]:
    request = Request(url, headers=headers, method="GET")
    try:
        with urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8")
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {detail[:800]}") from exc
    except URLError as exc:
        raise RuntimeError(f"network error: {exc}") from exc

    data = json.loads(body)
    if isinstance(data, dict) and data.get("errors"):
        raise RuntimeError(json.dumps(data["errors"], ensure_ascii=False, indent=2))
    if not isinstance(data, dict):
        raise RuntimeError("unexpected response: not a JSON object")
    return data


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


def write_outputs(list_id: str, members: list[dict[str, Any]], pages: list[dict[str, Any]], cursors: dict[str, str]) -> None:
    raw_dir = Path("data/raw")
    export_dir = Path("data/exports")
    raw_dir.mkdir(parents=True, exist_ok=True)
    export_dir.mkdir(parents=True, exist_ok=True)

    prefix = f"x_list_{list_id}_members"
    (raw_dir / f"{prefix}_pages.json").write_text(json.dumps({"pages": pages}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (export_dir / "recommended_members.json").write_text(json.dumps(get_handles(members), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (export_dir / f"{prefix}_handles.json").write_text(json.dumps(get_handles(members), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (export_dir / f"{prefix}_handles.txt").write_text(render_handles_txt(members), encoding="utf-8")
    (export_dir / f"{prefix}_handles.md").write_text(render_handles_md(members), encoding="utf-8")
    (export_dir / f"{prefix}_full.json").write_text(
        json.dumps({"count": len(members), "members": members, "cursors": cursors}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (export_dir / f"{prefix}_full.txt").write_text(render_txt(members), encoding="utf-8")
    (export_dir / f"{prefix}_full.md").write_text(render_md(members), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch members from an X/Twitter list.")
    parser.add_argument("list_id", help="X list id, for example: 2053756758662033590")
    parser.add_argument("--count", type=int, default=100, help="Members per request")
    parser.add_argument("--max-pages", type=int, default=50, help="Safety limit for pagination")
    parser.add_argument("--sleep", type=float, default=1.0, help="Seconds to sleep between pages")
    parser.add_argument("--timeout", type=int, default=30, help="HTTP timeout seconds")
    parser.add_argument("--operation-id", default=DEFAULT_OPERATION_ID, help="GraphQL operation id")
    parser.add_argument("--headers-file", help="JSON file containing cookie, x-csrf-token, authorization, etc.")
    parser.add_argument("--cookie", help="Raw X cookie string")
    parser.add_argument("--csrf-token", help="X csrf token. If omitted, ct0 is read from cookie")
    parser.add_argument("--authorization", help="X authorization bearer. Defaults to public web bearer")
    parser.add_argument("--user-agent", default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36")
    args = parser.parse_args()

    headers = build_headers(args)
    all_members: list[dict[str, Any]] = []
    pages: list[dict[str, Any]] = []
    cursor: str | None = None
    final_cursors: dict[str, str] = {}
    seen_cursors: set[str] = set()

    for page_number in range(1, args.max_pages + 1):
        url = build_url(args.list_id, args.count, cursor, args.operation_id)
        print(f"Fetching page {page_number}...")
        page = fetch_json(url, headers, args.timeout)
        pages.append(page)

        page_members = extract_members(page)
        added = dedupe_members(all_members, page_members)
        final_cursors = extract_cursors(page)
        next_cursor = final_cursors.get("bottom")
        print(f"  page members: {len(page_members)}, new: {added}, total: {len(all_members)}")

        if not next_cursor or next_cursor in seen_cursors or added == 0:
            break

        seen_cursors.add(next_cursor)
        cursor = next_cursor
        time.sleep(args.sleep)

    write_outputs(args.list_id, all_members, pages, final_cursors)
    print(f"Done. Exported {len(all_members)} members to data/exports")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
