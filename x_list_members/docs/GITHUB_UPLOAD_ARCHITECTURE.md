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
      fetch_x_list_members_api.py
      fetch_x_list_members.py
      update_list_and_publish.ps1
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
      archive/
        20260513_120000/
          x_list_2053756758662033590/
            recommended_members.json
            x_list_2053756758662033590_members_handles.json
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
        | archive old outputs before replacement
        v
data/archive/<timestamp>/x_list_2053756758662033590/
        |
        v
scripts/sync_to_github.ps1
        |
        v
GitHub: taochen991228/grok_report/x_list_members
```

## Official API Flow

Recommended when you want to avoid browser cookies:

```text
X API Bearer Token
        |
        v
GET https://api.x.com/2/lists/<list_id>/members
        |
        v
scripts/fetch_x_list_members_api.py
        |
        v
data/exports/recommended_members.json
        |
        v
scripts/sync_to_github.ps1
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
- `data/archive/<timestamp>/x_list_<list_id>/`: previous exported version before replacement.

## Fixed Latest Link

Keep this link stable and always replace the file behind it with the latest list members:

```text
https://github.com/taochen991228/grok_report/blob/main/x_list_members/data/exports/recommended_members.json
```

Use:

```powershell
powershell.exe -ExecutionPolicy Bypass -File .\scripts\update_list_and_publish.ps1 -List "https://x.com/i/lists/2053756758662033590"
```

Official API version:

```powershell
$env:X_API_BEARER_TOKEN="YOUR_X_API_BEARER_TOKEN"
powershell.exe -ExecutionPolicy Bypass -File .\scripts\update_list_and_publish.ps1 -UseOfficialApi -List "https://x.com/i/lists/2053756758662033590"
```

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
