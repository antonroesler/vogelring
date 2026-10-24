---
name: datenpruefung
description: "Datenqualität prüfen (fehlende Koordinaten, Dubletten, Sichtungen vor der Beringung, Ortsschreibweisen, unplausible Bewegungen) und als verständliche Liste mit Exporten aufbereiten; Korrekturen nur auf ausdrücklichen Wunsch."
---
# Datenprüfung

1. `data_quality` ausführen.
2. Ergebnis als kurze Liste: je Prüfung ein Satz in Alltagssprache (was ist das Problem, warum ist es wichtig, wie viele Fälle, 1–2 Beispiele mit Link zu https://vogelring.com/entries/<id> bzw. /birds/<ring>).
3. Die drei wichtigsten Punkte zuerst (Reihenfolge: falsche Daten > Dubletten > fehlende Koordinaten > Schreibweisen).
4. Für jede Prüfung mit Treffern einen XLSX-Export anbieten (`export_dataset` mit sprechendem Dateinamen); bei Schreibvarianten eine Tabelle (`create_table`) mit Vorschlag, welche Schreibweise die häufigste ist (Häufigkeiten mit `filter_choices`, `column: "place"`).
5. **Korrigieren nur auf Wunsch:** Die Prüfung ändert nichts. Korrekturen, die über den Änderungs-Ablauf gehen (Ortsschreibweise vereinheitlichen, Felder setzen, Farbring zuordnen), bietest du höchstens an; verlangt der Nutzer sie ausdrücklich, Skill `aenderung-vorschlagen`. Alles andere (z. B. Dubletten löschen) korrigiert er direkt in Vogelring über die Links („Ich kann in Vogelring nichts ändern, nur auswerten.“).
6. Abschließend: welche Auswertungen durch die Probleme beeinflusst werden (z. B. Karten ohne die Sichtungen ohne Koordinaten), ein Angebot, den Bericht als PDF zu erstellen, und `save_note` mit den Fallzahlen (Tag „Datenqualität“), damit die nächste Prüfung vergleichen kann.
