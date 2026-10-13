"""
MoveInSync Rating Intelligence — FastAPI Backend & Evidence API
===============================================================
Serves the validated analytical baseline, searchable/filterable Evidence Explorer,
human analyst classification override workflow, legitimate review import with
2-tier deduplication, transparent Issue Prioritization engine, Action Tracking
register updates, repeatable Monthly Investigation runner, and downloadable
CSV/JSON/PDF deliverables.
"""

import io
import csv
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from analysis.taxonomy import THEME_DEFINITIONS
from analysis.collect_evidence import compute_fallback_hash
from analysis.engine import (
    BUNDLE_ROOT,
    ROOT_DIR,
    RAW_DIR,
    PROCESSED_DIR,
    ANALYTICS_DIR,
    VALIDATION_DIR,
    DB_PATH,
    save_analyst_override,
    save_action_override,
    run_full_investigation,
)
from analysis.run_monthly import execute_monthly_investigation, MONTHLY_REPORTS_DIR

FRONTEND_DIR = BUNDLE_ROOT / "frontend"
REPORTS_DIR = BUNDLE_ROOT / "reports"

app = FastAPI(
    title="MoveInSync Rating Intelligence API",
    description="Evidence-First Product & Engineering Investigation System for MoveInSync (com.moveinsync.ets)",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# In-memory cache with automatic reload on modification
# ---------------------------------------------------------------------------
_CACHE: Dict[str, Any] = {
    "investigation_mtime": 0.0,
    "investigation": None,
    "reviews_mtime": 0.0,
    "reviews": None,
}


def get_investigation_data(force_reload: bool = False) -> Dict[str, Any]:
    inv_path = ANALYTICS_DIR / "investigation_results.json"
    if not inv_path.exists():
        run_full_investigation()
    mtime = inv_path.stat().st_mtime
    if force_reload or _CACHE["investigation"] is None or mtime > _CACHE["investigation_mtime"]:
        with open(inv_path, "r", encoding="utf-8") as f:
            _CACHE["investigation"] = json.load(f)
        _CACHE["investigation_mtime"] = mtime
    return _CACHE["investigation"]


def get_reviews_data(force_reload: bool = False) -> List[Dict[str, Any]]:
    rev_path = PROCESSED_DIR / "reviews_cleaned_enriched.json"
    if not rev_path.exists():
        run_full_investigation()
    mtime = rev_path.stat().st_mtime
    if force_reload or _CACHE["reviews"] is None or mtime > _CACHE["reviews_mtime"]:
        with open(rev_path, "r", encoding="utf-8") as f:
            _CACHE["reviews"] = json.load(f)
        _CACHE["reviews_mtime"] = mtime
    return _CACHE["reviews"]


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------
class OverrideRequest(BaseModel):
    themes: List[str] = Field(default_factory=list, description="List of corrected theme codes")
    sentiment: str = Field(default="negative", description="Corrected sentiment category")
    note: str = Field(default="", description="Analyst explanation for the classification override")
    auditor: str = Field(default="FDE-Reviewer", description="Analyst identifier")


class ActionUpdateRequest(BaseModel):
    status: Optional[str] = None
    verificationSource: Optional[str] = None
    nextStep: Optional[str] = None
    unresolvedQuestions: Optional[str] = None
    owner: Optional[str] = None
    targetEvaluationDate: Optional[str] = None


class MonthlyRunRequest(BaseModel):
    reportingMonth: str = Field(default="2026-10", description="Target reporting month YYYY-MM")


class ImportReviewsRequest(BaseModel):
    format: str = Field(default="json", description="'json' or 'csv'")
    payload: Any = Field(..., description="JSON array of review objects or CSV string")
    persistBatch: bool = Field(default=False, description="Whether to persist imported batch to data/raw/imports/")


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------
@app.get("/api/health")
def api_health() -> Dict[str, Any]:
    inv = get_investigation_data()
    revs = get_reviews_data()
    return {
        "status": "ok",
        "service": "MoveInSync Rating Intelligence",
        "investigationId": inv.get("investigationId"),
        "observationDate": inv["baseline"]["observationDate"],
        "verifiedAppId": inv["verifiedAppIdentity"]["applicationId"],
        "totalUniqueReviews": len(revs),
        "sqliteDbExists": DB_PATH.exists(),
        "caseStudyPdfExists": (REPORTS_DIR / "MoveInSync_Case_Study.pdf").exists(),
    }


@app.get("/api/investigation")
def api_get_investigation() -> Dict[str, Any]:
    """Return the complete validated investigation payload."""
    return get_investigation_data()


@app.get("/api/reviews/facets")
def api_get_review_facets() -> Dict[str, Any]:
    """Return available filter values (versions, themes, sub-issues, streams, length buckets)."""
    reviews = get_reviews_data()
    version_counts: Dict[str, int] = {}
    sub_issue_counts: Dict[str, int] = {}
    for r in reviews:
        v = r.get("reviewCreatedVersion") or "Unspecified"
        version_counts[v] = version_counts.get(v, 0) + 1
        for sub in r.get("subIssues", []):
            sub_issue_counts[sub] = sub_issue_counts.get(sub, 0) + 1

    top_versions = [
        {"version": k, "count": v}
        for k, v in sorted(version_counts.items(), key=lambda x: x[1], reverse=True)[:25]
    ]
    top_sub_issues = [
        {"subIssue": k, "count": v}
        for k, v in sorted(sub_issue_counts.items(), key=lambda x: x[1], reverse=True)
    ]
    themes = [
        {"themeCode": k, "issueId": v["id"], "shortName": v["shortName"], "category": v["category"]}
        for k, v in THEME_DEFINITIONS.items()
    ]
    return {
        "themes": themes,
        "subIssues": top_sub_issues,
        "versions": top_versions,
        "lengthBuckets": [
            "1-2 words (tap/micro)",
            "3-5 words",
            "6-14 words",
            "15+ words (substantive)",
        ],
    }


@app.get("/api/reviews")
def api_search_reviews(
    q: Optional[str] = Query(default=None, description="Full-text search across review content, ID, sub-issues"),
    score: Optional[str] = Query(default=None, description="1, 2, 3, 4, 5, 1-2, 1-3, or 4-5"),
    theme: Optional[str] = Query(default=None, description="Theme code filter or UNTHEMED"),
    sub_issue: Optional[str] = Query(default=None, description="Sub-issue code filter"),
    version: Optional[str] = Query(default=None, description="App version filter"),
    stream: Optional[str] = Query(default=None, description="newest, most_relevant, both"),
    sentiment: Optional[str] = Query(default=None, description="negative, positive, neutral, mixed_or_mismatch"),
    length_bucket: Optional[str] = Query(default=None, description="Length bucket or substantive_all"),
    special: Optional[str] = Query(default=None, description="has_override, edited_after_reply, has_reply, positive_with_caveat"),
    date_from: Optional[str] = Query(default=None, description="YYYY-MM-DD start date"),
    date_to: Optional[str] = Query(default=None, description="YYYY-MM-DD end date"),
    sort_by: str = Query(default="thumbs_desc", description="thumbs_desc, date_desc, date_asc, score_asc, score_desc, words_desc"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=5, le=200),
) -> Dict[str, Any]:
    """Search and filter actual review records with strict source vs interpretation separation."""
    reviews = get_reviews_data()
    filtered = reviews

    if q and q.strip():
        q_low = q.strip().lower()
        filtered = [
            r for r in filtered
            if q_low in r["content"].lower()
            or q_low in r["reviewId"].lower()
            or q_low in r["dedupHash"].lower()
            or any(q_low in s.lower() for s in r["subIssues"])
            or (r.get("replyContent") and q_low in r["replyContent"].lower())
        ]

    if score and score != "all":
        if score == "1-2":
            filtered = [r for r in filtered if r["score"] <= 2]
        elif score == "1-3":
            filtered = [r for r in filtered if r["score"] <= 3]
        elif score == "4-5":
            filtered = [r for r in filtered if r["score"] >= 4]
        elif score.isdigit():
            s_val = int(score)
            filtered = [r for r in filtered if r["score"] == s_val]

    if theme and theme != "all":
        if theme == "UNTHEMED":
            filtered = [r for r in filtered if not r["themes"]]
        else:
            filtered = [r for r in filtered if theme in r["themes"]]

    if sub_issue and sub_issue != "all":
        filtered = [r for r in filtered if sub_issue in r["subIssues"]]

    if version and version != "all":
        if version == "Unspecified":
            filtered = [r for r in filtered if not r.get("reviewCreatedVersion")]
        else:
            filtered = [r for r in filtered if r.get("reviewCreatedVersion") == version]

    if stream and stream != "all":
        if stream == "both":
            filtered = [r for r in filtered if "newest" in r["streams"] and "most_relevant" in r["streams"]]
        else:
            filtered = [r for r in filtered if stream in r["streams"]]

    if sentiment and sentiment != "all":
        filtered = [r for r in filtered if r["sentimentCategory"] == sentiment]

    if length_bucket and length_bucket != "all":
        if length_bucket == "substantive_all":
            filtered = [r for r in filtered if r["isSubstantive"]]
        else:
            filtered = [r for r in filtered if r["lengthBucket"] == length_bucket]

    if special and special != "all":
        if special == "has_override":
            filtered = [r for r in filtered if r.get("manualOverride") is not None]
        elif special == "edited_after_reply":
            filtered = [r for r in filtered if r.get("isEditedAfterReply")]
        elif special == "has_reply":
            filtered = [r for r in filtered if r.get("replyContent")]
        elif special == "positive_with_caveat":
            filtered = [r for r in filtered if r["score"] >= 4 and len(r["themes"]) > 0]

    if date_from:
        filtered = [r for r in filtered if r["date"] >= date_from]
    if date_to:
        filtered = [r for r in filtered if r["date"] <= date_to]

    # Sort
    if sort_by == "thumbs_desc":
        filtered = sorted(filtered, key=lambda r: (r["thumbsUpCount"], r["at"]), reverse=True)
    elif sort_by == "date_desc":
        filtered = sorted(filtered, key=lambda r: r["at"], reverse=True)
    elif sort_by == "date_asc":
        filtered = sorted(filtered, key=lambda r: r["at"])
    elif sort_by == "score_asc":
        filtered = sorted(filtered, key=lambda r: (r["score"], -r["thumbsUpCount"]))
    elif sort_by == "score_desc":
        filtered = sorted(filtered, key=lambda r: (r["score"], r["thumbsUpCount"]), reverse=True)
    elif sort_by == "words_desc":
        filtered = sorted(filtered, key=lambda r: r["wordCount"], reverse=True)

    total = len(filtered)
    mean_rating = round(sum(r["score"] for r in filtered) / max(1, total), 2) if total else 0.0
    neg_12_pct = round(sum(1 for r in filtered if r["score"] <= 2) / max(1, total) * 100, 1) if total else 0.0

    start = (page - 1) * page_size
    end = start + page_size
    page_items = filtered[start:end]

    return {
        "totalMatching": total,
        "page": page,
        "pageSize": page_size,
        "totalPages": max(1, (total + page_size - 1) // page_size),
        "filteredSummary": {
            "meanRating": mean_rating,
            "negative12Pct": neg_12_pct,
        },
        "reviews": page_items,
    }


@app.get("/api/reviews/{review_id}")
def api_get_single_review(review_id: str) -> Dict[str, Any]:
    reviews = get_reviews_data()
    for r in reviews:
        if r["reviewId"] == review_id or r["reviewId"].startswith(review_id):
            return r
    raise HTTPException(status_code=404, detail=f"Review '{review_id}' not found")


@app.post("/api/reviews/{review_id}/override")
def api_override_review_classification(review_id: str, req: OverrideRequest) -> Dict[str, Any]:
    """
    Save a human analyst classification override for a review, rerun the
    reproducible pipeline, and return the updated review record.
    """
    reviews = get_reviews_data()
    target = None
    for r in reviews:
        if r["reviewId"] == review_id or r["reviewId"].startswith(review_id):
            target = r
            break
    if not target:
        raise HTTPException(status_code=404, detail=f"Review '{review_id}' not found")

    valid_themes = [t for t in req.themes if t in THEME_DEFINITIONS]
    entry = save_analyst_override(
        review_id=target["reviewId"],
        themes=valid_themes,
        sentiment=req.sentiment,
        note=req.note,
        auditor=req.auditor,
    )
    updated_inv = run_full_investigation()
    _CACHE["investigation"] = updated_inv
    _CACHE["investigation_mtime"] = (ANALYTICS_DIR / "investigation_results.json").stat().st_mtime
    get_reviews_data(force_reload=True)

    updated_review = next(r for r in get_reviews_data() if r["reviewId"] == target["reviewId"])
    return {
        "status": "override_saved",
        "overrideEntry": entry,
        "updatedReview": updated_review,
        "totalAnalystOverrides": updated_inv["baseline"]["dataCompletenessAndLimitations"]["analystOverridesApplied"],
    }


@app.post("/api/import")
def api_import_reviews(req: ImportReviewsRequest) -> Dict[str, Any]:
    """
    Validate and deduplicate imported review records (JSON or CSV) against the existing
    corpus using primary `reviewId` and secondary SHA-256 fallback hash (`dedupHash`).
    """
    existing_reviews = get_reviews_data()
    existing_ids = {r["reviewId"] for r in existing_reviews}
    existing_prefixes = {r["reviewId"][:8] for r in existing_reviews}
    existing_hashes = {r["dedupHash"] for r in existing_reviews}

    raw_list: List[Dict[str, Any]] = []
    if req.format.lower() == "json":
        if isinstance(req.payload, str):
            try:
                parsed = json.loads(req.payload)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Invalid JSON string: {e}")
        else:
            parsed = req.payload
        if isinstance(parsed, dict) and "reviews" in parsed:
            parsed = parsed["reviews"]
        if not isinstance(parsed, list):
            raise HTTPException(status_code=400, detail="JSON payload must be a list of review objects")
        raw_list = parsed
    elif req.format.lower() == "csv":
        if not isinstance(req.payload, str):
            raise HTTPException(status_code=400, detail="CSV payload must be a string")
        reader = csv.DictReader(io.StringIO(req.payload))
        for row in reader:
            raw_list.append(dict(row))
    else:
        raise HTTPException(status_code=400, detail="Unsupported format. Use 'json' or 'csv'.")

    normalized_records: List[Dict[str, Any]] = []
    dup_by_id = 0
    dup_by_hash = 0
    new_unique = 0

    seen_batch_ids = set(existing_ids)
    seen_batch_hashes = set(existing_hashes)

    for item in raw_list:
        content = str(item.get("content") or item.get("text") or "").strip()
        if not content:
            continue
        try:
            score = int(item.get("score") or item.get("rating") or 3)
        except ValueError:
            score = 3
        score = max(1, min(5, score))
        at_str = str(item.get("at") or item.get("date") or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"))
        if len(at_str) == 10:
            at_str = f"{at_str}T00:00:00"
        user_name = str(item.get("userName") or item.get("author") or "ImportedUser")
        dedup_h = compute_fallback_hash(user_name, content, at_str[:19], score)
        rev_id = str(item.get("reviewId") or item.get("id") or "").strip() or f"imp-{dedup_h[:24]}"

        if rev_id in seen_batch_ids or (len(rev_id) >= 8 and rev_id[:8] in existing_prefixes and not rev_id.startswith("imp-")):
            dup_by_id += 1
            continue
        if dedup_h in seen_batch_hashes:
            dup_by_hash += 1
            continue

        seen_batch_ids.add(rev_id)
        seen_batch_hashes.add(dedup_h)
        new_unique += 1
        normalized_records.append({
            "reviewId": rev_id,
            "userName": user_name,
            "content": content,
            "score": score,
            "thumbsUpCount": int(item.get("thumbsUpCount") or item.get("likes") or 0),
            "reviewCreatedVersion": item.get("reviewCreatedVersion") or item.get("version") or None,
            "appVersion": item.get("appVersion") or item.get("reviewCreatedVersion") or None,
            "at": at_str,
            "replyContent": item.get("replyContent") or None,
            "repliedAt": item.get("repliedAt") or None,
            "dedupHash": dedup_h,
            "stream": "imported",
            "collectedAtUtc": datetime.now(timezone.utc).isoformat(),
        })

    if req.persistBatch and normalized_records:
        imp_dir = RAW_DIR / "imports"
        imp_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        with open(imp_dir / f"import_batch_{stamp}.json", "w", encoding="utf-8") as f:
            json.dump(normalized_records, f, indent=2, ensure_ascii=False)
        run_full_investigation()
        get_investigation_data(force_reload=True)
        get_reviews_data(force_reload=True)

    return {
        "status": "validated",
        "persisted": req.persistBatch,
        "recordsSubmitted": len(raw_list),
        "newUniqueReviewsAccepted": new_unique,
        "duplicatesPreventedByReviewId": dup_by_id,
        "duplicatesPreventedByFallbackHash": dup_by_hash,
        "totalDuplicatesPrevented": dup_by_id + dup_by_hash,
        "totalCorpusSize": len(get_reviews_data()) + (0 if req.persistBatch else new_unique),
    }


@app.patch("/api/actions/{action_id}")
def api_update_action_status(action_id: str, req: ActionUpdateRequest) -> Dict[str, Any]:
    """Update an action item in the Action Tracking register and persist."""
    inv = get_investigation_data()
    actions = inv["actionPlanAndTracking"]["actionTrackingRegister"]
    if not any(a["actionId"] == action_id for a in actions):
        raise HTTPException(status_code=404, detail=f"Action '{action_id}' not found")

    updates = {k: v for k, v in req.model_dump().items() if v is not None}
    save_action_override(action_id, updates)
    updated_inv = run_full_investigation()
    _CACHE["investigation"] = updated_inv
    _CACHE["investigation_mtime"] = (ANALYTICS_DIR / "investigation_results.json").stat().st_mtime

    updated_action = next(
        a for a in updated_inv["actionPlanAndTracking"]["actionTrackingRegister"]
        if a["actionId"] == action_id
    )
    return {
        "status": "updated",
        "action": updated_action,
        "actionTrackingRegister": updated_inv["actionPlanAndTracking"]["actionTrackingRegister"],
    }


@app.post("/api/monthly/run")
def api_run_monthly_investigation(req: MonthlyRunRequest) -> Dict[str, Any]:
    """Trigger a repeatable monthly investigation run and generate dated reports."""
    report = execute_monthly_investigation(reporting_month=req.reportingMonth)
    get_investigation_data(force_reload=True)
    get_reviews_data(force_reload=True)
    return report


@app.get("/api/monthly/history")
def api_get_monthly_history() -> Dict[str, Any]:
    """Return historical investigation runs recorded in SQLite and available monthly reports."""
    runs = []
    if DB_PATH.exists():
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        try:
            cur.execute(
                "SELECT run_id, reporting_period, executed_at, total_unique_reviews, newest_mean_rating, substantive_mean_rating, top_priority_issue_id FROM investigation_runs ORDER BY executed_at DESC LIMIT 20"
            )
            for row in cur.fetchall():
                runs.append({
                    "runId": row[0],
                    "reportingPeriod": row[1],
                    "executedAt": row[2],
                    "totalUniqueReviews": row[3],
                    "meanRating": row[4],
                    "substantiveMeanRating": row[5],
                    "topPriorityIssueId": row[6],
                })
        except Exception:
            pass
        finally:
            conn.close()

    files = []
    if MONTHLY_REPORTS_DIR.exists():
        for p in sorted(MONTHLY_REPORTS_DIR.glob("*.md"), reverse=True):
            files.append({
                "fileName": p.name,
                "sizeBytes": p.stat().st_size,
                "modifiedAt": datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc).isoformat(),
            })

    return {
        "runs": runs,
        "reportFiles": files,
    }


# ---------------------------------------------------------------------------
# Export & Download Endpoints
# ---------------------------------------------------------------------------
@app.get("/api/export/report.pdf")
def api_download_pdf_report() -> FileResponse:
    pdf_path = REPORTS_DIR / "MoveInSync_Case_Study.pdf"
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="Case Study PDF not found")
    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename="MoveInSync_Case_Study.pdf",
    )


