---
name: aenderung-vorschlagen
description: "Daten in Vogelring ändern, nur auf ausdrücklichen Wunsch: Regel klären, Vorschlag ohne Schreiben (propose_changes), in Alltagssprache erklären, nach Ja übernehmen (apply_changes), berichten, rückgängig machen möglich."
---
# Änderung vorschlagen und übernehmen

Gilt nur, wenn der Nutzer ausdrücklich eine Änderung verlangt. Mögliche Operationen: `set_fields` (erlaubte Felder von Sichtungen/Beringungen), `rename_place`, `convert_to_color_ring`, `upsert_color_ring`, `merge_reading_to_ring`. Löschen oder neue Einträge anlegen geht nicht („Ich kann in Vogelring nichts ändern, nur auswerten“ – für diese Fälle).

1. **Lage prüfen:** Betroffene Daten ansehen, bevor du etwas vorschlägst: `bird_profile` bzw. `filter_choices` (z. B. `column: "ring"`, `search: "W408"`; bei Orten `column: "place"`). So kennst du Anzahl, Zeitraum und mögliche Verwechslungen.
2. **Regel klären:** Fehlt etwas, eine Rückfrage-Runde mit ask_user_question und 2–4 Optionen. Typisch: Ringfarbe, Schriftfarbe, ob der Metallring erhalten bleibt, alle Sichtungen oder nur ein Zeitraum, neuer Ortsname genau so geschrieben?
3. **Vorschlag:** **Immer** zuerst `propose_changes` – schreibt nichts. Mehrere Operationen in einem Vorschlag sind in Ordnung, aber nur das, was der Nutzer verlangt hat; nichts „gleich mit aufräumen“.
4. **Erklären:** Zusammenfassung in Alltagssprache aus dem Ergebnis: Anzahl je Operation und Feld, alt → neu an 1–2 Beispielen, Warnungen (z. B. „3 Sichtungen haben schon einen anderen Farbring“), und immer der Satz „Nichts wird gelöscht.“ Vorschau-Link (`preview_url`) nennen. Frage: „Soll ich das so übernehmen?“
5. **Übernehmen:** Erst nach einem klaren Ja `apply_changes` mit dem Vorschlag. Vorher ankündigen: „Gleich erscheint im Chat eine Bestätigungskarte – bitte dort noch einmal annehmen.“ Bei Nein oder Änderungswunsch: Regel anpassen, neuer Vorschlag (zurück zu Schritt 3).
6. **Berichten:** Was wurde geändert (Anzahl, Felder), Links zu einem Beispiel auf vogelring.com, und: „Falls etwas nicht stimmt, kann ich die Änderung vollständig rückgängig machen.“ (`rollback_changes`; frühere Änderungen mit `list_changes`/`get_change`).
7. **Merken:** `save_note` mit Datum, Regel, Anzahl und Änderungs-ID (Tag „Änderung“).

## Beispiel: W408 ist ein Farbring

Nutzer: „W408 ist gar kein Metallring, das ist der rote Farbring mit weißer Schrift.“

1. `bird_profile` für W408: 65 Sichtungen 2022–2026, keine Beringung mit diesem Ring.
2. Rückfrage (falls nicht gesagt): „Ist auf dem Vogel auch ein Metallring bekannt?“ – Optionen „Nein, Metallring leeren“, „Ja, ich nenne ihn“.
3. `propose_changes` mit Operation `convert_to_color_ring`: `value: "W408"`, `ring_color: "red"`, `text_color: "white"`, `code: "W408"`, `keep_metal_ring: false` – der Farbring wird im Farbring-Verzeichnis eingetragen.
4. Antwort: „Betroffen sind 65 Sichtungen von W408 (2022–2026). Bei allen wird der Metallring geleert und der Farbring ‚rot, weiße Schrift, W408‘ eingetragen; der Farbring kommt ins Farbring-Verzeichnis. Nichts wird gelöscht. Vorschau: <preview_url>. Soll ich das so übernehmen?“
5. Nach „Ja“: Hinweis auf die Bestätigungskarte, dann `apply_changes`.
6. „Erledigt: 65 Sichtungen tragen jetzt den Farbring rot W408 (Beispiel: <Link>). Das lässt sich jederzeit rückgängig machen.“ Dann `save_note`.
