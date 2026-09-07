"""
CrimeHotspot model – stores geo-located crime/safety incident points in the database.
Supports uploaded CSV datasets and initial seed data.
"""
from datetime import datetime, timezone
from app.extensions import db


class CrimeHotspot(db.Model):
    __tablename__ = "crime_hotspots"

    id = db.Column(db.Integer, primary_key=True)
    lat = db.Column(db.Float, nullable=False, index=True)
    lng = db.Column(db.Float, nullable=False, index=True)
    intensity = db.Column(db.Float, nullable=False, default=0.5)
    crime_type = db.Column(db.String(100), nullable=True)
    label = db.Column(db.String(255), nullable=True)
    city = db.Column(db.String(100), nullable=True, index=True)
    source = db.Column(db.String(100), nullable=False, default="uploaded_csv")
    created_at = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "lat": round(self.lat, 6),
            "lng": round(self.lng, 6),
            "intensity": round(self.intensity, 3),
            "type": self.crime_type or "general",
            "label": self.label or f"{self.city or 'Area'} · {self.crime_type or 'Point'}",
            "city": self.city,
            "source": self.source,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