@app.get("/api/export/reviews.csv")
def api_download_reviews_csv() -> FileResponse:
    csv_path = PROCESSED_DIR / "reviews_export.csv"
    if not csv_path.exists():
        run_full_investigation()
    return FileResponse(
        path=csv_path,
        media_type="text/csv",
        filename="MoveInSync_Verified_Reviews_3333.csv",
    )


@app.get("/api/export/issues.csv")
def api_download_issues_csv() -> FileResponse:
    csv_path = PROCESSED_DIR / "issues_register.csv"
    if not csv_path.exists():
        run_full_investigation()
    return FileResponse(
        path=csv_path,
        media_type="text/csv",
        filename="MoveInSync_Prioritized_Issues_Register.csv",
    )


@app.get("/api/export/investigation.json")
def api_download_investigation_json() -> FileResponse:
    json_path = ANALYTICS_DIR / "investigation_results.json"
    if not json_path.exists():
        run_full_investigation()
    return FileResponse(
        path=json_path,
        media_type="application/json",
        filename="MoveInSync_Investigation_Results.json",
    )


@app.get("/api/export/monthly/{month}.md")
def api_download_monthly_markdown(month: str) -> PlainTextResponse:
    safe_month = month.replace("-", "_")
    md_path = MONTHLY_REPORTS_DIR / f"MoveInSync_Monthly_Investigation_{safe_month}.md"
    if not md_path.exists():
        execute_monthly_investigation(reporting_month=month)
    if not md_path.exists():
        raise HTTPException(status_code=404, detail=f"Monthly report for {month} not found")
    content = md_path.read_text(encoding="utf-8")
    return PlainTextResponse(
        content=content,
        headers={"Content-Disposition": f'attachment; filename="MoveInSync_Monthly_Investigation_{safe_month}.md"'},
    )


# ---------------------------------------------------------------------------
# Static Frontend Serving
# ---------------------------------------------------------------------------
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.get("/")
def serve_frontend_root() -> FileResponse:
    index_path = FRONTEND_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="Frontend index.html not found")
    return FileResponse(index_path)
