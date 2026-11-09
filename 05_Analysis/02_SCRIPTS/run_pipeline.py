"""
run_pipeline.py
===============
Master pipeline controller for the N-HYPPADEC GIS Decision-Support System.

Executes all 18 processing modules in dependency order.
Halts immediately on any critical QC failure — downstream modules
are NOT run until the upstream failure is resolved.

Usage:
    python run_pipeline.py                     # Full pipeline
    python run_pipeline.py --from 05_climate   # Resume from a module
    python run_pipeline.py --only 13_risk      # Run a single module
    python run_pipeline.py --dry-run           # Show execution plan only

Exit codes:
    0  — Pipeline completed successfully
    1  — Pipeline halted on critical QC failure
    2  — Pipeline halted on unhandled exception
    3  — Dry run (no execution)

Build dependency order (specification Section 3):
  Administrative boundaries → Communities → Rivers/Basins → Hydropower →
  Terrain → Environment → Infrastructure → Climate →
  Observed flood/erosion → Hazard → Exposure → Vulnerability →
  Criticality → Risk → Adaptation → Priority
"""

import argparse
import sys
import traceback
from datetime import datetime, date
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# PipelineCriticalError — raised by any module on critical QC failure
# ---------------------------------------------------------------------------

class PipelineCriticalError(RuntimeError):
    """
    Raised when a critical QC check fails.
    The pipeline halts — no downstream module is executed.
    Fix the failure and re-run the pipeline from the failed step.
    """
    pass


# ---------------------------------------------------------------------------
# Pipeline step definition
# ---------------------------------------------------------------------------

class PipelineStep:
    def __init__(
        self,
        step_id: str,
        name: str,
        module_fn: Callable,
        upstream_asset_ids: List[str],
        description: str,
    ):
        self.step_id            = step_id
        self.name               = name
        self.module_fn          = module_fn
        self.upstream_asset_ids = upstream_asset_ids
        self.description        = description
        self.status             = "PENDING"   # PENDING | RUNNING | PASSED | FAILED | SKIPPED
        self.start_time         = None
        self.end_time           = None
        self.error_message      = None

    @property
    def elapsed_seconds(self) -> Optional[float]:
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None


# ---------------------------------------------------------------------------
# Pipeline orchestrator
# ---------------------------------------------------------------------------

