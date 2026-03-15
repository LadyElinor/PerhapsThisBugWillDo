param(
    [string]$RepoPath = ".",
    [string]$Scope = "weevil-lunar",
    [string]$Message = "cleanup: park local workspace noise"
)

$ErrorActionPreference = "Stop"

Push-Location $RepoPath
try {
    $root = git rev-parse --show-toplevel
    if (-not $root) { throw "Not inside a git repository." }

    Write-Host "[clean-pause] repo root: $root"
    Write-Host "[clean-pause] scope: $Scope"

    # 1) Stash scoped changes (tracked + untracked)
    git stash push -u -m $Message -- $Scope

    # 2) Reset scoped tracked files
    git reset HEAD -- $Scope | Out-Null
    git checkout -- $Scope

    # 3) Remove scoped untracked files/directories
    git clean -fd -- $Scope

    Write-Host "[clean-pause] done"
    Write-Host "[clean-pause] latest stash:"
    git stash list | Select-Object -First 1
}
finally {
    Pop-Location
}
