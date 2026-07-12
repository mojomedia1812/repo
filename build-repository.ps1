[CmdletBinding()]
param(
    [Parameter()]
    [ValidatePattern('^https?://')]
    [string]$BaseUrl = 'https://mojomedia1812.github.io/repo/'
)

$ErrorActionPreference = 'Stop'

$root = $PSScriptRoot
$addonSource = Join-Path $root 'plugin.video.xvault'
$repositorySource = Join-Path $root 'repository.xvault'
$tmdbHelperPlayersSource = Join-Path $root 'tmdbhelper-players'
$output = Join-Path $root 'kodi-repository'

if (-not (Test-Path -LiteralPath (Join-Path $addonSource 'addon.xml'))) {
    throw 'plugin.video.xvault/addon.xml wurde nicht gefunden.'
}

if (-not $BaseUrl.EndsWith('/')) {
    $BaseUrl += '/'
}

$resolvedRoot = [System.IO.Path]::GetFullPath($root)
$resolvedOutput = [System.IO.Path]::GetFullPath($output)
if (-not $resolvedOutput.StartsWith($resolvedRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Ungueltiges Ausgabeverzeichnis: $resolvedOutput"
}

if (Test-Path -LiteralPath $output) {
    Remove-Item -LiteralPath $output -Recurse -Force
}
New-Item -ItemType Directory -Path $output | Out-Null

function Get-AddonMetadata {
    param([Parameter(Mandatory)][string]$AddonXml)

    [xml]$xml = Get-Content -LiteralPath $AddonXml -Raw -Encoding UTF8
    return @{
        Id = [string]$xml.addon.id
        Version = [string]$xml.addon.version
        Xml = $xml
    }
}

$addonExcludedParts = @(
    '.git',
    '__pycache__',
    'docs',
    'api',
    'cookies',
    'scrapers_source',
    'stream-link-auditor',
    'tools',
    '.github',
    '.pytest_cache',
    '.venv'
)
$addonExcludedFiles = @(
    '.gitignore',
    'DEPENDENCIES.md',
    'README.md'
)
$addonExcludedRelative = @(
    'resources/media/_movies-search.png',
    'resources/media/_series-search.png',
    'resources/media/box-office.png',
    'resources/media/downloads.png',
    'resources/media/highly-rated.png',
    'resources/media/in-theaters.png',
    'resources/media/most-popular.png',
    'resources/media/most-voted.png',
    'resources/media/plugin-info.png',
    'resources/media/resolveurl.png',
    'resources/media/tmdb_search.png',
    'resources/media/tools.png',
    'resources/media/url.png',
    'sites/README.md'
)
$addonExcludedSuffixes = @(
    '.pyc',
    '.pyo',
    '.zip'
)

function Test-AddonPackageFile {
    param(
        [Parameter(Mandatory)][System.IO.FileInfo]$File,
        [Parameter(Mandatory)][string]$RelativePath
    )

    $relative = $RelativePath.Replace('\', '/')
    if ($addonExcludedRelative -contains $relative) {
        return $false
    }
    foreach ($part in ($relative -split '/')) {
        if ($addonExcludedParts -contains $part) {
            return $false
        }
    }
    if ($addonExcludedFiles -contains $File.Name) {
        return $false
    }
    if ($addonExcludedSuffixes -contains $File.Extension.ToLowerInvariant()) {
        return $false
    }
    return $true
}

function New-AddonPackage {
    param(
        [Parameter(Mandatory)][string]$SourceDirectory,
        [Parameter(Mandatory)][string]$DestinationDirectory
    )

    $metadata = Get-AddonMetadata (Join-Path $SourceDirectory 'addon.xml')
    New-Item -ItemType Directory -Path $DestinationDirectory -Force | Out-Null

    $zipName = '{0}-{1}.zip' -f $metadata.Id, $metadata.Version
    $zipPath = Join-Path $DestinationDirectory $zipName
    Add-Type -AssemblyName System.IO.Compression
    Add-Type -AssemblyName System.IO.Compression.FileSystem

    $sourceRoot = [System.IO.Path]::GetFullPath($SourceDirectory).TrimEnd('\')
    $sourceName = Split-Path -Leaf $sourceRoot
    $zipStream = [System.IO.File]::Open(
        $zipPath,
        [System.IO.FileMode]::Create,
        [System.IO.FileAccess]::ReadWrite,
        [System.IO.FileShare]::None
    )
    try {
        $archive = [System.IO.Compression.ZipArchive]::new(
            $zipStream,
            [System.IO.Compression.ZipArchiveMode]::Create,
            $false
        )
        try {
            foreach ($file in Get-ChildItem -LiteralPath $sourceRoot -File -Recurse) {
                $relativePath = $file.FullName.Substring($sourceRoot.Length).TrimStart('\')
                if ($metadata.Id -eq 'plugin.video.xvault' -and -not (Test-AddonPackageFile -File $file -RelativePath $relativePath)) {
                    continue
                }
                $entryName = ($sourceName + '/' + $relativePath).Replace('\', '/')
                [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile(
                    $archive,
                    $file.FullName,
                    $entryName,
                    [System.IO.Compression.CompressionLevel]::Optimal
                ) | Out-Null
            }
        }
        finally {
            $archive.Dispose()
        }
    }
    finally {
        $zipStream.Dispose()
    }

    foreach ($asset in @('icon.png', 'fanart.jpg', 'fanart.png')) {
        $assetPath = Join-Path $SourceDirectory $asset
        if (Test-Path -LiteralPath $assetPath) {
            Copy-Item -LiteralPath $assetPath -Destination $DestinationDirectory
        }
    }

    return $metadata
}

function New-FlatZipPackage {
    param(
        [Parameter(Mandatory)][string]$SourceDirectory,
        [Parameter(Mandatory)][string]$ZipPath
    )

    Add-Type -AssemblyName System.IO.Compression
    Add-Type -AssemblyName System.IO.Compression.FileSystem

    if (Test-Path -LiteralPath $ZipPath) {
        Remove-Item -LiteralPath $ZipPath -Force
    }

    $sourceRoot = [System.IO.Path]::GetFullPath($SourceDirectory).TrimEnd('\')
    $zipStream = [System.IO.File]::Open(
        $ZipPath,
        [System.IO.FileMode]::Create,
        [System.IO.FileAccess]::ReadWrite,
        [System.IO.FileShare]::None
    )
    try {
        $archive = [System.IO.Compression.ZipArchive]::new(
            $zipStream,
            [System.IO.Compression.ZipArchiveMode]::Create,
            $false
        )
        try {
            foreach ($file in Get-ChildItem -LiteralPath $sourceRoot -File -Recurse) {
                $relativePath = $file.FullName.Substring($sourceRoot.Length).TrimStart('\')
                $entryName = $relativePath.Replace('\', '/')
                [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile(
                    $archive,
                    $file.FullName,
                    $entryName,
                    [System.IO.Compression.CompressionLevel]::Optimal
                ) | Out-Null
            }
        }
        finally {
            $archive.Dispose()
        }
    }
    finally {
        $zipStream.Dispose()
    }
}

# Build the repository installer with the selected public URL.
$repositoryBuild = Join-Path $output '_repository-build\repository.xvault'
New-Item -ItemType Directory -Path $repositoryBuild -Force | Out-Null
Copy-Item -Path (Join-Path $repositorySource '*') -Destination $repositoryBuild -Recurse

$repositoryXmlPath = Join-Path $repositoryBuild 'addon.xml'
[xml]$repositoryXml = Get-Content -LiteralPath $repositoryXmlPath -Raw -Encoding UTF8
$repositoryDir = $repositoryXml.addon.extension |
    Where-Object { $_.point -eq 'xbmc.addon.repository' } |
    Select-Object -ExpandProperty dir
$repositoryDir.info.InnerText = $BaseUrl + 'addons.xml'
$repositoryDir.checksum = $BaseUrl + 'addons.xml.md5'
$repositoryDir.datadir.InnerText = $BaseUrl
$repositoryXml.Save($repositoryXmlPath)

$videoMetadata = Get-AddonMetadata (Join-Path $addonSource 'addon.xml')
$videoDestination = Join-Path $output $videoMetadata.Id
New-AddonPackage -SourceDirectory $addonSource -DestinationDirectory $videoDestination | Out-Null

$repoDestination = Join-Path $output 'repository.xvault'
$repositoryMetadata = New-AddonPackage `
    -SourceDirectory $repositoryBuild `
    -DestinationDirectory $repoDestination

$tmdbHelperPlayersUrl = ''
if (Test-Path -LiteralPath $tmdbHelperPlayersSource) {
    $tmdbHelperPlayersDestination = Join-Path $output 'tmdbhelper-players'
    New-Item -ItemType Directory -Path $tmdbHelperPlayersDestination -Force | Out-Null
    $tmdbHelperPlayersZip = Join-Path $tmdbHelperPlayersDestination 'xvault-tmdbhelper-players.zip'
    New-FlatZipPackage -SourceDirectory $tmdbHelperPlayersSource -ZipPath $tmdbHelperPlayersZip
    Copy-Item -LiteralPath (Join-Path $tmdbHelperPlayersSource 'xvault.json') -Destination $tmdbHelperPlayersDestination -Force
    $tmdbHelperPlayersUrl = $BaseUrl + 'tmdbhelper-players/xvault-tmdbhelper-players.zip'
}

$videoIcon = Join-Path $addonSource 'resources\icon.png'
$videoFanart = Join-Path $addonSource 'resources\fanart.png'
if (Test-Path -LiteralPath $videoIcon) {
    Copy-Item -LiteralPath $videoIcon -Destination (Join-Path $videoDestination 'icon.png')
}
if (Test-Path -LiteralPath $videoFanart) {
    Copy-Item -LiteralPath $videoFanart -Destination (Join-Path $videoDestination 'fanart.png')
}

$addonXmlDocuments = @(
    (Get-Content -LiteralPath (Join-Path $addonSource 'addon.xml') -Raw -Encoding UTF8),
    (Get-Content -LiteralPath $repositoryXmlPath -Raw -Encoding UTF8)
)
$addonsXml = "<?xml version=`"1.0`" encoding=`"UTF-8`"?>`n<addons>`n"
foreach ($document in $addonXmlDocuments) {
    $withoutDeclaration = $document -replace '^\s*<\?xml[^?]*\?>\s*', ''
    $addonsXml += $withoutDeclaration.Trim() + "`n"
}
$addonsXml += "</addons>`n"

$addonsXmlPath = Join-Path $output 'addons.xml'
[System.IO.File]::WriteAllText(
    $addonsXmlPath,
    $addonsXml,
    [System.Text.UTF8Encoding]::new($false)
)

$md5 = [System.Security.Cryptography.MD5]::Create()
try {
    $stream = [System.IO.File]::OpenRead($addonsXmlPath)
    try {
        $hash = [System.BitConverter]::ToString($md5.ComputeHash($stream)).Replace('-', '').ToLowerInvariant()
    }
    finally {
        $stream.Dispose()
    }
}
finally {
    $md5.Dispose()
}
[System.IO.File]::WriteAllText(
    (Join-Path $output 'addons.xml.md5'),
    $hash,
    [System.Text.Encoding]::ASCII
)

$installerZip = Join-Path $root ('repository.xvault-{0}.zip' -f $repositoryMetadata.Version)
Copy-Item `
    -LiteralPath (Join-Path $repoDestination ('repository.xvault-{0}.zip' -f $repositoryMetadata.Version)) `
    -Destination $installerZip `
    -Force
Copy-Item -LiteralPath $installerZip -Destination $output -Force

$tmdbHelperSection = ''
if ($tmdbHelperPlayersUrl) {
    $tmdbHelperSection = @"
    <h2>TMDb Helper Player</h2>
    <p>In TMDb Helper unter Player aktualisieren diese ZIP-Adresse eintragen:</p>
    <p><code>$tmdbHelperPlayersUrl</code></p>
    <p><a href="tmdbhelper-players/xvault-tmdbhelper-players.zip">xvault-tmdbhelper-players.zip herunterladen</a></p>
"@
}

$indexHtml = @"
<!doctype html>
<html lang="de">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>xVAULT Kodi Repository</title>
    <style>
        body { max-width: 720px; margin: 4rem auto; padding: 0 1.25rem; font: 18px/1.5 system-ui, sans-serif; color: #eee; background: #121212; }
        a { color: #62b5ff; }
        code { background: #252525; padding: .15rem .35rem; }
    </style>
</head>
<body>
    <h1>xVAULT Kodi Repository</h1>
    <p>In Kodi diese Adresse als Dateiquelle eintragen:</p>
    <p><code>$BaseUrl</code></p>
    <p><a href="repository.xvault-$($repositoryMetadata.Version).zip">repository.xvault-$($repositoryMetadata.Version).zip installieren</a></p>
$tmdbHelperSection
</body>
</html>
"@
[System.IO.File]::WriteAllText(
    (Join-Path $output 'index.html'),
    $indexHtml,
    [System.Text.UTF8Encoding]::new($false)
)

Remove-Item -LiteralPath (Join-Path $output '_repository-build') -Recurse -Force

Write-Host "Repository erstellt: $output"
Write-Host "Kodi-Installer:       $installerZip"
Write-Host "Oeffentliche Basis-URL: $BaseUrl"
