"""Ready-made analyses (SQL + pandas) that return plain-language findings plus datasets for charts and maps."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date
from typing import Any

import numpy as np
import pandas as pd

from . import palette, runtime
from .transforms import haversine_km

HAV = (
    "6371 * acos(LEAST(1, cos(radians({a_lat})) * cos(radians({b_lat})) * cos(radians({b_lon}) - radians({a_lon})) "
    "+ sin(radians({a_lat})) * sin(radians({b_lat}))))"
)
KM_FROM_RINGING = HAV.format(a_lat="ringing_lat", a_lon="ringing_lon", b_lat="lat", b_lon="lon")


class AnalysisError(ValueError):
    pass


@dataclass
class Saved:
    dataset_id: str
    rows: int


def _like(pattern: str | None) -> str | None:
    if not pattern:
        return None
    p = pattern.strip().strip("%")
    return f"%{p}%"


def _fmt_date(v: Any) -> str | None:
    if v is None or (isinstance(v, float) and math.isnan(v)) or v is pd.NaT:
        return None
    try:
        return pd.Timestamp(v).strftime("%d.%m.%Y")
    except Exception:
        return str(v)


def _num(v: Any, nd: int = 1) -> Any:
    if v is None or (isinstance(v, float) and (math.isnan(v) or math.isinf(v))):
        return None
    if isinstance(v, (np.integer, int)):
        return int(v)
    f = float(v)
    return int(f) if f.is_integer() else round(f, nd)


def _lit(v: Any) -> str:
    if v is None:
        return "NULL"
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return str(v)
    return "'" + str(v).replace("'", "''") + "'"


def render_sql(sql: str, params: list | tuple | None) -> str:
    """Readable copy of a parameterised query (for the report appendix); not used for execution."""
    out = sql
    for v in params or ():
        out = out.replace("%s", _lit(v), 1)
    return out.strip()


async def _run(sql: str, params: list | tuple, *, name: str, description: str, source: str = "analysis") -> tuple[pd.DataFrame, Saved]:
    db = runtime.database()
    res = await db.query(sql, params=tuple(params) if params else None)
    df = res.to_frame()
    meta = runtime.datasets().save(df, name=name, sql=render_sql(sql, params), truncated=res.truncated, description=description, source=source)
    return df, Saved(meta.id, meta.row_count)


def _where(parts: list[str]) -> str:
    return (" AND " + " AND ".join(parts)) if parts else ""


def _filters_text(species: str | None, place: str | None, place_label: str, year_from: int | None, year_to: int | None) -> str:
    bits = []
    if species:
        bits.append(f"Art = {species}")
    if place:
        bits.append(f"{place_label} enthält „{place.strip('%')}“")
    if year_from and year_to:
        bits.append(f"Jahre {year_from}–{year_to}")
    elif year_from:
        bits.append(f"ab {year_from}")
    elif year_to:
        bits.append(f"bis {year_to}")
    return ", ".join(bits) if bits else "ohne Einschränkung"


# ---------------------------------------------------------------- bird profile


async def bird_profile(ring: str) -> dict[str, Any]:
    ring = ring.strip()
    sql = """
SELECT id, ring, reading, species, date, place, area, lat, lon, age, sex, status, partner, melder,
       large_group_size, small_group_size, breed_size, family_size, comment,
       ringing_date, ringing_place, ringing_lat, ringing_lon, ringer, ring_scheme, ringing_age, ringing_sex, ringed_as_species
