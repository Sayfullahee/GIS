-- =============================================================================
-- CHER-CDSS ADVANCED MASTER IMPLEMENTATION SCAFFOLD v4.1
-- PostgreSQL / PostGIS Central Authoritative Relational & Spatial Database DDL
-- Date: October 2026
-- Reference: CHER-CDSS Master Scaffold Section 4, Section 32, Section 44 (Stage 4)
-- =============================================================================

-- Enable PostGIS spatial extension
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create distinct lifecycle schemas
CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS clean;
CREATE SCHEMA IF NOT EXISTS derived;
CREATE SCHEMA IF NOT EXISTS lookups;
CREATE SCHEMA IF NOT EXISTS audit;

-- =============================================================================
-- 1. LOOKUPS SCHEMA (Controlled Vocabularies & Reference Registers)
-- =============================================================================

CREATE TABLE lookups.states (
    state_code      VARCHAR(10) PRIMARY KEY, -- e.g. 'NG-NIG'
    internal_code   VARCHAR(5) NOT NULL UNIQUE, -- e.g. 'NIG', 'KEB', 'PLA', 'BEN', 'KOG', 'KWA', 'KAD', 'NAS', 'TAR', 'GOM'
    state_name      VARCHAR(50) NOT NULL,
    capital         VARCHAR(50) NOT NULL,
    geopolitical_zone VARCHAR(50) NOT NULL,
    notes           TEXT
);

CREATE TABLE lookups.lgas (
    lga_id          VARCHAR(20) PRIMARY KEY, -- e.g. 'NG-NIG-001'
    lga_name        VARCHAR(100) NOT NULL,
    state_code      VARCHAR(10) NOT NULL REFERENCES lookups.states(state_code),
    area_sqkm       NUMERIC(10,2),
    notes           TEXT
);

CREATE TABLE lookups.lookup_code (
    lookup_id       VARCHAR(30) PRIMARY KEY,
    domain          VARCHAR(50) NOT NULL,
    code            VARCHAR(30) NOT NULL,
    label           VARCHAR(100) NOT NULL,
    description     TEXT,
    unit            VARCHAR(30),
    version         VARCHAR(20) DEFAULT 'v4.1'
);

CREATE TABLE lookups.reference_bounds (
    indicator_id    VARCHAR(30) PRIMARY KEY,
    indicator_name  VARCHAR(100) NOT NULL,
    component       VARCHAR(30) NOT NULL, -- Hazard, Exposure, Vulnerability, Criticality, Composite_Risk
    direction       VARCHAR(20) NOT NULL, -- Positive, Inverse
    min_ref         NUMERIC(12,4) NOT NULL,
    max_ref         NUMERIC(12,4) NOT NULL,
    unit            VARCHAR(30),
    transform       VARCHAR(30) DEFAULT 'none',
    baseline_version VARCHAR(20) DEFAULT 'Baseline_2026',
    frozen_date     DATE NOT NULL DEFAULT '2026-10-01'
);

-- =============================================================================
-- 2. METADATA, AUDIT & PROVENANCE TABLES (Section 32 v4.1)
-- =============================================================================

