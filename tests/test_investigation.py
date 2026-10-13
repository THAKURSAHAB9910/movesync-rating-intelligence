"""
MoveInSync Rating Intelligence — Automated Verification & Regression Test Suite
===============================================================================
Tests:
  1. Primary UUID (`reviewId`) and secondary SHA-256 (`dedupHash`) deduplication.
  2. Reproducible theme classification, sub-issue regex detectors, context-aware
     disambiguation, and star-text mismatch handling.
  3. 120-review stratified classifier validation benchmark (Micro-F1 >= 0.85).
  4. Transparent 5-factor prioritization formula math and rank verification.
  5. Repeatable monthly investigation comparison logic and report generation.
  6. FastAPI backend endpoints, search/filter accuracy, dry-run import dedup,
     and deliverable exports (8-page Case Study PDF, CSVs, JSON).
"""

import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from analysis.collect_evidence import compute_fallback_hash
from analysis.taxonomy import THEME_DEFINITIONS, classify_review_text
from analysis.engine import (
    ROOT_DIR,
    load_and_deduplicate_reviews,
    run_full_investigation,
)
from analysis.run_monthly import execute_monthly_investigation
from backend.app import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# 1. Deduplication & Fallback Hash Tests
# ---------------------------------------------------------------------------
def test_fallback_hash_determinism_and_normalization():
    """Fallback hash must normalize case/whitespace while distinguishing different dates or scores."""
    h1 = compute_fallback_hash("Rahul S.", "App keeps crashing on start!!", "2026-10-09T08:15:22", 1)
    h2 = compute_fallback_hash("  rahul s. ", "app keeps   crashing on start!!", "2026-10-09T21:59:00", 1)
    h3 = compute_fallback_hash("Rahul S.", "App keeps crashing on start!!", "2026-10-10T08:15:22", 1)
    h4 = compute_fallback_hash("Rahul S.", "App keeps crashing on start!!", "2026-10-09T08:15:22", 5)

    assert len(h1) == 24
    assert h1 == h2, "Same user, normalized text, same calendar day, and same score must produce identical fallback hash"
    assert h1 != h3, "Different calendar dates must produce distinct hashes"
    assert h1 != h4, "Different star ratings must produce distinct hashes"


def test_corpus_deduplication_exact_counts():
    """Verify 3,000 Newest + 600 Most Relevant deduplicate to 3,333 unique reviews (267 overlaps removed)."""
    reviews, stats = load_and_deduplicate_reviews()
    assert stats["rawNewestCount"] == 3000
    assert stats["rawMostRelevantCount"] == 600
    assert stats["exactReviewIdOverlapsRemoved"] == 267
    assert stats["totalUniqueVerifiedReviews"] == 3333
    assert len(reviews) == 3333

    # Verify every review has stable reviewId, dedupHash, and stream provenance
    seen_ids = set()
    for r in reviews:
        assert r["reviewId"] not in seen_ids
        seen_ids.add(r["reviewId"])
        assert len(r["dedupHash"]) == 24
        assert len(r["streams"]) >= 1


# ---------------------------------------------------------------------------
# 2. Theme Classification, Sub-Issue & Disambiguation Tests
# ---------------------------------------------------------------------------
def test_theme_and_sub_issue_classification():
    """Verify specific sub-issue regexes and root-cause themes fire accurately."""
    # Map auto-zoom reset + offline trip cache
    c1 = classify_review_text(
        "While tracking the cab, the map keeps zooming out automatically every few seconds to show destination.",
        score=1,
    )
    assert "LIVE_TRACKING_MAP_ETA" in c1["themes"]
    assert "map_auto_zoom_reset" in c1["subIssues"]
    assert c1["sentimentCategory"] == "negative"

    # Seatbelt popup blocking Boarding OTP in v12.19.0
    c2 = classify_review_text(
        "The new update shows a full screen seat belt alert popup and I cannot see my boarding OTP!",
        score=1,
    )
    assert "UX_MODALS_NOTIFICATIONS" in c2["themes"]
    assert "otp_blocked_by_seatbelt_modal" in c2["subIssues"]

    # False 'not downloaded from Play Store' integrity block
    c3 = classify_review_text(
        "Every 2 days it blocks me saying app not downloaded from Play Store and I have to uninstall and reinstall.",
        score=1,
    )
    assert "CRASH_LAUNCH_INTEGRITY" in c3["themes"]
    assert "false_playstore_integrity_block" in c3["subIssues"]

    # Morning no-show canceling evening ride
    c4 = classify_review_text(
        "If I miss my morning cab and get marked no show, the app automatically cancels my evening logout trip!",
        score=1,
    )
    assert "BOOKING_ROSTER_SYNC" in c4["themes"]
    assert "morning_noshow_cancels_evening_logout" in c4["subIssues"]


