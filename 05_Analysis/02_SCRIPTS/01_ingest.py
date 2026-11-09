"""
01_ingest.py
============
Source registration and raw data ingestion.

Responsibilities:
  - Register external datasets in SOURCE_REGISTER.csv
  - Copy/link raw files into 03_Data/RAW/ or 04_GIS/01_RAW/
  - Record acquisition date and version
  - Set QC_Status = INGESTED in PROCESSING_STATUS.csv
  - Write VERSION_LOG entry

Does NOT modify source data — raw files are never altered.
"""

import shutil
import json
from datetime import date
from pathlib import Path
from typing import Optional

import pandas as pd

from config import (
    PROJECT_ROOT, DATA_RAW, GIS_RAW,
    SOURCE_REGISTER, PROCESSING_STATUS,
    QCStatus, BASELINE_VERSION,
)
from logger import get_logger, log_separator
from qc_utils import update_processing_status, append_version_log

log = get_logger("01_ingest")


# ---------------------------------------------------------------------------
# Source registration
# ---------------------------------------------------------------------------

def register_source(
    source_id: str,
    dataset_name: str,
    provider: str,
    url_reference: str,
    version: str,
    acquisition_date: str,
    coverage: str,
    crs: str,
    resolution: str,
    license_: str,
    processing_applied: str,
    gis_layer: str,
    db_table: str,
    notes: str = "",
) -> bool:
    """
    Add or update a source entry in SOURCE_REGISTER.csv.
    Returns True if newly added, False if already present (no overwrite).
    """
    df = pd.read_csv(SOURCE_REGISTER)
    if source_id in df["Source_ID"].values:
        log.info(f"Source already registered: {source_id} — skipping")
        return False

    new_row = {
        "Source_ID":          source_id,
        "Dataset_Name":       dataset_name,
        "Provider":           provider,
        "URL_Reference":      url_reference,
        "Version":            version,
        "Acquisition_Date":   acquisition_date,
        "Coverage":           coverage,
        "CRS":                crs,
        "Resolution":         resolution,
        "License":            license_,
        "Processing_Applied": processing_applied,
        "GIS_Layer":          gis_layer,
        "DB_Table":           db_table,
        "Notes":              notes,
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(SOURCE_REGISTER, index=False)
    log.info(f"Source registered: {source_id} — {dataset_name}")
    return True


# ---------------------------------------------------------------------------
# Raw file ingestion
# ---------------------------------------------------------------------------

def ingest_file(
    source_path: Path,
    destination_dir: Path,
    asset_id: str,
    overwrite: bool = False,
) -> Optional[Path]:
    """
    Copy a raw source file into the project RAW directory.
    Source files are never modified — only copied.

    Parameters
    ----------
    source_path : Path
        Absolute path to the external source file.
    destination_dir : Path
        Target directory (DATA_RAW or GIS_RAW subfolder).
    asset_id : str
        Asset ID for PROCESSING_STATUS update (e.g. 'G01').
    overwrite : bool
        If False (default), skip if destination file already exists.

    Returns
    -------
    Path of the copied file, or None if skipped.
    """
    if not source_path.exists():
        log.error(f"Source file not found: {source_path}")
        return None

    destination_dir.mkdir(parents=True, exist_ok=True)
    dest_path = destination_dir / source_path.name

    if dest_path.exists() and not overwrite:
        log.info(f"Already ingested (skipping): {dest_path.name}")
        return dest_path

    shutil.copy2(source_path, dest_path)
    log.info(f"Ingested: {source_path.name} → {dest_path}")

    update_processing_status(
        asset_id=asset_id,
        new_status=QCStatus.INGESTED,
        notes=f"Raw file ingested from {source_path}",
    )
    append_version_log(
        version=BASELINE_VERSION,
        asset_id=asset_id,
        asset_type="Raw file",
        change_type="INGEST",
        description=f"Raw file ingested: {source_path.name}",
    )
    return dest_path


# ---------------------------------------------------------------------------
# CSV data ingestion (field databases)
# ---------------------------------------------------------------------------

def ingest_csv(
    source_path: Path,
    asset_id: str,
    encoding: str = "utf-8",
) -> Optional[pd.DataFrame]:
    """
    Load a raw CSV field database file, add Record_Created if absent,
    set QC_Status = RAW, and save to DATA_RAW.

    Returns the loaded DataFrame or None on failure.
    """
    if not source_path.exists():
        log.error(f"CSV not found: {source_path}")
        return None

    try:
        df = pd.read_csv(source_path, encoding=encoding)
    except Exception as exc:
        log.error(f"Failed to read {source_path}: {exc}")
        return None

    today = date.today().isoformat()

    # Add system fields if absent
    if "Record_Created" not in df.columns:
        df["Record_Created"] = today
    if "QC_Status" not in df.columns:
        df["QC_Status"] = QCStatus.RAW
    if "Data_Version" not in df.columns:
        df["Data_Version"] = BASELINE_VERSION

    dest_path = DATA_RAW / source_path.name
    df.to_csv(dest_path, index=False, encoding="utf-8")
    log.info(f"CSV ingested: {source_path.name} → {dest_path} ({len(df)} records)")

    update_processing_status(asset_id=asset_id, new_status=QCStatus.INGESTED)
    return df


# ---------------------------------------------------------------------------
# Batch ingestion from a manifest
# ---------------------------------------------------------------------------

def ingest_from_manifest(manifest_path: Path) -> dict:
    """
    Ingest multiple files from a manifest CSV with columns:
    source_path, destination_dir, asset_id, file_type

    Returns summary dict {asset_id: status}.
    """
    if not manifest_path.exists():
        log.error(f"Manifest not found: {manifest_path}")
        return {}

    manifest = pd.read_csv(manifest_path)
    results = {}

    for _, row in manifest.iterrows():
        src  = Path(row["source_path"])
        dest = Path(row["destination_dir"])
        aid  = row["asset_id"]
        ftype = row.get("file_type", "file")

        if ftype == "csv":
            result = ingest_csv(src, aid)
        else:
            result = ingest_file(src, dest, aid)

        results[aid] = "OK" if result is not None else "FAILED"
        log.info(f"  {aid}: {results[aid]}")

    return results


# ---------------------------------------------------------------------------
# KoboToolbox / ODK API Ingestion (Section 5.3 Institutional Upgrade Notes)
# ---------------------------------------------------------------------------

def ingest_from_kobo(form_id: Optional[str] = None, kobo_token: Optional[str] = None, local_cache_path: Optional[Path] = None, server_url: Optional[str] = None) -> pd.DataFrame:
    """
    Pull field survey submissions from KoboToolbox / ODK Central REST API.
    Saves immutable raw JSON payload to 03_Data/RAW/kobo_submissions/ and returns DataFrame.
    If form_id or kobo_token is not provided, attempts to load from environment (.env).
    If offline or in test mode, loads from local_cache_path if provided.
    """
    import os
    try:
        from dotenv import load_dotenv
        load_dotenv(PROJECT_ROOT / ".env")
    except ImportError:
        pass

    form_id = form_id or os.getenv("KOBO_FORM_ID")
    kobo_token = kobo_token or os.getenv("KOBO_API_TOKEN")
    base_url = (server_url or os.getenv("KOBO_SERVER_URL") or "https://kf.kobotoolbox.org").rstrip("/")

    kobo_raw_dir = DATA_RAW / "kobo_submissions"
    kobo_raw_dir.mkdir(parents=True, exist_ok=True)

    if form_id and kobo_token and not kobo_token.startswith("your_") and not form_id.startswith("your_"):
        try:
            import urllib.request
            url = f"{base_url}/api/v2/assets/{form_id}/data.json"
            req = urllib.request.Request(url, headers={"Authorization": f"Token {kobo_token}"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                submissions = data.get("results", [])
                df = pd.json_normalize(submissions)
                # Save immutable raw payload
                today_str = date.today().isoformat()
                raw_out = kobo_raw_dir / f"kobo_{form_id}_{today_str}.json"
                with open(raw_out, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
                log.info(f"Kobo API: {len(df)} submissions ingested from form {form_id} -> {raw_out}")
                return df
        except Exception as exc:
            log.warning(f"Kobo API ingestion network error ({exc}); checking local cache")

    if local_cache_path and Path(local_cache_path).exists():
        if str(local_cache_path).endswith(".json"):
            with open(local_cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            df = pd.json_normalize(data.get("results", data))
        else:
            df = pd.read_csv(local_cache_path)
        log.info(f"Loaded {len(df)} submissions from local Kobo cache: {local_cache_path}")
        return df

    log.info(f"Kobo form {form_id or 'NOT_SET'}: no active credentials or cache; returning empty frame")
    return pd.DataFrame()


# ---------------------------------------------------------------------------
# Run all
# ---------------------------------------------------------------------------

def run_all() -> None:
    """Run ingestion checks, registering required sources and verifying RAW assets."""
    log_separator(log, "01_INGEST — Source Registration and Raw Data Ingestion")
    DATA_RAW.mkdir(parents=True, exist_ok=True)
    GIS_RAW.mkdir(parents=True, exist_ok=True)

    default_sources = [
        ("SRC_SRTM", "SRTM 30m Digital Elevation Model", "NASA / USGS", "https://earthexplorer.usgs.gov", "v1.0", "2026-01-15", "Study Area", "EPSG:4326", "30m", "Open Access", "Reprojected to EPSG:32632", "G08", "None", "Baseline terrain data"),
        ("SRC_NIMET", "NiMet Daily Climate Observations", "NiMet", "https://nimet.gov.ng", "v1.0", "2026-02-01", "10 States", "EPSG:4326", "Point stations", "Official Agreement", "QC flagged Q15", "G21", "DB05", "Observed meteorological records"),
        ("SRC_FIELD_2026", "N-HYPPADEC Baseline Field Survey 2026", "N-HYPPADEC / Consultants", "Internal Server", "v1.0", "2026-06-01", "10 States", "EPSG:4326", "GPS Waypoints", "Institutional Proprietary", "Consent gated Q19", "G03,G19,G26", "DB01,DB02,DB03,DB06", "Primary field observations"),
        ("SRC_HYDRO_2026", "Federal Ministry of Water Resources / Hydropower Operators", "FMWR / Operators", "Internal Registry", "v1.0", "2026-03-10", "Dams & Reservoirs", "EPSG:4326", "Point facilities", "Official Data Request", "Operating status verification", "G07,G28", "DB04", "Hydropower and dam monitoring"),
    ]
    for src in default_sources:
        register_source(
            source_id=src[0], dataset_name=src[1], provider=src[2],
            url_reference=src[3], version=src[4], acquisition_date=src[5],
            coverage=src[6], crs=src[7], resolution=src[8], license_=src[9],
            processing_applied=src[10], gis_layer=src[11], db_table=src[12], notes=src[13]
        )

    for db_id in ["DB01", "DB02", "DB03", "DB04", "DB05", "DB06"]:
        matching = list(DATA_RAW.glob(f"{db_id}_*.csv"))
        if matching:
            update_processing_status(db_id, QCStatus.INGESTED, notes=f"Raw asset available: {matching[0].name}")
            log.info(f"Asset {db_id} verified in RAW: {matching[0].name}")

    log.info("01_ingest complete")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    run_all()
