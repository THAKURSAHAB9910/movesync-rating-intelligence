"""
MoveInSync Rating Intelligence — Repeatable Monthly Investigation Runner
========================================================================
Implements the 10-step monthly investigation workflow:
  1. Record reporting period and collection timestamp.
  2. Collect or import newly available public reviews (live or JSON/CSV import).
  3. Preserve original evidence and historical snapshots in SQLite & data/raw/.
  4. Validate records and deduplicate reviews (reviewId + SHA-256 fallback hash).
  5. Rerun cleaning, theme classification, sentiment analysis, and prioritization.
  6. Compare results with the previous month and established 12-month baseline.
  7. Identify New/Emerging, Persistent, Improving, and Worsening issues.
  8. Reassess the highest-priority issue and check for rank shifts.
  9. Update action tracking using verified implementation statuses.
 10. Generate a dated monthly Markdown & JSON report in reports/monthly/.
"""

import os
import sys
import csv
import json
import sqlite3
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

_PKG_ROOT = Path(__file__).resolve().parent.parent
if str(_PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(_PKG_ROOT))

from analysis.engine import (
    ROOT_DIR,
    run_full_investigation,
    RAW_DIR,
    ANALYTICS_DIR,
    DB_PATH,
)
from analysis.collect_evidence import compute_fallback_hash

MONTHLY_REPORTS_DIR = ROOT_DIR / "reports" / "monthly"


