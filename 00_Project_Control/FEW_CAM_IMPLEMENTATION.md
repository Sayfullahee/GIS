# FEW-CAM Flood Early Warning, Alarm & Community Awareness

**Module:** FEW-CAM | **Version:** 1.0 | **Status:** Implementation scaffold

## Scope and safety

FEW-CAM joins monitoring evidence, spatial exposure, graduated warnings,
notifications, community preparedness, event verification, impact assessment,
and warning-performance learning. CHER-CDSS is decision support, not an
independent public authority. A released warning is official only after the
applicable government/emergency-management authorisation. Example thresholds
are deliberately not active: the responsible authority must approve and
version every operational threshold and message before a pilot.

Do not publish household identifiers, individual contact information,
operational security details, or unapproved evacuation/tactical information.
The dashboard API is read-only and exposes aggregated notification/awareness
metrics and released-alert map products only when those files are supplied.
The PostGIS roles below control writes and visibility; assign real login users
to these NOLOGIN groups through the database administrator, not application
request parameters.

## Operational cycle and stage ownership

| Stage | Inputs and processing | Accountable role | Output and audit evidence |
|---|---|---|---|
| FEW-01 Data ingestion | Rainfall, approved forecasts, river/discharge/rate-of-rise, reservoir, satellite, historical events and field reports are received with source ID and observation time. | Field Officer / Data Officer | Immutable source/provenance references, ingestion time, source and QC state. |
| FEW-02 Quality control | Check units, timestamps, location, completeness, source quality, plausibility and duplicate records; quarantine failures. | Data Officer | Validated or rejected evidence, reason, validator and audit entry. |
| FEW-03 Condition detection | Compare QC-passed evidence to the current approved/versioned rule set; retain the input values and rule version. | Technical Officer | Proposed trigger and trigger record; no automatic official warning. |
| FEW-04 Spatial impact assessment | Intersect drainage/flood zones with communities, exposure, vulnerability and critical infrastructure. Keep household outputs aggregated. | GIS / Technical Officer | Affected polygons, state/LGA/community, exposed counts and confidence. |
| FEW-05 Risk assessment | Combine hazard, exposure, vulnerability and criticality under approved parameters; label uncertainty and scenario status. | Technical Officer | Explainable risk score, confidence and model/rule versions. |
| FEW-06 Warning determination | Propose Level 0–3 from validated evidence and approved thresholds; record trigger, affected area, confidence and rule. | Technical Officer | Proposed alert with linked evidence and area; no release at this stage. |
| FEW-07 Technical/human review | Review evidence freshness, spatial extent, risk, confidence, message, likely impacts and false-alarm/missed-event context. | Technical Officer (independent reviewer) | Reviewer identity/time and review outcome; review must be independent of approval. |
| FEW-08 Notification | After official release, distribute approved message through selected channels and record delivery/reach and acknowledgements. | Authorised releaser / Field Officer | Channel, message version, language, timestamps, delivery and acknowledgement records. Database trigger rejects notification against an unreleased alert. |
| FEW-09 Community awareness | Maintain community profiles; conduct preparedness activity in appropriate local languages; record audience, reach, materials and feedback. | Field Officer / Community focal point | Awareness/drill record and non-identifying feedback. |
| FEW-10 Event confirmation | Verify occurrence, non-occurrence or continuing uncertainty against observations and independent sources. | Data Officer; technical review for verification | Event record and verification status; retain false alarms. |
| FEW-11 Impact assessment | Record observed extent, depth/duration when available, affected people/assets/services, losses and confidence. | Field Officer / Data Officer | Linked event, impact records, provenance and validation audit. |
| FEW-12 Warning-performance evaluation | Calculate lead time, reach, acknowledgement, hit/miss/false-alarm outcomes, extent agreement, awareness coverage and audit completeness. | Technical Officer / evaluator | Versioned evaluation with denominators, source event, confidence and evaluator. |
| FEW-13 Lessons and threshold improvement | Review missed events, false alarms, performance and community feedback; propose threshold/message changes through formal approval. | Technical Officer / Management | Lessons, change request and approved next rule version; never silently overwrite the current rule. |

### Warning levels

