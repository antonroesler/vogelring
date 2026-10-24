---
name: kurzbericht
description: "Kurzpapier (2–6 Seiten) zu einer fachlichen Frage: Fragestellung, Kernaussagen, Ergebnisse mit Abbildungen, Einordnung, Empfehlungen, Datengrundlage in einfacher Sprache; als PDF und Word, auf Wunsch als PowerPoint."
---
# Kurzbericht zu einer Frage

1. **Frage schärfen:** Formuliere die Frage in einem Satz zurück. Falls Zeitraum, Art oder Ort fehlen: eine Rückfrage-Runde (ask_user_question, 2–4 Optionen je Frage). Gespeicherte Begriffe (`list_definitions`) und frühere Notizen (`list_notes`) verwenden.
2. **Analyseplan** (für dich, nicht für den Nutzer): 2–4 Teilfragen, je eine Ansicht (`create_view`), eine fertige Analyse oder – nur wenn nötig – eine Abfrage. Bei großen Berichten Teilfragen an Unter-Agenten delegieren, falls verfügbar.
3. **Rechnen:** Ansichten und Analysen ausführen; bei Abfragen `description` in Alltagssprache. Zahlen auf Plausibilität prüfen (Summen, Zeiträume).
4. **Abbildungen:** 2–6 Grafiken/Tabellen, jede mit Titel, der die Aussage enthält („Kanadagänse: die meisten Wiederfunde im Juni“). Am einfachsten als Mappe (`create_workbook`, Skill `mappe-bauen`), dann sieht der Nutzer alles zusammen in der App (`show_in_app`, `target: "workbook"`).
5. **Bericht** mit `create_report`: `title`, `question`, `key_findings` (3–6, jede mit Zahl), `sections` mit Text in einfacher Sprache (was sieht man, was heißt das, was ist unsicher) und `visual_ids`, `recommendations` (2–4 konkrete Punkte), `methods_note` mit Annahmen und Grenzen (Beobachterabhängigkeit, Luftlinie, fehlende Koordinaten). Nur Kacheln mit Notizen und keine eigenen Kernaussagen nötig: `workbook_report`.
6. **Präsentation** (wenn gewünscht oder für einen Vortrag): `create_deck` mit `report_id` des fertigen Berichts. Eigene Folien nur bei besonderen Wünschen: `spec.slides` mit `kind` title, key_findings (`bullets`), figure (`visual_ids`: 1), two_figures (2), table (`dataset_id`, max. 15 Zeilen), `notes` als Sprechernotizen in einfachem Deutsch; `question` für die Titelfolie.
7. **Antwort im Chat:** 3–5 Sätze Kernaussagen, Links zu PDF/Word/Webansicht (bzw. PowerPoint), ein Vorschlag für eine Anschlussfrage. `save_note` mit Frage, Kernzahlen und offenen Punkten.
