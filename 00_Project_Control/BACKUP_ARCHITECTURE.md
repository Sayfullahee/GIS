# Backup Architecture and Security Documentation
## N-HYPPADEC / CHER-CDSS Decision-Support System

**Version:** v1.0 | **Date:** 2026-10-02

---

## 1. Backup Tiers

Every component of the system is backed up across three independent tiers.
No tier is a substitute for the others — all three must be operational.

```
LIVE SYSTEM (working data)
        ↓  daily automated backup
LOCAL BACKUP (on-site; separate drive/device)
        ↓  weekly automated sync
OFFSITE / CLOUD BACKUP (geographically separate)
        ↓  at each major release
ARCHIVE (immutable release snapshots)
```

### Tier descriptions

| Tier | Location | Frequency | Retention | Purpose |
|---|---|---|---|---|
| Live | Working machine / institutional server | Continuous | Current only | Active production |
| Local backup | External drive or NAS on same site | Daily (automated) | 90 days rolling | Fast recovery from accidental loss |
| Offsite/cloud | Separate facility or S3-compatible cloud storage | Weekly (automated) | 12 months rolling | Recovery from site disaster |
| Archive | Cold storage / offline drive | At each versioned release | Permanent | Audit, reproducibility, legal compliance |

---

## 2. What Must Be Backed Up

Every backup must include all of the following. A backup missing any category is incomplete.

| Category | Contents | Backup Tier |
|---|---|---|
| **Database** | All DB CSV files (RAW, CLEAN, DERIVED) | All tiers |
| **GIS data** | All layers in 04_GIS/ (RAW, CLEAN, DERIVED, PROJECTS, EXPORTS, METADATA) | All tiers |
| **Scripts** | All Python scripts in 05_Analysis/02_SCRIPTS/ | All tiers |
| **Control files** | All files in 00_Project_Control/ | All tiers |
| **Reports** | All files in 06_Reports/ | All tiers |
| **Decision support outputs** | All files in 07_Decision_Support/ | All tiers |
| **Source registers** | SOURCE_REGISTER.csv, INDICATOR_REGISTER.csv, all LKP_ files | All tiers |
| **Processing logs** | All QC reports in 05_Analysis/04_QC/ | Local + offsite |
| **Archive** | All files in 09_Archive/ | Offsite + cold storage |
| **Update logs** | 08_Updates/UPDATE_LOG.csv | All tiers |
| **Metadata** | All METADATA.csv files in 04_GIS/06_METADATA/ | All tiers |
| **Risk model spec** | RISK_MODEL_SPEC.md | All tiers |

**Restricted data (DB02, G04):**
Household-level data must be backed up **separately** from non-restricted data,
with encryption applied to backups at rest and in transit.
Access to restricted backups is limited to Security Level 3 personnel.

---

## 3. Backup Schedule

| Action | Frequency | Tool / Method | Responsible |
|---|---|---|---|
| Incremental backup of all non-restricted data | Daily (automated, overnight) | rsync / robocopy to local NAS | System Administrator |
| Full backup of all non-restricted data | Weekly (Sunday) | Compressed archive to offsite/cloud | System Administrator |
| Restricted data backup (encrypted) | Weekly | Encrypted archive to separate secure location | Data Manager |
| Archive snapshot (release) | At every major version publication | Compressed archive to cold storage | Data Manager |
| Backup verification test | Monthly | Restore selected files; verify integrity | System Administrator |
| Full restoration test | Quarterly | Full restore to test environment | System Administrator + GIS Officer |
| Backup log review | Monthly | Review backup logs for failures | System Administrator |

---

## 4. Backup Verification

A backup that has never been tested is not a backup.

### Monthly verification checklist

```
[ ] Confirm daily backup completed without errors (review log)
[ ] Confirm offsite/cloud sync completed
[ ] Restore 3 randomly selected files and confirm contents intact
[ ] Confirm restricted backup encrypted and accessible only to authorised personnel
[ ] Record verification outcome in BACKUP_LOG.csv
```

### Quarterly full restoration test

```
[ ] Set up isolated test environment (do NOT restore to live system)
[ ] Restore complete backup to test environment
[ ] Verify: all DB CSV files readable
[ ] Verify: all GIS layers open correctly in QGIS
[ ] Verify: Python scripts execute without path errors
[ ] Verify: risk model produces same outputs as baseline (reproducibility test)
[ ] Verify: restricted data inaccessible without correct decryption key
[ ] Document test outcome and any issues found
[ ] Sign off: System Administrator + Data Manager
```

