<#
Preview known disposable outputs; -Apply archives them before removal.
Never selects source, environments, saved reports, or IDE/user configuration.
#>
[CmdletBinding()]
param([switch]$Apply)

$ErrorActionPreference = 'Stop'
$workspace = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$artifactRoot = Join-Path $workspace '.test-artifacts'
$configuredData = [Environment]::GetEnvironmentVariable('APP_DATA_DIR')
$configuredPath = if ($configuredData) { [IO.Path]::GetFullPath($configuredData) } else { $null }
$targets = @(Get-ChildItem -LiteralPath $workspace -Directory -Force | Where-Object {
    $_.Name -like '.pytest-*' -or $_.Name -in @('.pytest_cache', '.ruff_cache', 'build', 'dist') -or
    ($_.Name -eq 'front end' -and @(Get-ChildItem -LiteralPath $_.FullName -Force).Count -eq 0)
})
$files = @()
foreach ($target in $targets) {
    $full = [IO.Path]::GetFullPath($target.FullName)
    if ([IO.Path]::GetDirectoryName($full) -ne $workspace -or $target.LinkType) {
        throw "Refusing an unverified cleanup target: $full"
    }
    if ($configuredPath -and ($configuredPath -eq $full -or $configuredPath.StartsWith($full + '\', [StringComparison]::OrdinalIgnoreCase))) {
        throw "Cleanup target contains configured application data: $full"
    }
    # Validate each directory before descending; never follow links or junctions.
    $pending = [Collections.Generic.Stack[string]]::new()
    $pending.Push($full)
    while ($pending.Count) {
        foreach ($entry in Get-ChildItem -LiteralPath $pending.Pop() -Force) {
            if ($entry.LinkType) { throw "Refusing linked content: $($entry.FullName)" }
            if ($entry.PSIsContainer) { $pending.Push($entry.FullName) }
            else { $files += $entry }
        }
    }
}
$targets | Select-Object Name, FullName | Format-Table -AutoSize | Out-String | Write-Output
Write-Output ("Preview: {0} generated folders, {1} files. Saved data and virtual environments are excluded." -f $targets.Count, $files.Count)
if (-not $Apply -or -not $targets.Count) { return }

New-Item -ItemType Directory -Path $artifactRoot -Force | Out-Null
if ((Get-Item -LiteralPath $artifactRoot).LinkType) { throw 'Artifact directory must not be a link' }
$archivePath = Join-Path $artifactRoot ('cleanup-' + [guid]::NewGuid().ToString('N') + '.zip')
Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem
$archive = [IO.Compression.ZipFile]::Open($archivePath, [IO.Compression.ZipArchiveMode]::Create)
try {
    foreach ($file in $files) {
        $relative = $file.FullName.Substring($workspace.Length + 1).Replace('\', '/')
        [IO.Compression.ZipFileExtensions]::CreateEntryFromFile($archive, $file.FullName, $relative) | Out-Null
    }
} finally { $archive.Dispose() }
$verification = [IO.Compression.ZipFile]::OpenRead($archivePath)
try {
    if ($verification.Entries.Count -ne $files.Count) { throw 'Archive verification failed' }
    $lengths = @{}
    foreach ($entry in $verification.Entries) { $lengths[$entry.FullName] = $entry.Length }
    foreach ($file in $files) {
        $relative = $file.FullName.Substring($workspace.Length + 1).Replace('\', '/')
        if ($lengths[$relative] -ne (Get-Item -LiteralPath $file.FullName).Length) {
            throw "Source changed during backup; no folders removed: $relative"
        }
    }
} finally { $verification.Dispose() }
$removed = 0
foreach ($target in $targets) {
    # Targets were resolved and validated above; use only native literal-path deletion.
    try {
        Remove-Item -LiteralPath $target.FullName -Recurse -Force
        $removed++
    } catch {
        Write-Warning "Kept locked or inaccessible folder: $($target.FullName). $($_.Exception.Message)"
    }
}
Write-Output "Removed $removed of $($targets.Count) generated folders. Recoverable archive: $archivePath"