def test_context_disambiguation_and_star_text_mismatch():
    """
    1. 'logout trip' / 'login cab' refers to shift commute schedule, NOT authentication failure.
    2. 1-star review saying only 'good' is flagged as mixed_or_mismatch and not counted as a software defect.
    """
    shift_review = classify_review_text("My evening logout cab was delayed by 25 minutes due to driver routing.", score=2)
    assert "CAB_ROUTING_DISPATCH_OPS" in shift_review["themes"]
    assert "AUTH_OTP_SESSION" not in shift_review["themes"]

    auth_review = classify_review_text("App automatically logged out and login OTP is not coming on SMS.", score=1)
    assert "AUTH_OTP_SESSION" in auth_review["themes"]

    mismatch_review = classify_review_text("Good", score=1)
    assert mismatch_review["sentimentCategory"] == "mixed_or_mismatch"
    assert mismatch_review["isShortTapReview"] is True


# ---------------------------------------------------------------------------
# 3. Prioritization Formula & Ranking Verification Tests
# ---------------------------------------------------------------------------
def test_prioritization_formula_and_ranking():
    """
    Verify transparent 5-factor formula:
      PriorityScore = 10 * (0.25*P + 0.22*S + 0.20*V + 0.23*C + 0.10*F)
    and verify that ISS-01 ranks #1 while highest-raw-volume ISS-08 ranks #5.
    """
    inv_path = ROOT_DIR / "data" / "analytics" / "investigation_results.json"
    with open(inv_path, "r", encoding="utf-8") as f:
        inv = json.load(f)

    issues = inv["issuesRegister"]
    assert len(issues) == 8

    for idx, iss in enumerate(issues, start=1):
        assert iss["priorityRank"] == idx
        sb = iss["scoringBreakdown"]
        expected = round(
            10.0
            * (
                0.25 * sb["prevalenceAndVisibility"]
                + 0.22 * sb["severityAndImpact"]
                + 0.20 * sb["temporalVelocity"]
                + 0.23 * sb["confidenceAndAttributability"]
                + 0.10 * sb["engineeringFeasibility"]
            ),
            2,
        )
        assert abs(iss["priorityScore"] - expected) <= 0.01

    # Verify #1 is ISS-01 (Live Tracking, Map Auto-Zoom & ETA)
    assert issues[0]["issueId"] == "ISS-01"
    assert issues[0]["themeCode"] == "LIVE_TRACKING_MAP_ETA"
    assert issues[0]["priorityScore"] > issues[1]["priorityScore"]

    # Verify ISS-08 has highest raw negative count (429) but is NOT ranked #1
    iss_08 = next(i for i in issues if i["issueId"] == "ISS-08")
    assert iss_08["negCountTotal"] == max(i["negCountTotal"] for i in issues)
    assert iss_08["priorityRank"] == 5, "Confounded fleet operations must not rank #1 ahead of controllable software defects"

    # Verify Classifier Validation Micro-F1 >= 0.85
    assert inv["classifierValidation"]["sampleSize"] == 120
    assert inv["classifierValidation"]["microF1"] >= 0.85


