"""
Dataset management and CSV upload endpoints.
"""
from flask import Blueprint, jsonify, request, Response
from app.firebase_auth import firebase_auth_required

from app.services.dataset_service import (
    parse_and_ingest_csv,
    get_dataset_summary,
    seed_default_hotspots_if_empty,
    clear_dataset,
    generate_sample_csv,
)

dataset_bp = Blueprint("dataset", __name__)


@dataset_bp.post("/upload")
@firebase_auth_required
def upload_dataset():
    """
    Upload CSV dataset containing crime or safety hotspots.
    Form data:
      file: Multipart CSV file
      replace: Optional 'true'/'false' to replace existing records or append
    """
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded. Please provide a CSV file."}), 400

    uploaded_file = request.files["file"]
    if not uploaded_file.filename:
        return jsonify({"error": "No file selected."}), 400

    if not uploaded_file.filename.lower().endswith((".csv", ".txt")):
        return jsonify({"error": "Only CSV (.csv) files are supported for dataset ingestion."}), 400

    replace = request.form.get("replace", "false").lower() in ("true", "1", "yes")

    try:
        content = uploaded_file.read()
        res = parse_and_ingest_csv(
            content,
            source_name=uploaded_file.filename,
            replace_existing=replace,
        )
        if not res.get("success"):
            return jsonify(res), 400
        return jsonify(res), 200
    except Exception as exc:
        return jsonify({"error": f"Failed to parse and store dataset: {str(exc)}"}), 500


@dataset_bp.get("/summary")
@firebase_auth_required
def dataset_summary():
    """Return overview statistics and top hotspots in the connected database."""
    summary = get_dataset_summary()
    return jsonify(summary), 200


@dataset_bp.post("/seed")
@firebase_auth_required
def seed_dataset():
    """Seed database with default Kaggle/fallback hotspots if table is empty."""
    seeded_count = seed_default_hotspots_if_empty()
    summary = get_dataset_summary()
    return jsonify({
        "success": True,
        "seeded_count": seeded_count,
        "total_records": summary["total_records"],
        "message": f"Seeded {seeded_count} default hotspots." if seeded_count else "Database already contains hotspots.",
    }), 200


@dataset_bp.get("/sample-template")
def download_sample_template():
    """Download a ready-to-use CSV template for crime/safety data."""
    csv_data = generate_sample_csv()
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=saferoute_sample_dataset.csv"},
    )


@dataset_bp.delete("/clear")
@firebase_auth_required
def clear_records():
    """Clear all records from CrimeHotspot table."""
    keep_seed = request.args.get("restore_seed", "false").lower() in ("true", "1", "yes")
    result = clear_dataset(keep_default_seed=keep_seed)
    return jsonify(result), 200
