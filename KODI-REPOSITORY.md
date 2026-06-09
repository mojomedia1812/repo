# xVAULT Kodi Repository

Dieses Projekt erzeugt ein installierbares Kodi-Repository für xVAULT:

- `repository.xvault-1.0.0.zip`: in Kodi über **Aus ZIP-Datei installieren**
- `kodi-repository/`: kompletter Inhalt für einen HTTP(S)-Webserver
- `kodi-repository/addons.xml` und `addons.xml.md5`: Kodi-Index
- versionierte ZIP-Dateien für `plugin.video.xvault` und das Repository-Addon

## Repository bauen

PowerShell im Projektordner öffnen und die öffentliche URL des Webverzeichnisses
angeben:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\build-repository.ps1 `
    -BaseUrl 'https://mojomedia1812.github.io/repo/'
```

Danach den **Inhalt** von `kodi-repository/` unter genau dieser URL
veröffentlichen. Der Webserver muss die Dateien unverändert per HTTPS ausliefern.

Beispiel für GitHub Pages:

```powershell
.\build-repository.ps1 `
    -BaseUrl 'https://BENUTZERNAME.github.io/REPOSITORYNAME/'
```

In diesem Fall wird der Inhalt von `kodi-repository/` als Inhalt der
GitHub-Pages-Site veröffentlicht.

## In Kodi installieren

1. `repository.xvault-1.0.0.zip` auf das Kodi-Gerät übertragen.
2. In Kodi **Add-ons > Aus ZIP-Datei installieren** öffnen.
3. Die ZIP auswählen und anschließend **Aus Repository installieren** öffnen.
4. **xVAULT Repository > Video-Add-ons > xVAULT** auswählen.

Die konfigurierte Repository-Adresse ist:

`https://mojomedia1812.github.io/repo/`

## Abhängigkeiten

xVAULT benötigt unter anderem `script.module.resolveurl`. Kodi muss diese
Abhängigkeit aus einem bereits eingerichteten Repository beziehen können.
