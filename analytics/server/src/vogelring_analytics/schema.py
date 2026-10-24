"""Curated data dictionary for the Vogelring database (German, model-facing)."""

SCHEMA_DOC = """\
# Vogelring Datenbank – Datenwörterbuch

Alle Abfragen laufen read-only (max. 50 000 Zeilen, 30 s). Nutze fast immer die View `v_sightings`.

## v_sightings  (Sichtungen + verknüpfte Beringungsdaten; eine Zeile pro Sichtung)
Enthält zusätzlich Vögel, die beringt aber nie gesichtet wurden: dann ist `date` NULL.

| Spalte | Typ | Bedeutung |
|---|---|---|
| id | uuid | Sichtungs-ID → https://vogelring.com/entries/<id> |
| ring | text | Ringnummer = Vogel-ID → https://vogelring.com/birds/<ring> (kann NULL sein, wenn nur `reading`) |
| reading | text | tatsächlich abgelesener Text (unsicher, z.B. '...23886') |
| species | text | Art bei der Sichtung (Kanadagans, Graugans, Nilgans, Höckerschwan, Weißwangengans, Steinkauz, Kanada-x Graugans, …) |
| ringed_as_species | text | Art laut Beringung |
| date | date | Sichtungsdatum (NULL = nie gesichtet) |
| place | text | Ortsname, z.B. 'F, Ostpark', 'OF, Carl-Ulrich-Brücke', 'F, Mainkai, Innenstadt' |
| area | text | Kleinfläche innerhalb des Orts |
| lat, lon | numeric | Koordinaten der Sichtung (WGS84). Für Karten IMMER lat/lon nutzen |
| is_exact_location | bool | Koordinate exakt (true) oder nur ungefähr |
| age | int | Alter bei Sichtung: 1=ad(ult), 2=dj (diesjährig), 3=vj (vorjährig), 4=juv |
| sex | int | 0=unbekannt, 1=männlich, 2=weiblich |
| status | text | BV=Brutvogel, MG=Mausergast, NB=Nichtbrüter, RV=Reviervogel, TF=Totfund (selten gepflegt, meist NULL) |
| melder | text | Beobachter-Kürzel (IR = Ingo R.) |
| large_group_size / small_group_size | int | Gruppengrößen vor Ort |
| partner | text | Ring des Partners, oft 'ub'/'unberingt' |
| breed_size / family_size | int | Brutgröße / Familiengröße |
| comment | text | Kommentar |
| ringing_date | date | Beringungsdatum |
| ringing_place | text | Beringungsort, z.B. 'Frankfurt, Ostpark*[DEED, 5818]' |
| ringing_lat, ringing_lon | numeric | Koordinaten der Beringung |
| ringer | text | Beringer |
| ring_scheme | text | Ringzentrale |
| ringing_age | int | Alterscode bei Beringung: 1 Nestling, 2 Fängling, 3 Diesjährig, 4 Nicht diesjährig, 5 Vorjährig, 6 Älter als vorjährig, 7 3. Kalenderjahr, 8 Über 3 Jahre |
| ringing_sex | int | Geschlecht bei Beringung |
| ringing_status | text | Status bei Beringung |

## ringings  (eine Zeile pro Beringung)
ring, ring_scheme, species, date, place, lat, lon, ringer, age, sex, status, comment

## color_rings  (Farbringe zusätzlich zum Metallring)
ring (Metallring), color_ring (Code), color, position, date_from, date_to

## bird_relationships  (Verwandtschaft, gerichtet)
bird1_ring, bird2_ring, relationship_type (breeding_partner | parent_of | child_of | sibling_of), year, confidence, source, notes
Komfort-Views: bird_partners, bird_parents, bird_children, bird_siblings, bird_family_tree.

## Konventionen & Fallstricke
- Sichtungen zählen: `WHERE date IS NOT NULL`. Individuen zählen: `COUNT(DISTINCT ring)`.
- Ein Ort hat Schreibvarianten: 'F, Ostpark' = 'Frankfurt, Ostpark'. Suche mit `place ILIKE '%Ostpark%'`.
  'F, Mainkai, Innenstadt' umfasst die Beringungsorte Friedensbrücke, Innenstadt, Mainkai, Portikusinsel,
  Weseler Werft, Eiserner Steg.
- Monat: `EXTRACT(MONTH FROM date)`; Jahr: `EXTRACT(YEAR FROM date)`.
- Mauser (flugunfähig, Anfang Sommer): Graugans Mai–Juni; Kanadagans, Nilgans, Weißwangengans Juni–Juli.
  "Mausergast im Ostpark" = Sichtung im Ostpark in diesen Monaten (status 'MG' ist nur sporadisch gepflegt).
- Entfernungen: `earth_distance` ist nicht installiert; nutze Haversine in SQL oder filtere grob über lat/lon-Box.
  Frankfurt Zentrum ≈ 50.11, 8.68.
- Die Daten sagen mehr über den Beobachter als über die Vögel: keine Sichtung ≠ Vogel war nicht da.
- Für Karten: `SELECT ring, date, place, species, lat, lon, ringing_lat, ringing_lon, ringing_place, status …`
  und `lat IS NOT NULL`.
"""