FROM v_sightings WHERE ring = %s ORDER BY date NULLS LAST"""
    df, saved = await _run(sql, [ring], name=f"Sichtungen von Ring {ring}", description=f"Alle Sichtungen des Vogels mit Ring {ring}, chronologisch.")
    if df.empty:
        raise AnalysisError(f"Kein Vogel mit Ring '{ring}' gefunden (Ringnummer exakt, ohne Leerzeichen).")
    s = df[df["date"].notna()].copy()
    first = df.iloc[0]
    out: dict[str, Any] = {"ring": ring, "sightings_dataset_id": saved.dataset_id}
    out["ringing"] = {
        "date": _fmt_date(first.get("ringing_date")),
        "place": first.get("ringing_place"),
        "species": first.get("ringed_as_species"),
        "age_code": _num(first.get("ringing_age")),
        "age_label": palette.RINGING_AGE.get(int(first["ringing_age"]), None) if pd.notna(first.get("ringing_age")) else None,
        "ringer": first.get("ringer"),
        "scheme": first.get("ring_scheme"),
    }
    if s.empty:
        out["summary"] = "Der Vogel wurde beringt, aber bisher nie abgelesen."
        out["sightings"] = 0
        return out
    s["km_from_ringing"] = haversine_km(s["ringing_lat"], s["ringing_lon"], s["lat"], s["lon"]).round(1)
    places = s["place"].value_counts()
    far = s.loc[s["km_from_ringing"].idxmax()] if s["km_from_ringing"].notna().any() else None
    years = sorted(s["date"].dt.year.unique().tolist())
    months = s["date"].dt.month.value_counts().sort_index()
    seasons = s["date"].dt.month.map(lambda m: palette.season_for_month(int(m))["label"]).value_counts()
    partners = [p for p in s["partner"].dropna().astype(str).str.strip().unique() if p and p.lower() not in ("ub", "unberingt", "unb", "-")]
    last = s["date"].max()
    out.update({
        "sightings": int(len(s)),
        "first_sighting": _fmt_date(s["date"].min()),
        "last_sighting": _fmt_date(last),
        "days_since_last": int((pd.Timestamp(date.today()) - last).days),
        "years_seen": years,
        "n_places": int(len(places)),
        "top_places": [{"place": p, "sightings": int(n)} for p, n in places.head(6).items()],
        "farthest": None if far is None or pd.isna(far["km_from_ringing"]) else {"km": _num(far["km_from_ringing"]), "place": far["place"], "date": _fmt_date(far["date"])},
        "seasons": {k: int(v) for k, v in seasons.items()},
        "months": {palette.MONTHS_DE[int(m) - 1]: int(n) for m, n in months.items()},
        "status_values": {k: int(v) for k, v in s["status"].dropna().value_counts().items()},
        "partners": partners[:10],
        "dead_find": bool((s["status"] == "TF").any()),
        "link": f"https://vogelring.com/birds/{ring}",
    })
    # family + colour rings (best effort)
    try:
        rel_sql = "SELECT bird1_ring, bird2_ring, relationship_type, year, confidence FROM bird_relationships WHERE bird1_ring = %s OR bird2_ring = %s"
        rel = (await runtime.database().query(rel_sql, params=(ring, ring))).to_frame()
        out["relationships"] = [{"with": (r.bird2_ring if r.bird1_ring == ring else r.bird1_ring), "type": r.relationship_type, "year": _num(r.year), "direction": "→" if r.bird1_ring == ring else "←"} for r in rel.itertuples()][:30]
    except Exception:
        out["relationships"] = []
    try:
        cr = (await runtime.database().query("SELECT color_ring, color, position, date_from, date_to FROM color_rings WHERE ring = %s", params=(ring,))).to_frame()
        out["color_rings"] = [{"code": r.color_ring, "color": r.color, "position": r.position, "from": _fmt_date(r.date_from), "to": _fmt_date(r.date_to)} for r in cr.itertuples()]
    except Exception:
        out["color_rings"] = []
    span_years = years[-1] - years[0] + 1 if years else 0
    out["summary"] = (
        f"{int(len(s))} Sichtungen zwischen {out['first_sighting']} und {out['last_sighting']} ({span_years} Kalenderjahre), "
        f"an {len(places)} Orten; am häufigsten {places.index[0]} ({int(places.iloc[0])}×)."
        + (f" Weitester Fund {out['farthest']['km']} km vom Beringungsort ({out['farthest']['place']}, {out['farthest']['date']})." if out["farthest"] else "")
    )
    return out


# ---------------------------------------------------------------- cohort resighting


async def cohort_resighting(species: str | None, ringing_place: str | None, year_from: int | None, year_to: int | None, group_by: str) -> dict[str, Any]:
    conds, params = [], []
    if species:
        conds.append("ringed_as_species = %s"); params.append(species)
    if _like(ringing_place):
        conds.append("ringing_place ILIKE %s"); params.append(_like(ringing_place))
    if year_from:
        conds.append("EXTRACT(YEAR FROM ringing_date) >= %s"); params.append(year_from)
    if year_to:
        conds.append("EXTRACT(YEAR FROM ringing_date) <= %s"); params.append(year_to)
    sql = f"""
WITH s AS (
  SELECT ring, ringed_as_species, ringing_date, ringing_place, ringing_lat, ringing_lon, ringing_age, date, lat, lon,
         CASE WHEN lat IS NULL OR ringing_lat IS NULL THEN NULL ELSE {KM_FROM_RINGING} END AS km
  FROM v_sightings WHERE ring IS NOT NULL AND ringing_date IS NOT NULL{_where(conds)}
)
SELECT ring, MAX(ringed_as_species) AS art, MAX(ringing_date) AS beringung, MAX(ringing_place) AS beringungsort,
       MAX(ringing_lat) AS ringing_lat, MAX(ringing_lon) AS ringing_lon, MAX(ringing_age) AS alter_bei_beringung,
       EXTRACT(YEAR FROM MAX(ringing_date))::int AS beringungsjahr,
       COUNT(date) AS sichtungen, MIN(date) AS erste_sichtung, MAX(date) AS letzte_sichtung,
       (MIN(date) - MAX(ringing_date)) AS tage_bis_erste, (MAX(date) - MAX(ringing_date)) AS tage_bis_letzte,
       MAX(km) AS max_km
