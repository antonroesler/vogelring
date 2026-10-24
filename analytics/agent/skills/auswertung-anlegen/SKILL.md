---
name: auswertung-anlegen
description: "Aus einem wiederkehrenden Wunsch („das möchte ich öfter / jedes Jahr / selbst auswählen“) eine gespeicherte Auswertung mit Formular bauen: Eingaben, Schritte mit {{param}} und $steps, Testlauf, Hinweis auf die App."
---
# Auswertung anlegen

Eine Auswertung ist ein gespeichertes Rezept mit Eingabefeldern. Sie erscheint in der Analyse-App unter „Auswertungen“ als Karte mit Formular; der Nutzer kann sie dort jederzeit selbst ausführen.

1. **Vorhandenes prüfen:** `list_pipelines` (mit `search`). Passt eine bestehende Auswertung (z. B. „Saison im Überblick“, „Vogel-Steckbrief“, „Woher kommen die Vögel?“), führe sie mit `run_pipeline` aus und zeige sie, statt eine neue zu bauen. Kleine Erweiterung: `save_pipeline` mit derselben `pipeline_id`.
2. **Was soll wählbar sein?** Aus dem Gespräch ableiten (meist Ort, Art, Jahr); höchstens 4 Eingaben. Alles andere wird fest eingebaut. Nur bei echter Unklarheit eine Rückfrage (ask_user_question).
3. **Erst einmal von Hand bauen:** die Auswertung mit festen Werten durchspielen (`create_view`, Analysen, `create_report`), bis das Ergebnis passt. Die geprüften Spezifikationen werden die Schritte.
4. **Eingaben (`parameters`)** – je Eingabe:
   - `name`: kurzer Bezeichner ohne Umlaute (`ort`, `art`, `jahr`, `jahre`).
   - `label`: deutsche Beschriftung („Ort“, „Art“, „Jahr“). `help`: ein Satz mit Beispiel („Teil des Ortsnamens, z. B. ‚Ostpark‘.“).
   - `type`: `place`, `species`, `year`, `year_range`, `period`, `ring`, `place_group` (gespeicherte Ortsgruppe), `date`, `number`, `text`, `boolean`, `choice` (mit `choices`, nur wenn die Werte selbst verständlich sind, z. B. BV/MG).
   - `default` nur für feste Standards (z. B. `min_km: 5`); das Jahr nicht vorbelegen, sondern `required: true`.
   - Jahresbereich: eine Eingabe `jahre` (type `year_range`, Hilfe „z. B. 2021-2025“) → `"year_from": "{{jahre.from}}"`, `"year_to": "{{jahre.to}}"`.
   - Zeitraum (Monate oder Datumsbereich): eine Eingabe `zeitraum` (type `period`, Hilfe „Monatsnummern wie 6, 7 oder ein Datumsbereich wie 2025-05-01..2025-07-31; leer = ganzes Jahr“) speist alle drei Filter zugleich: `"months": "{{zeitraum.months}}"`, `"date_from": "{{zeitraum.date_from}}"`, `"date_to": "{{zeitraum.date_to}}"` (ohne eckige Klammern). Nicht ausgefüllte Teile fallen einfach weg.
   - Optionale Eingaben (`required: false`) dürfen überall stehen: in Listenfiltern (`"species": ["{{art}}"]` – leer = alle Arten), in Einzelfeldern (fällt leer weg) und in Analyse-Argumenten.
5. **Schritte (`steps`)** – je Schritt `id` (kurz, ohne Umlaute), `kind`, `title` (deutsch, erscheint im Protokoll), `spec`:
   - `view` (bevorzugt): ViewSpec wie bei `create_view`, z. B. `{"kind": "chart", "chart_kind": "bar", "metric": {"kind": "birds"}, "dimension": "month", "color": "year", "filters": {"places": ["{{ort}}"], "species": ["{{art}}"], "year_from": "{{jahre.from}}", "year_to": "{{jahre.to}}"}, "title": "{{ort}}: Vögel je Monat"}`.
   - `analysis`: `{"name": "seasonality", "args": {"place": "{{ort}}", "species": "{{art}}"}}` – erlaubt sind bird_profile, cohort_resighting, site_fidelity, dispersal, seasonality, companions, whats_new, data_quality.
   - `query` (nur wenn keine Ansicht passt): `{"sql": "SELECT … FROM v_sightings WHERE date IS NOT NULL AND place ILIKE '%' || {{ort|sql}} || '%' AND EXTRACT(YEAR FROM date) = {{jahr}}", "name": "…", "description": "…"}` – `{{x|sql}}` setzt Texte sicher in Anführungszeichen.
   - `chart` / `map` / `table`: Spezifikation wie create_chart/create_map/create_table, Daten über `"dataset_id": "$steps.<id>.dataset_id"` (bei Analysen auch `per_bird_dataset_id`, `sightings_dataset_id`).
   - `report`: ReportSpec mit `"visual_ids": ["$steps.<id>.visual_id"]`, `question`, Abschnitten in einfacher Sprache und `methods_note`. `deck`: DeckSpec mit Folien `{"kind": "figure", "visual_ids": ["$steps.<id>.visual_id"]}`. `export`: `{"dataset_id": "$steps.<id>.dataset_id", "filename": "…"}`.
   - Platzhalter: `"{{jahr}}"` allein behält den Typ (Zahl, Liste); in Texten wird eingesetzt („Saison {{jahr}}“, „{{jahre.from}}–{{jahre.to}}“). Felder einer Eingabe mit Punkt: `{{jahre.from}}`, `{{zeitraum.months}}`. `$steps.<id>.<feld>` verweist nur auf frühere Schritte.
6. **Rahmen:** `name` (kurz, als Frage oder Titel, z. B. „Mausergäste eines Jahres“), `description` (welche Frage beantwortet sie, ein bis zwei Sätze für die Karte), `outputs` (Schritt-IDs, die der Nutzer sieht: Grafiken, Bericht), `tags`, `icon` (z. B. `mdi-map`, `mdi-calendar-month`, `mdi-bird`).
7. **Speichern und testen:** `save_pipeline`, dann sofort `run_pipeline` mit typischen Werten aus dem Gespräch. Bei `status: "error"`: Meldung im `log` lesen, Spezifikation korrigieren, `save_pipeline` mit `pipeline_id`, erneut testen – ohne den Nutzer zu behelligen.
8. **Zeigen und erklären:** `show_in_app` mit `target: "pipeline"` und der pipeline_id. Dann in 2–3 Sätzen: „In der Analyse-App unter ‚Auswertungen‘ findest du jetzt die Karte ‚<name>‘. Dort wählst du <Eingaben> und klickst auf Ausführen; nach etwa einer Minute erscheinen <Ergebnisse>.“ Ergebnis des Testlaufs mit Links nennen.
9. **Merken:** `save_note` mit Name der Auswertung, Zweck und Testwerten (Tag „Auswertung“).