| Level | Name | Meaning |
|---|---|---|
| 0 | Normal Monitoring | Routine monitoring; no immediate threat. |
| 1 | Advisory | Increasing flood potential; preparedness and monitoring. |
| 2 | Flood Watch | Higher likelihood; preparedness and coordination increase. |
| 3 | Flood Warning | Flood imminent or occurring; follow approved emergency instructions. |

Levels do not themselves encode an evacuation order. The release authority and
approved local message govern any action instruction.

## Database and access controls

The PostGIS DDL adds nine tables to the existing 22-table core model and
extends its existing `clean.flood_events` table: alerts, alert triggers, alert
areas, notifications, acknowledgements, awareness activities, drills,
impacts, and warning-performance evaluations. It records rule/version,
confidence, reviewer, approver, releaser, timestamps and cancellation reason.
Audit triggers write inserts, updates and deletes to `audit.audit_trail`.

| Database group | Intended access |
|---|---|
| `few_field_officer` | Insert field event/impact, awareness, drill, notification and acknowledgement records; view released alerts only. |
| `few_data_officer` | Validate event records and review source/evidence records. |
| `few_technical_officer` | Create proposed alerts, triggers and areas; record technical review; cannot approve/release/cancel. |
| `few_authorised_releaser` | Approve, release and cancel alerts; release actions must be performed by a login assigned to this role. |
| `few_management_viewer` | Read released-alert views and warning-performance results. |

The alert workflow trigger binds the reviewer/releaser fields to the
authenticated PostgreSQL session user, requires independent review before
approval, and restricts approval/release/cancellation to the releaser group.
Production deployment still requires an administrator to provision individual
login roles, assign memberships, secure database credentials, and configure
network/TLS policy. Do not treat an API field claiming a role as authentication.

## GIS register

The register grows from 37 to 43 layers. G05 remains critical and explicitly
covers **main rivers, tributaries, distributaries, streams and drainage
channels**. G38–G43 are documented in
[`../04_GIS/06_METADATA/FEW_CAM_GIS_REGISTER.csv`](../04_GIS/06_METADATA/FEW_CAM_GIS_REGISTER.csv).

## Dashboard and data integration

The FastAPI dashboard exposes read-only `/api/flood/dashboard`,
`/api/flood/alerts`, `/api/flood/performance`, `/api/flood/warning-levels`,
and `/api/flood/geojson` endpoints. The alert, notification, acknowledgement,
awareness and performance data feeds are read from
`03_Data/CLEAN/Flood_*_CLEAN.csv`; the map endpoint reads
`04_GIS/03_DERIVED/G38_Flood_Alert_Zones_v1_0.geojson`. Missing feeds are
reported as `NOT_CONFIGURED`; the dashboard does not fabricate active alerts,
thresholds, performance or map features. Connect production feeds only after
source ownership, validation, publication and access review are agreed.

## Performance indicator definitions

- Lead time: observed event start minus official release time, in hours; retain
  negative/invalid timing as a QC issue rather than clipping it.
- Notification reach: reached recipients / intended recipients.
- Acknowledgement rate: acknowledgements / intended recipients, when recipient
  denominator is known; otherwise the dashboard reports acknowledgements per
  notification and caps the display at 100%.
- Hit rate: verified alert-linked events / (verified alert-linked events +
  verified events with no alert).
- False-alarm rate: alerts verified as false alarms / (verified alerts +
  verified false alarms).
- Extent agreement: retain alerted and observed area in km² for comparison;
  calculate an overlap statistic only when geometries and matching methods are
  available.
- Awareness coverage: high-risk communities reached / high-risk communities
  targeted.
- Audit completeness: required evidence/source, timestamp, trigger/rule,
  confidence, affected area and reviewer fields complete / required fields.
- Community response/preparedness: report measurable drill/activity outcomes
  and denominators; do not infer behaviour from message delivery alone.

For misses, create a performance record linked to the observed flood event even
when there is no alert. Preserve false alarms, missed warnings and uncertainty
as learning records.

## Pilot readiness gates

Before a pilot, identify participating communities and data-feed owners; approve
thresholds, message templates, languages and release authority; configure
PostgreSQL roles and accounts; establish notification providers and delivery
denominators; validate G38–G43 geometry and G05 network completeness; rehearse
normal, advisory, watch, warning, cancellation, false-alarm and missed-event
cases; and obtain an independent review of safety, privacy and performance
definitions. The included field form records observations and awareness
activities; it does not issue warnings or claim technical event verification.
