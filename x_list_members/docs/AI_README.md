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
- `list.category`: owner-defined category.
- `list.tags`: owner-defined tags.
- `list.source_url`: original X list URL.
- `member_count`: number of extracted members.
- `handles`: simple `@username` array.
- `members`: full extracted profile objects.

## Classification Rule

When classifying AI results:

1. Use `list.list_id` as the stable primary key.
2. Use `list.category` and `list.tags` as the first-level grouping hints.
3. Use member profile fields only after the list metadata.
4. Keep output grouped by `list_id` so results from different lists do not merge accidentally.

## Example Output Shape

```json
{
  "source_list_id": "2053094822601425075",
  "source_list_name": "x_list_2053094822601425075",
  "source_category": "uncategorized",
  "matched_handles": ["@example"],
  "classification": "alpha-research",
  "reason": "The matched accounts publish alpha/research content."
}
```
