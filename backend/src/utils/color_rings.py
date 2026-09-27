"""
Color ring (Farbring) domain helpers: palette, normalization and search parsing.

A color ring is identified by ring color + (optional) text color + inscription code.
"rot H3E4" and "gelb H3E4" are two different rings.

The palette keys are stored in the database; German labels and abbreviations are
used for display and search. Keep in sync with frontend/src/utils/colorRings.ts.
"""

import re
from dataclasses import dataclass, field

# key -> (German label, search abbreviations)
COLOR_PALETTE: dict[str, tuple[str, tuple[str, ...]]] = {
    "white": ("weiß", ("w", "weiss")),
    "black": ("schwarz", ("s", "n")),
    "red": ("rot", ("r",)),
    "orange": ("orange", ("o",)),
    "yellow": ("gelb", ("y", "ge")),
    "lightgreen": ("hellgrün", ("hg", "hellgruen", "lime")),
    "darkgreen": ("dunkelgrün", ("dg", "g", "gruen", "grün", "dunkelgruen")),
    "lightblue": ("hellblau", ("hb",)),
    "darkblue": ("dunkelblau", ("db", "b", "blau")),
    "violet": ("violett", ("v", "lila")),
    "pink": ("rosa", ("p", "pink")),
    "brown": ("braun", ("br",)),
    "grey": ("grau", ("gr",)),
}

MARK_TYPES = {"leg": "Beinring", "neck": "Halsring", "wing": "Flügelmarke"}
LEGS = {"left": "links", "right": "rechts"}

_TOKEN_TO_COLOR: dict[str, str] = {}
for _key, (_label, _abbrevs) in COLOR_PALETTE.items():
    for _token in (_key, _label, *_abbrevs):
        _TOKEN_TO_COLOR[_token.lower()] = _key


def color_from_token(token: str) -> str | None:
    """Map a color key, German name or abbreviation to a palette key."""
    return _TOKEN_TO_COLOR.get(token.strip().lower())


def color_label(key: str | None) -> str | None:
    if not key:
        return None
    return COLOR_PALETTE.get(key, (key, ()))[0]


def normalize_code(code: str | None) -> str | None:
    """Inscriptions are compared case-insensitively and without whitespace."""
    if code is None:
        return None
    normalized = re.sub(r"\s+", "", code).upper()
    return normalized or None


def validate_color(key: str | None, field_name: str) -> str | None:
    if key in (None, ""):
        return None
    if key not in COLOR_PALETTE:
        raise ValueError(f"Unbekannte Farbe für {field_name}: {key}")
    return key


@dataclass
class RingQuery:
    """A parsed ring search like "rot/weiß H3E4" or "282*"."""

    code_pattern: str
    ring_color: str | None = None
    text_color: str | None = None
    tokens: list[str] = field(default_factory=list)

    @property
    def has_color(self) -> bool:
        return self.ring_color is not None


def parse_ring_query(query: str) -> RingQuery:
    """Split a search string into optional ring/text colors and a code pattern.

    Leading or trailing color words are only treated as colors if something else
    is left over, so a bare "R" or "gelb" is still searched as a code.
    """
    normalized = query.replace("...", "*").replace("…", "*")
    tokens = [t for t in re.split(r"[\s/,;]+", normalized) if t]

    colors: list[str] = []
    rest: list[str] = []
    for token in tokens:
        color = color_from_token(token)
        if color and len(colors) < 2 and not rest:
            colors.append(color)
        else:
            rest.append(token)

    if not rest:
        # Nothing but color words: search them as a code instead
        return RingQuery(code_pattern="".join(tokens).upper(), tokens=tokens)

    return RingQuery(
        code_pattern="".join(rest).upper(),
        ring_color=colors[0] if colors else None,
        text_color=colors[1] if len(colors) > 1 else None,
        tokens=tokens,
    )


def matches_pattern(pattern: str, value: str | None) -> bool:
    """Case-insensitive wildcard match. Without '*', matches a substring."""
    if not value or not pattern:
        return False
    value = value.upper()
    pattern = pattern.upper()
    if "*" not in pattern:
        return pattern in value
    regex = ".*".join(re.escape(part) for part in pattern.split("*"))
    return re.fullmatch(regex, value) is not None