FROM s GROUP BY ring"""
    desc = f"Je beringtem Vogel: Anzahl Wiederfunde, erste/letzte Sichtung, größte Entfernung. Auswahl: {_filters_text(species, ringing_place, 'Beringungsort', year_from, year_to)}."
    df, per_bird = await _run(sql, params, name="Wiederfunde je beringtem Vogel", description=desc)
    if df.empty:
        raise AnalysisError("Keine beringten Vögel für diese Auswahl.")
    df["wiedergefunden"] = df["sichtungen"] > 0
    df["nach_1_jahr"] = df["tage_bis_letzte"].fillna(-1) >= 365
    df["nach_3_jahren"] = df["tage_bis_letzte"].fillna(-1) >= 3 * 365
    key = {"ringing_year": "beringungsjahr", "species": "art", "ringing_place": "beringungsort", "ringing_age": "alter_bei_beringung"}[group_by]
    g = df.groupby(key, dropna=False)
    coh = pd.DataFrame({
        "beringt": g.size(),
        "wiedergefunden": g["wiedergefunden"].sum().astype(int),
        "wiederfundrate_prozent": (g["wiedergefunden"].mean() * 100).round(1),
        "sichtungen_je_wiedergefundenem_vogel_median": g.apply(lambda x: x.loc[x["wiedergefunden"], "sichtungen"].median()).round(1),
        "tage_bis_erste_sichtung_median": g["tage_bis_erste"].median().round(0),
        "nach_1_jahr_noch_gesehen_prozent": (g["nach_1_jahr"].mean() * 100).round(1),
        "nach_3_jahren_noch_gesehen_prozent": (g["nach_3_jahren"].mean() * 100).round(1),
        "max_entfernung_km_median": g["max_km"].median().round(1),
    }).reset_index()
    if key == "alter_bei_beringung":
        coh["alter_bei_beringung_text"] = coh[key].map(lambda v: palette.RINGING_AGE.get(int(v), str(v)) if pd.notna(v) else "unbekannt")
    coh = coh.sort_values(key, na_position="last")
    meta = runtime.datasets().save(coh, name=f"Wiederfundraten nach {key}", sql=render_sql(sql, params), description=f"Je {key}: wie viele Vögel beringt, wie viele davon mindestens einmal wiedergefunden, und wie lange sie nachweisbar blieben. {desc}", source="analysis")
    overall = {
        "ringed": int(len(df)),
        "resighted": int(df["wiedergefunden"].sum()),
        "rate_percent": _num(df["wiedergefunden"].mean() * 100),
        "after_1_year_percent": _num(df["nach_1_jahr"].mean() * 100),
        "after_3_years_percent": _num(df["nach_3_jahren"].mean() * 100),
        "median_days_to_first": _num(df["tage_bis_erste"].median(), 0),
        "median_max_km": _num(df["max_km"].median()),
    }
    rows = [{k: _num(v) if isinstance(v, (int, float, np.integer, np.floating)) else (str(v) if v is not None else None) for k, v in r.items()} for r in coh.head(40).to_dict("records")]
    explain = (
        "Wiederfundrate = Anteil der beringten Vögel, die mindestens einmal wieder abgelesen wurden. "
        "„Nach 1 Jahr noch gesehen“ = Anteil, dessen letzte Sichtung mindestens ein Jahr nach der Beringung liegt (ein vorsichtiges Maß für Überleben + Ortstreue; nicht gesehen heißt nicht tot)."
    )
    return {"filters": _filters_text(species, ringing_place, "Beringungsort", year_from, year_to), "overall": overall, "cohorts": rows, "cohort_dataset_id": meta.id, "per_bird_dataset_id": per_bird.dataset_id, "how_to_read": explain}


# ---------------------------------------------------------------- site fidelity


async def site_fidelity(place: str, species: str | None, year_from: int | None, year_to: int | None) -> dict[str, Any]:
    like = _like(place)
    conds, params = ["ring IN (SELECT DISTINCT ring FROM v_sightings WHERE place ILIKE %s AND date IS NOT NULL AND ring IS NOT NULL)"], [like]
    if species:
        conds.append("species = %s"); params.append(species)
    if year_from:
        conds.append("EXTRACT(YEAR FROM date) >= %s"); params.append(year_from)
    if year_to:
        conds.append("EXTRACT(YEAR FROM date) <= %s"); params.append(year_to)
    sql = f"SELECT ring, species, date, place, lat, lon, ringing_place, ringing_date FROM v_sightings WHERE date IS NOT NULL AND ring IS NOT NULL AND {' AND '.join(conds)} ORDER BY ring, date"
    desc = f"Alle Sichtungen der Vögel, die mindestens einmal an einem Ort mit „{place}“ im Namen gesehen wurden ({_filters_text(species, None, '', year_from, year_to)})."
    df, all_saved = await _run(sql, params, name=f"Sichtungen der {place}-Vögel", description=desc)
    if df.empty:
        raise AnalysisError(f"Keine Sichtungen an einem Ort mit „{place}“.")
    df["at_place"] = df["place"].astype(str).str.contains(place.strip("%"), case=False, regex=False)
    df["year"] = df["date"].dt.year
    per = df.groupby("ring").agg(art=("species", "first"), sichtungen=("date", "size"), am_ort=("at_place", "sum"), erste=("date", "min"), letzte=("date", "max"), orte=("place", "nunique"))
    per["anteil_am_ort_prozent"] = (per["am_ort"] / per["sichtungen"] * 100).round(1)
    yrs = df[df["at_place"]].groupby("ring")["year"].nunique()
    per["jahre_am_ort"] = yrs.reindex(per.index).fillna(0).astype(int)
    per = per.reset_index().sort_values(["jahre_am_ort", "am_ort"], ascending=False)
    per_meta = runtime.datasets().save(per, name=f"Ortstreue je Vogel – {place}", sql=render_sql(sql, params), description=f"Je Vogel: wie viele seiner Sightings am Ort „{place}“ waren und in wie vielen Jahren er dort gesehen wurde. {desc}", source="analysis")
    # year-to-year return
    years = sorted(df["year"].unique())
    rows = []
    for y in years[:-1]:
        at_y = set(df.loc[df["at_place"] & (df["year"] == y), "ring"])
        if not at_y:
            continue
        seen_next = set(df.loc[df["year"] == y + 1, "ring"])
        at_next = set(df.loc[df["at_place"] & (df["year"] == y + 1), "ring"])
        rows.append({"jahr": int(y), "voegel_am_ort": len(at_y), "im_folgejahr_irgendwo_gesehen": len(at_y & seen_next), "im_folgejahr_wieder_am_ort": len(at_y & at_next),
                     "rueckkehrrate_prozent": round(len(at_y & at_next) / len(at_y) * 100, 1), "ortstreue_unter_wiedergesehenen_prozent": round(len(at_y & at_next) / len(at_y & seen_next) * 100, 1) if at_y & seen_next else None})
    ret = pd.DataFrame(rows)
    ret_meta = runtime.datasets().save(ret, name=f"Rückkehrraten {place}", sql=render_sql(sql, params), description=f"Je Jahr: Vögel am Ort „{place}“, davon im Folgejahr wieder dort gesehen (Rückkehrrate) bzw. unter den überhaupt wiedergesehenen (Ortstreue). {desc}", source="analysis")
    summary = {
        "birds": int(len(per)),
        "birds_multi_year": int((per["jahre_am_ort"] >= 2).sum()),
        "median_share_at_place_percent": _num(per["anteil_am_ort_prozent"].median()),
        "mean_return_rate_percent": _num(ret["rueckkehrrate_prozent"].mean()) if not ret.empty else None,
        "mean_fidelity_percent": _num(ret["ortstreue_unter_wiedergesehenen_prozent"].mean()) if not ret.empty else None,
        "most_loyal": [{"ring": r.ring, "years": int(r.jahre_am_ort), "sightings_at_place": int(r.am_ort)} for r in per.head(8).itertuples()],
    }
    explain = "Rückkehrrate = Anteil der in einem Jahr am Ort gesehenen Vögel, die im Folgejahr wieder dort abgelesen wurden. Ortstreue = dasselbe, aber nur unter den Vögeln, die im Folgejahr überhaupt irgendwo gesehen wurden (so wird Sterblichkeit/Abwanderung herausgerechnet)."
    return {"place": place, "filters": _filters_text(species, None, "", year_from, year_to), "summary": summary, "per_year": rows, "per_bird_dataset_id": per_meta.id, "per_year_dataset_id": ret_meta.id, "sightings_dataset_id": all_saved.dataset_id, "how_to_read": explain}


# ---------------------------------------------------------------- dispersal


async def dispersal(species: str | None, ringing_place: str | None, ring: str | None, min_km: float, year_from: int | None, year_to: int | None) -> dict[str, Any]:
    conds, params = [], []
    if ring:
        conds.append("ring = %s"); params.append(ring.strip())
    if species:
        conds.append("species = %s"); params.append(species)
    if _like(ringing_place):
        conds.append("ringing_place ILIKE %s"); params.append(_like(ringing_place))
    if year_from:
        conds.append("EXTRACT(YEAR FROM date) >= %s"); params.append(year_from)
    if year_to:
        conds.append("EXTRACT(YEAR FROM date) <= %s"); params.append(year_to)
    sql = f"""
