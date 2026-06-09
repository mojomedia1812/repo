# xVAULT Kodi Repository

Dieses Repository enthält das Kodi-Video-Add-on `plugin.video.xvault`, das
Repository-Add-on `repository.xvault` und ein PowerShell-Buildskript.

Die vollständige Build- und Installationsanleitung steht in
[`KODI-REPOSITORY.md`](KODI-REPOSITORY.md).

## Kurzstart

```powershell
.\build-repository.ps1 -BaseUrl 'https://mojomedia1812.github.io/repo/'
```

Anschließend wird der Inhalt von `kodi-repository/` unter dieser URL
veröffentlicht. Die erzeugte `repository.xvault-1.0.0.zip` ist der
Installations-Einstiegspunkt für Kodi.