CREATE TABLE clean.data_provenance (
    provenance_id   VARCHAR(40) PRIMARY KEY,
    source_name     VARCHAR(150) NOT NULL,
    acquisition_date DATE NOT NULL,
    processing_method TEXT NOT NULL,
    software_version VARCHAR(100) NOT NULL,
    analyst_name    VARCHAR(100) NOT NULL,
    limitations     TEXT,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE clean.data_confidence (
    confidence_id   VARCHAR(40) PRIMARY KEY,
    entity_or_layer VARCHAR(100) NOT NULL,
    completeness_pct NUMERIC(5,2) NOT NULL CHECK (completeness_pct BETWEEN 0 AND 100),
    recency_months  INTEGER NOT NULL CHECK (recency_months >= 0),
    source_quality  VARCHAR(30) NOT NULL,
    validation_status VARCHAR(30) NOT NULL,
    rating          VARCHAR(20) NOT NULL CHECK (rating IN ('High', 'Moderate', 'Low', 'Unknown')),
    decision_use    TEXT NOT NULL,
    assessed_date   DATE NOT NULL DEFAULT CURRENT_DATE
);

CREATE TABLE audit.audit_trail (
    audit_id        BIGSERIAL PRIMARY KEY,
    table_name      VARCHAR(100) NOT NULL,
    record_pk       VARCHAR(100) NOT NULL,
    column_name     VARCHAR(100) NOT NULL,
    original_value  TEXT,
    corrected_value TEXT,
    reason          TEXT NOT NULL,
    user_name       VARCHAR(100) NOT NULL,
    timestamp       TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- 3. ADMINISTRATIVE & SPATIAL MASTERS (Section 32 v4.1)
-- =============================================================================

-- Ward Master (Administrative Level 3 - Sub-layer G02W)
CREATE TABLE clean.ward_master (
    ward_id         VARCHAR(30) PRIMARY KEY, -- e.g. 'NG-NIG-001-W01'
    ward_name       VARCHAR(100) NOT NULL,
    lga_id          VARCHAR(20) NOT NULL REFERENCES lookups.lgas(lga_id),
    state_code      VARCHAR(10) NOT NULL REFERENCES lookups.states(state_code),
    boundary_version VARCHAR(30) NOT NULL DEFAULT 'v2026.1',
    validity_start  DATE NOT NULL DEFAULT '2026-01-01',
    validity_end    DATE,
    geom            GEOMETRY(MultiPolygon, 4326),
    provenance_id   VARCHAR(40) REFERENCES clean.data_provenance(provenance_id)
);

-- Community Master (G03)
CREATE TABLE clean.community_master (
    community_id    VARCHAR(30) PRIMARY KEY, -- e.g. 'NG-NIG-001-0001'
    community_name  VARCHAR(150) NOT NULL,
    ward_id         VARCHAR(30) REFERENCES clean.ward_master(ward_id),
    lga_id          VARCHAR(20) NOT NULL REFERENCES lookups.lgas(lga_id),
    state_code      VARCHAR(10) NOT NULL REFERENCES lookups.states(state_code),
    latitude        NUMERIC(10,6) NOT NULL CHECK (latitude BETWEEN 4.0 AND 14.5),
    longitude       NUMERIC(10,6) NOT NULL CHECK (longitude BETWEEN 2.0 AND 15.5),
    gps_accuracy_m  NUMERIC(8,2) NOT NULL CHECK (gps_accuracy_m >= 0),
    survey_date     DATE NOT NULL,
    population      INTEGER CHECK (population >= 0),
    primary_livelihood VARCHAR(50),
    electricity_access VARCHAR(30),
    water_source    VARCHAR(50),
    flood_experience VARCHAR(20),
    erosion_presence VARCHAR(20),
    adaptation_status VARCHAR(50),
    geom            GEOMETRY(Point, 4326),
    provenance_id   VARCHAR(40) REFERENCES clean.data_provenance(provenance_id),
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Facility Master (Hydropower, dams, powerplants - G07)
CREATE TABLE clean.facility_master (
    facility_id     VARCHAR(30) PRIMARY KEY, -- e.g. 'FAC-HYD-NIG-001' (Kainji, etc.)
    facility_name   VARCHAR(150) NOT NULL,
    facility_type   VARCHAR(50) NOT NULL, -- Hydropower Dam, Water Treatment, Substation
    installed_capacity_mw NUMERIC(10,2),
    operator        VARCHAR(150) NOT NULL,
    status          VARCHAR(50) NOT NULL, -- Operational, Disrupted, Maintenance
    state_code      VARCHAR(10) NOT NULL REFERENCES lookups.states(state_code),
    lga_id          VARCHAR(20) REFERENCES lookups.lgas(lga_id),
    linked_basin    VARCHAR(100),
    latitude        NUMERIC(10,6) NOT NULL CHECK (latitude BETWEEN 4.0 AND 14.5),
    longitude       NUMERIC(10,6) NOT NULL CHECK (longitude BETWEEN 2.0 AND 15.5),
    geom            GEOMETRY(Point, 4326),
    provenance_id   VARCHAR(40) REFERENCES clean.data_provenance(provenance_id)
);

-- Climate Stations (G20)
CREATE TABLE clean.climate_station (
    station_id      VARCHAR(30) PRIMARY KEY, -- e.g. 'STA-NIM-NIG-001'
    station_name    VARCHAR(150) NOT NULL,
    operator        VARCHAR(100) NOT NULL, -- NiMet, NIHSA, N-HYPPADEC
    elevation_m     NUMERIC(8,2),
    state_code      VARCHAR(10) NOT NULL REFERENCES lookups.states(state_code),
    latitude        NUMERIC(10,6) NOT NULL CHECK (latitude BETWEEN 3.5 AND 14.5),
    longitude       NUMERIC(10,6) NOT NULL CHECK (longitude BETWEEN 2.0 AND 15.5),
    operating_since DATE,
    geom            GEOMETRY(Point, 4326),
    provenance_id   VARCHAR(40) REFERENCES clean.data_provenance(provenance_id)
);

-- =============================================================================
-- 4. OPERATIONAL & MONITORING TABLES (Section 32)
-- =============================================================================

-- Household Survey (Level 3 RESTRICTED - G04)
CREATE TABLE clean.household_survey (
    household_id    VARCHAR(40) PRIMARY KEY,
    community_id    VARCHAR(30) NOT NULL REFERENCES clean.community_master(community_id),
    state_code      VARCHAR(10) NOT NULL REFERENCES lookups.states(state_code),
    consent_given   BOOLEAN NOT NULL CHECK (consent_given = TRUE),
    head_gender     VARCHAR(20),
    household_size  INTEGER CHECK (household_size > 0),
    livelihood_type VARCHAR(50),
    monthly_income_band VARCHAR(50),
    food_insecurity_score NUMERIC(5,2),
    flood_loss_amount NUMERIC(14,2),
    erosion_loss_amount NUMERIC(14,2),
    adaptation_coping_mechanism TEXT,
    survey_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    provenance_id   VARCHAR(40) REFERENCES clean.data_provenance(provenance_id)
);

-- Erosion Sites (G26)
CREATE TABLE clean.erosion_sites (
    erosion_id      VARCHAR(30) PRIMARY KEY, -- e.g. 'ERO-NIG-001-0001'
    community_id    VARCHAR(30) REFERENCES clean.community_master(community_id),
    state_code      VARCHAR(10) NOT NULL REFERENCES lookups.states(state_code),
    erosion_type    VARCHAR(50) NOT NULL, -- Gully, Sheet, Rill, Riverbank
    severity_rank   SMALLINT NOT NULL CHECK (severity_rank BETWEEN 0 AND 4),
    length_m        NUMERIC(10,2),
    width_m         NUMERIC(10,2),
    depth_m         NUMERIC(10,2),
    activity_status VARCHAR(30) NOT NULL, -- Active, Stabilizing, Dormant
    bank_proximity_m NUMERIC(10,2),
    infrastructure_threat VARCHAR(100),
    latitude        NUMERIC(10,6) NOT NULL,
    longitude       NUMERIC(10,6) NOT NULL,
    geom            GEOMETRY(Point, 4326),
    provenance_id   VARCHAR(40) REFERENCES clean.data_provenance(provenance_id),
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Flood Events (G25)
CREATE TABLE clean.flood_events (
    flood_event_id  VARCHAR(40) PRIMARY KEY,
    event_name      VARCHAR(150),
    start_date      DATE NOT NULL,
    end_date        DATE,
    state_code      VARCHAR(10) NOT NULL REFERENCES lookups.states(state_code),
    community_id    VARCHAR(30) REFERENCES clean.community_master(community_id),
    peak_depth_m    NUMERIC(6,2),
    duration_days   INTEGER,
    source_agency   VARCHAR(100) NOT NULL,
    confidence_rating VARCHAR(20) NOT NULL CHECK (confidence_rating IN ('High', 'Moderate', 'Low', 'Unknown')),
    impact_summary  TEXT,
    geom            GEOMETRY(MultiPolygon, 4326),
    provenance_id   VARCHAR(40) REFERENCES clean.data_provenance(provenance_id)
);

-- Hydropower & Water Observations (G28)
CREATE TABLE clean.hydropower_water (
    hydro_record_id VARCHAR(40) PRIMARY KEY,
    facility_id     VARCHAR(30) NOT NULL REFERENCES clean.facility_master(facility_id),
    state_code      VARCHAR(10) NOT NULL REFERENCES lookups.states(state_code),
    obs_date        DATE NOT NULL,
    reservoir_elevation_m NUMERIC(10,2),
    inflow_m3_s     NUMERIC(12,2),
    outflow_m3_s    NUMERIC(12,2),
    generation_mwh  NUMERIC(12,2),
    disruption_flag BOOLEAN DEFAULT FALSE,
    disruption_reason TEXT,
    provenance_id   VARCHAR(40) REFERENCES clean.data_provenance(provenance_id)
);

-- Climate Observations (G21)
CREATE TABLE clean.climate_observations (
    climate_id      VARCHAR(40) PRIMARY KEY,
    station_id      VARCHAR(30) NOT NULL REFERENCES clean.climate_station(station_id),
    state_code      VARCHAR(10) NOT NULL REFERENCES lookups.states(state_code),
    obs_date        DATE NOT NULL,
    rainfall_mm     NUMERIC(8,2) CHECK (rainfall_mm >= 0),
    temp_min_c      NUMERIC(5,2),
    temp_max_c      NUMERIC(5,2),
    provenance_id   VARCHAR(40) REFERENCES clean.data_provenance(provenance_id)
);

-- Infrastructure (G19)
CREATE TABLE clean.infrastructure (
    infrastructure_id VARCHAR(40) PRIMARY KEY,
    facility_name   VARCHAR(150) NOT NULL,
    infra_type      VARCHAR(50) NOT NULL, -- Health, Education, Bridge, Culvert, Water
    condition_rating SMALLINT CHECK (condition_rating BETWEEN 1 AND 5),
    community_id    VARCHAR(30) REFERENCES clean.community_master(community_id),
    state_code      VARCHAR(10) NOT NULL REFERENCES lookups.states(state_code),
    hazard_exposure VARCHAR(50),
    service_disruption_days INTEGER DEFAULT 0,
    latitude        NUMERIC(10,6) NOT NULL,
    longitude       NUMERIC(10,6) NOT NULL,
    geom            GEOMETRY(Point, 4326),
    provenance_id   VARCHAR(40) REFERENCES clean.data_provenance(provenance_id)
);

-- Food Security Monitoring
CREATE TABLE clean.food_security (
    food_record_id  VARCHAR(40) PRIMARY KEY,
    community_id    VARCHAR(30) NOT NULL REFERENCES clean.community_master(community_id),
    state_code      VARCHAR(10) NOT NULL REFERENCES lookups.states(state_code),
    reporting_period VARCHAR(30) NOT NULL, -- e.g. '2026-Q3'
    crop_loss_pct   NUMERIC(5,2) CHECK (crop_loss_pct BETWEEN 0 AND 100),
    livestock_loss_pct NUMERIC(5,2) CHECK (livestock_loss_pct BETWEEN 0 AND 100),
    market_access_score NUMERIC(5,2),
    food_insecurity_index NUMERIC(5,2),
    provenance_id   VARCHAR(40) REFERENCES clean.data_provenance(provenance_id)
);

-- Community Security Impact (Development-Impact Only - Section 14)
CREATE TABLE clean.security_impact (
    security_event_id VARCHAR(40) PRIMARY KEY,
    community_id    VARCHAR(30) REFERENCES clean.community_master(community_id),
    state_code      VARCHAR(10) NOT NULL REFERENCES lookups.states(state_code),
    event_date      DATE NOT NULL,
    impact_type     VARCHAR(50) NOT NULL, -- Displacement, Farm Access Denial, Market Disruption, Project Access Constraint
    displaced_persons_count INTEGER DEFAULT 0,
    farm_access_restricted BOOLEAN DEFAULT FALSE,
    project_delay_days INTEGER DEFAULT 0,
    confidence_rating VARCHAR(20) NOT NULL CHECK (confidence_rating IN ('High', 'Moderate', 'Low', 'Unknown')),
    provenance_id   VARCHAR(40) REFERENCES clean.data_provenance(provenance_id)
);

-- Loss and Damage Register (Section 32 v4.1)
CREATE TABLE clean.loss_damage (
    loss_id         VARCHAR(40) PRIMARY KEY,
    hazard_type     VARCHAR(50) NOT NULL, -- Flood, Erosion, Compound
    linked_event_id VARCHAR(40), -- FK to flood_events or erosion_sites
    community_id    VARCHAR(30) NOT NULL REFERENCES clean.community_master(community_id),
    state_code      VARCHAR(10) NOT NULL REFERENCES lookups.states(state_code),
    asset_or_livelihood_type VARCHAR(100) NOT NULL,
    physical_quantity NUMERIC(12,2),
    unit            VARCHAR(30),
    financial_loss_ngn NUMERIC(16,2),
    confidence_rating VARCHAR(20) NOT NULL CHECK (confidence_rating IN ('High', 'Moderate', 'Low', 'Unknown')),
    provenance_id   VARCHAR(40) REFERENCES clean.data_provenance(provenance_id)
);

-- Interventions and MRV (G36 - Section 15)
CREATE TABLE clean.interventions (
    intervention_id VARCHAR(40) PRIMARY KEY, -- e.g. 'INT-NIG-001-0001'
    project_title   VARCHAR(200) NOT NULL,
    project_type    VARCHAR(100) NOT NULL, -- Drainage, Gully Stabilization, Solar Borehole, Embankment
    community_id    VARCHAR(30) REFERENCES clean.community_master(community_id),
    state_code      VARCHAR(10) NOT NULL REFERENCES lookups.states(state_code),
    budget_ngn      NUMERIC(16,2),
    status          VARCHAR(50) NOT NULL, -- Proposed, Ongoing, Completed, Commissioned
    start_date      DATE,
    completion_date DATE,
    risk_before     NUMERIC(6,2), -- Pre-implementation risk score
    risk_after      NUMERIC(6,2), -- Post-implementation risk score
    ies_score       NUMERIC(6,2), -- Intervention Effectiveness Score (%)
    residual_risk   NUMERIC(6,2), -- Residual risk post-intervention
    provenance_id   VARCHAR(40) REFERENCES clean.data_provenance(provenance_id)
);

-- =============================================================================
-- 5. DERIVED & ANALYTICAL OUTPUTS (DERIVED SCHEMA)
-- =============================================================================

CREATE TABLE derived.indicators (
    indicator_entry_id BIGSERIAL PRIMARY KEY,
    indicator_id    VARCHAR(30) NOT NULL REFERENCES lookups.reference_bounds(indicator_id),
    community_id    VARCHAR(30) NOT NULL REFERENCES clean.community_master(community_id),
    state_code      VARCHAR(10) NOT NULL REFERENCES lookups.states(state_code),
    raw_value       NUMERIC(14,4) NOT NULL,
    normalized_value NUMERIC(6,2) NOT NULL CHECK (normalized_value BETWEEN 0 AND 100),
    period          VARCHAR(20) NOT NULL, -- e.g. '2026-Baseline'
    method_version  VARCHAR(20) NOT NULL DEFAULT 'v4.1',
    calculated_at   TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE derived.risk_assessments (
    risk_id         VARCHAR(40) PRIMARY KEY,
    community_id    VARCHAR(30) NOT NULL REFERENCES clean.community_master(community_id),
    state_code      VARCHAR(10) NOT NULL REFERENCES lookups.states(state_code),
    h_hazard        NUMERIC(6,2) NOT NULL CHECK (h_hazard BETWEEN 0 AND 100),
    e_exposure      NUMERIC(6,2) NOT NULL CHECK (e_exposure BETWEEN 0 AND 100),
    v_vulnerability NUMERIC(6,2) NOT NULL CHECK (v_vulnerability BETWEEN 0 AND 100),
    c_criticality   NUMERIC(6,2) NOT NULL CHECK (c_criticality BETWEEN 0 AND 100),
    r_composite_risk NUMERIC(6,2) NOT NULL CHECK (r_composite_risk BETWEEN 0 AND 100),
    r_multiplicative NUMERIC(6,2) NOT NULL CHECK (r_multiplicative BETWEEN 0 AND 100),
    confidence_rating VARCHAR(20) NOT NULL CHECK (confidence_rating IN ('High', 'Moderate', 'Low', 'Unknown')),
    model_version   VARCHAR(20) NOT NULL DEFAULT 'Risk_Model_v4.1',
    ref_bounds_id   VARCHAR(30) NOT NULL DEFAULT 'Baseline_2026',
    calculated_at   TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE derived.priority_areas (
    priority_id     VARCHAR(40) PRIMARY KEY,
    community_id    VARCHAR(30) NOT NULL REFERENCES clean.community_master(community_id),
    state_code      VARCHAR(10) NOT NULL REFERENCES lookups.states(state_code),
    composite_risk  NUMERIC(6,2) NOT NULL,
    adaptation_gap  NUMERIC(6,2) NOT NULL,
    priority_score  NUMERIC(6,2) NOT NULL,
    priority_tier   VARCHAR(20) NOT NULL CHECK (priority_tier IN ('Tier 1 Critical', 'Tier 2 High', 'Tier 3 Moderate', 'Tier 4 Monitor')),
    confidence_rating VARCHAR(20) NOT NULL,
    approval_status VARCHAR(50) DEFAULT 'Proposed',
    approval_date   DATE
);

CREATE TABLE derived.scenarios (
    scenario_id     VARCHAR(40) PRIMARY KEY,
    scenario_name   VARCHAR(100) NOT NULL,
    scenario_type   VARCHAR(50) NOT NULL, -- Climate Stress, Land-Use Change, Adaptation Investment
    assumptions_json JSONB NOT NULL,
    projected_risk_mean NUMERIC(6,2) NOT NULL,
    model_version   VARCHAR(20) NOT NULL DEFAULT 'Scenario_v4.1',
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- 5A. FLOOD EARLY WARNING, ALARM & COMMUNITY AWARENESS (FEW-CAM)
-- =============================================================================

CREATE TABLE clean.flood_alerts (
    alert_id        VARCHAR(40) PRIMARY KEY,
    issued_at       TIMESTAMP WITH TIME ZONE,
    state_code      VARCHAR(10) NOT NULL REFERENCES lookups.states(state_code),
    lga_id          VARCHAR(20) REFERENCES lookups.lgas(lga_id),
    warning_level   SMALLINT NOT NULL CHECK (warning_level BETWEEN 0 AND 3),
    trigger_type    VARCHAR(50) NOT NULL,
    hazard_score    NUMERIC(6,2) CHECK (hazard_score BETWEEN 0 AND 100),
    confidence      VARCHAR(20) NOT NULL CHECK (confidence IN ('High', 'Moderate', 'Low', 'Unknown')),
    status          VARCHAR(20) NOT NULL DEFAULT 'proposed'
                    CHECK (status IN ('proposed', 'in_review', 'approved', 'released', 'cancelled', 'expired', 'false_alarm')),
    rule_id         VARCHAR(50) NOT NULL,
    rule_version    VARCHAR(30) NOT NULL,
    reviewed_by     VARCHAR(100),
    reviewed_at     TIMESTAMP WITH TIME ZONE,
    approved_by     VARCHAR(100),
    approved_at     TIMESTAMP WITH TIME ZONE,
    released_by     VARCHAR(100),
    released_at     TIMESTAMP WITH TIME ZONE,
    expired_by      VARCHAR(100),
    expired_at      TIMESTAMP WITH TIME ZONE,
    cancelled_by    VARCHAR(100),
    cancelled_at    TIMESTAMP WITH TIME ZONE,
    cancellation_reason TEXT,
    notes           TEXT,
    created_by      VARCHAR(100) NOT NULL,
    created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (reviewed_at IS NULL OR reviewed_by IS NOT NULL),
    CHECK (approved_at IS NULL OR approved_by IS NOT NULL),
    CHECK (released_at IS NULL OR (approved_at IS NOT NULL AND released_by IS NOT NULL)),
    CHECK (expired_at IS NULL OR expired_by IS NOT NULL),
    CHECK (cancelled_at IS NULL OR (cancelled_by IS NOT NULL AND cancellation_reason IS NOT NULL)),
    CHECK (status <> 'approved' OR (approved_at IS NOT NULL AND approved_by IS NOT NULL)),
    CHECK (status <> 'released' OR (released_at IS NOT NULL AND released_by IS NOT NULL)),
    CHECK (status <> 'expired' OR (expired_at IS NOT NULL AND expired_by IS NOT NULL)),
    CHECK (status <> 'cancelled' OR (cancelled_at IS NOT NULL AND cancelled_by IS NOT NULL AND cancellation_reason IS NOT NULL)),
    CHECK (status NOT IN ('released', 'expired') OR issued_at IS NOT NULL),
    CHECK (approved_at IS NULL OR reviewed_at IS NULL OR approved_at >= reviewed_at),
    CHECK (released_at IS NULL OR released_at >= approved_at),
    CHECK (released_at IS NULL OR issued_at = released_at),
    CHECK (expired_at IS NULL OR expired_at >= released_at),
    CHECK (cancelled_at IS NULL OR cancelled_at >= issued_at)
);

CREATE TABLE clean.flood_alert_triggers (
    trigger_id      VARCHAR(40) PRIMARY KEY,
    alert_id        VARCHAR(40) NOT NULL REFERENCES clean.flood_alerts(alert_id),
    source_type     VARCHAR(40) NOT NULL,
    source_name     VARCHAR(150) NOT NULL,
    source_record_id VARCHAR(100),
    observed_at     TIMESTAMP WITH TIME ZONE NOT NULL,
    recorded_at     TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    observed_value  NUMERIC(14,4),
    threshold_value NUMERIC(14,4),
    unit            VARCHAR(30),
    rule_id         VARCHAR(50) NOT NULL,
    rule_version    VARCHAR(30) NOT NULL,
    confidence      VARCHAR(20) NOT NULL CHECK (confidence IN ('High', 'Moderate', 'Low', 'Unknown')),
    qc_status       VARCHAR(20) NOT NULL DEFAULT 'raw'
                    CHECK (qc_status IN ('raw', 'validated', 'rejected')),
    qc_by           VARCHAR(100),
    qc_at           TIMESTAMP WITH TIME ZONE,
    qc_reason       TEXT,
    provenance_id   VARCHAR(40) REFERENCES clean.data_provenance(provenance_id),
    evidence_note   TEXT,
    CHECK (qc_status NOT IN ('validated', 'rejected') OR (qc_by IS NOT NULL AND qc_at IS NOT NULL)),
    CHECK (qc_status <> 'rejected' OR qc_reason IS NOT NULL)
);

CREATE TABLE clean.flood_alert_areas (
    alert_area_id   VARCHAR(40) PRIMARY KEY,
    alert_id        VARCHAR(40) NOT NULL REFERENCES clean.flood_alerts(alert_id),
    state_code      VARCHAR(10) NOT NULL REFERENCES lookups.states(state_code),
    lga_id          VARCHAR(20) REFERENCES lookups.lgas(lga_id),
    community_id    VARCHAR(30) REFERENCES clean.community_master(community_id),
    affected_area_sqkm NUMERIC(12,3) CHECK (affected_area_sqkm >= 0),
    exposed_population INTEGER CHECK (exposed_population >= 0),
    exposed_households INTEGER CHECK (exposed_households >= 0),
    exposed_critical_assets INTEGER CHECK (exposed_critical_assets >= 0),
    geom            GEOMETRY(MultiPolygon, 4326) NOT NULL,
    assessed_at     TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    confidence      VARCHAR(20) NOT NULL CHECK (confidence IN ('High', 'Moderate', 'Low', 'Unknown'))
);

CREATE TABLE clean.flood_notifications (
    notification_id VARCHAR(40) PRIMARY KEY,
    alert_id        VARCHAR(40) NOT NULL REFERENCES clean.flood_alerts(alert_id),
    community_id    VARCHAR(30) REFERENCES clean.community_master(community_id),
    channel         VARCHAR(30) NOT NULL CHECK (channel IN ('sms', 'radio', 'community_leader', 'field_team', 'digital', 'other')),
    language_code   VARCHAR(20),
    message_version VARCHAR(40) NOT NULL,
    sent_at         TIMESTAMP WITH TIME ZONE,
    delivery_status VARCHAR(20) NOT NULL
                    CHECK (delivery_status IN ('queued', 'sent', 'partial', 'failed', 'cancelled')),
    recipient_count INTEGER NOT NULL DEFAULT 0 CHECK (recipient_count >= 0),
    reached_count   INTEGER NOT NULL DEFAULT 0 CHECK (reached_count >= 0 AND reached_count <= recipient_count),
    provider_reference VARCHAR(100),
    sent_by         VARCHAR(100) NOT NULL,
    CHECK (delivery_status NOT IN ('sent', 'partial') OR sent_at IS NOT NULL)
);

CREATE TABLE clean.flood_acknowledgements (
    acknowledgement_id VARCHAR(40) PRIMARY KEY,
    notification_id VARCHAR(40) NOT NULL REFERENCES clean.flood_notifications(notification_id),
    acknowledged_at TIMESTAMP WITH TIME ZONE NOT NULL,
    acknowledgement_status VARCHAR(20) NOT NULL
                    CHECK (acknowledgement_status IN ('received', 'understood', 'help_requested', 'unable_to_act', 'unconfirmed')),
    recipient_token VARCHAR(40) NOT NULL,
    community_id    VARCHAR(30) REFERENCES clean.community_master(community_id),
    respondent_role VARCHAR(50),
    acknowledgement_source VARCHAR(30) NOT NULL,
    notes           TEXT,
    UNIQUE (notification_id, recipient_token)
);

CREATE TABLE clean.flood_awareness (
    awareness_id    VARCHAR(40) PRIMARY KEY,
    alert_id        VARCHAR(40) REFERENCES clean.flood_alerts(alert_id),
    community_id    VARCHAR(30) NOT NULL REFERENCES clean.community_master(community_id),
    activity_type   VARCHAR(40) NOT NULL
                    CHECK (activity_type IN ('preparedness_session', 'public_information', 'household_outreach', 'post_event_review', 'other')),
    conducted_at    TIMESTAMP WITH TIME ZONE NOT NULL,
    method          VARCHAR(30) NOT NULL,
    language_code   VARCHAR(20) NOT NULL,
    target_audience VARCHAR(100) NOT NULL,
    audience_count INTEGER CHECK (audience_count >= 0),
    reach_count     INTEGER CHECK (reach_count >= 0),
    materials       TEXT,
    feedback        TEXT,
    facilitator_id  VARCHAR(100) NOT NULL,
    confidence      VARCHAR(20) NOT NULL CHECK (confidence IN ('High', 'Moderate', 'Low', 'Unknown')),
    publication_status VARCHAR(20) NOT NULL DEFAULT 'restricted'
                    CHECK (publication_status IN ('restricted', 'approved'))
);

CREATE TABLE clean.flood_drills (
    drill_id        VARCHAR(40) PRIMARY KEY,
    community_id    VARCHAR(30) NOT NULL REFERENCES clean.community_master(community_id),
    state_code      VARCHAR(10) NOT NULL REFERENCES lookups.states(state_code),
    drill_date      DATE NOT NULL,
    drill_type      VARCHAR(40) NOT NULL,
    scenario_summary TEXT NOT NULL,
    participants_count INTEGER CHECK (participants_count >= 0),
    outcome         VARCHAR(30) NOT NULL CHECK (outcome IN ('completed', 'partial', 'cancelled')),
    lessons_learned TEXT,
    facilitator_id  VARCHAR(100) NOT NULL,
    provenance_id   VARCHAR(40) REFERENCES clean.data_provenance(provenance_id)
);

ALTER TABLE clean.flood_events
    ADD COLUMN IF NOT EXISTS alert_id VARCHAR(40) REFERENCES clean.flood_alerts(alert_id),
    ADD COLUMN IF NOT EXISTS verification_status VARCHAR(20) NOT NULL DEFAULT 'unverified'
        CHECK (verification_status IN ('unverified', 'verified', 'false_alarm')),
    ADD COLUMN IF NOT EXISTS verified_by VARCHAR(100),
    ADD COLUMN IF NOT EXISTS verified_at TIMESTAMP WITH TIME ZONE,
    ADD COLUMN IF NOT EXISTS false_alarm_reason TEXT,
    ADD COLUMN IF NOT EXISTS observed_extent GEOMETRY(MultiPolygon, 4326),
    ADD CONSTRAINT chk_flood_event_verified_fields
        CHECK (verification_status <> 'verified' OR (verified_by IS NOT NULL AND verified_at IS NOT NULL)),
    ADD CONSTRAINT chk_flood_event_false_alarm_reason
        CHECK (verification_status <> 'false_alarm' OR (verified_by IS NOT NULL AND verified_at IS NOT NULL AND false_alarm_reason IS NOT NULL));

CREATE TABLE clean.flood_impacts (
    impact_id       VARCHAR(40) PRIMARY KEY,
    flood_event_id  VARCHAR(40) NOT NULL REFERENCES clean.flood_events(flood_event_id),
    community_id    VARCHAR(30) REFERENCES clean.community_master(community_id),
    state_code      VARCHAR(10) NOT NULL REFERENCES lookups.states(state_code),
    impact_category VARCHAR(40) NOT NULL,
    asset_type      VARCHAR(60),
    affected_count  INTEGER CHECK (affected_count >= 0),
    estimated_loss_ngn NUMERIC(16,2) CHECK (estimated_loss_ngn >= 0),
    service_disruption_days INTEGER CHECK (service_disruption_days >= 0),
    assessed_at     TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    assessed_by     VARCHAR(100) NOT NULL,
    confidence      VARCHAR(20) NOT NULL CHECK (confidence IN ('High', 'Moderate', 'Low', 'Unknown')),
    provenance_id   VARCHAR(40) REFERENCES clean.data_provenance(provenance_id),
    notes           TEXT
);

CREATE TABLE clean.flood_warning_performance (
    performance_id VARCHAR(40) PRIMARY KEY,
    alert_id        VARCHAR(40) REFERENCES clean.flood_alerts(alert_id),
    flood_event_id  VARCHAR(40) REFERENCES clean.flood_events(flood_event_id),
    evaluated_at    TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    evaluated_by    VARCHAR(100) NOT NULL,
    lead_time_hours NUMERIC(10,2) CHECK (lead_time_hours >= 0),
    recipient_count INTEGER CHECK (recipient_count >= 0),
    reached_count   INTEGER CHECK (reached_count >= 0 AND reached_count <= recipient_count),
    acknowledgement_count INTEGER CHECK (acknowledgement_count >= 0 AND acknowledgement_count <= recipient_count),
    hit_status      VARCHAR(20) NOT NULL CHECK (hit_status IN ('hit', 'miss', 'false_alarm', 'unverified')),
    alerted_extent_sqkm NUMERIC(12,3) CHECK (alerted_extent_sqkm >= 0),
    observed_extent_sqkm NUMERIC(12,3) CHECK (observed_extent_sqkm >= 0),
    high_risk_communities INTEGER CHECK (high_risk_communities >= 0),
    communities_reached INTEGER CHECK (communities_reached >= 0 AND communities_reached <= high_risk_communities),
    audit_completeness_pct NUMERIC(5,2) CHECK (audit_completeness_pct BETWEEN 0 AND 100),
    response_preparedness TEXT,
    confidence       VARCHAR(20) NOT NULL CHECK (confidence IN ('High', 'Moderate', 'Low', 'Unknown')),
    lessons_learned TEXT,
    publication_status VARCHAR(20) NOT NULL DEFAULT 'restricted'
                    CHECK (publication_status IN ('restricted', 'approved')),
    CHECK (alert_id IS NOT NULL OR flood_event_id IS NOT NULL)
);

CREATE INDEX idx_flood_alert_state_status ON clean.flood_alerts(state_code, status, warning_level);
CREATE INDEX idx_flood_alert_issued ON clean.flood_alerts(issued_at DESC);
CREATE INDEX idx_flood_trigger_alert_time ON clean.flood_alert_triggers(alert_id, observed_at);
CREATE INDEX idx_flood_area_geom ON clean.flood_alert_areas USING GIST(geom);
CREATE INDEX idx_flood_area_alert ON clean.flood_alert_areas(alert_id);
CREATE INDEX idx_flood_notification_alert ON clean.flood_notifications(alert_id, sent_at);
CREATE INDEX idx_flood_awareness_community_date ON clean.flood_awareness(community_id, conducted_at);
CREATE INDEX idx_flood_event_observed_extent ON clean.flood_events USING GIST(observed_extent);
CREATE INDEX idx_flood_impact_event ON clean.flood_impacts(flood_event_id);
CREATE INDEX idx_flood_performance_alert ON clean.flood_warning_performance(alert_id, evaluated_at);

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'few_field_officer') THEN
        CREATE ROLE few_field_officer NOLOGIN;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'few_data_officer') THEN
        CREATE ROLE few_data_officer NOLOGIN;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'few_technical_officer') THEN
        CREATE ROLE few_technical_officer NOLOGIN;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'few_authorised_releaser') THEN
        CREATE ROLE few_authorised_releaser NOLOGIN;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'few_management_viewer') THEN
        CREATE ROLE few_management_viewer NOLOGIN;
    END IF;
END;
$$;

CREATE OR REPLACE FUNCTION clean.enforce_flood_alert_workflow()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        IF NEW.status <> 'proposed'
           OR NEW.created_by IS DISTINCT FROM SESSION_USER
           OR NOT pg_has_role(SESSION_USER, 'few_technical_officer', 'member')
           OR NEW.reviewed_by IS NOT NULL OR NEW.reviewed_at IS NOT NULL
           OR NEW.approved_by IS NOT NULL OR NEW.approved_at IS NOT NULL
           OR NEW.released_by IS NOT NULL OR NEW.released_at IS NOT NULL
           OR NEW.expired_by IS NOT NULL OR NEW.expired_at IS NOT NULL
           OR NEW.cancelled_by IS NOT NULL OR NEW.cancelled_at IS NOT NULL THEN
            RAISE EXCEPTION 'Only a technical officer may create a new proposed alert';
        END IF;
        RETURN NEW;
    END IF;
    IF NEW.reviewed_at IS DISTINCT FROM OLD.reviewed_at THEN
        IF NOT pg_has_role(SESSION_USER, 'few_technical_officer', 'member')
           OR NEW.reviewed_by IS DISTINCT FROM SESSION_USER THEN
            RAISE EXCEPTION 'Only the assigned technical reviewer may record a review';
        END IF;
    END IF;
    IF TG_OP = 'UPDATE' AND (
        NEW.status IS DISTINCT FROM OLD.status
        OR NEW.approved_by IS DISTINCT FROM OLD.approved_by
        OR NEW.approved_at IS DISTINCT FROM OLD.approved_at
        OR NEW.issued_at IS DISTINCT FROM OLD.issued_at
        OR NEW.released_by IS DISTINCT FROM OLD.released_by
        OR NEW.released_at IS DISTINCT FROM OLD.released_at
        OR NEW.expired_by IS DISTINCT FROM OLD.expired_by
        OR NEW.expired_at IS DISTINCT FROM OLD.expired_at
        OR NEW.cancelled_by IS DISTINCT FROM OLD.cancelled_by
        OR NEW.cancelled_at IS DISTINCT FROM OLD.cancelled_at
    ) THEN
        IF NEW.status = 'in_review'
           AND (OLD.status <> 'proposed'
                OR NOT pg_has_role(SESSION_USER, 'few_technical_officer', 'member')) THEN
            RAISE EXCEPTION 'Only a technical officer may start review of a proposed alert';
        END IF;
        IF NEW.status IN ('approved', 'released', 'cancelled', 'expired')
           AND (NOT pg_has_role(SESSION_USER, 'few_authorised_releaser', 'member')
                OR (NEW.status = 'approved' AND NEW.approved_by IS DISTINCT FROM SESSION_USER)
                OR (NEW.status = 'released' AND NEW.released_by IS DISTINCT FROM SESSION_USER)
                OR (NEW.status = 'cancelled' AND NEW.cancelled_by IS DISTINCT FROM SESSION_USER)
                OR (NEW.status = 'expired' AND NEW.expired_by IS DISTINCT FROM SESSION_USER)) THEN
            RAISE EXCEPTION 'Only an authorised releaser may approve, release, cancel, or expire an alert';
        END IF;
        IF NEW.status IN ('approved', 'released', 'false_alarm') AND (
            NEW.reviewed_at IS NULL OR NEW.reviewed_by IS NULL
        ) THEN
            RAISE EXCEPTION 'Approval or false-alarm classification requires a completed technical review';
        END IF;
        IF NEW.status IN ('approved', 'released') AND (
            NEW.reviewed_by = NEW.approved_by OR NEW.approved_at IS NULL
        ) THEN
            RAISE EXCEPTION 'Approval requires a completed independent technical review';
        END IF;
        IF (NEW.approved_by IS DISTINCT FROM OLD.approved_by
            OR NEW.approved_at IS DISTINCT FROM OLD.approved_at)
           AND (OLD.status <> 'in_review' OR NEW.status <> 'approved'
                OR NEW.approved_by IS DISTINCT FROM SESSION_USER
                OR NEW.reviewed_at IS NULL OR NEW.reviewed_by = SESSION_USER) THEN
            RAISE EXCEPTION 'Approval identity and time must be recorded by a releaser after independent review';
        END IF;
        IF (NEW.issued_at IS DISTINCT FROM OLD.issued_at
            OR NEW.released_by IS DISTINCT FROM OLD.released_by
            OR NEW.released_at IS DISTINCT FROM OLD.released_at)
           AND (OLD.status <> 'approved' OR NEW.status <> 'released'
                OR NEW.released_by IS DISTINCT FROM SESSION_USER
                OR NEW.issued_at IS DISTINCT FROM NEW.released_at) THEN
            RAISE EXCEPTION 'Release identity and time must be recorded by the authorised releaser during release';
        END IF;
        IF (NEW.cancelled_by IS DISTINCT FROM OLD.cancelled_by
            OR NEW.cancelled_at IS DISTINCT FROM OLD.cancelled_at)
           AND (NEW.status <> 'cancelled' OR NEW.cancelled_by IS DISTINCT FROM SESSION_USER) THEN
            RAISE EXCEPTION 'Cancellation identity and time must be recorded by the authorised releaser';
        END IF;
        IF (NEW.expired_by IS DISTINCT FROM OLD.expired_by
            OR NEW.expired_at IS DISTINCT FROM OLD.expired_at)
           AND (OLD.status <> 'released' OR NEW.status <> 'expired'
                OR NEW.expired_by IS DISTINCT FROM SESSION_USER) THEN
            RAISE EXCEPTION 'Expiry identity and time must be recorded by the authorised releaser';
        END IF;
        IF NEW.status = 'approved' AND OLD.status <> 'in_review' THEN
            RAISE EXCEPTION 'An alert must complete technical review before approval';
        END IF;
        IF NEW.status = 'released' AND OLD.status <> 'approved' THEN
            RAISE EXCEPTION 'An alert must be approved before release';
        END IF;
        IF NEW.status = 'expired' AND OLD.status <> 'released' THEN
            RAISE EXCEPTION 'Only a released alert may be expired';
        END IF;
        IF NEW.status IN ('approved', 'released') AND (
            NOT EXISTS (SELECT 1 FROM clean.flood_alert_triggers
                        WHERE alert_id = NEW.alert_id AND qc_status = 'validated')
            OR NOT EXISTS (SELECT 1 FROM clean.flood_alert_areas WHERE alert_id = NEW.alert_id)
        ) THEN
            RAISE EXCEPTION 'Approval requires QC-validated evidence triggers and an assessed affected area';
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog, clean;

CREATE TRIGGER trg_enforce_flood_alert_workflow
BEFORE INSERT OR UPDATE ON clean.flood_alerts
FOR EACH ROW EXECUTE FUNCTION clean.enforce_flood_alert_workflow();

CREATE OR REPLACE FUNCTION clean.require_released_flood_alert()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.sent_by IS DISTINCT FROM SESSION_USER THEN
        RAISE EXCEPTION 'Notification sender must match the authenticated database user';
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM clean.flood_alerts
        WHERE alert_id = NEW.alert_id AND status = 'released'
    ) THEN
        RAISE EXCEPTION 'Notifications may only be issued for an officially released flood alert';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog, clean;

CREATE TRIGGER trg_require_released_alert_for_notification
BEFORE INSERT ON clean.flood_notifications
FOR EACH ROW EXECUTE FUNCTION clean.require_released_flood_alert();

CREATE OR REPLACE FUNCTION clean.enforce_flood_trigger_qc()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        IF NEW.qc_status <> 'raw' OR NEW.qc_by IS NOT NULL OR NEW.qc_at IS NOT NULL THEN
            RAISE EXCEPTION 'New flood trigger evidence must enter as RAW for Data Officer validation';
        END IF;
        RETURN NEW;
    END IF;
    IF (NEW.qc_status IS DISTINCT FROM OLD.qc_status
        OR NEW.qc_by IS DISTINCT FROM OLD.qc_by
        OR NEW.qc_at IS DISTINCT FROM OLD.qc_at)
       AND (NOT pg_has_role(SESSION_USER, 'few_data_officer', 'member')
            OR NEW.qc_by IS DISTINCT FROM SESSION_USER
            OR NEW.qc_at IS NULL) THEN
        RAISE EXCEPTION 'Only a Data Officer may record flood-trigger QC';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog, clean;

CREATE TRIGGER trg_enforce_flood_trigger_qc
BEFORE INSERT OR UPDATE ON clean.flood_alert_triggers
FOR EACH ROW EXECUTE FUNCTION clean.enforce_flood_trigger_qc();

CREATE OR REPLACE FUNCTION clean.enforce_flood_event_verification()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        IF NEW.verification_status <> 'unverified'
           OR NEW.verified_by IS NOT NULL OR NEW.verified_at IS NOT NULL THEN
            RAISE EXCEPTION 'Field-submitted flood events must enter as unverified';
        END IF;
        RETURN NEW;
    END IF;
    IF NEW.verification_status IS DISTINCT FROM OLD.verification_status
       OR NEW.verified_by IS DISTINCT FROM OLD.verified_by
       OR NEW.verified_at IS DISTINCT FROM OLD.verified_at THEN
        IF NOT pg_has_role(SESSION_USER, 'few_data_officer', 'member')
           OR NEW.verified_by IS DISTINCT FROM SESSION_USER
           OR NEW.verified_at IS NULL THEN
            RAISE EXCEPTION 'Only a Data Officer may verify a flood event';
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_enforce_flood_event_verification
BEFORE INSERT OR UPDATE ON clean.flood_events
FOR EACH ROW EXECUTE FUNCTION clean.enforce_flood_event_verification();

CREATE VIEW clean.flood_released_alerts AS
SELECT alert_id, issued_at, state_code, lga_id, warning_level, trigger_type,
       hazard_score, confidence, status, released_at, notes
FROM clean.flood_alerts
WHERE status = 'released';

CREATE VIEW clean.flood_released_alert_areas AS
SELECT area.alert_area_id, area.alert_id, area.state_code, area.lga_id,
       area.community_id, area.affected_area_sqkm, area.exposed_population,
       area.exposed_households, area.exposed_critical_assets, area.geom,
       area.assessed_at, area.confidence
FROM clean.flood_alert_areas AS area
JOIN clean.flood_alerts AS alert USING (alert_id)
WHERE alert.status = 'released';

CREATE VIEW clean.flood_published_warning_performance AS
SELECT performance_id, alert_id, evaluated_at, lead_time_hours,
       recipient_count, reached_count, acknowledgement_count, hit_status,
       alerted_extent_sqkm, observed_extent_sqkm, high_risk_communities,
       communities_reached, audit_completeness_pct, confidence
FROM clean.flood_warning_performance
WHERE publication_status = 'approved';

CREATE VIEW clean.flood_published_awareness_summary AS
SELECT community_id, COUNT(*) AS activity_count,
       SUM(audience_count) AS audience_count, SUM(reach_count) AS reach_count,
       MAX(conducted_at) AS latest_activity
FROM clean.flood_awareness
WHERE publication_status = 'approved'
GROUP BY community_id;

CREATE OR REPLACE FUNCTION clean.enforce_flood_performance_publication()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'INSERT' AND NEW.publication_status <> 'restricted')
       OR (TG_OP = 'UPDATE' AND NEW.publication_status IS DISTINCT FROM OLD.publication_status) THEN
        IF NOT pg_has_role(SESSION_USER, 'few_authorised_releaser', 'member') THEN
            RAISE EXCEPTION 'Only an authorised releaser may publish a warning-performance evaluation';
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_enforce_flood_performance_publication
BEFORE INSERT OR UPDATE ON clean.flood_warning_performance
FOR EACH ROW EXECUTE FUNCTION clean.enforce_flood_performance_publication();

