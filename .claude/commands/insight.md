# Insight Workflow: YouTube -> NotebookLM -> Analyse

Dieser Workflow ist eine vollstaendige Recherche-Pipeline. Er nimmt einen Suchbegriff oder YouTube-URLs entgegen, laedt Transkripte herunter, analysiert sie mit NotebookLM und speichert strukturierte Ergebnisse.

## Eingabe
`$ARGUMENTS` -- Entweder ein Suchbegriff ODER eine kommagetrennte Liste von YouTube-URLs.

---

## Schritt 1: YouTube-Daten herunterladen

Bestimme den Modus anhand der Eingabe:

**Falls Suchbegriff** (keine URLs erkannt):
```bash
python3 scripts/yt_scraper.py search "$ARGUMENTS" --max-results 10
```

**Falls URLs** (youtube.com oder youtu.be erkannt):
Extrahiere alle URLs aus der Eingabe und fuehre aus:
```bash
python3 scripts/yt_scraper.py urls URL1 URL2 ...
```

Lies anschliessend die `_index.json` aus dem erzeugten Output-Verzeichnis, um den Run-Pfad und die Video-Liste zu erhalten.

---

## Schritt 2: NotebookLM Notebook erstellen

Erstelle ein Notebook mit einem beschreibenden Titel:
```bash
notebooklm create "Recherche: [Thema/Datum]"
```
Speichere die Notebook-ID fuer die naechsten Schritte.

---

## Schritt 3: Transkripte als Quellen hochladen

Fuer jede `.md`-Datei im Output-Verzeichnis (NICHT die `_index.json`):
```bash
notebooklm source add "pfad/zur/datei.md"
```

**WICHTIG:**
- Maximal 50 Quellen pro Notebook!
- Falls mehr als 50 Videos: Erstelle mehrere Notebooks und teile die Quellen auf.
- Warte nach dem Upload aller Quellen kurz, damit NotebookLM die Indexierung abschliessen kann:
```bash
notebooklm source list
```

---

## Schritt 4: Analyse mit NotebookLM

### 4a: Einzelne Video-Insights
Fuer jedes Video stelle gezielte Fragen:
```bash
notebooklm ask "Erstelle eine detaillierte Zusammenfassung fuer das Video '[Titel]'. Nenne die Kernaussagen, wichtigsten Erkenntnisse, genannte Quellen/Studien und konkrete Handlungsempfehlungen." -s <source_id>
```

Speichere die Antwort als Variable fuer Schritt 5.

### 4b: Uebergreifende Essenz
Frage nach der Gesamtanalyse ueber alle Quellen:
```bash
notebooklm ask "Analysiere ALLE hochgeladenen Video-Transkripte. Erstelle: 1) Eine uebergreifende Zusammenfassung der wichtigsten Themen und Trends. 2) Gemeinsamkeiten und Widerspueche zwischen den Videos. 3) Die Top-5 wichtigsten Erkenntnisse. 4) Konkrete Handlungsempfehlungen."
```

### 4c: Optionaler Report
```bash
notebooklm generate report "Umfassende Analyse aller Video-Quellen mit Einzelzusammenfassungen und uebergreifender Synthese" --wait
```

---

## Schritt 5: Ergebnisse speichern

Erstelle im Output-Verzeichnis des aktuellen Runs einen Unterordner `analysis/`:

### 5a: Einzelne Insights
Fuer jedes Video erstelle: `analysis/insight_[video_id]_[titel].md`
```markdown
# Insight: [Video-Titel]

## Metadaten
- Kanal: ...
- URL: ...
- Dauer: ... | Aufrufe: ... | Datum: ...

## Zusammenfassung
[NotebookLM-Antwort]

## Kernaussagen
[Extrahierte Kernpunkte]
```

### 5b: Gesamtanalyse
Erstelle: `analysis/_GESAMT_ANALYSE.md`
```markdown
# Gesamtanalyse: [Thema]
Erstellt am: [Datum]
Quellen: [Anzahl] Videos

## Uebergreifende Zusammenfassung
[...]

## Gemeinsame Themen und Trends
[...]

## Widerspueche und unterschiedliche Perspektiven
[...]

## Top-5 Erkenntnisse
1. ...
2. ...
3. ...
4. ...
5. ...

## Handlungsempfehlungen
[...]

## Quellenverzeichnis
| # | Titel | Kanal | URL |
|---|-------|-------|-----|
| 1 | ...   | ...   | ... |
```

---

## Schritt 6: Abschluss

Zeige dem Nutzer:
1. Pfad zum Output-Verzeichnis mit allen Dateien
2. Kurze Zusammenfassung: Wie viele Videos verarbeitet, wie viele Transkripte, NotebookLM Notebook-ID
3. Frage ob er weitere Analysen, ein Audio-Summary oder eine Mindmap wuenscht