class Pipeline:
    def __init__(self, steps: List[PipelineStep]):
        self.steps      = steps
        self.step_index = {s.step_id: s for s in steps}
        self.run_start  = None
        self.run_end    = None

    def run(
        self,
        from_step: Optional[str] = None,
        only_step: Optional[str] = None,
        dry_run:   bool = False,
    ) -> int:
        """
        Execute pipeline steps in order.
        Returns exit code (0 = success, 1 = critical failure, 2 = exception).
        """
        from logger import get_logger, log_separator
        log = get_logger("run_pipeline")
        self.run_start = datetime.now()

        # Determine which steps to run
        if only_step:
            steps_to_run = [s for s in self.steps if s.step_id == only_step]
            if not steps_to_run:
                log.error(f"Step '{only_step}' not found. "
                          f"Available: {[s.step_id for s in self.steps]}")
                return 2
        elif from_step:
            ids = [s.step_id for s in self.steps]
            if from_step not in ids:
                log.error(f"Step '{from_step}' not found.")
                return 2
            start_idx    = ids.index(from_step)
            steps_to_run = self.steps[start_idx:]
        else:
            steps_to_run = self.steps

        # Show execution plan
        log_separator(log, "N-HYPPADEC PIPELINE — EXECUTION PLAN")
        log.info(f"Run date:    {date.today().isoformat()}")
        log.info(f"Steps:       {len(steps_to_run)}/{len(self.steps)} total")
        log.info(f"Dry run:     {dry_run}")
        log.info("")
        for i, step in enumerate(steps_to_run, 1):
            log.info(f"  [{i:02d}] {step.step_id:20s} — {step.description}")
        log.info("")

        if dry_run:
            log.info("DRY RUN — no modules executed.")
            return 3

        # Execute
        log_separator(log, "PIPELINE EXECUTION")
        failed_steps = []

        for step in steps_to_run:
            log.info(f"\n{'='*60}")
            log.info(f"STEP: {step.step_id} — {step.description}")
            log.info(f"{'='*60}")

            step.status     = "RUNNING"
            step.start_time = datetime.now()

            try:
                step.module_fn()
                step.status   = "PASSED"
                step.end_time = datetime.now()
                log.info(
                    f"✓ PASSED: {step.step_id} "
                    f"({step.elapsed_seconds:.1f}s)"
                )

            except PipelineCriticalError as exc:
                step.status        = "FAILED"
                step.end_time      = datetime.now()
                step.error_message = str(exc)
                failed_steps.append(step)

                log.error(f"\n{'!'*60}")
                log.error(f"CRITICAL QC FAILURE: {step.step_id}")
                log.error(f"  {exc}")
                log.error(f"{'!'*60}")
                log.error(
                    "\nPIPELINE HALTED.\n"
                    "Downstream modules will NOT run until this failure is resolved.\n"
                    f"Fix the issue in {step.step_id} and re-run:\n"
                    f"  python run_pipeline.py --from {step.step_id}"
                )

                self.run_end = datetime.now()
                self._print_summary(steps_to_run, log)
                return 1

            except Exception as exc:
                step.status        = "FAILED"
                step.end_time      = datetime.now()
                step.error_message = str(exc)
                failed_steps.append(step)

                log.error(f"\nUNHANDLED EXCEPTION in {step.step_id}:")
                log.error(traceback.format_exc())

                self.run_end = datetime.now()
                self._print_summary(steps_to_run, log)
                return 2

        self.run_end = datetime.now()
        self._print_summary(steps_to_run, log)

        if not failed_steps:
            log.info("\n✓ PIPELINE COMPLETE — all steps passed.")
            return 0
        return 1

    def _print_summary(self, steps: List[PipelineStep], log) -> None:
        """Print final execution summary."""
        elapsed = (self.run_end - self.run_start).total_seconds() if self.run_end else 0
        passed  = sum(1 for s in steps if s.status == "PASSED")
        failed  = sum(1 for s in steps if s.status == "FAILED")
        pending = sum(1 for s in steps if s.status == "PENDING")

        log.info(f"\n{'='*60}")
        log.info("PIPELINE SUMMARY")
        log.info(f"{'='*60}")
        log.info(f"  Total elapsed:  {elapsed:.1f}s ({elapsed/60:.1f} min)")
        log.info(f"  Steps passed:   {passed}")
        log.info(f"  Steps failed:   {failed}")
        log.info(f"  Steps pending:  {pending}")
        log.info("")
        for step in steps:
            icon    = "✓" if step.status == "PASSED" else \
                      "✗" if step.status == "FAILED" else \
                      "·" if step.status == "PENDING" else "▶"
            elapsed_str = f"{step.elapsed_seconds:.1f}s" if step.elapsed_seconds else "—"
            log.info(f"  {icon} {step.step_id:20s} {step.status:10s} {elapsed_str}")
            if step.error_message:
                log.info(f"      ↳ {step.error_message[:120]}")


# ---------------------------------------------------------------------------
# Build the full pipeline step sequence
# ---------------------------------------------------------------------------