CREATE OR REPLACE FUNCTION clean.enforce_flood_awareness_publication()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'INSERT' AND NEW.publication_status <> 'restricted')
       OR (TG_OP = 'UPDATE' AND NEW.publication_status IS DISTINCT FROM OLD.publication_status) THEN
        IF NOT pg_has_role(SESSION_USER, 'few_authorised_releaser', 'member') THEN
            RAISE EXCEPTION 'Only an authorised releaser may publish community-awareness records';
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_enforce_flood_awareness_publication
BEFORE INSERT OR UPDATE ON clean.flood_awareness
FOR EACH ROW EXECUTE FUNCTION clean.enforce_flood_awareness_publication();

GRANT USAGE ON SCHEMA clean TO few_field_officer, few_data_officer,
    few_technical_officer, few_authorised_releaser, few_management_viewer;
GRANT USAGE ON SCHEMA audit TO few_data_officer, few_technical_officer,
    few_authorised_releaser;
GRANT SELECT ON clean.flood_alerts, clean.flood_alert_triggers,
    clean.flood_alert_areas, clean.flood_events TO few_data_officer, few_technical_officer;
GRANT UPDATE (qc_status, qc_by, qc_at, qc_reason)
    ON clean.flood_alert_triggers TO few_data_officer;
GRANT INSERT ON clean.flood_alerts TO few_technical_officer;
GRANT INSERT ON clean.flood_alert_triggers, clean.flood_alert_areas
    TO few_technical_officer;
