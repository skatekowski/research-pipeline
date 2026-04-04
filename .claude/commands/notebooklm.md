# NotebookLM Skill

Du steuerst Google NotebookLM ueber die CLI `notebooklm` (Paket: notebooklm-py). Fuehre die Anfrage des Nutzers (`$ARGUMENTS`) aus, indem du die passenden CLI-Befehle verwendest.

## Wichtig: Authentifizierung
Falls ein Auth-Fehler auftritt, weise den Nutzer darauf hin:
```
Bitte fuehre in einem separaten Terminal aus:  notebooklm login
```

## Verfuegbare Operationen

### Notebooks verwalten
- `notebooklm list` -- Alle Notebooks anzeigen
- `notebooklm create "Titel"` -- Neues Notebook erstellen
- `notebooklm use <id>` -- Notebook aktivieren (unterstuetzt Teil-IDs)
- `notebooklm delete <id>` -- Notebook loeschen
- `notebooklm rename "Neuer Titel"` -- Aktives Notebook umbenennen
- `notebooklm summary` -- KI-Zusammenfassung des aktiven Notebooks

### Quellen verwalten
- `notebooklm source list` -- Quellen im aktiven Notebook anzeigen
- `notebooklm source add "url_oder_pfad"` -- URL oder Datei als Quelle hinzufuegen
- `notebooklm source wait <id>` -- Warten bis Quelle verarbeitet ist
- `notebooklm source fulltext <id>` -- Volltext einer Quelle abrufen
- `notebooklm source delete <id>` -- Quelle entfernen
**Limit: Maximal 50 Quellen pro Notebook!**

### Fragen stellen
- `notebooklm ask "Frage"` -- Frage an die Quellen stellen
- `notebooklm ask "Frage" -s <source_id>` -- Frage an spezifische Quelle

### Inhalte generieren
- `notebooklm generate report "Beschreibung"` -- Bericht generieren
- `notebooklm generate audio "Beschreibung"` -- Audio/Podcast generieren
- `notebooklm generate mind-map` -- Mindmap generieren
- `notebooklm generate quiz "Thema"` -- Quiz generieren

### Downloads
- `notebooklm download report pfad.md` -- Bericht herunterladen
- `notebooklm download mind-map pfad.json` -- Mindmap herunterladen

### Sprache
- `notebooklm language set de` -- Auf Deutsch umstellen

## Befehlsausfuehrung

Interpretiere die natuerlichsprachliche Eingabe des Nutzers und bilde sie auf die passenden CLI-Befehle ab. Fuehre die Befehle sequenziell aus und zeige die Ergebnisse uebersichtlich an.