SELECT ring, species, date, place, lat, lon, ringing_date, ringing_place, ringing_lat, ringing_lon, ROUND(({KM_FROM_RINGING})::numeric, 1) AS km
FROM v_sightings WHERE date IS NOT NULL AND lat IS NOT NULL AND ringing_lat IS NOT NULL AND ring IS NOT NULL{_where(conds)}"""
    desc = f"Sichtungen mit Entfernung zum Beringungsort (Luftlinie). Auswahl: {_filters_text(species, ringing_place, 'Beringungsort', year_from, year_to)}{', Ring ' + ring if ring else ''}."
    df, all_saved = await _run(sql, params, name="Entfernungen zum Beringungsort", description=desc)
    if df.empty:
        raise AnalysisError("Keine Sichtungen mit Koordinaten für diese Auswahl.")
    df["km"] = pd.to_numeric(df["km"], errors="coerce")
    idx = df.groupby("ring")["km"].idxmax()
    far = df.loc[idx, ["ring", "species", "ringing_place", "ringing_date", "ringing_lat", "ringing_lon", "place", "date", "lat", "lon", "km"]].rename(columns={"place": "weitester_ort", "date": "datum_weitester_fund", "km": "max_km"})
    far = far.sort_values("max_km", ascending=False)
    far = far[far["max_km"] >= min_km]
    edges = [0, 1, 5, 20, 100, 500, float("inf")]
    labels = ["< 1 km", "1–5 km", "5–20 km", "20–100 km", "100–500 km", "> 500 km"]
    far["klasse"] = pd.cut(far["max_km"], bins=edges, labels=labels, right=False).astype(str)
    far_meta = runtime.datasets().save(far.reset_index(drop=True), name="Weitester Fund je Vogel", sql=render_sql(sql, params), description=f"Je Vogel der am weitesten vom Beringungsort entfernte Fund (mit Koordinaten von Beringung und Fund, für Karten). {desc}", source="analysis")
    dist = far["klasse"].value_counts().reindex(labels, fill_value=0)
    summary = {
        "birds": int(len(far)),
        "sightings": int(len(df)),
        "median_max_km": _num(far["max_km"].median()),
        "mean_max_km": _num(far["max_km"].mean()),
        "share_over_20km_percent": _num((far["max_km"] >= 20).mean() * 100),
        "share_over_100km_percent": _num((far["max_km"] >= 100).mean() * 100),
        "distance_classes": {k: int(v) for k, v in dist.items()},
        "farthest": [{"ring": r.ring, "species": r.species, "km": _num(r.max_km), "place": r.weitester_ort, "date": _fmt_date(r.datum_weitester_fund), "ringing_place": r.ringing_place} for r in far.head(8).itertuples()],
    }
    return {"filters": desc, "summary": summary, "per_bird_dataset_id": far_meta.id, "sightings_dataset_id": all_saved.dataset_id,
            "how_to_read": "Entfernungen sind Luftlinie zwischen Beringungsort und Fundort. Je Vogel zählt der weiteste Fund. Vögel ohne Koordinaten fehlen."}


# ---------------------------------------------------------------- seasonality


async def seasonality(place: str | None, species: str | None, year_from: int | None, year_to: int | None) -> dict[str, Any]:
    conds, params = [], []
    if _like(place):
        conds.append("place ILIKE %s"); params.append(_like(place))
    if species:
        conds.append("species = %s"); params.append(species)
    if year_from:
        conds.append("EXTRACT(YEAR FROM date) >= %s"); params.append(year_from)
    if year_to:
        conds.append("EXTRACT(YEAR FROM date) <= %s"); params.append(year_to)
    sql = f"""