GRANT UPDATE (status, reviewed_by, reviewed_at, notes, updated_at)
    ON clean.flood_alerts TO few_technical_officer;
GRANT SELECT ON clean.flood_alerts TO few_authorised_releaser;
GRANT UPDATE (status, approved_by, approved_at, released_by, released_at, issued_at,
    expired_by, expired_at, cancelled_by, cancelled_at, cancellation_reason, updated_at)
    ON clean.flood_alerts TO few_authorised_releaser;
GRANT SELECT ON clean.flood_released_alerts, clean.flood_released_alert_areas
    TO few_field_officer, few_management_viewer;
GRANT INSERT ON clean.flood_warning_performance TO few_technical_officer;
GRANT UPDATE (publication_status) ON clean.flood_warning_performance
    TO few_authorised_releaser;
GRANT UPDATE (publication_status) ON clean.flood_awareness
    TO few_authorised_releaser;
GRANT SELECT (performance_id, publication_status) ON clean.flood_warning_performance
    TO few_authorised_releaser;
GRANT SELECT (awareness_id, publication_status) ON clean.flood_awareness
    TO few_authorised_releaser;
GRANT SELECT ON clean.flood_published_warning_performance TO few_management_viewer;
GRANT SELECT ON clean.flood_published_awareness_summary TO few_management_viewer;
GRANT INSERT ON clean.flood_events, clean.flood_impacts, clean.flood_awareness,
    clean.flood_drills, clean.flood_acknowledgements, clean.flood_notifications
    TO few_field_officer;
