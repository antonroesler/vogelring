"""House colours: Vuetify theme, species colours from the Vue app, Ingo's season convention."""

from __future__ import annotations

THEME = {
    "primary": "#00436C",
    "secondary": "#228096",
    "accent": "#37906D",
    "error": "#D07B4D",
    "warning": "#EAD054",
    "background": "#F7F4F1",
    "text": "#00436C",
    "muted": "#5F6B73",
}

# Distinct, readable on a light basemap. Order matters (first = most used).
CATEGORY_PALETTE = [
    "#228096", "#D07B4D", "#37906D", "#EAD054", "#00436C", "#8E44AD",
    "#E91E63", "#69AC91", "#C0392B", "#2980B9", "#F39C12", "#7F8C8D",
    "#16A085", "#9B59B6", "#D35400", "#1ABC9C", "#34495E", "#E67E22",
    "#2ECC71", "#3498DB",
]

SPECIES_COLORS = {
    "Nilgans": "#D07B4D",
    "Kanadagans": "#37906D",
    "Graugans": "#228096",
    "Bläss-x Graugans": "#69AC91",
    "KxG": "#EAD054",
    "Kanada-x Graugans": "#EAD054",
    "Höckerschwan": "#00436C",
    "Weißwangengans": "#9BC8B6",
    "Mandarinente": "#DC9C7A",
    "Kormoran": "#E7BDA6",
    "Steinkauz": "#8E44AD",
}
SPECIES_DEFAULT = "#9AA5AD"

# Ingo's convention for recapture maps.
SEASONS = [
    {"key": "nov_jan", "label": "Nov–Jan", "months": (11, 12, 1), "color": "#1E3A8A"},
    {"key": "feb_mar", "label": "Feb–Mär", "months": (2, 3), "color": "#F2C230"},
    {"key": "apr_jun", "label": "Apr–Jun", "months": (4, 5, 6), "color": "#2E8B57"},
    {"key": "jul_okt", "label": "Jul–Okt", "months": (7, 8, 9, 10), "color": "#D7263D"},
]
_SEASON_BY_MONTH = {m: s for s in SEASONS for m in s["months"]}

MONTHS_DE = ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]
MONTHS_DE_LONG = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"]


def season_for_month(month: int | None) -> dict | None:
    if month is None:
        return None
    return _SEASON_BY_MONTH.get(int(month))


def species_color(name: str | None) -> str:
    if not name:
        return SPECIES_DEFAULT
    return SPECIES_COLORS.get(name, SPECIES_DEFAULT)


def category_colors(values: list[str], explicit: dict[str, str] | None = None) -> dict[str, str]:
    out: dict[str, str] = {}
    i = 0
    for v in values:
        if explicit and v in explicit:
            out[v] = explicit[v]
        else:
            out[v] = CATEGORY_PALETTE[i % len(CATEGORY_PALETTE)]
            i += 1
    return out


def month_label(value) -> str:
    try:
        m = int(value)
        if 1 <= m <= 12:
            return MONTHS_DE[m - 1]
    except (TypeError, ValueError):
        pass
    return str(value)


RINGING_AGE = {
    1: "Nestling", 2: "Fängling", 3: "Diesjährig", 4: "Nicht diesjährig", 5: "Vorjährig",
    6: "Älter als vorjährig", 7: "3. Kalenderjahr", 8: "Über 3 Jahre",
}
SIGHTING_AGE = {1: "adult", 2: "diesjährig", 3: "vorjährig", 4: "juvenil"}
STATUS = {"BV": "Brutvogel", "MG": "Mausergast", "NB": "Nichtbrüter", "RV": "Reviervogel", "TF": "Totfund"}
