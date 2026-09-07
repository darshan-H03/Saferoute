"""
Dataset upload, ingestion & database persistence tests.
Run: python -m tests.test_dataset_upload
"""
import io
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from app.extensions import db
from app.models.hotspot import CrimeHotspot


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def run():
    app = create_app(
        config_overrides={
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "TESTING": True,
            "DEMO_MODE": True,
        }
    )

    with app.app_context():
        client = app.test_client()

        # Register user for auth token
        r = client.post(
            "/api/auth/register",
            json={"name": "Data Admin", "email": "admin@example.com", "password": "password123"},
        )
        assert r.status_code == 201, r.data
        token = r.get_json()["access_token"]
        auth = auth_header(token)

        # 1. Download sample CSV template
        r = client.get("/api/dataset/sample-template")
        assert r.status_code == 200
        assert "latitude" in r.data.decode("utf-8")
        assert "longitude" in r.data.decode("utf-8")

        # 2. Empty dataset summary
        r = client.get("/api/dataset/summary", headers=auth)
        assert r.status_code == 200
        data = r.get_json()
        assert data["total_records"] == 0

        # 3. Validation: Upload without file
        r = client.post("/api/dataset/upload", headers=auth)
        assert r.status_code == 400

        # 4. Upload valid CSV with custom column aliases
        csv_content = (
            "lat,lon,crime_description,city,intensity\n"
            "12.9716,77.5946,Robbery,Bangalore,0.85\n"
            "12.9352,77.6245,Pickpocketing,Bangalore,0.60\n"
            "28.6139,77.2090,Vehicle Theft,Delhi,0.70\n"
            "19.0760,72.8777,Harassment,Mumbai,0.75\n"
            "invalid,invalid,Bad Row,Skip,1.0\n"  # should be safely skipped
        ).encode("utf-8")

        r = client.post(
            "/api/dataset/upload",
            headers=auth,
            data={"file": (io.BytesIO(csv_content), "test_crimes.csv")},
            content_type="multipart/form-data",
        )
        assert r.status_code == 200, r.data
        res = r.get_json()
        assert res["success"] is True
        assert res["records_added"] == 4
        assert res["skipped_rows"] == 1
        assert res["total_in_database"] == 4

        # 5. Verify persistence in CrimeHotspot database table
        assert CrimeHotspot.query.count() == 4
        blr = CrimeHotspot.query.filter_by(city="Bangalore").all()
        assert len(blr) == 2

        # 6. Verify summary reflects uploaded points
        r = client.get("/api/dataset/summary", headers=auth)
        assert r.status_code == 200
        summary = r.get_json()
        assert summary["total_records"] == 4
        assert len(summary["sample_points"]) == 4

        # 7. Verify maps crime-hotspots API serves database records
        r = client.get("/api/maps/crime-hotspots", headers=auth)
        assert r.status_code == 200
        map_data = r.get_json()
        assert len(map_data["hotspots"]) == 4
        assert map_data["meta"]["source"] == "database"

        # 8. Clear dataset
        r = client.delete("/api/dataset/clear", headers=auth)
        assert r.status_code == 200
        assert CrimeHotspot.query.count() == 0

        # 9. Seed default hotspots
        r = client.post("/api/dataset/seed", headers=auth)
        assert r.status_code == 200
        seed_res = r.get_json()
        assert seed_res["total_records"] > 0
        assert CrimeHotspot.query.count() == seed_res["total_records"]

        print("All Dataset Upload & Database Ingestion tests passed cleanly.")


if __name__ == "__main__":
    run()
