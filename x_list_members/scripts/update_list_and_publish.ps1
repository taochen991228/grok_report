param(
    [Parameter(Mandatory = $true)]
    [string]$List,
    [string]$HeadersFile = ".\config\x_headers.json",
    [switch]$UseOfficialApi,
    [string]$BearerToken = "",
    [int]$Count = 100,
    [int]$MaxPages = 50,
    [double]$Sleep = 1,
    [string]$CommitMessage = ""
)

$ErrorActionPreference = "Stop"

function Resolve-ProjectRoot {
    $scriptDir = Split-Path -Parent $PSCommandPath
    return (Resolve-Path (Join-Path $scriptDir "..")).Path
}

function Get-ListId {
    param([string]$Value)

    if ($Value -match "(\d+)$") {
        return $Matches[1]
    }

    if ($Value -match "/i/lists/(\d+)") {
        return $Matches[1]
    }

    throw "Could not parse list id from $Value"
}

$projectRoot = Resolve-ProjectRoot
Push-Location $projectRoot
try {
    $listId = Get-ListId -Value $List
    if (-not $CommitMessage) {
        $CommitMessage = "update x list $listId members"
    }

    if ($UseOfficialApi) {
        $apiArgs = @(".\scripts\fetch_x_list_members_api.py", $List, "--max-results", $Count, "--max-pages", $MaxPages, "--sleep", $Sleep)
        if ($BearerToken) {
            $apiArgs += @("--bearer-token", $BearerToken)
        }
        python @apiArgs
    }
    else {
        python .\scripts\fetch_x_list_members.py $List --headers-file $HeadersFile --count $Count --max-pages $MaxPages --sleep $Sleep
    }

    powershell.exe -ExecutionPolicy Bypass -File .\scripts\sync_to_github.ps1 -CommitMessage $CommitMessage

    Write-Host "Updated fixed GitHub link:"
    Write-Host "https://github.com/taochen991228/grok_report/blob/main/x_list_members/data/exports/recommended_members.json"
}
finally {
    Pop-Location
}
