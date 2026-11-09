@echo off
title "CHER-CDSS Data Update and Ingestion Controller - N-HYPPADEC"
echo ======================================================================
echo   N-HYPPADEC CHER-CDSS DATA UPDATE CONTROLLER (v4.2)
echo ======================================================================

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found at .venv\Scripts\python.exe
    pause
    exit /b 1
)

if "%1"=="--auto" goto AUTO_UPDATE
if "%1"=="--kobo" goto CLI_KOBO
if "%1"=="--pipeline" goto CLI_PIPELINE
if "%1"=="--verify" goto CLI_VERIFY

:MENU
echo.
echo Select an update action:
echo   [1] Sync & Ingest Mobile Field Surveys (KoboToolbox / ODK 5-Gate QC)
echo   [2] Process Raw Data Files (01_ingest -^> 02_validate -^> 03_clean -^> 04_integrate)
echo   [3] Recompute Risk & Priority Area Rankings (13_risk -^> 15_priority)
echo   [4] Run Full End-to-End Pipeline (Stages 01 to 26)
echo   [5] Run Verification & Acceptance Test Suite
echo   [6] Exit
echo.
set /p opt="Enter choice [1-6]: "

if "%opt%"=="1" goto KOBO_SYNC
if "%opt%"=="2" goto PROCESS_RAW
if "%opt%"=="3" goto RISK_PRIORITY
if "%opt%"=="4" goto FULL_PIPELINE
if "%opt%"=="5" goto RUN_TESTS
if "%opt%"=="6" exit /b 0
goto MENU

:KOBO_SYNC
echo.
echo [1/1] Running KoboToolbox / ODK Ingestion & 5-Gate Quality Pipeline...
.venv\Scripts\python.exe 02_Fieldwork\kobo_sync_pipeline.py
echo.
echo Kobo sync completed. Check the dashboard 'Field Ops' tab to review quarantine records.
pause
goto MENU

:PROCESS_RAW
echo.
echo [1/4] Running 01_ingest.py...
.venv\Scripts\python.exe 05_Analysis\02_SCRIPTS\01_ingest.py
if errorlevel 1 goto FAILED

echo [2/4] Running 02_validate.py...
.venv\Scripts\python.exe 05_Analysis\02_SCRIPTS\02_validate.py
if errorlevel 1 goto FAILED

echo [3/4] Running 03_clean.py...
.venv\Scripts\python.exe 05_Analysis\02_SCRIPTS\03_clean.py
if errorlevel 1 goto FAILED

echo [4/4] Running 04_integrate.py...
.venv\Scripts\python.exe 05_Analysis\02_SCRIPTS\04_integrate.py
if errorlevel 1 goto FAILED

echo.
echo [SUCCESS] Raw data ingestion, validation, cleaning, and spatial integration complete.
pause
goto MENU

:RISK_PRIORITY
echo.
echo [1/2] Recomputing Master Composite Risk (13_risk.py)...
.venv\Scripts\python.exe 05_Analysis\02_SCRIPTS\13_risk.py
if errorlevel 1 goto FAILED

echo [2/2] Recomputing Top Priority Areas (15_priority.py)...
.venv\Scripts\python.exe 05_Analysis\02_SCRIPTS\15_priority.py
if errorlevel 1 goto FAILED

echo.
echo [SUCCESS] Risk scores and Top-20 Priority Area registers successfully updated.
pause
goto MENU

:FULL_PIPELINE
echo.
echo Running Full End-to-End Analysis Pipeline (Stages 01 to 26)...
.venv\Scripts\python.exe 05_Analysis\02_SCRIPTS\run_pipeline.py --extended
if errorlevel 1 goto FAILED
echo.
echo [SUCCESS] Full pipeline execution completed successfully.
pause
goto MENU

:RUN_TESTS
echo.
echo Running CHER-CDSS Test Suite...
.venv\Scripts\python.exe 05_Analysis\02_SCRIPTS\test_pipeline.py --quick
.venv\Scripts\python.exe scratch\test_ai_integration.py
pause
goto MENU

:AUTO_UPDATE
echo [AUTO] Running Scheduled Data Ingestion & Risk Recomputation...
.venv\Scripts\python.exe 02_Fieldwork\kobo_sync_pipeline.py
.venv\Scripts\python.exe 05_Analysis\02_SCRIPTS\04_integrate.py
.venv\Scripts\python.exe 05_Analysis\02_SCRIPTS\13_risk.py
.venv\Scripts\python.exe 05_Analysis\02_SCRIPTS\15_priority.py
exit /b %errorlevel%

:CLI_KOBO
.venv\Scripts\python.exe 02_Fieldwork\kobo_sync_pipeline.py
exit /b %errorlevel%

:CLI_PIPELINE
.venv\Scripts\python.exe 05_Analysis\02_SCRIPTS\run_pipeline.py --extended
exit /b %errorlevel%

:CLI_VERIFY
.venv\Scripts\python.exe 05_Analysis\02_SCRIPTS\test_pipeline.py --quick
.venv\Scripts\python.exe scratch\test_ai_integration.py
exit /b %errorlevel%

:FAILED
echo.
echo [ERROR] Pipeline step halted due to critical QC failure or exception.
echo Please review log outputs in 00_Project_Control/PROCESSING_STATUS.csv.
pause
exit /b 1
