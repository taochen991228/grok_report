# AI Reading Guide

Use this file when another AI needs to read and classify exported X list members.

## Start Here

Read this one file:

```text
data/exports/ai_all_lists.json
```

GitHub URL:

```text
https://github.com/taochen991228/grok_report/blob/main/x_list_members/data/exports/ai_all_lists.json
```

## Data Shape

Each list object contains only:

- `list_id`: unique X list ID.
- `name`: top-level heading AI should use in final reports.
- `handles`: primary `@username` array for matching, counting, and classification.

No UID, profile description, metrics, tags, source URL, or output paths are included in the AI entry file.

## Classification Rule

When classifying AI results:

1. Use `list_id` as the stable primary key.
2. Use `name` as the top-level heading.
3. Use `handles` for statistics and matching.
4. Keep output grouped by `list_id`.

Current top-level headings:

- `陶辰-消息kol`
- `ash-每日重要信息`

## Example

```json
{
  "list_id": "2053094822601425075",
  "name": "ash-每日重要信息",
  "matched_handles": ["@example"],
  "classification": "alpha-research"
}
```
