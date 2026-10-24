# Vogelring Analyse – Design-System

Ziel: Vogelring (vogelring.com), der Chat (LibreChat, chat.vogelring.com) und die Analyse-App fühlen sich wie **ein**
Werkzeug an. Grundlage ist die LibreChat-Oberfläche (gemessen am 24.10.2026 an chat.vogelring.com, v0.8.8):
neutrale Grautöne, 1-px-Rahmen statt Schatten, große Radien, Inter. Die Vogelring-Markenfarbe (Dunkelblau) ist der
einzige Akzent. Nicht übertreiben: keine Verläufe, keine Glas-Effekte, keine Illustrationen.

## Tokens (CSS-Variablen in `src/styles.css`, Werte als RGB-Tripel wie in LibreChat)

| Token | Hell | Dunkel | LibreChat-Quelle |
|---|---|---|---|
| `--text-primary` | 33 33 33 | 236 236 236 | gleich |
| `--text-secondary` | 66 66 66 | 205 205 205 | gleich |
| `--text-tertiary` | 89 89 89 | 153 150 150 | gleich |
| `--surface-primary` (Seiten-/Kartenfläche) | 255 255 255 | 13 13 13 | gleich |
| `--surface-primary-alt` | 247 247 248 | 23 23 23 | gleich |
| `--surface-secondary` (Sidebar, Kopfzeile, Eingabefelder-Hintergrund in Dialogen) | 247 247 248 | 33 33 33 | gleich |
| `--surface-tertiary` (Chips, Tags) | 236 236 236 | 47 47 47 | gleich |
| `--surface-hover` | 227 227 227 | 57 57 57 | gleich |
| `--surface-active` (aktiver Nav-Eintrag) | 236 236 236 | 89 89 89 | gleich |
| `--surface-dialog` | 255 255 255 | 18 18 18 | gleich |
| `--border-light` (Standardrahmen) | 227 227 227 | 47 47 47 | gleich |
| `--border-medium` (Eingabefelder, Fokus-Vorstufe) | 205 205 205 | 66 66 66 | gleich |
| `--border-heavy` | 153 150 150 | 89 89 89 | gleich |
| `--brand` (Vogelring-Blau: Primärbuttons, aktive Icons, Links, Fokusring) | 0 67 108 | 125 185 230 | vogelring.com `primary #00436C`; dunkel aufgehellt für Kontrast |
| `--brand-soft` (Hintergrund hinter Brand-Icons, aktive Chips) | 230 239 245 | 20 45 65 | abgeleitet |
| `--success` | 4 120 87 | 16 185 129 | LibreChat `surface-submit` |
| `--warning` | 180 83 9 | 251 191 36 | LibreChat `text-warning` |
| `--danger` | 185 28 28 | 248 113 113 | LibreChat `surface-destructive` |

Dunkelmodus folgt `prefers-color-scheme`, mit Umschalter in der Sidebar (Hell / Dunkel / System, in localStorage).
LibreChat hält sich an dasselbe Schema, Ingo sieht also auf beiden Bildschirmen dieselbe Stimmung.

## Typografie

- Schrift: **Inter** (lokal gebündelt über `@fontsource-variable/inter`, kein Google-Fonts-Request), Fallback `system-ui, sans-serif`.
  Zahlen in Tabellen und Kennzahlen mit `font-variant-numeric: tabular-nums`.
- Grundgröße 16 px / Zeilenhöhe 24 px (LibreChat-Body). Sekundärtext 14 px. Kleingedrucktes 12 px.
- Seitentitel 24 px / 600. Kartentitel 16 px / 600. Nav-Einträge 14 px / 500. Abschnittslabels 12 px / 600, Großbuchstaben mit `letter-spacing: .04em`, Farbe tertiär.
- Keine Versalien in Buttons, kein Letter-Spacing (Vuetify-Default abschalten).

## Form

