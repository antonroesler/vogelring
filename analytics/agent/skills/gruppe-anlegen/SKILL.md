---
name: gruppe-anlegen
description: "Eine wiederkehrende Auswahl des Nutzers („meine Ostpark-Gänse“, eine Ringliste, Graugänse die als Jungvögel beringt wurden) als Gruppe speichern, wiederverwenden und mit anderen Gruppen vergleichen – auch mit Oder-Logik und Ausschlüssen („Mai oder Juni, oder April als Mausergast“), als Vogelgruppe („alle Sichtungen der Vögel, die im Ostpark mausern“) und als Verknüpfung bestehender Gruppen (Vereinigung, Schnittmenge, Differenz)."
---
# Gruppe anlegen und nutzen

Eine Gruppe ist eine gespeicherte, benannte Auswahl von Sichtungen: Filter (Art, Orte, Zeitraum, Status, Beringungsort, Alter bei Beringung …), optional eine feste Ringliste und von Hand ausgeschlossene Einträge. Sie erscheint in der Analyse-App unter „Gruppen“; der Nutzer kann sie dort bearbeiten, Zahlen sehen, einzelne Einträge ausschließen und Gruppen vergleichen. Die alten „Datensätze“ der früheren App sind als Gruppen importiert.

Es gibt zwei Arten (`scope`):
- **Sichtungsgruppe** (`"sightings"`, Standard): nur die Sichtungen, auf die die Bedingung zutrifft („Ablesungen im Ostpark im Mai“).
- **Vogelgruppe** (`"birds"`): alle Sichtungen der Vögel (Ringe), auf die die Bedingung mindestens einmal zutrifft („alles, was wir von den Vögeln kennen, die im Ostpark mausern“). In `filters.groups` liefert eine Vogelgruppe also alle Sichtungen dieser Vögel, an jedem Ort und zu jeder Zeit.

1. **Vorhandenes prüfen:** `list_groups` (mit `search`). Sagt der Nutzer „meine Kanadagänse im Ostpark“ o. ä., meint er meist eine bestehende Gruppe – verwende sie, statt die Filter neu zu erfinden. `get_group` zeigt die genaue Festlegung, `group_summary` die aktuellen Zahlen (Sichtungen, Vögel, Orte, Zeitraum, Arten, Status, je Jahr). Mach das **vor jeder** Ansicht, Mappe oder Auswertung mit zwei oder mehr Filterbedingungen, nicht nur, wenn der Nutzer „Gruppe“ sagt. Lege nie eine zweite Gruppe für dieselbe Auswahl an: Gibt es eine ähnliche, ändere sie mit `update_group` (nach kurzer Rückfrage, wenn sich ihre Bedeutung ändert) oder verwende sie.
2. **Lesart klären:** Bevor du Filter baust, übersetzt du die Sprache des Nutzers in Logik:
   - Felder in einem Filterblock gelten zusammen (UND): `{"places": ["Ostpark"], "months": [4], "status": ["MG"]}` = im Ostpark **und** im April **und** Mausergast.
   - „oder“, „entweder … oder“, „sowie auch“ → `any_of: [{…}, {…}]`: mindestens einer der Blöcke trifft zu. Jeder Block ist ein normaler Filtersatz (UND innerhalb des Blocks); Blöcke enthalten selbst kein weiteres `any_of` (nur eine Ebene).
   - „außer“, „aber nicht“, „ohne“ → `none_of: [{…}]` (keiner dieser Blöcke trifft zu) bzw. `exclude_groups`, wenn das Ausgeschlossene schon eine Gruppe ist.
   - **Sichtungsebene oder Vogelebene?** „Sichtungen/Ablesungen, bei denen …“ → normale Filter. „Vögel, die (irgendwann) …“, „die Gänse, die im Ostpark mausern“ → Vogelebene: `birds_of: {…}` (alle Zeilen der Vögel mit mindestens einer solchen Sichtung) bzw. `birds_not_of: {…}` (Vögel, die **nie** eine solche Sichtung hatten). Der Block darf `groups`, `any_of` und `none_of` enthalten und funktioniert in jeder Datenquelle (Sichtungen, Beringungen, Vögel, Beziehungen). Als gespeicherte Gruppe: `scope: "birds"`.
   - Ist ein Satz mehrdeutig und macht die Lesart einen deutlichen Unterschied („die Gänse, die im April im Ostpark waren“), stelle **eine** Rückfrage mit `ask_user_question` und den beiden Lesarten als Optionen, z. B. „Nur die Ablesungen im Ostpark im April“ und „Alles, was wir von diesen Vögeln kennen“.
   - Nie mit einem einzelnen UND-Filter annähern oder auf `query_sql` ausweichen, nur weil Oder- oder Ausschluss-Logik vorkommt. Im Absatz „So bin ich vorgegangen“ sagst du, wie du die Logik gelesen hast („Ich habe ‚Mauser‘ gelesen als: im Ostpark gesehen im Mai oder Juni, oder im April mit Status Mausergast.“).
