---
name: ortstreue
description: "Ortstreue und Rückkehrraten für einen Ort (wie viele Vögel kommen im Folgejahr wieder, wer sind die treuesten Vögel), mit Diagramm und Tabelle."
---
# Ortstreue

1. **Ort klären:** exakte Schreibweise mit `filter_choices` (`column: "place"`, `search` = Teil des Namens); bei einer gespeicherten Ortsgruppe den Begriff nennen.
2. `site_fidelity` mit dem Ort (Teilstring) und optional Art/Zeitraum.
3. Erkläre die zwei Kennzahlen in einfachen Worten: **Rückkehrrate** = von den Vögeln eines Jahres wieder am Ort im Folgejahr; **Ortstreue** = dasselbe nur unter den überhaupt wiedergesehenen Vögeln, also ohne Sterblichkeit/Abwanderung.
4. **Grafik:** `create_chart` `line` oder `bar` je Jahr mit beiden Prozentwerten (`y: ["rueckkehrrate_prozent", "ortstreue_unter_wiedergesehenen_prozent"]`, `y_axis.format: "percent"`), dazu `create_table` der treuesten Vögel (Ring verlinkt, Jahre am Ort, Sichtungen am Ort).
5. **Ergänzend** als Ansicht: Vögel je Jahr am Ort (`create_view`, `metric: {kind: "birds"}`, `dimension: "year"`, `filters.places`) – zeigt, ob kleine Jahrgänge die Raten verzerren.
6. **Einordnung:** Beobachtungsaufwand je Jahr beeinflusst die Werte; kleine Jahrgänge (< 10 Vögel) vorsichtig interpretieren.
7. **Vorschlag:** Vergleich mit einem zweiten Ort (zwei Kacheln in einer Mappe) oder Karte der Vögel, die abgewandert sind. Fragt der Nutzer jedes Jahr danach: als Auswertung speichern (Skill `auswertung-anlegen`).