GRANT UPDATE (verification_status, verified_by, verified_at, false_alarm_reason)
    ON clean.flood_events TO few_data_officer;
GRANT SELECT ON audit.audit_trail TO few_data_officer, few_technical_officer,
    few_authorised_releaser;

CREATE OR REPLACE FUNCTION audit.log_flood_cam_change()
RETURNS TRIGGER AS $$
DECLARE
    row_data JSONB;
    record_id TEXT;
BEGIN
    row_data := CASE WHEN TG_OP = 'DELETE' THEN to_jsonb(OLD) ELSE to_jsonb(NEW) END;
    record_id := COALESCE(
        row_data->>'alert_id', row_data->>'trigger_id', row_data->>'alert_area_id',
        row_data->>'notification_id', row_data->>'acknowledgement_id',
        row_data->>'awareness_id', row_data->>'drill_id', row_data->>'flood_event_id',
        row_data->>'impact_id', row_data->>'performance_id'
    );
    INSERT INTO audit.audit_trail (
        table_name, record_pk, column_name, original_value, corrected_value, reason, user_name
    ) VALUES (
        TG_TABLE_SCHEMA || '.' || TG_TABLE_NAME,
        record_id,
        '*',
        CASE WHEN TG_OP IN ('UPDATE', 'DELETE') THEN to_jsonb(OLD)::TEXT END,
        CASE WHEN TG_OP IN ('INSERT', 'UPDATE') THEN to_jsonb(NEW)::TEXT END,
        'FEW-CAM ' || TG_OP,
        SESSION_USER
    );
    RETURN CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog, audit, clean;

