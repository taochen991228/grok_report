param(
    [string]$RepoUrl = "https://github.com/taochen991228/grok_report.git",
    [string]$Branch = "main",
    [string]$TargetDir = "x_list_members",
    [string]$WorkDir = "",
    [string]$CommitMessage = "update x list member exports"
)

$ErrorActionPreference = "Stop"

function Resolve-ProjectRoot {
    $scriptDir = Split-Path -Parent $PSCommandPath
    return (Resolve-Path (Join-Path $scriptDir "..")).Path
}

function Copy-ProjectFile {
    param(
        [string]$ProjectRoot,
        [string]$RelativePath,
        [string]$DestinationRoot
    )

    $source = Join-Path $ProjectRoot $RelativePath
    if (-not (Test-Path -LiteralPath $source)) {
        Write-Host "Skip missing: $RelativePath"
        return
    }

    $destination = Join-Path $DestinationRoot $RelativePath
    $destinationParent = Split-Path -Parent $destination
    New-Item -ItemType Directory -Force -Path $destinationParent | Out-Null
    Copy-Item -LiteralPath $source -Destination $destination -Force
}

function Assert-InsideDirectory {
    param(
        [string]$ChildPath,
        [string]$ParentPath
    )

    $resolvedChild = [System.IO.Path]::GetFullPath($ChildPath)
    $resolvedParent = [System.IO.Path]::GetFullPath($ParentPath)
    if (-not $resolvedChild.StartsWith($resolvedParent, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Unsafe path: $resolvedChild is outside $resolvedParent"
    }
}

function Invoke-Git {
    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$Args
    )

    git @Args
    if ($LASTEXITCODE -ne 0) {
        throw "git $($Args -join ' ') failed with exit code $LASTEXITCODE"
    }
}

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw "git is not installed or not available in PATH."
}

$projectRoot = Resolve-ProjectRoot
if (-not $WorkDir) {
    $WorkDir = Join-Path $projectRoot ".github_upload\grok_report"
}
$workDirParent = Split-Path -Parent $WorkDir
New-Item -ItemType Directory -Force -Path $workDirParent | Out-Null

if (-not (Test-Path -LiteralPath $WorkDir)) {
    Invoke-Git clone --branch $Branch $RepoUrl $WorkDir
}

if (-not (Test-Path -LiteralPath $WorkDir)) {
    throw "Clone directory was not created: $WorkDir"
}

Push-Location $WorkDir
try {
    Invoke-Git fetch origin $Branch
    Invoke-Git checkout $Branch
    Invoke-Git pull --ff-only origin $Branch

    Invoke-Git config user.name "taochen991228"
    Invoke-Git config user.email "taochen991228@users.noreply.github.com"

    $targetPath = Join-Path $WorkDir $TargetDir
    Assert-InsideDirectory -ChildPath $targetPath -ParentPath $WorkDir

    if (Test-Path -LiteralPath $targetPath) {
        Remove-Item -LiteralPath $targetPath -Recurse -Force
    }
    New-Item -ItemType Directory -Force -Path $targetPath | Out-Null

    $filesToUpload = @(
        "README.md",
        "docs\GITHUB_UPLOAD_ARCHITECTURE.md",
        "scripts\extract_x_list_members.py",
        "scripts\sync_to_github.ps1",
        "data\raw\x_list_2053756758662033590_members_response.json",
        "data\exports\recommended_members.json",
        "data\exports\x_list_2053756758662033590_members_handles.json",
        "data\exports\x_list_2053756758662033590_members_handles.txt",
        "data\exports\x_list_2053756758662033590_members_handles.md",
        "data\exports\x_list_2053756758662033590_members_full.json",
        "data\exports\x_list_2053756758662033590_members_full.txt",
        "data\exports\x_list_2053756758662033590_members_full.md"
    )

    foreach ($file in $filesToUpload) {
        Copy-ProjectFile -ProjectRoot $projectRoot -RelativePath $file -DestinationRoot $targetPath
    }

    Invoke-Git add -- $TargetDir

    $status = git status --porcelain
    if (-not $status) {
        Write-Host "No GitHub upload needed. Nothing changed."
        exit 0
    }

    Invoke-Git commit -m $CommitMessage
    Invoke-Git push origin $Branch

    Write-Host "Uploaded to $RepoUrl on branch $Branch under /$TargetDir"
}
finally {
    Pop-Location
}
