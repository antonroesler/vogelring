---
name: mappe-bauen
description: "Mappe (Dashboard) aus 2–6 Ansichten zusammenstellen: gemeinsame Filter, sprechende Kacheltitel, Notiz je Kachel, Raster-Layout; danach als Bericht (PDF/Word) oder Präsentation (PowerPoint) ausgeben."
---
# Mappe bauen

Eine Mappe zeigt mehrere Ansichten zu einer Frage nebeneinander, mit gemeinsamen Filtern. Sie liegt in der Analyse-App unter „Mappen“ und lässt sich als Bericht oder Präsentation ausgeben.

1. **Frage und Leitfaden:** eine Frage pro Mappe, 2–6 Kacheln, die zusammen eine Geschichte erzählen: Überblick (wie viele?) → zeitlicher Verlauf (wann?) → Raum (wo?) → Vergleich/Herkunft (womit?/woher?). Mehr als 6 Kacheln: auf zwei Mappen aufteilen.
2. **Gemeinsame Filter (`filters`)** für das, was für alle Kacheln gilt (Ort/`place_groups`, Art, Zeitraum). Schreibweisen vorher mit `filter_choices`, Begriffe mit `list_definitions`. Achtung: Listen werden mit den Kachelfiltern vereinigt, Einzelwerte der Mappe gewinnen. Wird ein Feld zwischen Kacheln verglichen (z. B. Ostpark gegen Nordufer, 2024 gegen 2025), gehört es **nicht** in die gemeinsamen Filter, sondern in die Kacheln.
3. **Kacheln (`tiles`)** – je Kachel genau eines von:
   - `view_id` einer gespeicherten Ansicht (`list_views`), oder
   - `view`: ViewSpec wie bei `create_view` (`kind`, `chart_kind`, `metric`, `dimension`, `color`, `filters`, `map` …).
   Dazu `title` mit der Aussage („Die meisten Vögel im Juni“), `note` (2–3 Sätze in einfacher Sprache: was sieht man, was heißt das, Vorsicht wo nötig), Größe `w` (Rasterbreite 1–12: 12 volle Breite, 6 halbe) und `h` (1–3). Karten `w: 12, h: 2`; Diagramme paarweise `w: 6`; Tabellen `w: 6` oder 12.
4. **Rahmen:** `title` („Ostpark: Mausersaison 2025“), `description` (die Frage in einem Satz), `notes` (Einleitung und Annahmen, z. B. „Mausergast = Juni–Juli im Ostpark; gezählt werden verschiedene Vögel“ – im Bericht erscheint das als Methodenhinweis).
5. **Anlegen:** `create_workbook` mit `render: true`. In der Antwort stehen je Kachel `summary` und ggf. `error`. Fehlerhafte Kacheln korrigieren und `create_workbook` mit `workbook_id` und der vollständigen, korrigierten Spezifikation erneut aufrufen. Leere Kacheln (0 Zeilen) prüfen: meist eine Schreibweise.
6. **Zeigen:** `show_in_app` mit `target: "workbook"` und der workbook_id; dem Nutzer sagen: „Die Mappe liegt in der Analyse-App unter ‚Mappen‘; dort kannst du die Filter oben selbst ändern.“
7. **Im Chat:** pro Kachel ein Satz Ergebnis mit Zahl, dann „So bin ich vorgegangen“ und der Link zur Mappe.
8. **Ausgeben:** Bericht mit `workbook_report` (ein Abschnitt je Kachel, die Notiz wird zum Text); für Kernaussagen und Empfehlungen stattdessen `create_report` mit den visual_ids der Kacheln. Präsentation mit `workbook_deck` oder `create_deck` mit der `report_id`. Links zu PDF, Word bzw. PowerPoint nennen.
9. **Wiederkehrend?** Will der Nutzer die Mappe für andere Orte/Jahre: als Auswertung speichern (Skill `auswertung-anlegen`) – je Kachel ein `view`-Schritt mit `{{param}}` in den Filtern, am Ende ein `report`-Schritt.
