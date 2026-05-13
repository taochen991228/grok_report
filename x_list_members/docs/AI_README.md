# AI Reading Guide

Use this file when another AI needs to read and classify exported X list members.

## Start Here

Read the index first:

```text
data/exports/ai_lists_index.json
```

GitHub URL:

```text
https://github.com/taochen991228/grok_report/blob/main/x_list_members/data/exports/ai_lists_index.json
```

The index tells you which lists exist and where each list's context file lives.

## Per-List Context

Each list has:

```text
data/exports/lists/x_list_<list_id>/ai_context.json
```

This is the preferred file for classification. It contains:

- `list.list_id`: unique X list ID.
- `list.name`: human readable list name.
- `list.ai_output_heading`: top-level heading AI should use in final reports.
- `list.category`: owner-defined category.
- `list.tags`: owner-defined tags.
- `list.source_url`: original X list URL.
- `member_count`: number of extracted members.
- `handles`: simple `@username` array.
- `members`: full extracted profile objects.

## Classification Rule

When classifying AI results:

1. Use `list.list_id` as the stable primary key.
2. Use `list.ai_output_heading` as the top-level heading in final output.
3. Use `list.category` and `list.tags` as grouping hints inside that heading.
4. Use member profile fields only after the list metadata.
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