- Radien: Karten/Dialoge/Eingaben **12 px** (LibreChat-Chip/Dialog), Buttons **9999 px** (Pill, wie der Senden-Knopf) für Primär-/Sekundär-Buttons, 8 px für Toggle-Gruppen und Chips.
- **Rahmen statt Schatten**: `1px solid rgb(var(--border-light))`, Elevation 0 überall. Dialoge dürfen einen weichen Schatten haben (`0 8px 32px rgba(0,0,0,.12)`).
- Abstände auf 4-px-Raster: Seiten-Padding 24 px (≥ 1280 px: 32 px), Kartenpolster 20 px, Abstand zwischen Karten 16 px, zwischen Abschnitten 24 px.
- Icons 20 px (MDI, Strichstärke bleibt), Farbe tertiär, aktiv Brand.

## Bausteine

- **Shell**: Sidebar 260 px, `surface-secondary`, rechter Rahmen `border-light`, Logo oben (Feder-Icon in `brand-soft`-Kreis + „Vogelring Analyse“), Nav-Einträge als 36-px-Zeilen mit 8-px-Radius, aktiv = `surface-active` + Brand-Icon + Text 600. Unten: Chat-Link, vogelring.com-Link, Theme-Umschalter, Einklappen. Kopfzeile 56 px, `surface-primary`, unterer Rahmen, links Seitentitel 16 px/600, rechts Status-Chip (Live) und „Agent fragen“-Button.
- **Buttons**: Primär = Brand-Füllung, weißer Text, Pill. Sekundär = `surface-primary` + `border-light`, Text primär (wie der Agent-Chip „Vogelring“ im Chat). Tertiär = Text-only. Höhe 36 px, Padding 0 16 px, Icon links 18 px. Gefährlich = `danger` nur als Text/Outline, gefüllt erst im Bestätigungsdialog.
- **Karten**: `surface-primary`, Rahmen, 12 px, hover: Rahmen `border-medium` + Hintergrund `surface-primary-alt` (nur bei klickbaren Karten). Kartentitel-Zeile mit Icon in `brand-soft`-Quadrat 32 px / 8 px Radius.
- **Eingabefelder**: Vuetify `outlined`, Rahmen `border-medium`, Fokus Brand 1 px + 3-px-Ring `rgb(var(--brand) / .2)`, Radius 12 px, Höhe 40 px (`comfortable`). Labels oberhalb (persistent-placeholder-Stil) statt schwebend, wo möglich.
- **Chips/Tags**: `surface-tertiary`, 8 px Radius, 12 px Text, kein Rahmen. Filter-Chips mit × zum Entfernen.
- **Tabellen**: Kopfzeile `surface-secondary`, 12 px/600 Großbuchstaben, Zeilenrahmen `border-light`, Zeilenhöhe 40 px, Zebra aus, hover `surface-primary-alt`, Zahlen rechtsbündig tabular.
- **Aktivität/Live-Feed**: Zeitstempel 12 px tertiär, Icon 16 px, Text 14 px, Zeilen 32 px, Rahmenlinien hell. Neue Ereignisse blenden sanft ein (160 ms).
- **Leerzustände**: Icon 40 px tertiär, Titel 16 px/600, Text 14 px sekundär, ein Primär-Button. Keine Illustrationen.
- **Diagramme**: Hintergrund transparent, Achsen/Gitter `border-light`, Beschriftung `text-secondary` 12 px, Farben aus der bestehenden Chart-Palette, Tooltip `surface-dialog` + Rahmen. Karten (Leaflet) ohne Rahmen innerhalb der Karte-Kachel, Zoom-Controls im Pill-Stil.
- **Chat-Drawer**: 420 px, `surface-primary`, linker Rahmen; Kopfzeile wie die Haupt-Kopfzeile; iframe darunter randlos.

## Bewegung

Nur funktional: Hover/Fokus 120 ms, Drawer 200 ms `cubic-bezier(.22,1,.36,1)` (LibreChat `--resize-ease`), Live-Einblendung 160 ms. `prefers-reduced-motion` respektieren.

## Barrierefreiheit

Kontrast ≥ 4.5:1 für Text (Brand-Blau auf Weiß: 9.9:1; Dunkelmodus-Brand auf 13-13-13: 9.3:1), sichtbarer Fokusring
überall, Tastaturbedienung für Karten (Router-Links), `aria-live="polite"` für den Live-Feed, Zielgröße ≥ 36 px.
