# GitHub Upload Architecture

Target repository:

```text
https://github.com/taochen991228/grok_report/tree/main
```

## Goal

Upload the X list member extraction project and exported data to GitHub in a clean, repeatable structure.

## Recommended Repository Layout

Inside the GitHub repository, keep this project under one folder:

```text
grok_report/
  x_list_members/
    .gitignore
    README.md
    config/
      x_headers.example.json
    scripts/
      extract_x_list_members.py
      fetch_x_list_members.py
      sync_to_github.ps1
    data/
      raw/
        x_list_2053756758662033590_members_response.json
      exports/
        recommended_members.json
        x_list_2053756758662033590_members_handles.json
        x_list_2053756758662033590_members_handles.txt
        x_list_2053756758662033590_members_handles.md
        x_list_2053756758662033590_members_full.json
        x_list_2053756758662033590_members_full.txt
        x_list_2053756758662033590_members_full.md
    docs/
      GITHUB_UPLOAD_ARCHITECTURE.md
```

## Data Flow

```text
X ListMembers API response
        |
        v
data/raw/x_list_2053756758662033590_members_response.json
        |
        v
scripts/extract_x_list_members.py
        |
        v
data/exports/recommended_members.json
data/exports/x_list_2053756758662033590_members_handles.*
data/exports/x_list_2053756758662033590_members_full.*
        |
        v
scripts/sync_to_github.ps1
        |
        v
GitHub: taochen991228/grok_report/x_list_members
```

## File Naming Rules

- `x_list_2053756758662033590_members_response.json`: original X GraphQL response.
- `recommended_members.json`: clean recommended account list, easiest to copy and reuse.
- `x_list_2053756758662033590_members_handles.json`: standard account-list export.
- `x_list_2053756758662033590_members_handles.txt`: one account per line.
- `x_list_2053756758662033590_members_handles.md`: Markdown account list.
- `x_list_2053756758662033590_members_full.json`: full extracted profile fields.
- `x_list_2053756758662033590_members_full.txt`: readable full profile list.
- `x_list_2053756758662033590_members_full.md`: Markdown table with profile links.

## Upload Strategy

Use a temporary clone instead of turning the local working folder into the GitHub repo.

Why:

- keeps `C:\Users\tjs\Desktop\grok` clean;
- avoids overwriting unrelated repository files;
- uploads only the intended project files;
- works even if the GitHub repository already has other content.

Default temporary clone path:

```text
C:\Users\tjs\Desktop\grok\.github_upload\grok_report
```

## Upload Command

From this folder:

```powershell
.\scripts\sync_to_github.ps1
```

Custom commit message:

```powershell
.\scripts\sync_to_github.ps1 -CommitMessage "update x list member exports"
```

## Authentication

The script uses normal `git clone` and `git push`.

If GitHub asks for login:

- use Git Credential Manager if it opens a browser login;
- or use a GitHub personal access token when prompted for the password.

The repository must allow your GitHub account to push to `taochen991228/grok_report`.