SELECT EXTRACT(YEAR FROM date)::int AS jahr, EXTRACT(MONTH FROM date)::int AS monat, COUNT(*) AS sichtungen, COUNT(DISTINCT ring) AS individuen, COUNT(DISTINCT date) AS beobachtungstage
FROM v_sightings WHERE date IS NOT NULL{_where(conds)} GROUP BY 1, 2 ORDER BY 1, 2"""
    desc = f"Sichtungen und verschiedene Vögel je Monat und Jahr. Auswahl: {_filters_text(species, place, 'Ort', year_from, year_to)}."
    df, saved = await _run(sql, params, name="Saisonverlauf je Monat", description=desc)
    if df.empty:
        raise AnalysisError("Keine Sichtungen für diese Auswahl.")
    df["monat_name"] = df["monat"].map(lambda m: palette.MONTHS_DE[int(m) - 1])
    runtime.datasets().save(df, name="Saisonverlauf je Monat", sql=render_sql(sql, params), description=desc, source="analysis")
    by_month = df.groupby("monat").agg(sichtungen=("sichtungen", "sum"), individuen=("individuen", "sum"), jahre=("jahr", "nunique")).reindex(range(1, 13), fill_value=0)
    by_month["individuen_pro_jahr"] = (by_month["individuen"] / by_month["jahre"].replace(0, np.nan)).round(1)
    peak = int(by_month["individuen_pro_jahr"].idxmax())
    low = int(by_month["individuen_pro_jahr"].idxmin())
    per_year_peak = df.loc[df.groupby("jahr")["individuen"].idxmax(), ["jahr", "monat", "individuen"]]
    summary = {
        "years": sorted(df["jahr"].unique().tolist()),
        "peak_month": palette.MONTHS_DE_LONG[peak - 1],
        "quietest_month": palette.MONTHS_DE_LONG[low - 1],
        "per_month_individuals_per_year": {palette.MONTHS_DE[m - 1]: _num(v) for m, v in by_month["individuen_pro_jahr"].items()},
        "per_year_peak": [{"year": int(r.jahr), "month": palette.MONTHS_DE[int(r.monat) - 1], "individuals": int(r.individuen)} for r in per_year_peak.itertuples()],
        "observation_days_total": int(df["beobachtungstage"].sum()),
    }
    return {"filters": _filters_text(species, place, "Ort", year_from, year_to), "summary": summary, "dataset_id": saved.dataset_id,
            "how_to_read": "„Individuen“ = verschiedene Ringe im jeweiligen Monat. Monate mit wenigen Beobachtungstagen wirken leerer, als sie sind – beobachtungstage zeigt, wie oft überhaupt geschaut wurde."}


# ---------------------------------------------------------------- companions


async def companions(ring: str, window_days: int, min_shared_days: int) -> dict[str, Any]:
    ring = ring.strip()
    sql = """
