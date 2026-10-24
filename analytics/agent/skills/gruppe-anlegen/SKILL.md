---
name: gruppe-anlegen
description: "Eine wiederkehrende Auswahl des Nutzers („meine Ostpark-Gänse“, eine Ringliste, Graugänse die als Jungvögel beringt wurden) als Gruppe speichern, wiederverwenden und mit anderen Gruppen vergleichen."
---
# Gruppe anlegen und nutzen

Eine Gruppe ist eine gespeicherte, benannte Auswahl von Sichtungen: Filter (Art, Orte, Zeitraum, Status, Beringungsort, Alter bei Beringung …), optional eine feste Ringliste und von Hand ausgeschlossene Einträge. Sie erscheint in der Analyse-App unter „Gruppen“; der Nutzer kann sie dort bearbeiten, Zahlen sehen, einzelne Einträge ausschließen und Gruppen vergleichen. Die alten „Datensätze“ der früheren App sind als Gruppen importiert.

1. **Vorhandenes prüfen:** `list_groups` (mit `search`). Sagt der Nutzer „meine Kanadagänse im Ostpark“ o. ä., meint er meist eine bestehende Gruppe – verwende sie, statt die Filter neu zu erfinden. `get_group` zeigt die genaue Festlegung, `group_summary` die aktuellen Zahlen (Sichtungen, Vögel, Orte, Zeitraum, Arten, Status, je Jahr).
2. **Neue Gruppe:** `create_group` mit
   - `name`: kurz, so wie der Nutzer sie nennt („Graugänse Ostpark, als Jungvögel beringt“).
   - `description`: ein Satz in Alltagssprache, was die Gruppe bedeutet.
   - `filters`: wie bei `create_view` (species, places, ringing_places, ringing_age, status, years, date_from/date_to, months, place_groups, periods, ring_contains für „W“-Ringe …). Ortsnamen vorher mit `filter_choices` prüfen.
   - `ring_list`: nur wenn die Gruppe aus einer festen Liste von Ringen besteht (wird mit den Filtern kombiniert).
   - `color`: Hex-Farbe für Vergleiche (optional; die App wählt sonst eine).
   - `tags`: 1–3 Schlagwörter (Art, Ort, Thema).
   Die Antwort enthält die `group_id` und eine deutsche Beschreibung der Auswahl – diese dem Nutzer vorlesen, damit er prüfen kann, ob es stimmt.
3. **Verwenden:** in jeder Ansicht, Mappe oder Auswertung `"filters": {"groups": ["<group_id>"]}` (zusätzliche Filter sind erlaubt und schränken weiter ein). Mehrere Gruppen in `groups` = Vereinigung. In Auswertungen eignet sich eine Eingabe vom Typ `group`, damit der Nutzer die Gruppe im Formular wählt: `"filters": {"groups": ["{{gruppe}}"]}`.
4. **Vergleichen:** `compare_groups` mit 2–4 Gruppen, `metric` (sightings, birds, observation_days, places), `dimension` (`group` = nur Summen; sonst year, month, season, status, place, ringing_place, distance_class … mit Farbe nach Gruppe) und `chart_kind`. Ergebnis ist eine normale Ansicht mit Bild und Links. Für eigene Vergleiche: `create_view` mit `filters.groups` und `color: "group"` bzw. `dimension: "group"`.
5. **Ändern:** `update_group` mit JSON-Merge-Patch (`{"filters": {"years": [2025]}}`, `{"excluded_ids": [...]}`, `{"color": "#228096"}`). Ansichten, die die Gruppe nutzen, zeigen die Änderung beim nächsten Aufbau.
6. **Zeigen und erklären:** `show_in_app` mit `target: "group"` und der group_id. Dann in 2–3 Sätzen sagen, was die Gruppe bedeutet, wie viele Sichtungen und Vögel sie umfasst, und dass sie unter „Gruppen“ bearbeitet werden kann (dort lassen sich einzelne Einträge ausschließen, z. B. Fehlablesungen).
7. **Merken:** wichtige Gruppen und was der Nutzer damit vorhat in einer Notiz festhalten (`save_note`, Tag „Gruppe“).