def build_pipeline(include_extended: bool = False) -> Pipeline:
    """
    Construct the pipeline in dependency order.
    Returns 18 core steps by default, or all 22 steps when include_extended=True.
    Each step imports its module function lazily to avoid circular imports.
    """

    def _run(module_name: str, fn_name: str = "run_all") -> Callable:
        """Lazy import wrapper — imports module only when step executes."""
        def _exec():
            import importlib
            mod = importlib.import_module(module_name)
            getattr(mod, fn_name)()
        return _exec

    steps = [
        PipelineStep(
            "01_ingest", "Source Registration and Ingestion",
            _run("01_ingest"),
            upstream_asset_ids=[],
            description="Register sources; ingest raw data files",
        ),
        PipelineStep(
            "02_validate", "Database QC — Structural/Referential/Coordinate",
            _run("02_validate"),
            upstream_asset_ids=[],
            description="Q01-Q10 QC checks on DB01-DB06; halt on critical failure",
        ),
        PipelineStep(
            "03_clean", "Promote Validated Datasets to CLEAN",
            _run("03_clean"),
            upstream_asset_ids=["DB01","DB02","DB03","DB04","DB05","DB06"],
            description="Consent gate; code standardisation; write CLEAN CSVs",
        ),
        PipelineStep(
            "04_integrate", "Spatial Joins and DB-to-GIS Sync",
            _run("04_integrate"),
            upstream_asset_ids=["DB01","DB03","DB06"],
            description="SJ01-SJ12; derive hydropower distance; rebuild G03/G19/G26",
        ),
        PipelineStep(
            "05_climate", "Climate Data Processing",
            _run("05_climate"),
            upstream_asset_ids=["DB05"],
            description="Temporal aggregation; extreme events; G21 station summary",
        ),
        PipelineStep(
            "06_flood", "Flood Indicator Computation",
            _run("06_flood"),
            upstream_asset_ids=["DB01"],
            description="IND01 flood frequency; IND02 flood severity",
        ),
        PipelineStep(
            "07_erosion", "Erosion Indicator Computation",
            _run("07_erosion"),
            upstream_asset_ids=["DB03"],
            description="IND03 erosion severity; IND04 river proximity; G27 hotspots",
        ),
        PipelineStep(
            "08_hydropower", "Hydropower Indicator Computation",
            _run("08_hydropower"),
            upstream_asset_ids=["DB04"],
            description="IND07 electricity disruption; IND08 hydropower disruption; G28",
        ),
        PipelineStep(
            "09_exposure", "Exposure Index (G29, G30, G32)",
            _run("09_exposure"),
            upstream_asset_ids=["DB01","DB03","DB06"],
            description="Flood exposure; erosion exposure; E_Score 0-100",
        ),
        PipelineStep(
            "10_vulnerability", "Vulnerability Index (G33)",
            _run("10_vulnerability"),
            upstream_asset_ids=["DB01"],
            description="IND09 inverted; DB02 aggregated; V_Score 0-100",
        ),
        PipelineStep(
            "11_criticality", "Criticality Index (G34)",
            _run("11_criticality"),
            upstream_asset_ids=["DB01","DB06"],
            description="IND08 NULL outside BUF004; C_Score 0-100",
        ),
        PipelineStep(
            "12_hazard", "Hazard Index (G31) + G25 Validation",
            _run("12_hazard"),
            upstream_asset_ids=["DB01","DB03"],
            description="IND01-IND04 weighted; validate against G25; halt if < 70% pass",
        ),
        PipelineStep(
            "13_risk", "Composite Risk Index (G35)",
            _run("13_risk"),
            upstream_asset_ids=["G31","G32","G33","G34"],
            description="R = 0.35H + 0.25E + 0.25V + 0.15C; S1/S2 sensitivity models",
        ),
        PipelineStep(
            "14_adaptation", "Adaptation Inventory (G36)",
            _run("14_adaptation"),
            upstream_asset_ids=["DB01","DB06"],
            description="Adaptation categories; IND09 raw; IND10 if formula approved",
        ),
        PipelineStep(
            "15_priority", "Priority Areas (G37)",
            _run("15_priority"),
            upstream_asset_ids=["G35","G36"],
            description="Priority_Score = 0.70R + 0.30IND10; tier/rank; top-20 list",
        ),
        PipelineStep(
            "16_qc", "Cross-Cutting QC (Q11-Q20)",
            _run("16_qc"),
            upstream_asset_ids=[],
            description="Privacy; provenance; version; enumerator; cross-DB; geom sync",
        ),
        PipelineStep(
            "17_reports", "Analytical Tables and Profiles",
            _run("17_reports"),
            upstream_asset_ids=["G35","G37"],
            description="Community profiles; state summaries; descriptive stats; risk dist",
        ),
        PipelineStep(
            "18_maps", "Map Register and Export Preparation",
            _run("18_maps"),
            upstream_asset_ids=[],
            description="27-map register; QGIS-ready GeoJSON; cartographic checklists",
        ),
        # ── Environmental domain extensions (v2.0) ──────────────────────────
        PipelineStep(
            "20_climate_change", "Climate Change Indicators (IND11–13, G38–G42)",
            _run("20_climate_change"),
            upstream_asset_ids=["DB05"],
            description="Rainfall/temperature trends; SPI drought frequency; CC_Score",
        ),
        PipelineStep(
            "21_flooding", "Multi-Return-Period Flood Model (G43–G46)",
            _run("21_flooding"),
            upstream_asset_ids=["DB05","DB01"],
            description="Gumbel RP rainfall; HAND inundation; FL_Score per community",
        ),
        PipelineStep(
            "22_land_degradation", "Land Degradation — NDVI + RUSLE (G47–G50)",
            _run("22_land_degradation"),
            upstream_asset_ids=["DB01"],
            description="NDVI trend IND15; RUSLE soil loss IND16; LD_Score",
        ),
        PipelineStep(
            "23_deforestation", "Deforestation Pressure Index (G51–G54)",
            _run("23_deforestation"),
            upstream_asset_ids=["DB01"],
            description="Hansen GFC IND17; deforestation pressure DF_Score",
        ),
        PipelineStep(
            "24_waste_pollution", "Waste Pollution Exposure (G55–G58)",
            _run("24_waste_pollution"),
            upstream_asset_ids=["DB01"],
            description="DB08 waste sites; leachate IND18–19; WP_Score",
        ),
        PipelineStep(
            "25_biodiversity", "Biodiversity Loss Index (G59–G63)",
            _run("25_biodiversity"),
            upstream_asset_ids=["DB01"],
            description="Habitat integrity IND20; PA coverage IND21; BL_Score",
        ),
        PipelineStep(
            "26_eri", "Environmental Risk Index v2.0 (G64)",
            _run("26_eri"),
            upstream_asset_ids=["G31","G32","G33","G34"],
            description="ERI = 0.25H+0.15E+0.15V+0.10C+0.10CC+0.08LD+0.07DF+0.05WP+0.05BL",
        ),
    ]

    if include_extended:
        steps.extend([
            PipelineStep(
                "19_scenarios", "Scenario Modelling & Stress Testing",
                _run("19_scenarios"),
                upstream_asset_ids=["G35"],
                description="Stage 21: Climate stress (+15% rain), land degradation, adaptation investment",
            ),
            PipelineStep(
                "20_interventions_mrv", "Interventions & MRV Outcome Evaluation",
                _run("20_interventions_mrv"),
                upstream_asset_ids=["G35","G36"],
                description="Stage 15: IES calculation under Section 34 rules; residual risk; MRV portfolio",
            ),
            PipelineStep(
                "21_remote_sensing", "Remote Sensing & Earth Observation Analytics",
                _run("21_remote_sensing"),
                upstream_asset_ids=["DB01","DB03"],
                description="Stage 9: Sentinel SAR flood inundation; NDVI vegetation anomalies; riverbank retreat",
            ),
            PipelineStep(
                "generate_gis_layers", "Production GIS Vector Layers Generation",
                _run("generate_gis_layers"),
                upstream_asset_ids=["G01","G02","G03","G35","G37"],
                description="Generate QGIS-ready GeoJSON layers in 04_GIS/02_CLEAN and 04_GIS/03_DERIVED",
            ),
        ])

    return Pipeline(steps)