CREATE TRIGGER trg_audit_flood_alerts AFTER INSERT OR UPDATE OR DELETE ON clean.flood_alerts
FOR EACH ROW EXECUTE FUNCTION audit.log_flood_cam_change();
CREATE TRIGGER trg_audit_flood_alert_triggers AFTER INSERT OR UPDATE OR DELETE ON clean.flood_alert_triggers
FOR EACH ROW EXECUTE FUNCTION audit.log_flood_cam_change();
CREATE TRIGGER trg_audit_flood_alert_areas AFTER INSERT OR UPDATE OR DELETE ON clean.flood_alert_areas
FOR EACH ROW EXECUTE FUNCTION audit.log_flood_cam_change();
CREATE TRIGGER trg_audit_flood_notifications AFTER INSERT OR UPDATE OR DELETE ON clean.flood_notifications
FOR EACH ROW EXECUTE FUNCTION audit.log_flood_cam_change();
CREATE TRIGGER trg_audit_flood_acknowledgements AFTER INSERT OR UPDATE OR DELETE ON clean.flood_acknowledgements
FOR EACH ROW EXECUTE FUNCTION audit.log_flood_cam_change();
CREATE TRIGGER trg_audit_flood_awareness AFTER INSERT OR UPDATE OR DELETE ON clean.flood_awareness
FOR EACH ROW EXECUTE FUNCTION audit.log_flood_cam_change();
CREATE TRIGGER trg_audit_flood_drills AFTER INSERT OR UPDATE OR DELETE ON clean.flood_drills
FOR EACH ROW EXECUTE FUNCTION audit.log_flood_cam_change();
CREATE TRIGGER trg_audit_flood_events AFTER INSERT OR UPDATE OR DELETE ON clean.flood_events
FOR EACH ROW EXECUTE FUNCTION audit.log_flood_cam_change();
CREATE TRIGGER trg_audit_flood_impacts AFTER INSERT OR UPDATE OR DELETE ON clean.flood_impacts
FOR EACH ROW EXECUTE FUNCTION audit.log_flood_cam_change();
CREATE TRIGGER trg_audit_flood_warning_performance AFTER INSERT OR UPDATE OR DELETE ON clean.flood_warning_performance
FOR EACH ROW EXECUTE FUNCTION audit.log_flood_cam_change();

