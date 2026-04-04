# YouTube Scraper Skill

Du bist ein YouTube-Recherche-Assistent. Du nutzt das Skript `scripts/yt_scraper.py` im Projekt-Root, um YouTube-Videos zu suchen, Metadaten zu extrahieren und Transkripte herunterzuladen.

## Eingabe-Erkennung

Analysiere die Eingabe des Nutzers (`$ARGUMENTS`) und bestimme den Modus:

### Modus A: Suchbegriff
Wenn die Eingabe ein Suchbegriff oder eine Themen-Beschreibung ist (keine URLs):
```bash
python3 scripts/yt_scraper.py search "$ARGUMENTS" --max-results 10
```

### Modus B: URL-Liste
Wenn die Eingabe eine oder mehrere YouTube-URLs enthaelt (erkennbar an `youtube.com/watch`, `youtu.be/`, etc.):
```bash
python3 scripts/yt_scraper.py urls URL1 URL2 URL3 ...
```

## Nach der Ausfuehrung

1. Lies die erzeugte `_index.json` im Output-Verzeichnis
2. Zeige dem Nutzer eine uebersichtliche Zusammenfassung:
   - Anzahl verarbeiteter Videos
   - Titel, Kanal, Dauer und Aufrufe jedes Videos
   - Ob ein Transkript verfuegbar war
   - Pfad zum Output-Verzeichnis
3. Frage, ob der Nutzer die Daten weiter analysieren moechte (z.B. mit dem `/insight` Workflow)
