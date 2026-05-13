# AI Reading Guide

Use this file when another AI needs to read and classify exported X list members.

## Start Here

For most AI workflows, read this one file:

```text
data/exports/ai_all_lists.json
```

GitHub URL:

```text
https://github.com/taochen991228/grok_report/blob/main/x_list_members/data/exports/ai_all_lists.json
```

This file includes all list metadata and compact members in one place.

## Optional Index

Use the index only if you want to discover list files without loading all members:

```text
data/exports/ai_lists_index.json
```

## Data Fields

Each list object contains:

- `list.list_id`: unique X list ID.
- `list.name`: human readable list name.
- `list.ai_output_heading`: top-level heading AI should use in final reports.
- `list.category`: owner-defined category.
- `list.tags`: owner-defined tags.
- `list.source_url`: original X list URL.
- `member_count`: number of extracted members.
- `handles`: primary `@username` array for matching, counting, and classification.

UIDs, profile descriptions, metrics, and URLs are intentionally not included in `ai_all_lists.json`. Read `members_full.json` only when those details are explicitly needed.

## Classification Rule

When classifying AI results:

1. Use `list.list_id` as the stable primary key.
2. Use `list.ai_output_heading` as the top-level heading in final output.
3. Use `list.category` and `list.tags` as grouping hints inside that heading.
4. Use `handles` for statistics and matching.
5. Keep output grouped by `list_id` so results from different lists do not merge accidentally.

Current top-level headings:

- `陶辰-消息kol`
- `ash-每日重要信息`

## Example Output Shape

```json
{
  "source_list_id": "2053094822601425075",
  "top_level_heading": "ash-每日重要信息",
  "source_list_name": "ash-每日重要信息",
  "source_category": "ash-每日重要信息",
  "matched_handles": ["@example"],
  "classification": "alpha-research",
  "reason": "The matched accounts publish alpha/research content."
}
```
