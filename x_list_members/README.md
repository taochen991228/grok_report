# X List Member Extractor

Extract members from an X/Twitter ListMembers GraphQL response.

List URL:

```text
https://x.com/i/lists/2053756758662033590/members
```

## Directory Layout

```text
grok/
  README.md
  scripts/
    extract_x_list_members.py
  data/
    raw/
      x_list_2053756758662033590_members_response.json
    exports/
      x_list_2053756758662033590_members_handles.json
      x_list_2053756758662033590_members_handles.txt
      x_list_2053756758662033590_members_handles.md
      x_list_2053756758662033590_members_full.json
      x_list_2053756758662033590_members_full.txt
      x_list_2053756758662033590_members_full.md
```

## Recommended Output

Use JSON handles when you want the clean copy/paste format:

```powershell
python .\scripts\extract_x_list_members.py --format handles-json
```

Output:

```json
[
  "@username1",
  "@username2",
  "@username3"
]
```

## Other Commands

Export all formats:

```powershell
python .\scripts\extract_x_list_members.py --format all
```

Export one format:

```powershell
python .\scripts\extract_x_list_members.py --format handles-txt
python .\scripts\extract_x_list_members.py --format handles-md
python .\scripts\extract_x_list_members.py --format full-json
python .\scripts\extract_x_list_members.py --format full-txt
python .\scripts\extract_x_list_members.py --format full-md
```

## Upload To GitHub

Target repository:

```text
https://github.com/taochen991228/grok_report/tree/main
```

Upload this project and exported data into `x_list_members/` inside that repository:

```powershell
.\scripts\sync_to_github.ps1
```

Use a custom commit message:

```powershell
.\scripts\sync_to_github.ps1 -CommitMessage "update x list members"
```

## File Naming

- `*_members_response.json`: raw GraphQL API response from X.
- `*_members_handles.json`: recommended simple JSON array of `@handles`.
- `*_members_handles.txt`: one handle per line.
- `*_members_handles.md`: Markdown bullet list.
- `*_members_full.json`: full extracted profile fields, useful for later filtering or ranking.
- `*_members_full.txt`: readable full member list.
- `*_members_full.md`: Markdown table with profile links.