WITH me AS (SELECT DISTINCT date, place FROM v_sightings WHERE ring = %s AND date IS NOT NULL)
SELECT s.ring, MAX(s.species) AS art, COUNT(DISTINCT s.date) AS gemeinsame_tage, COUNT(DISTINCT s.place) AS gemeinsame_orte,
       MIN(s.date) AS erstes_treffen, MAX(s.date) AS letztes_treffen, STRING_AGG(DISTINCT s.place, '; ') AS orte
FROM v_sightings s JOIN me ON s.place = me.place AND s.date BETWEEN me.date - %s AND me.date + %s
WHERE s.ring IS NOT NULL AND s.ring <> %s
GROUP BY s.ring HAVING COUNT(DISTINCT s.date) >= %s ORDER BY 3 DESC LIMIT 300"""
    desc = f"Vögel, die am selben Ort und am selben Tag (±{window_days} Tage) wie Ring {ring} gesehen wurden, mindestens {min_shared_days}-mal."
    df, saved = await _run(sql, [ring, window_days, window_days, ring, min_shared_days], name=f"Begleiter von {ring}", description=desc)
    own = (await runtime.database().query("SELECT COUNT(DISTINCT date) AS tage FROM v_sightings WHERE ring = %s AND date IS NOT NULL", params=(ring,))).to_frame()
    own_days = int(own["tage"].iloc[0]) if not own.empty else 0
    if own_days == 0:
        raise AnalysisError(f"Ring {ring} hat keine Sichtungen.")
    df["anteil_prozent"] = (df["gemeinsame_tage"] / own_days * 100).round(1)
    runtime.datasets().save(df, name=f"Begleiter von {ring}", sql=render_sql(sql, [ring, window_days, window_days, ring, min_shared_days]), description=desc + f" Anteil = gemeinsame Tage geteilt durch die {own_days} Beobachtungstage von {ring}.", source="analysis")
    top = [{"ring": r.ring, "species": r.art, "shared_days": int(r.gemeinsame_tage), "share_percent": _num(r.anteil_prozent), "places": int(r.gemeinsame_orte), "first": _fmt_date(r.erstes_treffen), "last": _fmt_date(r.letztes_treffen)} for r in df.head(10).itertuples()]
    return {"ring": ring, "own_observation_days": own_days, "companions": int(len(df)), "top": top, "dataset_id": saved.dataset_id,
            "how_to_read": "„Gemeinsam gesehen“ heißt: am selben Ort am selben Tag abgelesen. Das ist ein Hinweis auf Paar- oder Gruppenbindung, kein Beweis. Partner laut Eintrag stehen zusätzlich im Vogelprofil."}


# ---------------------------------------------------------------- what's new


async def whats_new(since: str) -> dict[str, Any]:
    sql = f"""
SELECT id, ring, reading, species, date, place, lat, lon, status, age, melder, partner, comment, ringing_place, ringing_date,
       CASE WHEN lat IS NULL OR ringing_lat IS NULL THEN NULL ELSE ROUND(({KM_FROM_RINGING})::numeric, 1) END AS km_vom_beringungsort,
       (SELECT MIN(date) FROM v_sightings v2 WHERE v2.ring = v.ring) AS erste_sichtung_des_vogels,
       (SELECT MIN(date) FROM v_sightings v3 WHERE v3.place = v.place) AS erste_sichtung_am_ort
