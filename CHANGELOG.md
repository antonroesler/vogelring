# Changelog

All notable changes to Vogelring will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.5.0](https://github.com/antonroesler/vogelring/compare/v2.4.0...v2.5.0) (2025-09-28)


### ✨ Features

* **frontend:** add totfund status and centralized status formatting ([5ea2cc4](https://github.com/antonroesler/vogelring/commit/5ea2cc456bc918f308678762de71daf95646abde)), closes [#48](https://github.com/antonroesler/vogelring/issues/48)
* **frontend:** enhance shareable report with coordinates, sex, and group size columns ([306c620](https://github.com/antonroesler/vogelring/commit/306c620b436b1e3ebc4ca41464409177b54246ae))


### 🐛 Bug Fixes

* Rastvogel -&gt; Reviervogel ([462ded7](https://github.com/antonroesler/vogelring/commit/462ded70ec740cc666e763ad8587209264a93cad))
* set ringing id in family relationship ([97e6cbe](https://github.com/antonroesler/vogelring/commit/97e6cbefd584d825c412cd0e922336104790f203))
* ui improvements and fixed for working with family relationships ([8d9d540](https://github.com/antonroesler/vogelring/commit/8d9d540635367c816b96dc70b070a44fbe9f294c))


### 🔧 Miscellaneous

* more rules ([e5cf6de](https://github.com/antonroesler/vogelring/commit/e5cf6de6b3f0b2b4dd438b039dfd9ee1edbca407))
* rules ([5679d9a](https://github.com/antonroesler/vogelring/commit/5679d9a23f3bee401a528d819782a74ddffb6285))


### 📚 Documentation

* family relationships ([9c4aba2](https://github.com/antonroesler/vogelring/commit/9c4aba2c43a86cb98803da189ec2998b9ff802d2))

## [2.4.0](https://github.com/antonroesler/vogelring/compare/v2.3.0...v2.4.0) (2025-09-27)


### ✨ Features

* coordinates in report ([39d7cc5](https://github.com/antonroesler/vogelring/commit/39d7cc581a42c3f1d29b422452377cad2984dceb))
* family relationship list ([7f0b638](https://github.com/antonroesler/vogelring/commit/7f0b6382ecc532ffd4322c429eab3f51b041ff34))
* new field comment for ringings ([7103f10](https://github.com/antonroesler/vogelring/commit/7103f104ef71eafd32f803afec42b10c9347b941))


### 🐛 Bug Fixes

* clear field settings ([0eb10ff](https://github.com/antonroesler/vogelring/commit/0eb10ff13506b6c07f185d91f9e44bac237af3a0))

## [2.3.0](https://github.com/antonroesler/vogelring/compare/v2.2.0...v2.3.0) (2025-09-22)


### ✨ Features

* family relationships re-modelling ([#49](https://github.com/antonroesler/vogelring/issues/49)) ([ac44680](https://github.com/antonroesler/vogelring/commit/ac44680a578a5905cce54060ff9c1ba5bb606cae))

## [2.2.0](https://github.com/antonroesler/vogelring/compare/v2.1.0...v2.2.0) (2025-09-18)


### ✨ Features

* expiration date for reports ([3980196](https://github.com/antonroesler/vogelring/commit/3980196360ad016187c82639e2d4af3d2006b80d))
* version check ([44cf183](https://github.com/antonroesler/vogelring/commit/44cf18382d01bf864b81bb84d4a9d6334b40bfbc))


### 🐛 Bug Fixes

* row click in ringing table ([c259b71](https://github.com/antonroesler/vogelring/commit/c259b7137623679d26af87a174f0ba6c9651e565))
* shareable report ([b1d1f6a](https://github.com/antonroesler/vogelring/commit/b1d1f6a6c25b5e734b30aab061d96f2929c91cb0))


### 🔧 Miscellaneous

* remove old script ([4e43d0f](https://github.com/antonroesler/vogelring/commit/4e43d0fb599e19f50d6e783a4680eb09d5766476))


### 📚 Documentation

* set change log date of version 1.0.0 ([874aa7a](https://github.com/antonroesler/vogelring/commit/874aa7a9f20176f2509753f48f54b3b2eada998a))


### ♻️ Code Refactoring

* use correct ringing age mapping ([7781f47](https://github.com/antonroesler/vogelring/commit/7781f475a646e66c27c72db112eed2d4d70da2fc))

## [2.1.0](https://github.com/antonroesler/vogelring/compare/v2.0.0...v2.1.0) (2025-09-14)

### ✨ Features

- Entragsliste für Beringungen
- Tägliches Datenbank Backup

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

## [1.0.0] - 2025-01-01

### ✨ Features

- Ursprünlicher Release von Vogelring auf AWS
