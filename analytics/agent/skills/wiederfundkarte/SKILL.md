---
name: wiederfundkarte
description: "Standard-Wiederfundkarte nach Ingos Konventionen (Jahreszeitenfarben, Beringungsorte als Dreiecke, ausgeschlossene Orte mit Stern, keine Ortsnamen) für eine Vogelgruppe, einen Ort oder eine Art – als gespeicherte Ansicht."
---
# Wiederfundkarte

Konventionen, die immer gelten, wenn nichts anderes gewünscht ist: Kreise = Sichtungen in Jahreszeitenfarben, Dreiecke = Beringungsorte, ausgeschlossene Orte als Stern mit Anzahl in der Fußnote. Keine Ortsnamen auf der Karte (`labels: false`, Standard) – sie überlagern sich bei vielen Orten; nur wenn der Nutzer sie ausdrücklich verlangt.

1. **Auswahl klären:** Art, Ort/Ortsgruppe, Zeitraum, Vogelgruppe. Schreibweisen mit `filter_choices` (column `place` bzw. `species`) prüfen; gespeicherte Begriffe mit `list_definitions` – Ortsgruppen in `filters.place_groups`, Zeiträume in `filters.periods`, Vogelgruppen in `filters.ring_groups`.
2. **Ansicht anlegen** mit `create_view`:
   - `kind: "map"`, `source: "sightings"`, `title` mit Art/Gruppe, Ort und Zeitraum.
   - `filters`: z. B. `species`, `places`, `years` bzw. `date_from`/`date_to`, `months` oder `seasons`, `only_with_coords: true`.
   - `map`: `color_mode: "season"` (Standard), `show_ringing_sites: true`, `exclude_star: true` (kein `labels`). Der Kartenausschnitt passt sich dem Großteil der Punkte an; einzelne weit entfernte Wiederfunde (z. B. einer in England bei 100 in Frankfurt) bleiben außerhalb und stehen in der Fußnote – nenne sie im Text. `fit: "all"` zeigt alle Punkte, `bounds: [[lat, lon], [lat, lon]]` legt den Ausschnitt fest.
   - „ohne Ostpark“: `filters.exclude_places: ["Ostpark"]` – der Stern und die Fußnote mit der Anzahl ausgeschlossener Sichtungen entstehen automatisch.
3. **Varianten über `map`:** Bewegungen je Vogel `tracks: true` (nur bei ≤ 30 Vögeln, sonst unübersichtlich); „je mehr Vögel, desto größer“ `bubbles_by_place: true`; Farbe nach Art `color_mode: "species"`, nach Vogel `"individual"`, nach Jahr `"year"`, nach Status `"category"` + `color_column: "status"`. Zoom/`center` nur auf Wunsch.
4. **Sonderfälle** (aggregierte Flusslinien zwischen Orten, Daten aus einer Analyse wie `dispersal`): `create_map` mit Ebene „Wiederfunde“ (`color: {mode: "season"}`, `dedupe: "coords_per_group"`, `size.min` 9, `label: {column: "place", font_size: 12}`), Ebene „Beringungsorte“ (`lat_column: "ringing_lat"`, `lon_column: "ringing_lon"`, `shape: "triangle"`, `dedupe: "coords"`, `size.min` 14, `color: {mode: "fixed", value: "#00436C", label: "Beringungsort"}`) und `flows`.
5. **Änderungen** („anderer Titel“, „nur 2024“, „mit Linien“): `update_view` mit kleinem Patch, z. B. `{"filters": {"years": [2024]}}` oder `{"map": {"tracks": true}}`.
6. **Zeigen:** `show_in_app` mit `target: "view"` und der view_id; als HTML-Artifact die embed_url im iframe einbetten.
7. **Antwort:** Legende in Worten erklären (Nov–Jan dunkelblau, Feb–Mär gelb, Apr–Jun grün, Jul–Okt rot; Dreieck = Beringungsort), interaktiver und PDF-Link, „So bin ich vorgegangen“ (wie viele Sichtungen ohne Koordinaten fehlen).
