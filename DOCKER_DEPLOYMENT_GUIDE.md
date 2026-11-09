# CHER-CDSS Docker Deployment & Operations Guide
## Enterprise Containerized Architecture v4.1
### PostgreSQL 16/PostGIS 3.4 + GeoServer + MinIO + FastAPI | October 2026

---

## 1. Architecture Overview

The containerized stack implements the **Section 3 Master Architecture** of the CHER-CDSS Master Scaffold v4.1:

| Container Service | Base Image | Role & Mounts | Ports |
|---|---|---|---|
| `cher_cdss_postgis` | `postgis/postgis:16-3.4` | Central spatial database for all 22 core tables. Initializes schemas via [`03_Data/POSTGRESQL_DDL_v4.1.sql`](file:///c:/xampp/htdocs/GIS/03_Data/POSTGRESQL_DDL_v4.1.sql). | `5432` |
| `cher_cdss_geoserver`| `kartoza/geoserver:2.24.2` | Web Map Services (WMS/WFS) for the 37 GIS layers. Pre-configured for PostGIS connection. | `8080` |
| `cher_cdss_minio` | `minio/minio:latest` | S3-compatible raw immutable file storage for field photos, satellite scenes, and database backups. | `9000` (API), `9001` (UI) |
| `cher_cdss_api` | Custom (`Dockerfile`) | FastAPI REST API engine, analytical risk models, and Leaflet Web GIS dashboard. | `8000` |

---

## 2. Quickstart Deployment

### Prerequisites
- Docker Engine v24.0+ and Docker Compose v2.20+
- At least 4GB of free RAM and 20GB of disk space

### Step 1: Clone and Configure Environment
```bash
cp .env.example .env
# Edit .env with secure production passwords
```

### Step 2: Build and Start Containers
```bash
docker compose up -d --build
```

### Step 3: Verify Container Health
```bash
docker compose ps
```
All four services (`cher_cdss_postgis`, `cher_cdss_geoserver`, `cher_cdss_minio`, `cher_cdss_api`) should report status `Up` or `healthy`.

---

## 3. Service Access Endpoints

- **Executive Web GIS Dashboard:** [http://localhost:8000/](http://localhost:8000/)
- **Interactive OpenAPI Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **API Health Check:** [http://localhost:8000/api/health](http://localhost:8000/api/health)
- **GeoServer Web Admin:** [http://localhost:8080/geoserver/web/](http://localhost:8080/geoserver/web/) (User: `admin`, Pass: from `.env`)
- **MinIO Storage Console:** [http://localhost:9001/](http://localhost:9001/) (User: `nhyppadec_minio_admin`, Pass: from `.env`)
- **PostgreSQL Connection:** `localhost:5432`, DB: `cher_cdss`, User: `nhyppadec_admin`

---

## 4. Database Automated Initialization Verification

On first container startup, `03_Data/POSTGRESQL_DDL_v4.1.sql` is executed by PostgreSQL. Verify schema deployment:

```bash
docker exec -it cher_cdss_postgis psql -U nhyppadec_admin -d cher_cdss -c "\dn"
```
**Expected schemas:** `raw`, `clean`, `derived`, `lookups`, `audit`.

Verify tables:
```bash
docker exec -it cher_cdss_postgis psql -U nhyppadec_admin -d cher_cdss -c "SELECT count(*) FROM information_schema.tables WHERE table_schema IN ('clean', 'derived', 'lookups');"
```

---

## 5. Automated Backup Procedure (Stage 26)

To execute an on-demand database backup into the backup directory:
```bash
docker exec -t cher_cdss_postgis pg_dump -U nhyppadec_admin -F c cher_cdss > backup_cher_cdss_$(date +%Y%m%d).dump
```

To test restore verification (mandatory before production sign-off):
```bash
docker exec -i cher_cdss_postgis pg_restore -U nhyppadec_admin -d cher_cdss_test < backup_cher_cdss_20261007.dump
```
