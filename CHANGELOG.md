# Changelog

All notable changes to Vogelring will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.0](https://github.com/antonroesler/vogelring/compare/v2.0.0...v2.1.0) (2025-09-14)


### ✨ Features

* add ringing entry list API and frontend components for filtering and displaying ringings ([#39](https://github.com/antonroesler/vogelring/issues/39)) ([a71780f](https://github.com/antonroesler/vogelring/commit/a71780f18d005a30814c4b24411c8281feb32c09))
* enhance backup script to copy backups to shared directory and improve data directory exclusion ([9585d35](https://github.com/antonroesler/vogelring/commit/9585d352dda76ec798cc553ae4467f94b5b08567))


### 🐛 Bug Fixes

* determine species by most common in sightings ([d46fdd7](https://github.com/antonroesler/vogelring/commit/d46fdd764f8c58a1746c5a3a7d1815ac6532dc4c))
* open correct bird when click chart in radius analysis ([7cb381c](https://github.com/antonroesler/vogelring/commit/7cb381c3c666fbd61a17a7a3a05c091cbf6261c3))


### 🔧 Miscellaneous

* update change log ([c50eb0c](https://github.com/antonroesler/vogelring/commit/c50eb0c0d86463a6e45bf8004ec85a293bf804c8))

## [2.0.0](https://github.com/antonroesler/vogelring/compare/v1.0.0...v2.0.0) (2025-09-14)

### ⚠ BREAKING CHANGES

- Vogelring läuft jetzt auf einem privaten Server
- Nutzung einer SQL Datenbank für ein deutlich schnelleres Erlebnis beim Laden, Erstellen und Löschen von Daten
- Authentifizeirung über Cloudflare Zero Trust

### ✨ Features

- Neue Analytics Platform für bessere Analyse Möglichkeiten
- Das ausklappen der Zeilen kann über den Einstellungspunkt Hover-Erweiterung ausgeschalten werden
- Bessere Sortierung von Duplikaten
- Changelog für Versionen eingeführt

### 🐛 Bug Fixes

- Änderung Paar Status zu Familien Status
- Problem beim Löschen von Duplikaten behoben

### 🔧 Miscellaneous

- Footer entfernt

## [1.0.0] - 2025-09-14

### ✨ Features

- Ursprünlicher Release von Vogelring auf AWS
