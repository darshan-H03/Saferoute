"""
Dataset ingestion & management service for SafeRoute.
Handles CSV upload, schema normalization, database persistence, and statistics.
"""
from __future__ import annotations

import csv
import io
from datetime import datetime, timezone
from typing import Any

from app.extensions import db
from app.models.hotspot import CrimeHotspot


# Column name aliases for flexible CSV ingestion
LAT_ALIASES = {"lat", "latitude", "latitude_deg", "y", "lat_coord", "point_y"}
LNG_ALIASES = {"lng", "lon", "longitude", "longitude_deg", "x", "long", "lng_coord", "point_x"}
CRIME_TYPE_ALIASES = {
    "crime_description",
    "crime_type",
    "crimedescription",
    "crimetype",
    "description",
    "incident_type",
    "offense",
    "offence",
    "type",
    "crime",
    "domain",
    "category",
}
CITY_ALIASES = {"city", "town", "district", "location", "place", "area", "neighbourhood", "neighborhood"}
INTENSITY_ALIASES = {"intensity", "severity", "risk", "weight", "crime_count", "count", "score", "level"}
LABEL_ALIASES = {"label", "name", "title", "address", "landmark"}

# Severity dictionary for standardizing crime descriptions
SEVERITY_WEIGHTS = {
    "homicide": 1.0,
    "murder": 1.0,
    "sexual assault": 0.98,
    "rape": 0.98,
    "kidnapping": 0.95,
    "assault": 0.90,
    "domestic violence": 0.88,
    "firearm": 0.92,
    "weapon": 0.92,
    "robbery": 0.85,
    "extortion": 0.82,
    "burglary": 0.78,
    "theft": 0.70,
    "illegal possession": 0.72,
    "vandalism": 0.55,
    "fraud": 0.50,
    "identity theft": 0.48,
    "harassment": 0.75,
    "eve teasing": 0.80,
    "stalking": 0.80,
    "chain snatching": 0.82,
    "traffic violation": 0.35,
    "public intoxication": 0.40,
}


def _match_column(header: list[str], aliases: set[str]) -> str | None:
    """Find matching column name regardless of casing or symbols."""
    clean_map = {col.lower().replace(" ", "").replace("_", "").replace("-", ""): col for col in header}
    for alias in aliases:
        clean_alias = alias.lower().replace(" ", "").replace("_", "").replace("-", "")
        if clean_alias in clean_map:
            return clean_map[clean_alias]
    return None


def _normalize_intensity(raw_val: Any, crime_desc: str) -> float:
    """Convert raw intensity / score / count or text to a normalized float 0.1 - 1.0."""
    if raw_val is not None and str(raw_val).strip():
        try:
            val = float(str(raw_val).strip())
            if 0.0 <= val <= 1.0:
                return max(0.1, round(val, 3))
            elif val <= 10.0:
                return max(0.1, min(1.0, round(val / 10.0, 3)))
            elif val <= 100.0:
                return max(0.1, min(1.0, round(val / 100.0, 3)))
            else:
                # Large counts or IDs
                return 0.65
        except (ValueError, TypeError):
            pass

    # Infer from crime description if no numerical intensity
    desc_lower = (crime_desc or "").lower()
    for key, weight in SEVERITY_WEIGHTS.items():
        if key in desc_lower:
            return weight

    return 0.50