# ---------------------------------------------------------------------------
# Pipeline state persistence — saves/loads run state for resume
# ---------------------------------------------------------------------------

def save_pipeline_state(pipeline: Pipeline, state_path: Path) -> None:
    """Save current step statuses to a CSV for resume support."""
    import csv
    rows = []
    for step in pipeline.steps:
        rows.append({
            "step_id":       step.step_id,
            "status":        step.status,
            "start_time":    step.start_time.isoformat() if step.start_time else "",
            "end_time":      step.end_time.isoformat()   if step.end_time   else "",
            "error_message": step.error_message or "",
        })
    state_path.parent.mkdir(parents=True, exist_ok=True)
    with open(state_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


# ---------------------------------------------------------------------------
# CLI argument parsing
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "N-HYPPADEC GIS Pipeline Master Controller\n"
            "Executes all 18 processing modules in dependency order.\n"
            "Halts on any critical QC failure."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--from",
        dest="from_step",
        metavar="STEP_ID",
        help="Resume pipeline from this step (e.g. 05_climate)",
    )
    parser.add_argument(
        "--only",
        dest="only_step",
        metavar="STEP_ID",
        help="Run only this single step",
    )
    parser.add_argument(
        "--dry-run",
        dest="dry_run",
        action="store_true",
        help="Show execution plan without running any steps",
    )
    parser.add_argument(
        "--list",
        dest="list_steps",
        action="store_true",
        help="List all available pipeline steps and exit",
    )
    parser.add_argument(
        "--extended", "--all",
        dest="extended",
        action="store_true",
        help="Include extended advanced modules (19_scenarios, 20_interventions_mrv, 21_remote_sensing, generate_gis_layers)",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> int:
    args     = parse_args()
    include_ext = args.extended or (args.only_step in ["19_scenarios", "20_interventions_mrv", "21_remote_sensing", "generate_gis_layers"])
    pipeline = build_pipeline(include_extended=include_ext)

    if args.list_steps:
        print("\nAvailable pipeline steps:")
        print(f"{'Step ID':<22} Description")
        print("-" * 70)
        for step in pipeline.steps:
            print(f"{step.step_id:<22} {step.description}")
        print()
        return 0

    from config import ANALYSIS_QC
    state_path = ANALYSIS_QC / f"pipeline_state_{date.today().isoformat()}.csv"

    exit_code = pipeline.run(
        from_step=args.from_step,
        only_step=args.only_step,
        dry_run=args.dry_run,
    )

    # Save state regardless of outcome
    if not args.dry_run:
        try:
            save_pipeline_state(pipeline, state_path)
        except Exception:
            pass  # Don't mask pipeline exit code

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