FROM v_sightings v WHERE date >= %s::date ORDER BY date DESC"""
    desc = f"Alle Sichtungen seit {since}."
    df, saved = await _run(sql, [since], name=f"Sichtungen seit {since}", description=desc)
    if df.empty:
        return {"since": since, "sightings": 0, "summary": f"Seit {since} wurden keine Sichtungen eingetragen.", "dataset_id": saved.dataset_id}
    since_ts = pd.Timestamp(since)
    new_birds = df[df["erste_sichtung_des_vogels"] >= since_ts]["ring"].dropna().unique()
    new_places = df[df["erste_sichtung_am_ort"] >= since_ts]["place"].dropna().unique()
    far = df[pd.to_numeric(df["km_vom_beringungsort"], errors="coerce") >= 20].sort_values("km_vom_beringungsort", ascending=False)
    dead = df[df["status"] == "TF"]
    out = {
        "since": since,
        "sightings": int(len(df)),
        "individuals": int(df["ring"].nunique()),
        "observation_days": int(df["date"].nunique()),
        "species": {k: int(v) for k, v in df["species"].value_counts().head(8).items()},
        "top_places": {k: int(v) for k, v in df["place"].value_counts().head(8).items()},
        "new_birds": [str(r) for r in new_birds[:25]],
        "new_birds_count": int(len(new_birds)),
        "new_places": [str(p) for p in new_places[:15]],
        "far_recaptures": [{"ring": r.ring, "km": _num(r.km_vom_beringungsort), "place": r.place, "date": _fmt_date(r.date), "ringing_place": r.ringing_place} for r in far.head(8).itertuples()],
        "dead_finds": [{"ring": r.ring, "place": r.place, "date": _fmt_date(r.date)} for r in dead.head(8).itertuples()],
        "dataset_id": saved.dataset_id,
    }
    out["summary"] = f"Seit {since}: {out['sightings']} Sichtungen von {out['individuals']} Vögeln an {out['observation_days']} Beobachtungstagen; {out['new_birds_count']} erstmals abgelesene Vögel, {len(new_places)} neue Orte, {len(far)} Funde ≥ 20 km vom Beringungsort, {len(dead)} Totfunde."
    return out


# ---------------------------------------------------------------- data quality


CHECKS: list[dict[str, str]] = [
    {"key": "ohne_koordinaten", "label": "Sichtungen ohne Koordinaten", "why": "Diese Sichtungen fehlen auf Karten und bei Entfernungen.",
     "sql": "SELECT id, ring, date, place, species FROM v_sightings WHERE date IS NOT NULL AND (lat IS NULL OR lon IS NULL) ORDER BY date DESC LIMIT 300"},
    {"key": "ohne_ring_und_ablesung", "label": "Sichtungen ohne Ring und ohne Ablesung", "why": "Lassen sich keinem Vogel zuordnen.",
     "sql": "SELECT id, date, place, species, comment FROM v_sightings WHERE date IS NOT NULL AND ring IS NULL AND (reading IS NULL OR reading = '') ORDER BY date DESC LIMIT 300"},
    {"key": "ring_ohne_beringung", "label": "Abgelesene Ringe ohne Beringungsdatensatz", "why": "Alter, Beringungsort und Entfernung fehlen für diese Vögel.",
     "sql": "SELECT ring, MIN(date) AS erste_sichtung, COUNT(*) AS sichtungen, MAX(species) AS species FROM v_sightings WHERE ring IS NOT NULL AND date IS NOT NULL AND ringing_date IS NULL GROUP BY ring ORDER BY 3 DESC LIMIT 300"},
    {"key": "vor_beringung", "label": "Sichtungen vor dem Beringungsdatum", "why": "Vermutlich Tippfehler im Datum oder falscher Ring.",
     "sql": "SELECT id, ring, date, ringing_date, place FROM v_sightings WHERE date IS NOT NULL AND ringing_date IS NOT NULL AND date < ringing_date ORDER BY date LIMIT 300"},
    {"key": "zukunft", "label": "Sichtungen mit Datum in der Zukunft", "why": "Tippfehler im Datum.",
     "sql": "SELECT id, ring, date, place FROM v_sightings WHERE date > CURRENT_DATE ORDER BY date LIMIT 300"},
    {"key": "dubletten", "label": "Mehrfacheinträge (gleicher Ring, Tag und Ort)", "why": "Könnten doppelt erfasst sein und zählen doppelt.",
     "sql": "SELECT ring, date, place, COUNT(*) AS einträge FROM v_sightings WHERE ring IS NOT NULL AND date IS NOT NULL GROUP BY ring, date, place HAVING COUNT(*) > 1 ORDER BY 4 DESC, date DESC LIMIT 300"},
    {"key": "art_abweichend", "label": "Art bei Sichtung weicht von Art bei Beringung ab", "why": "Entweder Hybrid/Fehlbestimmung oder Ringverwechslung.",
     "sql": "SELECT ring, species, ringed_as_species, COUNT(*) AS sichtungen FROM v_sightings WHERE species IS NOT NULL AND ringed_as_species IS NOT NULL AND species <> ringed_as_species GROUP BY ring, species, ringed_as_species ORDER BY 4 DESC LIMIT 300"},
    {"key": "partner_unbekannt", "label": "Partner-Ring ohne eigenen Datensatz", "why": "Der als Partner eingetragene Ring ist sonst nirgends erfasst (Tippfehler?).",
     "sql": "SELECT partner AS partner_ring, COUNT(*) AS sichtungen, MIN(ring) AS beispiel_vogel, MAX(date) AS letzte FROM v_sightings WHERE partner IS NOT NULL AND partner <> '' AND lower(partner) NOT IN ('ub', 'unberingt', 'unb', '-') AND partner NOT IN (SELECT DISTINCT ring FROM v_sightings WHERE ring IS NOT NULL) GROUP BY partner ORDER BY 2 DESC LIMIT 300"},
    {"key": "unplausible_geschwindigkeit", "label": "Unplausible Ortswechsel (> 400 km pro Tag)", "why": "Zwei aufeinanderfolgende Sichtungen liegen zu weit auseinander – Ring- oder Koordinatenfehler.",
     "sql": f"""WITH o AS (SELECT ring, date, place, lat, lon, LAG(date) OVER w AS prev_date, LAG(place) OVER w AS prev_place, LAG(lat) OVER w AS plat, LAG(lon) OVER w AS plon
                FROM v_sightings WHERE ring IS NOT NULL AND date IS NOT NULL AND lat IS NOT NULL WINDOW w AS (PARTITION BY ring ORDER BY date))
                SELECT ring, prev_date, prev_place, date, place, ROUND(({HAV.format(a_lat='plat', a_lon='plon', b_lat='lat', b_lon='lon')})::numeric, 1) AS km, (date - prev_date) AS tage
                FROM o WHERE prev_date IS NOT NULL AND ({HAV.format(a_lat='plat', a_lon='plon', b_lat='lat', b_lon='lon')}) / GREATEST(date - prev_date, 1) > 400 ORDER BY km DESC LIMIT 300"""},
    {"key": "ortsvarianten", "label": "Orte mit mehreren Schreibweisen", "why": "Dieselbe Stelle wird sonst in Auswertungen als mehrere Orte gezählt.",
     "sql": """SELECT key AS schluessel, STRING_AGG(place || ' (' || n || ')', ' | ' ORDER BY n DESC) AS schreibweisen, COUNT(*) AS varianten
               FROM (SELECT place, COUNT(*) AS n, lower(regexp_replace(regexp_replace(place, '^(Frankfurt|F)\\s*,\\s*', 'f,', 'i'), '[^a-zäöüß0-9]', '', 'g')) AS key
                     FROM v_sightings WHERE place IS NOT NULL AND date IS NOT NULL GROUP BY place) p
               GROUP BY key HAVING COUNT(*) > 1 ORDER BY varianten DESC LIMIT 300"""},
]


async def data_quality() -> dict[str, Any]:
    results = []
    datasets = runtime.datasets()
    db = runtime.database()
    for chk in CHECKS:
        try:
            res = await db.query(chk["sql"])
            df = res.to_frame()
        except Exception as exc:
            results.append({"check": chk["key"], "label": chk["label"], "error": str(exc).strip()[:200]})
            continue
        item: dict[str, Any] = {"check": chk["key"], "label": chk["label"], "count": int(len(df)), "why_it_matters": chk["why"]}
        if len(df):
            meta = datasets.save(df, name=f"Prüfung: {chk['label']}", sql=chk["sql"], description=f"{chk['label']} – {chk['why']} (max. 300 Zeilen)", source="analysis")
            item["dataset_id"] = meta.id
            item["examples"] = [{k: (_fmt_date(v) if isinstance(v, pd.Timestamp) else (_num(v) if isinstance(v, (float, np.floating, np.integer)) else v)) for k, v in r.items()} for r in df.head(3).to_dict("records")]
            if len(df) >= 300:
                item["note"] = "mindestens 300 (Liste gekürzt)"
        results.append(item)
    totals = (await db.query("SELECT COUNT(*) FILTER (WHERE date IS NOT NULL) AS sichtungen, COUNT(DISTINCT ring) AS voegel, MIN(date) AS von, MAX(date) AS bis FROM v_sightings")).to_frame().iloc[0]
    return {
        "database": {"sightings": int(totals["sichtungen"]), "birds": int(totals["voegel"]), "from": _fmt_date(totals["von"]), "to": _fmt_date(totals["bis"])},
        "checks": results,
        "how_to_read": "Jede Prüfung zeigt Einträge, die vermutlich korrigiert werden sollten. Die Listen lassen sich als XLSX exportieren (export_dataset) und in vogelring.com über die Links nachschlagen.",
    }