def parse_and_ingest_csv(
    file_content: str | bytes,
    source_name: str = "uploaded_csv",
    replace_existing: bool = False,
    batch_size: int = 1000,
) -> dict:
    """
    Parses CSV text or bytes and saves records to CrimeHotspot table in bulk.
    Clears cache so routing and maps use updated data immediately.
    """
    if isinstance(file_content, bytes):
        try:
            text = file_content.decode("utf-8")
        except UnicodeDecodeError:
            text = file_content.decode("latin-1")
    else:
        text = file_content

    reader = csv.reader(io.StringIO(text))
    try:
        header = next(reader)
    except StopIteration:
        return {"success": False, "error": "CSV file is completely empty."}

    lat_col = _match_column(header, LAT_ALIASES)
    lng_col = _match_column(header, LNG_ALIASES)

    if not lat_col or not lng_col:
        return {
            "success": False,
            "error": (
                f"CSV must contain latitude and longitude columns. "
                f"Found columns: {', '.join(header[:8])}"
            ),
        }

    crime_col = _match_column(header, CRIME_TYPE_ALIASES)
    city_col = _match_column(header, CITY_ALIASES)
    intensity_col = _match_column(header, INTENSITY_ALIASES)
    label_col = _match_column(header, LABEL_ALIASES)

    col_idx = {name: idx for idx, name in enumerate(header)}
    lat_i = col_idx[lat_col]
    lng_i = col_idx[lng_col]
    crime_i = col_idx.get(crime_col)
    city_i = col_idx.get(city_col)
    intensity_i = col_idx.get(intensity_col)
    label_i = col_idx.get(label_col)

    if replace_existing:
        CrimeHotspot.query.delete()
        db.session.commit()

    valid_objects: list[CrimeHotspot] = []
    skipped_rows = 0
    total_parsed = 0
    cities_seen = set()

    for row_num, row in enumerate(reader, start=2):
        if not row or len(row) <= max(lat_i, lng_i):
            continue

        raw_lat = row[lat_i].strip()
        raw_lng = row[lng_i].strip()

        try:
            lat = float(raw_lat)
            lng = float(raw_lng)
        except (ValueError, TypeError):
            skipped_rows += 1
            continue

        # Check valid geo coordinate bounds
        if not (-90.0 <= lat <= 90.0 and -180.0 <= lng <= 180.0) or (lat == 0.0 and lng == 0.0):
            skipped_rows += 1
            continue

        crime_val = row[crime_i].strip() if crime_i is not None and crime_i < len(row) else "Crime / Incident"
        city_val = row[city_i].strip() if city_i is not None and city_i < len(row) else None
        raw_int = row[intensity_i].strip() if intensity_i is not None and intensity_i < len(row) else None
        label_val = row[label_i].strip() if label_i is not None and label_i < len(row) else None

        intensity = _normalize_intensity(raw_int, crime_val)

        if city_val:
            cities_seen.add(city_val)

        hotspot = CrimeHotspot(
            lat=lat,
            lng=lng,
            intensity=intensity,
            crime_type=crime_val[:100],
            label=label_val[:255] if label_val else f"{city_val or 'Area'} · {crime_val[:40]}",
            city=city_val[:100] if city_val else None,
            source=source_name[:100],
            created_at=datetime.now(timezone.utc),
        )
        valid_objects.append(hotspot)
        total_parsed += 1

        if len(valid_objects) >= batch_size:
            db.session.bulk_save_objects(valid_objects)
            db.session.commit()
            valid_objects.clear()

    if valid_objects:
        db.session.bulk_save_objects(valid_objects)
        db.session.commit()

    # Clear cached hotspots so new points appear immediately on map & route calculations
    _invalidate_crime_cache()

    total_in_db = CrimeHotspot.query.count()

    return {
        "success": True,
        "records_added": total_parsed,
        "skipped_rows": skipped_rows,
        "total_in_database": total_in_db,
        "cities": sorted(list(cities_seen))[:15],
        "message": f"Successfully ingested {total_parsed} hotspot records into database.",
    }


