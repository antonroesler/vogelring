# Export-Verlauf + Nachtrag der „gemeldet“-Markierung

**Datum:** 2026-07-25
**Kontext:** Der Wiederfunde-Export (RING) setzt das `melded`-Flag bewusst nicht — die
Vogelwarte bestätigt eine Lieferung erst Tage später. Bisher gab es keine Möglichkeit,
danach genau die exportierten Einträge gesammelt als gemeldet zu markieren.

## Was gebaut wurde

- **`sighting_exports` / `sighting_export_items`** — jeder Export merkt sich, welche
  Sichtungen er enthalten hat. `sighting_id` ohne Foreign Key: das Löschen einer
  Sichtung darf nicht die Aufzeichnung dessen löschen, was geliefert wurde.
- **`GET /api/sightings/exports`** — Verlauf, neueste zuerst, mit `pending_count`
  (wie viele Einträge des Laufs noch nicht gemeldet sind).
- **`GET /api/sightings/exports/{id}/sightings`** — die Einträge eines Laufs.
- **`POST /api/sightings/exports/{id}/mark-melded`** — Bulk-Update auf gemeldet.
  Idempotent; merkt sich pro Eintrag, ob *dieser* Lauf ihn umgestellt hat.
- **`POST /api/sightings/exports/{id}/unmark-melded`** — Undo, setzt nur zurück, was
  der Lauf selbst gesetzt hat. Einträge, die vorher schon gemeldet waren, bleiben es.
- **`POST /api/sightings/exports/backfill`** — rekonstruiert einen Export, der vor
  dieser Funktion geliefert wurde. `dry_run` (Default) schreibt nichts.
- **UI:** Button „Exporte“ neben „Wiederfunde-Export“ in der Eintragliste, mit Badge
  für Läufe, die noch auf Bestätigung warten.

Die Tabellen entstehen beim Start über `create_tables()` — keine manuelle Migration.

## Rekonstruktion von Ingos Export (Stand 2026-07-25, noch NICHT ausgeführt)

Ingos Export ging bereits raus und wurde von der Vogelwarte angenommen, bevor der
Verlauf existierte. Da nichts aufgezeichnet wurde, stammt die Rekonstruktion aus den
Nginx-Access-Logs auf dem Pi (`/mnt/ssd/logs/vogelring/nginx/access.log`).

Das Log-Format enthält keine Benutzerkennung, aber zwei Clients sind klar trennbar:

| Client | IPv6-Präfix | Requests gesamt | Zuordnung |
|---|---|---|---|
| Windows / Firefox | `2a02:908:1d8:5560` | 30.858 | **Ingo** (täglicher Nutzer) |
| macOS / Chrome | `2a0d:3341:bbe3:5210` | 114 | Anton (Tests) |

Exporte von Ingo:

| Zeitpunkt (UTC) | Zeitraum | Größe |
|---|---|---|
| 14.07. 17:43:10 | 2026-01-01 – 2026-02-28 | 23.044 B |
| 15.07. 16:17:21 | 2026-01-01 – 2026-07-15 | 64.459 B |
| 19.07. 07:28:36 | 2026-06-01 – 2026-07-19 | 39.096 B |
| 19.07. 07:57:34 | 2026-06-01 – 2026-07-19 | 33.859 B |
| 20.07. 04:28:26 | 2026-01-01 – 2026-07-20 | 86.899 B |
| **22.07. 04:53:14** | **2026-01-01 – 2026-07-22** | **86.908 B** |

Der letzte Lauf (22.07.) ist der angenommene. Gegenprobe per Read-only-SQL auf prod:

```
Zeitraum 2026-01-01 … 2026-07-22, melded IS NOT TRUE
  ohne Zeitpunkt-Grenze (Stand heute):        1421
  mit created_at <= 2026-07-22 04:53:14:      1407   <- der Export
  erst nach dem Export erfasst:                 14   <- dürfen NICHT markiert werden
  im Zeitraum bereits gemeldet:                 93
```

Der Lauf vom 20.07. rekonstruiert auf dieselben **1407** Einträge wie der vom 22.07. —
die beiden Mengen sind identisch. Welcher der beiden angenommen wurde, ändert das
Ergebnis also nicht.

### Auszuführen (nach dem Deploy, über die UI)

Eintragliste → **Exporte** → *Früheren Export nachtragen*:

| Feld | Wert |
|---|---|
| Von | `2026-01-01` |
| Bis | `2026-07-22` |
| Export-Zeitpunkt | `22.07.2026 06:53` (Ortszeit CEST = 04:53:14 UTC) |
| Notiz | z. B. „Export Ingo 22.07.2026 — von Vogelwarte angenommen“ |

Erst **Prüfen** — die Anzeige muss **1407** ergeben. Erst dann nachtragen. Der Vorgang
landet als Lauf im Verlauf und ist dort rückgängig zu machen.

Der Export-Zeitpunkt ist der entscheidende Schutz: ohne ihn würden die 14 Einträge,
die Ingo nach dem Export erfasst hat, fälschlich als gemeldet markiert und beim
nächsten Export fehlen.