3. **Neue Gruppe:** `create_group` mit
   - `name`: kurz, so wie der Nutzer sie nennt („Graugänse Ostpark, als Jungvögel beringt“).
   - `description`: ein Satz in Alltagssprache, was die Gruppe bedeutet.
   - `scope`: `"sightings"` (Standard) oder `"birds"` für eine Vogelgruppe (siehe oben).
   - `filters`: wie bei `create_view` (species, places, ringing_places, ringing_age, status, years, date_from/date_to, months, place_groups, periods, ring_contains für „W“-Ringe …), dazu bei Bedarf `any_of`, `none_of`, `birds_of`, `birds_not_of`, `groups`, `all_groups`, `exclude_groups`. Ortsnamen vorher mit `filter_choices` prüfen.
   - `ring_list`: nur wenn die Gruppe aus einer festen Liste von Ringen besteht (wird mit den Filtern kombiniert).
   - `color`: Hex-Farbe für Vergleiche (optional; die App wählt sonst eine).
   - `tags`: 1–3 Schlagwörter (Art, Ort, Thema).
   Die Antwort enthält die `group_id` und eine deutsche Beschreibung der Auswahl – diese dem Nutzer vorlesen, damit er prüfen kann, ob es stimmt. Bei Oder-Logik und Vogelgruppen ist das besonders wichtig, z. B. „alle Sichtungen der Vögel mit mindestens einer Sichtung an Orten mit ‚Ostpark‘ im Namen, entweder (in den Monaten Mai–Juni) oder (in den Monaten April, mit Status Mausergast)“.
4. **Gruppen verknüpfen:** Aus bestehenden Gruppen a und b entsteht mit `create_group` eine neue Gruppe:
   - Vereinigung (in mindestens einer): `"filters": {"groups": [a, b]}`
   - Schnittmenge (in allen): `"filters": {"all_groups": [a, b]}`
   - Differenz (in a, aber nicht in b): `"filters": {"groups": [a], "exclude_groups": [b]}`
   Statt ids gehen auch die exakten Gruppennamen. Die neue Gruppe folgt späteren Änderungen von a und b. Vogel- und Sichtungsgruppen dürfen gemischt werden. In der App heißt das der Knopf „Verknüpfen“ unter „Gruppen“.
5. **Verwenden:** in jeder Ansicht, Mappe oder Auswertung `"filters": {"groups": ["<group_id>"]}` (zusätzliche Filter sind erlaubt und schränken weiter ein). Mehrere Gruppen in `groups` = Vereinigung, `all_groups` = Schnittmenge, `exclude_groups` = ohne diese Gruppen. In Auswertungen eignet sich eine Eingabe vom Typ `group`, damit der Nutzer die Gruppe im Formular wählt: `"filters": {"groups": ["{{gruppe}}"]}`. Für eine einmalige Frage ohne Speichern geht dieselbe Logik direkt in den Filtern (`any_of`, `birds_of` …); biete dann das Speichern an (Schritt 9).
6. **Vergleichen:** `compare_groups` mit 2–4 Gruppen, `metric` (sightings, birds, observation_days, places), `dimension` (`group` = nur Summen; sonst year, month, season, status, place, ringing_place, distance_class … mit Farbe nach Gruppe) und `chart_kind`. Ergebnis ist eine normale Ansicht mit Bild und Links. Für eigene Vergleiche: `create_view` mit `filters.groups` und `color: "group"` bzw. `dimension: "group"`.
7. **Ändern:** `update_group` mit JSON-Merge-Patch (`{"filters": {"years": [2025]}}`, `{"excluded_ids": [...]}`, `{"color": "#228096"}`, `{"scope": "birds"}`). Ansichten, die die Gruppe nutzen, zeigen die Änderung beim nächsten Aufbau. Achtung: Ein Patch auf `filters.any_of` ersetzt die ganze Liste – schicke sie vollständig mit. Alternativ `create_group` mit `group_id`, um die Gruppe ganz neu festzulegen.
8. **Zeigen und erklären:** `show_in_app` mit `target: "group"` und der group_id. Dann in 2–3 Sätzen sagen, was die Gruppe bedeutet (deutsche Beschreibung der Engine vorlesen), wie viele Sichtungen und Vögel sie umfasst (`group_summary`), und dass sie unter „Gruppen“ bearbeitet werden kann: dort lassen sich Oder-Bedingungen und Ausschlüsse ändern, zwischen Vogel- und Sichtungsgruppe wechseln, einzelne Einträge ausschließen (z. B. Fehlablesungen) und Gruppen verknüpfen. Bei Vogelgruppen liefert `group_summary` zusätzlich `scope` und `matching_sightings` – nenne beide Zahlen: „312 Sichtungen erfüllen die Mauser-Bedingung; insgesamt kennen wir von diesen 58 Vögeln 2.140 Sichtungen an 71 Orten.“
9. **Proaktiv anbieten:** Biete am Ende der Antwort in einem Satz an, eine Auswahl als Gruppe zu speichern, wenn sie drei oder mehr Bedingungen kombiniert, Oder- oder Ausschluss-Logik nutzt, auf Vogelebene definiert ist oder der Nutzer dieselbe Auswahl im Gespräch zum zweiten Mal braucht. Schlage dabei einen Namen vor: „Soll ich das als Gruppe ‚Mausergäste Ostpark‘ speichern? Dann kannst du sie in jeder Auswertung wiederverwenden.“ Ohne Nachfrage anlegen, wenn der Nutzer schon von „meinen …“ spricht, „merk dir“ sagt oder zustimmt – aber immer erst suchen (Schritt 1).
10. **Merken:** wichtige Gruppen und was der Nutzer damit vorhat in einer Notiz festhalten (`save_note`, Tag „Gruppe“).

