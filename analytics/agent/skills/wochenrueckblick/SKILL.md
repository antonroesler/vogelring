---
name: wochenrueckblick
description: "Rückblick „Was ist neu“ seit einem Datum (Standard: letzte 7 Tage) mit Zahlen, neuen Vögeln, weiten Funden, Totfunden und einer Karte der neuen Sichtungen; geeignet für geplante Zusammenfassungen."
---
# Wochenrückblick

1. **Zeitraum:** Standard heute minus 7 Tage (bei „Monat“: minus 30 Tage). `whats_new` mit dem Datum ausführen.
2. **Antwort** in 5–8 Sätzen: Anzahl Sichtungen/Vögel/Beobachtungstage, häufigste Arten und Orte, erstmals abgelesene Vögel (verlinken), weite Funde (≥ 20 km, mit Beringungsort), Totfunde, neue Orte.
3. **Karte** der neuen Sichtungen, wenn ≥ 5 Sichtungen mit Koordinaten vorliegen: `create_view` mit `kind: "map"`, `filters: {date_from: "<Datum>", only_with_coords: true}`, `map: {color_mode: "species", labels: true}`, Titel „Neue Sichtungen seit <TT.MM.JJJJ>“. Danach `show_in_app` mit der view_id.
4. Ein Satz „So bin ich vorgegangen“ (alle Einträge mit Sichtungsdatum ab …).
5. Ein Hinweis auf Auffälliges (z. B. ungewöhnlich wenige Beobachtungstage, Sichtungen ohne Koordinaten) und ein Vorschlag (z. B. Vogelprofil eines neuen Vogels).
6. **Gedächtnis:** In geplanten Chats vorher `list_notes` (Tag „Wochenrückblick“) lesen und Veränderungen zur Vorwoche nennen; danach `save_note` mit den Kernzahlen und Tag „Wochenrückblick“.