---

## 5. Archive Policy

| Event | Action |
|---|---|
| New baseline published (v1.0) | Full system snapshot archived to cold storage |
| Major version update (v2.0) | Previous version snapshot archived before new version published |
| Staff change (technical role) | Archive snapshot taken before transition |
| Annual review | Archive snapshot of current state |
| System decommission | All archives transferred to institutional long-term storage |

Archives are **immutable** — files in `09_Archive/` must never be modified.
A new observation or correction creates a new record; it does not alter the archive.

---

## 6. Security and Access Control

### 6.1 Access levels

| Level | Who | Data Accessible |
|---|---|---|
| Level 1 — Public | Anyone | Published reports; generalised maps; approved statistics |
| Level 2 — Project Team | All CHER-CDSS staff | Clean analytical data; detailed GIS; analysis outputs; draft reports |
| Level 3 — Restricted | Data Manager + PI only | DB02 household data; G04 household layer; confidential coordinates |
| Level 4 — Administrative | System Administrator | Server administration; database credentials; backup controls; security keys |

### 6.2 Access control rules

```
[ ] No shared passwords — each user has their own account
[ ] Restricted data (Level 3) stored in separate directory with OS-level permissions
[ ] Database credentials never stored in plain text in scripts — use environment variables
[ ] Audit log maintained for all access to Level 3 data
[ ] Staff leavers: accounts disabled within 24 hours; passwords rotated
[ ] New staff: minimum-privilege access only; escalate by role as needed
[ ] Remote access: encrypted connection (VPN or SSH) required
[ ] No household GPS coordinates in any shared or public directory
```

### 6.3 Credential management

```python
# Example: load database credentials from environment variables (NEVER hardcode)
import os

DB_HOST     = os.environ.get("CHER_DB_HOST")
DB_USER     = os.environ.get("CHER_DB_USER")
DB_PASSWORD = os.environ.get("CHER_DB_PASSWORD")
DB_NAME     = os.environ.get("CHER_DB_NAME")
```

Store credentials in a `.env` file that is:
- Listed in `.gitignore` (never committed to version control)
- Readable only by the owning user (chmod 600 on Linux)
- Backed up in encrypted form to Level 4 secure storage only

### 6.4 Version control (Git)

```
git init                          # Initialise repository in GIS/ root
echo "03_Data/RAW/" >> .gitignore  # Never commit raw field data
echo ".env" >> .gitignore          # Never commit credentials
echo "*.gpkg" >> .gitignore        # Large GIS files — use Git LFS or exclude
git add 05_Analysis/02_SCRIPTS/    # Track all Python scripts
git add 00_Project_Control/        # Track all control files
git commit -m "Phase 10 complete — baseline v1.0"
```

Every change to scripts or control files should be committed with a meaningful message.
Commit messages must include the update cycle or version being applied.

---

## 7. Disaster Recovery

### 7.1 Recovery time objectives

| Scenario | Target Recovery Time | Recovery Source |
|---|---|---|
| Accidental file deletion | < 1 hour | Local backup (daily) |
| Workstation failure | < 4 hours | Local backup + scripts re-installed |
| Site disaster (fire/flood) | < 24 hours | Offsite/cloud backup |
| Complete system loss | < 72 hours | Archive + offsite backup |
| Corruption of CLEAN data | Immediately on detection | Archive of last validated version |

### 7.2 Recovery procedure

1. Identify scope of loss (which files/layers/databases affected)
2. Halt pipeline — do not run any processing on potentially corrupted data
3. Restore from most recent verified backup to isolated test environment
4. Verify restored data integrity (checksums; record counts; QC re-run)
5. Notify CHER-CDSS Coordinator and Data Manager
6. Once verified, restore to live system
7. Document incident and recovery in `00_Project_Control/INCIDENT_LOG.csv`
8. Investigate root cause and implement preventive measures

---

## 8. BACKUP_LOG.csv Template

Location: `00_Project_Control/BACKUP_LOG.csv`

```
Backup_Date, Backup_Type, Tier, Size_GB, Duration_min,
Restricted_Data_Included, Encrypted, Verified, Verification_Method,
Verified_By, Issues, Notes
```