## Beispiel: Vögel, die im Ostpark mausern

Frage: „Zeig mir alle Orte, an denen die Vögel auftauchen, die im Ostpark mausern.“

> Das Beispiel ist **erfunden** und zeigt nur die Art der Frage und die Syntax. Was „Mauser im Ostpark“ fachlich bedeutet, legt allein der Nutzer fest – nimm seine Worte, und wenn er keine Regel nennt, frage nach (ask_user_question mit 2–3 plausiblen Lesarten) statt eine anzunehmen.

- Lesart: Gemeint sind **Vögel** (Vogelebene), und von ihnen **alle** Sichtungen, nicht nur die im Ostpark. Angenommen, der Nutzer sagt: Mauser im Ostpark heißt im Ostpark gesehen im Mai oder Juni, **oder** im April mit Status Mausergast (MG).
- `list_groups` mit `search: "Mauser"` bzw. `"Ostpark"`. Gibt es „Mausergäste Ostpark“ schon, nimm sie.
- Sonst `filter_choices` für „Ostpark“ und dann:
  ```json
  create_group {
    "name": "Mausergäste Ostpark",
    "description": "Vögel, die im Ostpark mausern (Mai/Juni oder April als Mausergast), mit allen ihren Sichtungen.",
    "scope": "birds",
    "filters": {"places": ["Ostpark"], "any_of": [{"months": [5, 6]}, {"months": [4], "status": ["MG"]}]}
  }
  ```
- Beschreibung vorlesen: „alle Sichtungen der Vögel mit mindestens einer Sichtung an Orten mit ‚Ostpark‘ im Namen, entweder (in den Monaten Mai–Juni) oder (in den Monaten April, mit Status Mausergast)“.
- Orte zeigen: `create_view` mit Datenquelle Sichtungen, `"filters": {"groups": ["<group_id>"]}`, `dimension: "place"`, `metric: "birds"` (Rangliste: an wie vielen verschiedenen dieser Vögel wurde jeder Ort beobachtet) oder `kind: "map"` für die Karte.
- Ohne Speichern ginge dasselbe direkt: `"filters": {"birds_of": {"places": ["Ostpark"], "any_of": [{"months": [5, 6]}, {"months": [4], "status": ["MG"]}]}}` – dann am Ende anbieten, es als Gruppe „Mausergäste Ostpark“ zu speichern.
- Abschluss: `group_summary` mit beiden Zahlen („312 Sichtungen erfüllen die Mauser-Bedingung; insgesamt kennen wir von diesen 58 Vögeln 2.140 Sichtungen an 71 Orten“), `show_in_app` mit `target: "group"`, Hinweis auf „Gruppen“, und im Absatz „So bin ich vorgegangen“ die Lesart der Mauser-Bedingung nennen.
