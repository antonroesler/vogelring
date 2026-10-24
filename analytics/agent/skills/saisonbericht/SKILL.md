---
name: saisonbericht
description: "Saisonbericht für einen Ort oder eine Art (z. B. Mauser im Ostpark, Winter am Main) als Mappe mit Karte, Monatsdiagramm und Vorjahresvergleich, daraus PDF/Word und auf Wunsch PowerPoint."
---
# Saisonbericht

Verwende diesen Ablauf, wenn ein Bericht über eine Saison, ein Jahr oder eine Mauserzeit an einem Ort (oder für eine Art) gewünscht ist.

1. **Vorhandenes prüfen:** `list_pipelines` – die Auswertung „Saison im Überblick“ (Ort, Art, Jahr) liefert Monatsdiagramm, Karte und Kurzbericht in einem Schritt. Reicht das dem Nutzer, `run_pipeline` und fertig.
2. **Rahmen klären** (eine Rückfrage-Runde, nur falls unklar): Ort/Art, Zeitraum (z. B. Mai–Juli 2025), Vergleichsjahre (Standard: die 4 Vorjahre), Zielgruppe. Schreibweisen mit `filter_choices`, Begriffe mit `list_definitions`.
3. **Zahlen für den Text:** `seasonality` für Ort/Art über alle Vergleichsjahre (Spitzenmonate, ruhigste Monate); optional `site_fidelity` (wie viele waren schon im Vorjahr da) und `cohort_resighting` (Jahrgänge).
4. **Mappe bauen** mit `create_workbook` (siehe Skill `mappe-bauen`):
   - `title` „<Ort/Art>: Saison <Jahr>“, `description` mit der Fragestellung, `filters` gemeinsam: `places` bzw. `place_groups`, `species`.
   - `notes`: Annahmen (Mausermonate, Ortsabgrenzung, Zählweise Vögel vs. Sichtungen) – erscheint im Bericht als Methodenhinweis.
   - Kachel „Wann waren sie da?“: `view` mit `kind: "chart"`, `chart_kind: "bar"`, `metric: {kind: "birds"}`, `dimension: "month"`, `color: "year"`, `filters.years` = Saisonjahr + Vergleichsjahre, `annotate_moult: true`.
   - Kachel „Wo wurden sie gesehen?“: `view` mit `kind: "map"`, `filters.years: [<Jahr>]` (+ `months` der Saison), `map.color_mode: "season"`.
   - Kachel „Vergleich mit den Vorjahren“: `chart_kind: "line"`, `dimension: "year"`, `metric: {kind: "birds"}`, `filters.months` der Saison.
   - Optional „Woher kamen sie?“: `kind: "table"`, `group_by: ["ringing_place"]`, `metric: {kind: "birds"}`, `sort: "desc"`.
   - Jede Kachel mit `note` (2–3 Sätze: was sieht man, was heißt das).
5. **Prüfen:** Kacheln mit `error` korrigieren (Schreibweise, Filter) und `create_workbook` mit `workbook_id` erneut aufrufen. `show_in_app` mit `target: "workbook"`.
6. **Bericht:** `workbook_report` mit der workbook_id. Für einen ausführlicheren Text mit Kernaussagen und Empfehlungen stattdessen `create_report` mit den visual_ids der Kacheln: Abschnitte „Wie viele Vögel waren da?“, „Wann waren sie da?“, „Woher kamen sie?“, „Vergleich mit den Vorjahren“, „Einordnung“, „Empfehlungen“; `methods_note` mit allen Annahmen.
7. **Präsentation** auf Wunsch: `workbook_deck` bzw. `create_deck` mit `report_id`.
8. **Im Chat:** 3–5 Sätze Zusammenfassung, Links (PDF, Word, Webansicht), ein Satz zur Mappe in der App. Will der Nutzer das jedes Jahr: Skill `auswertung-anlegen`. Zum Schluss `save_note` mit den Kernzahlen.