-- =============================================================================
-- 6. IMMUTABLE RAW LANDING TABLES (RAW SCHEMA)
-- =============================================================================

CREATE TABLE raw.submissions_landing (
    raw_submission_id BIGSERIAL PRIMARY KEY,
    source_system   VARCHAR(50) NOT NULL, -- KoboToolbox, ODK, Excel_Ingest
    form_id         VARCHAR(100) NOT NULL,
    payload_json    JSONB NOT NULL,
    received_at     TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    processed_status VARCHAR(20) DEFAULT 'PENDING'
);

-- Trigger to prevent any updates or deletions in raw schema (Immutable rule)
CREATE OR REPLACE FUNCTION raw.reject_raw_modifications()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'RAW landing tables are immutable. Updates and deletes are prohibited by CHER-CDSS Rule 41.2.';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_immutable_raw
BEFORE UPDATE OR DELETE ON raw.submissions_landing
FOR EACH ROW EXECUTE FUNCTION raw.reject_raw_modifications();

-- =============================================================================
-- 7. SPATIAL & PERFORMANCE INDEXES
-- =============================================================================

CREATE INDEX idx_community_geom ON clean.community_master USING GIST(geom);
CREATE INDEX idx_erosion_geom ON clean.erosion_sites USING GIST(geom);
CREATE INDEX idx_facility_geom ON clean.facility_master USING GIST(geom);
CREATE INDEX idx_station_geom ON clean.climate_station USING GIST(geom);
CREATE INDEX idx_infra_geom ON clean.infrastructure USING GIST(geom);
CREATE INDEX idx_flood_geom ON clean.flood_events USING GIST(geom);
CREATE INDEX idx_ward_geom ON clean.ward_master USING GIST(geom);