def parse_imported_records(file_path: Path) -> List[Dict[str, Any]]:
    """
    Parse legitimate review export from JSON or CSV into the canonical raw schema
    so it can be validated and deduplicated by `load_and_deduplicate_reviews`.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Import file not found: {file_path}")

    suffix = file_path.suffix.lower()
    records: List[Dict[str, Any]] = []

    if suffix == ".json":
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and "reviews" in data:
            data = data["reviews"]
        if not isinstance(data, list):
            raise ValueError("Imported JSON must be a list of review objects or contain a 'reviews' list.")
        records = data
    elif suffix == ".csv":
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append({
                    "reviewId": row.get("reviewId") or row.get("id") or "",
                    "userName": row.get("userName") or row.get("author") or "ImportedUser",
                    "content": row.get("content") or row.get("text") or "",
                    "score": int(row.get("score") or row.get("rating") or 3),
                    "thumbsUpCount": int(row.get("thumbsUpCount") or row.get("likes") or 0),
                    "reviewCreatedVersion": row.get("reviewCreatedVersion") or row.get("version") or None,
                    "at": row.get("at") or row.get("date") or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
                    "replyContent": row.get("replyContent") or None,
                    "repliedAt": row.get("repliedAt") or None,
                })
    else:
        raise ValueError(f"Unsupported import file format '{suffix}'. Use .json or .csv.")

    # Normalize & validate imported records
    validated: List[Dict[str, Any]] = []
    for r in records:
        content = str(r.get("content") or "").strip()
        score = int(r.get("score") or 3)
        if score < 1 or score > 5:
            score = max(1, min(5, score))
        at_str = str(r.get("at") or r.get("date") or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"))
        if len(at_str) == 10:
            at_str = f"{at_str}T00:00:00"
        dedup_h = compute_fallback_hash(r.get("userName"), content, at_str[:19], score)
        rev_id = str(r.get("reviewId") or "").strip() or f"imp-{dedup_h[:24]}"
        validated.append({
            "reviewId": rev_id,
            "userName": r.get("userName") or "ImportedUser",
            "content": content,
            "score": score,
            "thumbsUpCount": int(r.get("thumbsUpCount") or 0),
            "reviewCreatedVersion": r.get("reviewCreatedVersion") or r.get("appVersion") or None,
            "appVersion": r.get("appVersion") or r.get("reviewCreatedVersion") or None,
            "at": at_str,
            "replyContent": r.get("replyContent"),
            "repliedAt": r.get("repliedAt"),
            "dedupHash": dedup_h,
            "stream": "imported",
            "collectedAtUtc": datetime.now(timezone.utc).isoformat(),
        })
    return validated


def execute_monthly_investigation(
    reporting_month: str = "2026-10",
    import_records: Optional[List[Dict[str, Any]]] = None,
    PersistImportName: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Execute the 10-step monthly investigation workflow for `reporting_month`,
    preserving historical snapshots and outputting a dated monthly report.
    """
    executed_at = datetime.now(timezone.utc).isoformat()
    MONTHLY_REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # Step 2 & 3: If new records are imported, preserve raw snapshot in data/raw/imports/
    if import_records:
        imp_dir = RAW_DIR / "imports"
        imp_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        fname = PersistImportName or f"imported_reviews_{reporting_month}_{stamp}.json"
        with open(imp_dir / fname, "w", encoding="utf-8") as f:
            json.dump(import_records, f, indent=2, ensure_ascii=False)

    # Step 4 & 5: Run deduplication, cleaning, classification, trend analysis, and prioritization
    payload = run_full_investigation(extra_records=None)  # imports in data/raw/imports are auto-loaded

    snapshots = payload["monthlyMonitoring"]["snapshots"]
    if reporting_month not in snapshots:
        # Default to latest available month if requested month has no reviews yet
        available = sorted(snapshots.keys())
        selected_month = available[-1]
    else:
        selected_month = reporting_month

    month_snap = snapshots[selected_month]
    issues_reg = payload["issuesRegister"]
    top_overall = issues_reg[0]
    actions = payload["actionPlanAndTracking"]["actionTrackingRegister"]

    # Step 6 & 7: Classify issues for this month into Worsening, Improving, Persistent, New
    worsening = [i for i in month_snap["issueComparisons"] if i["monthlyStatus"] == "Worsening"]
    improving = [i for i in month_snap["issueComparisons"] if i["monthlyStatus"] == "Improving"]
    persistent = [i for i in month_snap["issueComparisons"] if i["monthlyStatus"] == "Persistent"]
    emerging = [i for i in month_snap["issueComparisons"] if i["monthlyStatus"] == "New / Emerging"]

    # Step 8 & 9: Build dated monthly report payload
    run_id = f"monthly-{selected_month}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    monthly_report = {
        "runId": run_id,
        "reportingPeriod": selected_month,
        "isPartialMonth": month_snap["isPartialMonth"],
        "executedAtUtc": executed_at,
        "previousPeriodCompared": month_snap["previousPeriodCompared"],
        "corpusTotals": {
            "totalUniqueVerifiedReviews": payload["baseline"]["dataCompletenessAndLimitations"]["totalUniqueVerifiedReviews"],
            "duplicatesRemoved": (
                payload["baseline"]["dataCompletenessAndLimitations"]["exactReviewIdOverlapsRemoved"]
                + payload["baseline"]["dataCompletenessAndLimitations"]["fallbackHashOverlapsRemoved"]
            ),
            "importedRecordsCount": payload["baseline"]["dataCompletenessAndLimitations"]["rawImportedCount"],
        },
        "monthMetrics": {
            "totalReviews": month_snap["totalReviews"],
            "meanRating": month_snap["meanRating"],
            "negative12Count": month_snap["negative12Count"],
            "negative12Pct": month_snap["negative12Pct"],
            "negative13Count": month_snap["negative13Count"],
            "substantiveCount": month_snap["substantiveCount"],
            "substantiveMeanRating": month_snap["substantiveMeanRating"],
        },
        "statusBreakdown": {
            "worseningIssues": worsening,
            "improvingIssues": improving,
            "persistentIssues": persistent,
            "emergingIssues": emerging,
        },
        "priorityReassessment": {
            "overallRank1IssueId": top_overall["issueId"],
            "overallRank1Title": top_overall["title"],
            "overallRank1Score": top_overall["priorityScore"],
            "monthTopSoftwareIssue": month_snap["topSoftwareIssueInMonth"],
            "reassessmentDecision": (
                f"Maintain {top_overall['issueId']} ({top_overall['shortName']}, score {top_overall['priorityScore']}/100) as Primary 2-Sprint "
                f"Architectural Initiative while executing urgent Week-1 Hotfixes for month-specific spikes in "
                f"{month_snap['topSoftwareIssueInMonth']['issueId']} ({month_snap['topSoftwareIssueInMonth']['shortName']}, "
                f"{month_snap['topSoftwareIssueInMonth']['currentShareOfNegPct']}% of {selected_month} negative reviews)."
            ),
        },
        "actionTrackerSnapshot": actions,
    }

    # Step 10: Write dated JSON and Markdown reports to reports/monthly/
    json_out = MONTHLY_REPORTS_DIR / f"MoveInSync_Monthly_Investigation_{selected_month.replace('-', '_')}.json"
    md_out = MONTHLY_REPORTS_DIR / f"MoveInSync_Monthly_Investigation_{selected_month.replace('-', '_')}.md"

    with open(json_out, "w", encoding="utf-8") as f:
        json.dump(monthly_report, f, indent=2, ensure_ascii=False)

    md_lines = [
        f"# MoveInSync Rating Intelligence — Monthly Investigation Report ({selected_month})",
        "",
        f"- **Run ID:** `{run_id}`",
        f"- **Execution Timestamp (UTC):** `{executed_at}`",
        f"- **Reporting Period:** `{selected_month}` {'(Month-to-Date Partial Window)' if month_snap['isPartialMonth'] else '(Complete Calendar Month)'}",
        f"- **Compared Against Prior Month:** `{month_snap['previousPeriodCompared']}` and 12-Month Verified Baseline",
        f"- **Total Deduplicated Corpus Size:** `{monthly_report['corpusTotals']['totalUniqueVerifiedReviews']:,}` unique reviews (`{monthly_report['corpusTotals']['duplicatesRemoved']}` cross-stream duplicates removed)",
        "",
        "## 1. Monthly Rating & Volume Summary",
        "",
        "| Metric | Value |",
        "| :--- | :--- |",
        f"| **Written Reviews Collected in `{selected_month}`** | `{month_snap['totalReviews']}` |",
        f"| **All-Review Mean Rating (`{selected_month}`)** | `{month_snap['meanRating']:.2f}★` |",
        f"| **1–2★ Negative Review Share (`{selected_month}`)** | `{month_snap['negative12Pct']}%` (`{month_snap['negative12Count']}` reviews) |",
        f"| **Substantive Reviews ($\\ge 6$ words) Mean Rating** | `{month_snap['substantiveMeanRating']:.2f}★` (`n = {month_snap['substantiveCount']}`) |",
        "",
        "## 2. Month-over-Month Issue Trajectory (`vs Prior Month & 12m Baseline`)",
        "",
        "| Issue ID | Theme | Month Neg Count | Month Share (%) | Prior Month (%) | MoM Delta (pts) | 12m Baseline (%) | Status |",
        "| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |",
    ]
    for ic in month_snap["issueComparisons"]:
        md_lines.append(
            f"| `{ic['issueId']}` | {ic['shortName']} | {ic['currentCount']} | **{ic['currentShareOfNegPct']}%** | "
            f"{ic['previousMonthSharePct']}% | `{ic['deltaMoMPts']:+.1f}` | {ic['baseline12mSharePct']}% | **{ic['monthlyStatus']}** |"
        )

    md_lines.extend([
        "",
        "## 3. Priority Reassessment & Next-Month Engineering Plan",
        "",
        f"- **Primary Architectural Priority (`#1` Overall):** `{top_overall['issueId']}` — *{top_overall['title']}* (`{top_overall['priorityScore']}/100`)",
        f"- **Highest Software Spike in `{selected_month}`:** `{month_snap['topSoftwareIssueInMonth']['issueId']}` — *{month_snap['topSoftwareIssueInMonth']['shortName']}* (`{month_snap['topSoftwareIssueInMonth']['currentShareOfNegPct']}%` of negative reviews in `{selected_month}`)",
        f"- **Decision:** {monthly_report['priorityReassessment']['reassessmentDecision']}",
        "",
        "## 4. Verified Action Tracking Register",
        "",
        "| Action ID | Issue | Owner | Current Status | Verification | Target Evaluation |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |",
    ])
    for act in actions:
        md_lines.append(
            f"| `{act['actionId']}` | `{act['issueId']}` | {act['owner']} | **{act['status']}** | {act['verificationSource']} | {act['targetEvaluationDate']} |"
        )

    with open(md_out, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines) + "\n")

    # Record historical run in SQLite `investigation_runs` table
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT OR REPLACE INTO investigation_runs VALUES (?,?,?,?,?,?,?,?)
        """,
        (
            run_id,
            selected_month,
            executed_at,
            monthly_report["corpusTotals"]["totalUniqueVerifiedReviews"],
            month_snap["meanRating"],
            month_snap["substantiveMeanRating"],
            top_overall["issueId"],
            json.dumps(monthly_report),
        ),
    )
    conn.commit()
    conn.close()

    monthly_report["reportFiles"] = {
        "markdownPath": str(md_out.relative_to(ROOT_DIR)).replace("\\", "/"),
        "jsonPath": str(json_out.relative_to(ROOT_DIR)).replace("\\", "/"),
    }
    return monthly_report


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Run MoveInSync Monthly Rating Intelligence Workflow")
    parser.add_argument("--month", default="2026-10", help="Target reporting month (YYYY-MM), e.g., 2026-08, 2026-09, 2026-10")
    parser.add_argument("--import-file", default=None, help="Optional path to JSON/CSV review export to import and deduplicate")
    args = parser.parse_args()

    imported = None
    if args.import_file:
        imported = parse_imported_records(Path(args.import_file))
        print(f"Loaded {len(imported)} records from {args.import_file}")

    report = execute_monthly_investigation(reporting_month=args.month, import_records=imported)
    print(f"=== MONTHLY INVESTIGATION COMPLETED ({report['reportingPeriod']}) ===")
    print(f"Run ID: {report['runId']}")
    print(f"Total Corpus Reviews: {report['corpusTotals']['totalUniqueVerifiedReviews']} (Duplicates prevented: {report['corpusTotals']['duplicatesRemoved']})")
    print(f"Month Metrics ({report['reportingPeriod']}): n={report['monthMetrics']['totalReviews']}, Mean={report['monthMetrics']['meanRating']}★, Substantive Mean={report['monthMetrics']['substantiveMeanRating']}★")
    print(f"Markdown Report: {report['reportFiles']['markdownPath']}")


if __name__ == "__main__":
    main()