def get_dataset_summary() -> dict:
    """Returns overview statistics of dataset records in the connected database."""
    total = CrimeHotspot.query.count()
    if total == 0:
        return {
            "total_records": 0,
            "has_data": False,
            "cities": [],
            "top_crime_types": [],
            "sample_points": [],
        }

    # Query distinct cities and counts
    cities_query = (
        db.session.query(CrimeHotspot.city, db.func.count(CrimeHotspot.id))
        .filter(CrimeHotspot.city.isnot(None))
        .group_by(CrimeHotspot.city)
        .order_by(db.func.count(CrimeHotspot.id).desc())
        .limit(10)
        .all()
    )

    types_query = (
        db.session.query(CrimeHotspot.crime_type, db.func.count(CrimeHotspot.id))
        .filter(CrimeHotspot.crime_type.isnot(None))
        .group_by(CrimeHotspot.crime_type)
        .order_by(db.func.count(CrimeHotspot.id).desc())
        .limit(8)
        .all()
    )

    sample = (
        CrimeHotspot.query.order_by(CrimeHotspot.id.desc())
        .limit(10)
        .all()
    )

    return {
        "total_records": total,
        "has_data": True,
        "top_cities": [{"city": c[0], "count": c[1]} for c in cities_query],
        "top_crime_types": [{"type": t[0], "count": t[1]} for t in types_query],
        "sample_points": [s.to_dict() for s in sample],
    }


def seed_default_hotspots_if_empty() -> int:
    """
    Populates database with Kaggle/fallback hotspots if table is currently empty.
    Returns number of seeded records.
    """
    if CrimeHotspot.query.first() is not None:
        return 0

    from app.services.crime_data import load_crime_dataset

    data = load_crime_dataset()
    hotspots = data.get("hotspots", [])
    if not hotspots:
        return 0

    batch = []
    for h in hotspots:
        city = None
        label = h.get("label", "")
        if " · " in label:
            parts = label.split(" · ")
            if len(parts) >= 2:
                city = parts[0]

        hotspot = CrimeHotspot(
            lat=float(h["lat"]),
            lng=float(h["lng"]),
            intensity=float(h.get("intensity", 0.5)),
            crime_type=str(h.get("type", "Crime"))[:100],
            label=label[:255] if label else None,
            city=city[:100] if city else None,
            source="seed_kaggle",
            created_at=datetime.now(timezone.utc),
        )
        batch.append(hotspot)
        if len(batch) >= 1000:
            db.session.bulk_save_objects(batch)
            db.session.commit()
            batch.clear()

    if batch:
        db.session.bulk_save_objects(batch)
        db.session.commit()

    return len(hotspots)


def clear_dataset(keep_default_seed: bool = False) -> dict:
    """Deletes uploaded datasets and optionally restores default seed."""
    CrimeHotspot.query.delete()
    db.session.commit()
    _invalidate_crime_cache()

    restored = 0
    if keep_default_seed:
        restored = seed_default_hotspots_if_empty()

    return {
        "success": True,
        "total_in_database": CrimeHotspot.query.count(),
        "message": "Dataset cleared." if not restored else f"Dataset reset to {restored} default seed hotspots.",
    }


def generate_sample_csv() -> str:
    """Returns downloadable sample CSV template string."""
    rows = [
        ["latitude", "longitude", "crime_type", "city", "intensity", "label"],
        ["12.9716", "77.5946", "Robbery", "Bangalore", "0.85", "MG Road Central"],
        ["12.9352", "77.6245", "Theft", "Bangalore", "0.60", "Koramangala 5th Block"],
        ["12.9784", "77.6408", "Assault", "Bangalore", "0.90", "Indiranagar 100ft Road"],
        ["13.0020", "77.5700", "Burglary", "Bangalore", "0.75", "Malleshwaram 8th Cross"],
        ["12.8450", "77.6600", "Vandalism", "Bangalore", "0.50", "Electronic City Phase 1"],
        ["12.9141", "77.6387", "Eve Teasing", "Bangalore", "0.70", "HSR Layout Sector 1"],
        ["28.6139", "77.2090", "Harassment", "Delhi", "0.80", "Connaught Place"],
        ["19.0760", "72.8777", "Pickpocketing", "Mumbai", "0.65", "Dadar Station Area"],
    ]
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerows(rows)
    return output.getvalue()


def _invalidate_crime_cache():
    """Clear memory caches across crime_data service."""
    try:
        from app.services.crime_data import load_crime_dataset
        load_crime_dataset.cache_clear()
    except Exception:
        pass
