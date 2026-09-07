import { useEffect, useState, useRef } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { datasetApi } from "../api/client";

export default function DatasetUpload() {
  const { token } = useAuth();
  const fileInputRef = useRef(null);

  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [clearing, setClearing] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [replaceExisting, setReplaceExisting] = useState(false);
  const [message, setMessage] = useState(null);
  const [error, setError] = useState(null);

  const loadSummary = async () => {
    try {
      setLoading(true);
      const res = await datasetApi.summary(token);
      setSummary(res);
    } catch (err) {
      setError(err.message || "Failed to load dataset status from database.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSummary();
  }, [token]);

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setMessage(null);
      setError(null);
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!selectedFile) {
      setError("Please choose a CSV file to upload.");
      return;
    }

    try {
      setUploading(true);
      setMessage(null);
      setError(null);

      const formData = new FormData();
      formData.append("file", selectedFile);
      formData.append("replace", replaceExisting ? "true" : "false");

      const res = await datasetApi.upload(token, formData);
      setMessage(
        `Success! Ingested ${res.records_added} hotspots into database. (Total in DB: ${res.total_in_database})`
      );
      setSelectedFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
      await loadSummary();
    } catch (err) {
      setError(err.message || "Failed to upload and parse dataset.");
    } finally {
      setUploading(false);
    }
  };

  const handleSeedDefault = async () => {
    try {
      setLoading(true);
      setMessage(null);
      setError(null);
      const res = await datasetApi.seed(token);
      setMessage(res.message);
      await loadSummary();
    } catch (err) {
      setError(err.message || "Failed to seed default hotspots.");
    } finally {
      setLoading(false);
    }
  };

  const handleClear = async () => {
    if (!window.confirm("Are you sure you want to delete all crime hotspots from the database?")) {
      return;
    }
    try {
      setClearing(true);
      setMessage(null);
      setError(null);
      const res = await datasetApi.clear(token, false);
      setMessage(res.message);
      await loadSummary();
    } catch (err) {
      setError(err.message || "Failed to clear dataset.");
    } finally {
      setClearing(false);
    }
  };

  return (
    <div className="container" style={{ maxWidth: 1040, margin: "0 auto", padding: "1.5rem" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "1.5rem", flexWrap: "wrap", gap: "1rem" }}>
        <div>
          <h1 style={{ margin: "0 0 0.5rem 0", fontSize: "1.8rem" }}>Database Dataset Management</h1>
          <p style={{ margin: 0, color: "var(--muted)", maxWidth: 650 }}>
            Upload CSV datasets with crime, incident, or safety points. Records are saved directly into your connected database and immediately drive SafeRoute&apos;s heatmaps and safe route navigation scoring.
          </p>
        </div>
        <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
          <a
            href={datasetApi.templateUrl()}
            download="saferoute_sample_dataset.csv"
            className="btn btn-outline"
            style={{ padding: "0.5rem 1rem", fontSize: "0.9rem", textDecoration: "none" }}
          >
            📥 Download Sample CSV
          </a>
          <Link
            to="/journey"
            className="btn btn-primary"
            style={{ padding: "0.5rem 1rem", fontSize: "0.9rem" }}
          >
            🗺️ View on Map
          </Link>
        </div>
      </div>

      {message && (
        <div style={{ padding: "1rem", borderRadius: 8, background: "rgba(34, 197, 94, 0.15)", border: "1px solid #22c55e", color: "#86efac", marginBottom: "1.5rem" }}>
          ✓ {message}
        </div>
      )}

      {error && (
        <div style={{ padding: "1rem", borderRadius: 8, background: "rgba(239, 68, 68, 0.15)", border: "1px solid #ef4444", color: "#fca5a5", marginBottom: "1.5rem" }}>
          ✕ {error}
        </div>
      )}

      {/* Database Statistics Cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "1rem", marginBottom: "1.5rem" }}>
        <div className="card" style={{ padding: "1.25rem", background: "var(--bg-panel)", border: "1px solid var(--border)", borderRadius: "var(--radius)" }}>
          <div style={{ color: "var(--muted)", fontSize: "0.85rem", textTransform: "uppercase", letterSpacing: "0.05em" }}>Total Database Records</div>
          <div style={{ fontSize: "2rem", fontWeight: 700, marginTop: "0.25rem", color: "var(--accent)" }}>
            {loading ? "..." : summary?.total_records?.toLocaleString() || 0}
          </div>
          <div style={{ fontSize: "0.8rem", color: "var(--muted)", marginTop: "0.25rem" }}>
            Active geo-located hotspots
          </div>
        </div>

        <div className="card" style={{ padding: "1.25rem", background: "var(--bg-panel)", border: "1px solid var(--border)", borderRadius: "var(--radius)" }}>
          <div style={{ color: "var(--muted)", fontSize: "0.85rem", textTransform: "uppercase", letterSpacing: "0.05em" }}>Top Cities Covered</div>
          <div style={{ fontSize: "1.1rem", fontWeight: 600, marginTop: "0.5rem", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
            {summary?.top_cities?.length ? summary.top_cities.slice(0, 3).map((c) => c.city).join(", ") : "None loaded"}
          </div>
          <div style={{ fontSize: "0.8rem", color: "var(--muted)", marginTop: "0.25rem" }}>
            {summary?.top_cities?.length || 0} distinct cities in DB
          </div>
        </div>

        <div className="card" style={{ padding: "1.25rem", background: "var(--bg-panel)", border: "1px solid var(--border)", borderRadius: "var(--radius)" }}>
          <div style={{ color: "var(--muted)", fontSize: "0.85rem", textTransform: "uppercase", letterSpacing: "0.05em" }}>Incident Categories</div>
          <div style={{ fontSize: "1.1rem", fontWeight: 600, marginTop: "0.5rem", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
            {summary?.top_crime_types?.length ? summary.top_crime_types.slice(0, 3).map((t) => t.type).join(", ") : "Standard types"}
          </div>
          <div style={{ fontSize: "0.8rem", color: "var(--muted)", marginTop: "0.25rem" }}>
            Mapped with weighted severity
          </div>
        </div>
      </div>

      {/* Upload Box */}
      <div className="card" style={{ padding: "1.75rem", background: "var(--bg-panel)", border: "1px solid var(--border)", borderRadius: "var(--radius)", marginBottom: "1.5rem" }}>
        <h2 style={{ fontSize: "1.25rem", margin: "0 0 0.5rem 0" }}>Upload New CSV Dataset</h2>
        <p style={{ color: "var(--muted)", fontSize: "0.9rem", margin: "0 0 1.25rem 0" }}>
          Upload files formatted with columns such as <code>latitude</code>, <code>longitude</code>, <code>crime_type</code>, <code>city</code>, and optional <code>intensity</code> (0.1 to 1.0).
        </p>

        <form onSubmit={handleUpload}>
          <div style={{
            border: "2px dashed var(--border)",
            borderRadius: "var(--radius)",
            padding: "2rem",
            textAlign: "center",
            background: "rgba(0, 0, 0, 0.15)",
            marginBottom: "1.25rem",
            cursor: "pointer",
          }}
          onClick={() => fileInputRef.current?.click()}
          >
            <input
              type="file"
              ref={fileInputRef}
              accept=".csv,text/csv"
              onChange={handleFileChange}
              style={{ display: "none" }}
            />
            <div style={{ fontSize: "2.5rem", marginBottom: "0.5rem" }}>📄</div>
            <div style={{ fontWeight: 600, marginBottom: "0.25rem" }}>
              {selectedFile ? selectedFile.name : "Click to select a CSV dataset file"}
            </div>
            <div style={{ fontSize: "0.85rem", color: "var(--muted)" }}>
              {selectedFile ? `${(selectedFile.size / 1024).toFixed(1)} KB` : "Supports standard CSV with lat / lng coordinates"}
            </div>
          </div>

          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "1rem" }}>
            <label style={{ display: "flex", alignItems: "center", gap: "0.5rem", fontSize: "0.9rem", cursor: "pointer" }}>
              <input
                type="checkbox"
                checked={replaceExisting}
                onChange={(e) => setReplaceExisting(e.target.checked)}
              />
              Replace existing records in database (unchecked = append)
            </label>

            <div style={{ display: "flex", gap: "0.75rem" }}>
              {summary?.total_records === 0 && (
                <button
                  type="button"
                  className="btn btn-outline"
                  onClick={handleSeedDefault}
                  disabled={loading}
                >
                  ⚡ Load Default Kaggle Seed
                </button>
              )}
              <button
                type="submit"
                className="btn btn-primary"
                disabled={!selectedFile || uploading}
                style={{ minWidth: 140 }}
              >
                {uploading ? "Ingesting..." : "Upload & Save to DB"}
              </button>
            </div>
          </div>
        </form>
      </div>

      {/* Database Sample Records */}
      {summary?.sample_points?.length > 0 && (
        <div className="card" style={{ padding: "1.5rem", background: "var(--bg-panel)", border: "1px solid var(--border)", borderRadius: "var(--radius)" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
            <h3 style={{ margin: 0, fontSize: "1.1rem" }}>Latest Database Records Preview</h3>
            <button
              type="button"
              className="btn btn-outline"
              style={{ color: "var(--danger)", borderColor: "rgba(239, 68, 68, 0.4)", fontSize: "0.85rem", padding: "0.4rem 0.8rem" }}
              onClick={handleClear}
              disabled={clearing}
            >
              {clearing ? "Clearing..." : "🗑️ Clear Dataset"}
            </button>
          </div>

          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.85rem", textAlign: "left" }}>
              <thead>
                <tr style={{ borderBottom: "1px solid var(--border)", color: "var(--muted)" }}>
                  <th style={{ padding: "0.6rem 0.5rem" }}>ID</th>
                  <th style={{ padding: "0.6rem 0.5rem" }}>Coordinates</th>
                  <th style={{ padding: "0.6rem 0.5rem" }}>Incident Type</th>
                  <th style={{ padding: "0.6rem 0.5rem" }}>City / Label</th>
                  <th style={{ padding: "0.6rem 0.5rem" }}>Severity</th>
                  <th style={{ padding: "0.6rem 0.5rem" }}>Source</th>
                </tr>
              </thead>
              <tbody>
                {summary.sample_points.map((pt) => (
                  <tr key={pt.id} style={{ borderBottom: "1px solid rgba(240, 246, 252, 0.06)" }}>
                    <td style={{ padding: "0.6rem 0.5rem", color: "var(--muted)" }}>#{pt.id}</td>
                    <td style={{ padding: "0.6rem 0.5rem", fontFamily: "monospace" }}>{pt.lat}, {pt.lng}</td>
                    <td style={{ padding: "0.6rem 0.5rem" }}>{pt.type}</td>
                    <td style={{ padding: "0.6rem 0.5rem" }}>{pt.label}</td>
                    <td style={{ padding: "0.6rem 0.5rem" }}>
                      <span style={{
                        padding: "0.15rem 0.5rem",
                        borderRadius: 4,
                        fontSize: "0.75rem",
                        fontWeight: 600,
                        background: pt.intensity >= 0.8 ? "rgba(239, 68, 68, 0.2)" : pt.intensity >= 0.5 ? "rgba(234, 179, 8, 0.2)" : "rgba(34, 197, 94, 0.2)",
                        color: pt.intensity >= 0.8 ? "#fca5a5" : pt.intensity >= 0.5 ? "#fde047" : "#86efac",
                      }}>
                        {(pt.intensity * 100).toFixed(0)}%
                      </span>
                    </td>
                    <td style={{ padding: "0.6rem 0.5rem", color: "var(--muted)" }}>{pt.source}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
