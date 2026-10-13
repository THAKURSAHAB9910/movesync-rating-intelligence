# MoveInSync Rating Intelligence — Monthly Monitoring & Rerun Runbook

## 1. Overview of the 10-Step Monthly Investigation Workflow

The monthly investigation engine (`analysis/run_monthly.py`) is designed so product and engineering teams can rerun the exact same investigation every month without double-counting historical reviews or overwriting prior audit trails:

1. **Record Reporting Period & Timestamp**: Logs `reportingPeriod` (`YYYY-MM`) and `executedAtUtc`.
2. **Ingest New Public Evidence**: Collects newly posted public reviews or imports a legitimate JSON/CSV export (`--import-file`).
3. **Preserve Historical Snapshots**: Raw files remain immutable in `data/raw/` and `data/raw/imports/`; historical run summaries are appended to SQLite table `investigation_runs` in `data/movesync_intelligence.db`.
4. **Validate & Deduplicate**: Checks every incoming review against existing `reviewId` UUIDs and 24-char SHA-256 `dedupHash` fingerprints.
5. **Rerun Cleaning, Classification & Prioritization**: Executes `run_full_investigation()` incorporating any human analyst overrides in `data/validation/analyst_overrides.json`.
6. **Month-over-Month & Baseline Comparison**: Compares the target month against both the immediately preceding month and the 12-month verified baseline.
7. **Trajectory Classification**: Labels each theme in the target month as:
   - `New / Emerging`: $0$ mentions in prior month $\rightarrow >0$ in current month.
   - `Worsening`: Month-over-Month share increase $\ge +3.0\text{ pts}$ or $\ge +4.0\text{ pts}$ above 12-month baseline.
   - `Improving`: Month-over-Month share decrease $\le -3.0\text{ pts}$ and below 12-month baseline.
   - `Persistent`: Within $\pm 3.0\text{ pts}$ of prior month.
8. **Reassess #1 Engineering Priority**: Evaluates whether the #1 overall architectural priority (`ISS-01`) or month-specific hotfix priority (`ISS-03` / `ISS-02`) has shifted.
9. **Sync Action Tracking Register**: Merges verified engineering status updates from `data/validation/action_overrides.json`.
10. **Generate Dated Monthly Deliverables**: Outputs `reports/monthly/MoveInSync_Monthly_Investigation_<YYYY_MM>.md` and `.json`.

---

## 2. Manual CLI Execution

Run a monthly investigation for any reporting month (`YYYY-MM`) from the repository root:

```bash
# Rerun monthly investigation for October 2026
python -m analysis.run_monthly --month 2026-10

# Run with a newly exported JSON or CSV review batch
python -m analysis.run_monthly --month 2026-11 --import-file path/to/new_reviews.json

# Regenerate the 8-page Case Study PDF after a monthly update
python -m analysis.generate_report
```

---

## 3. Interactive Dashboard Execution

1. Start the FastAPI server:
   ```bash
   python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
   ```
2. Open `http://127.0.0.1:8000` in your browser.
3. Navigate to **Tab 05 — Monthly Monitoring & Exports** (or click **Run Monthly Audit** in the top header).
4. Select the target month (`2026-08`, `2026-09`, `2026-10`) and click **Execute Monthly Investigation Run**.
5. Click **Download Dated Monthly Report (.md)** to export the generated Markdown report.

---

## 4. Scheduling Instructions (Cron / Windows Task Scheduler)

> **Honesty Note**: No unattended background job is claimed to be active by default on the user's machine. To schedule automated monthly execution on the 1st of every month at 06:00 UTC, use either of the following configurations:

### Option A: Windows Task Scheduler (PowerShell)
```powershell
$Action = New-ScheduledTaskAction -Execute "python" -Argument "-m analysis.run_monthly --month $(Get-Date -Format 'yyyy-MM')" -WorkingDirectory "C:\Users\Vishe\Downloads\MoveInSync"
$Trigger = New-ScheduledTaskTrigger -Monthly -DaysOfMonth 1 -At 6:00AM
Register-ScheduledTask -TaskName "MoveInSync_Monthly_Rating_Intelligence" -Action $Action -Trigger $Trigger -Description "Runs MoveInSync monthly Play Store rating investigation and generates dated report."
```

### Option B: Linux Crontab / CI Runner
```cron
0 6 1 * * cd /path/to/movesync-rating-intelligence && python -m analysis.run_monthly --month $(date +\%Y-\%m) >> logs/monthly_cron.log 2>&1
```