CREATE INDEX idx_comm_state_lga ON clean.community_master(state_code, lga_id);
CREATE INDEX idx_ero_community ON clean.erosion_sites(community_id);
-- =============================================================================
-- 8. NATIONAL ENVIRONMENTAL PROBLEMS TAXONOMY & SPATIAL REGISTER (G65)
-- =============================================================================

CREATE TABLE clean.lkp_environmental_problems (
    problem_id          VARCHAR(10) PRIMARY KEY, -- EP01..EP12
    problem_code        VARCHAR(30) UNIQUE NOT NULL,
    problem_name        VARCHAR(60) NOT NULL,
    symbol_type         VARCHAR(30) NOT NULL,
    symbol_shape        VARCHAR(30) NOT NULL,
    symbol_color_hex    VARCHAR(10) NOT NULL,
    symbol_char         VARCHAR(10) NOT NULL,
    category            VARCHAR(40) NOT NULL,
    primary_risk_comp   VARCHAR(50) NOT NULL,
    related_domain_code VARCHAR(20),
    gis_layer_code      VARCHAR(20) DEFAULT 'G65',
    photo_legend_order  INTEGER NOT NULL,
    description         TEXT NOT NULL,
    key_affected_states TEXT
);

CREATE TABLE clean.g65_environmental_problems (
    record_id           VARCHAR(20) PRIMARY KEY,
    state_code          VARCHAR(10) NOT NULL,
    state_name          VARCHAR(50) NOT NULL,
    problem_code        VARCHAR(30) NOT NULL REFERENCES clean.lkp_environmental_problems(problem_code),
    problem_name        VARCHAR(60) NOT NULL,
    severity_level      VARCHAR(20) NOT NULL,
    observed_source     VARCHAR(100) NOT NULL,
    validation_status   VARCHAR(50) DEFAULT 'Validated',
    notes               TEXT,
    geom                geometry(Point, 4326) NOT NULL
);

CREATE INDEX idx_g65_geom ON clean.g65_environmental_problems USING GIST(geom);
CREATE INDEX idx_g65_state_prob ON clean.g65_environmental_problems(state_code, problem_code);

-- End of CHER-CDSS v4.1 DDL