# ---------------------------------------------------------------------------
# 4. Repeatable Monthly Investigation Workflow Tests
# ---------------------------------------------------------------------------
def test_monthly_comparison_and_report_generation():
    """Verify monthly runner compares against prior month and 12m baseline and writes dated reports."""
    report = execute_monthly_investigation(reporting_month="2026-09")
    assert report["reportingPeriod"] == "2026-09"
    assert report["previousPeriodCompared"] == "2026-08"
    assert report["monthMetrics"]["totalReviews"] == 245
    assert report["corpusTotals"]["totalUniqueVerifiedReviews"] == 3333

    # Verify delta calculation consistency
    for ic in report["statusBreakdown"]["worseningIssues"] + report["statusBreakdown"]["persistentIssues"]:
        expected_delta = round(ic["currentShareOfNegPct"] - ic["previousMonthSharePct"], 1)
        assert abs(ic["deltaMoMPts"] - expected_delta) <= 0.15

    md_path = ROOT_DIR / report["reportFiles"]["markdownPath"]
    assert md_path.exists()
    assert md_path.stat().st_size > 1000


# ---------------------------------------------------------------------------
# 5. FastAPI Endpoints & Deliverable Export Verification Tests
# ---------------------------------------------------------------------------
def test_fastapi_endpoints_and_deliverables():
    """Verify REST endpoints, search/filter queries, dry-run import dedup, and PDF/CSV exports."""
    # Health check
    r_health = client.get("/api/health")
    assert r_health.status_code == 200
    h_data = r_health.json()
    assert h_data["verifiedAppId"] == "com.moveinsync.ets"
    assert h_data["totalUniqueReviews"] == 3333
    assert h_data["caseStudyPdfExists"] is True

    # Evidence Explorer filtering: reviews edited after developer reply (55 total; 33 in 1-3★; 29 in 1-2★)
    r_edited_all = client.get("/api/reviews?special=edited_after_reply")
    assert r_edited_all.status_code == 200
    assert r_edited_all.json()["totalMatching"] == 55

    r_edited_13 = client.get("/api/reviews?special=edited_after_reply&score=1-3")
    assert r_edited_13.status_code == 200
    assert r_edited_13.json()["totalMatching"] == 33

    r_edited_neg = client.get("/api/reviews?special=edited_after_reply&score=1-2")
    assert r_edited_neg.status_code == 200
    assert r_edited_neg.json()["totalMatching"] == 29

    # Evidence Explorer filtering by sub-issue: otp_blocked_by_seatbelt_modal
    r_seatbelt = client.get("/api/reviews?sub_issue=otp_blocked_by_seatbelt_modal")
    assert r_seatbelt.status_code == 200
    assert r_seatbelt.json()["totalMatching"] >= 3

    # Import dry-run deduplication: 1 existing reviewId + 1 brand-new review
    sample_import = [
        {
            "reviewId": "026c2e2a-7197-4609-85cf-94611b36a788",
            "userName": "ExistingUser",
            "content": "Duplicate test record",
            "score": 1,
            "at": "2026-10-11T10:00:00",
        },
        {
            "reviewId": "pytest-unique-review-99999",
            "userName": "PytestCommuter",
            "content": "Brand new test review reporting map zoom reset.",
            "score": 1,
            "at": "2026-10-13T01:00:00",
        },
    ]
    r_imp = client.post(
        "/api/import",
        json={"format": "json", "payload": sample_import, "persistBatch": False},
    )
    assert r_imp.status_code == 200
    imp_res = r_imp.json()
    assert imp_res["recordsSubmitted"] == 2
    assert imp_res["duplicatesPreventedByReviewId"] == 1
    assert imp_res["newUniqueReviewsAccepted"] == 1

    # Deliverable A: Case Study PDF export
    r_pdf = client.get("/api/export/report.pdf")
    assert r_pdf.status_code == 200
    assert r_pdf.headers["content-type"] == "application/pdf"
    assert len(r_pdf.content) > 500_000

    # CSV exports
    r_rev_csv = client.get("/api/export/reviews.csv")
    assert r_rev_csv.status_code == 200
    assert "reviewId,dedupHash,date" in r_rev_csv.text[:200]

    r_iss_csv = client.get("/api/export/issues.csv")
    assert r_iss_csv.status_code == 200
    assert "ISS-01" in r_iss_csv.text

    # Frontend HTML root
    r_root = client.get("/")
    assert r_root.status_code == 200
    assert "MoveInSync Rating Intelligence" in r_root.text
