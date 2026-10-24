---
name: vogelprofil
description: "Steckbrief eines einzelnen Vogels (Ringnummer) mit Lebenslauf, Karte aller Funde, Begleitern und Familie; auf Wunsch als PDF oder über die Auswertung „Vogel-Steckbrief“."
---
# Vogelprofil

1. `bird_profile` mit der Ringnummer (exakt, ohne Leerzeichen). Bei „nicht gefunden“: `filter_choices` mit `column: "ring"` und `search` = Teil der Nummer (oder `query_sql` mit `reading ILIKE '%…%'`) und dem Nutzer die Treffer zur Auswahl geben (ask_user_question, max. 4 Optionen).
2. **Antwort** in dieser Reihenfolge: Beringung (wann, wo, Alter), Sichtungen (Anzahl, Zeitraum, Jahre), Orte (Lieblingsort, Anzahl Orte), weitester Fund, Jahreszeiten, Partner/Familie, Besonderheiten (Totfund, Farbringe). Ringnummer verlinken (https://vogelring.com/birds/<ring>).
3. **Grafiken** als Ansichten mit `filters.rings: ["<ring>"]`:
   - Karte: `create_view` mit `kind: "map"`, `map: {color_mode: "season", tracks: true, show_ringing_sites: true}`.
   - Lebenslauf: `create_view` mit `kind: "chart"`, `chart_kind: "timeline"`, `x_column: "date"`, `series_column: "place"`, `color: "season"`.
   - Danach `show_in_app` mit der view_id der Karte.
4. Auf Wunsch `companions` (gemeinsam gesehene Vögel) und Familiennetz: `create_view` mit `source: "relationships"`, `filters.rings: ["<ring>"]`, `chart_kind: "graph"`, `source_column: "bird1_ring"`, `target_column: "bird2_ring"`, `edge_label_column: "relationship_type"`.
5. **PDF-Steckbrief:** Die Auswertung „Vogel-Steckbrief“ (`list_pipelines`, dann `run_pipeline` mit `{"ring": "<ring>"}`) liefert Zeitstrahl, Karte und Bericht. Hinweis an den Nutzer: „In der Analyse-App unter ‚Auswertungen‘ kannst du den Steckbrief für jeden Ring selbst erstellen.“
6. „So bin ich vorgegangen“: nur Sichtungen mit Datum, Entfernungen Luftlinie zum Beringungsort.
