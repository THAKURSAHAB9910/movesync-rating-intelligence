"""
MoveInSync Rating Intelligence — Publication-Grade 8-Page Case Study PDF Generator
==================================================================================
Generates high-DPI data visualizations from validated analytical records and builds
the 8-page recruiter-ready report at `reports/MoveInSync_Case_Study.pdf`.
"""

import json
from pathlib import Path
from typing import Dict, Any, List

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    PageBreak,
)
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT_DIR = Path(__file__).resolve().parent.parent
ANALYTICS_PATH = ROOT_DIR / "data" / "analytics" / "investigation_results.json"
REPORTS_DIR = ROOT_DIR / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"
PDF_OUTPUT_PATH = REPORTS_DIR / "MoveInSync_Case_Study.pdf"

# Register DejaVuSans from matplotlib's bundled fonts so ★, ≥, ≤, × render as crisp vector glyphs
MPL_FONT_DIR = Path(matplotlib.get_data_path()) / "fonts" / "ttf"
if (MPL_FONT_DIR / "DejaVuSans.ttf").exists():
    pdfmetrics.registerFont(TTFont("DejaVu", str(MPL_FONT_DIR / "DejaVuSans.ttf")))
    pdfmetrics.registerFont(TTFont("DejaVu-Bold", str(MPL_FONT_DIR / "DejaVuSans-Bold.ttf")))
    pdfmetrics.registerFont(TTFont("DejaVu-Oblique", str(MPL_FONT_DIR / "DejaVuSans-Oblique.ttf")))
    FONT_REG = "DejaVu"
    FONT_BOLD = "DejaVu-Bold"
    FONT_ITALIC = "DejaVu-Oblique"
else:
    FONT_REG = "Helvetica"
    FONT_BOLD = "Helvetica-Bold"
    FONT_ITALIC = "Helvetica-Oblique"

# Brand / Executive Palette
NAVY = "#0F172A"
SLATE = "#334155"
MUTED = "#64748B"
BLUE = "#1D4ED8"
TEAL = "#0D9488"
AMBER = "#D97706"
RED = "#DC2626"
GREEN = "#16A34A"


def generate_all_charts(data: Dict[str, Any]) -> Dict[str, Path]:
    """Generate 5 publication-grade matplotlib figures from validated analytical data."""
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    plt.rcParams["font.sans-serif"] = "DejaVu Sans"
    plt.rcParams["axes.edgecolor"] = "#CBD5E1"
    plt.rcParams["axes.linewidth"] = 0.8

    baseline = data["baseline"]
    issues = data["issuesRegister"]
    paths: Dict[str, Path] = {}

    # -------------------------------------------------------------------------
    # FIG 1: Rating Bifurcation (Storefront vs Sample Cohorts & Word Length)
    # -------------------------------------------------------------------------
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.5, 3.2), dpi=220)
    fig.patch.set_facecolor("white")

    cohorts_labels = [
        "Play Store IN\n(N=114,881)",
        "Play Store US\n(N=114,881)",
        "Newest Sample\n(n=3,000)",
        "Substantive >=6w\n(n=1,066)",
        "Detailed >=15w\n(n=483)",
        "Most Relevant\n(n=600)",
    ]
    cohorts_means = [
        baseline["storefrontSnapshots"]["india"]["displayedRating"],
        baseline["storefrontSnapshots"]["unitedStates"]["displayedRating"],
        baseline["sampleCohorts"]["newest3000"]["meanRating"],
        baseline["sampleCohorts"]["substantiveNewest"]["meanRating"],
        baseline["sampleCohorts"]["detailedNewest15Plus"]["meanRating"],
        baseline["sampleCohorts"]["mostRelevant600"]["meanRating"],
    ]
    bar_colors = [GREEN, TEAL, "#3B82F6", AMBER, RED, "#991B1B"]

    y_pos = np.arange(len(cohorts_labels))
    bars = ax1.barh(y_pos, cohorts_means, color=bar_colors, height=0.62, edgecolor="none")
    ax1.set_yticks(y_pos)
    ax1.set_yticklabels(cohorts_labels, fontsize=7.8, fontweight="bold", color=NAVY)
    ax1.invert_yaxis()
    ax1.set_xlim(0, 5.4)
    ax1.axvline(4.64, color=GREEN, linestyle="--", linewidth=0.9, alpha=0.6)
    ax1.set_xlabel("Mean Star Rating (1.0★ to 5.0★)", fontsize=7.8, color=SLATE)
    ax1.set_title("A. Storefront Headline vs. Collected Written Cohorts\n(Observed Oct 13, 2026 | com.moveinsync.ets)", fontsize=8.5, fontweight="bold", color=NAVY, pad=6)
    ax1.grid(axis="x", linestyle=":", alpha=0.5)
    for bar, val in zip(bars, cohorts_means):
        ax1.text(val + 0.08, bar.get_y() + bar.get_height() / 2, f"{val:.2f}★", va="center", fontsize=7.8, fontweight="bold", color=NAVY)

    len_strata = baseline["ratingBifurcationExplanation"]["lengthStratification"]
    b_labels = [s["bucket"].replace(" (", "\n(") for s in len_strata]
    b_means = [s["meanRating"] for s in len_strata]
    b_neg_pct = [s["negative12Pct"] for s in len_strata]

    x_idx = np.arange(len(b_labels))
    width = 0.36
    ax2_twin = ax2.twinx()
    rects1 = ax2.bar(x_idx - width / 2, b_means, width, label="Mean Rating (★)", color=BLUE)
    rects2 = ax2_twin.bar(x_idx + width / 2, b_neg_pct, width, label="1–2★ Negative Share (%)", color=RED, alpha=0.85)

    ax2.set_xticks(x_idx)
    ax2.set_xticklabels(b_labels, fontsize=7.4, color=NAVY)
    ax2.set_ylim(0, 5.5)
    ax2_twin.set_ylim(0, 85)
    ax2.set_ylabel("Mean Star Rating (★)", fontsize=7.8, color=BLUE, fontweight="bold")
    ax2_twin.set_ylabel("1–2★ Negative Share (%)", fontsize=7.8, color=RED, fontweight="bold")
    ax2.set_title("B. Rating Collapse by Review Length\n(Chronological Newest Stream, n=3,000, Sep 2025–Oct 2026)", fontsize=8.5, fontweight="bold", color=NAVY, pad=6)
    ax2.grid(axis="y", linestyle=":", alpha=0.4)

    for r1, v1 in zip(rects1, b_means):
        ax2.text(r1.get_x() + r1.get_width() / 2, v1 + 0.12, f"{v1:.2f}★", ha="center", fontsize=7.4, fontweight="bold", color=BLUE)
    for r2, v2 in zip(rects2, b_neg_pct):
        ax2_twin.text(r2.get_x() + r2.get_width() / 2, v2 + 1.8, f"{v2:.1f}%", ha="center", fontsize=7.4, fontweight="bold", color=RED)

    plt.tight_layout()
    p1 = FIGURES_DIR / "fig1_rating_bifurcation.png"
    plt.savefig(p1, bbox_inches="tight")
    plt.close(fig)
    paths["fig1"] = p1

    # -------------------------------------------------------------------------
    # FIG 2: Monthly Volume & Rating Trajectory (Sep 2025 – Oct 2026)
    # -------------------------------------------------------------------------
    m_series = baseline["monthlySeries"]
    months = [m["yearMonth"] + ("*" if m["isPartialMonth"] else "") for m in m_series]
    pos_counts = [m["starDistribution"]["4"] + m["starDistribution"]["5"] for m in m_series]
    neu_counts = [m["starDistribution"]["3"] for m in m_series]
    neg_counts = [m["negative12Count"] for m in m_series]
    all_means = [m["meanRatingAll"] for m in m_series]
    sub_means = [m["meanRatingSubstantive"] for m in m_series]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.5, 3.2), dpi=220)
    fig.patch.set_facecolor("white")

    x = np.arange(len(months))
    ax1.bar(x, neg_counts, label="1–2★ Negative", color=RED, width=0.62)
    ax1.bar(x, neu_counts, bottom=neg_counts, label="3★ Neutral", color=AMBER, width=0.62)
    bottom_pos = [n + u for n, u in zip(neg_counts, neu_counts)]
    ax1.bar(x, pos_counts, bottom=bottom_pos, label="4–5★ Positive (incl. 1-word)", color="#22C55E", alpha=0.8, width=0.62)
    ax1.set_xticks(x)
    ax1.set_xticklabels(months, rotation=45, ha="right", fontsize=7.0, color=NAVY)
    ax1.set_ylabel("Monthly Written Reviews (count)", fontsize=7.8, color=SLATE)
    ax1.set_title("A. Monthly Review Volume by Rating Tier\n(n=3,000 Newest Reviews, Sep 22, 2025 – Oct 11, 2026; *partial)", fontsize=8.3, fontweight="bold", color=NAVY)
    ax1.legend(loc="upper left", fontsize=6.8, frameon=True)
    ax1.grid(axis="y", linestyle=":", alpha=0.4)

    ax2.plot(x, all_means, marker="o", linewidth=2, color=BLUE, label="All Written Reviews Mean (★)")
    ax2.plot(x, sub_means, marker="s", linewidth=2, color=RED, linestyle="-", label="Substantive (>=6 words) Mean (★)")
    ax2.axhline(3.0, color=MUTED, linestyle="--", linewidth=0.8, label="3.0★ Neutral Threshold")
    ax2.set_xticks(x)
    ax2.set_xticklabels(months, rotation=45, ha="right", fontsize=7.0, color=NAVY)
    ax2.set_ylim(1.8, 4.6)
    ax2.set_ylabel("Mean Star Rating (★)", fontsize=7.8, color=SLATE)
    ax2.set_title("B. Monthly Mean Rating: All vs. Substantive (>=6 words)\n(Demonstrating Chronic Sub-3.0★ Substantive Sentiment)", fontsize=8.3, fontweight="bold", color=NAVY)
    ax2.legend(loc="lower left", fontsize=6.8, frameon=True)
    ax2.grid(True, linestyle=":", alpha=0.4)

    for idx in [0, 4, 9, 11, 12, 13]:
        if idx < len(x):
            ax2.annotate(f"{sub_means[idx]:.2f}★", (x[idx], sub_means[idx] - 0.18), fontsize=6.6, ha="center", color=RED, fontweight="bold")
            ax2.annotate(f"{all_means[idx]:.2f}★", (x[idx], all_means[idx] + 0.10), fontsize=6.6, ha="center", color=BLUE, fontweight="bold")

    plt.tight_layout()
    p2 = FIGURES_DIR / "fig2_monthly_trends.png"
    plt.savefig(p2, bbox_inches="tight")
    plt.close(fig)
    paths["fig2"] = p2

    # -------------------------------------------------------------------------
    # FIG 3: Complaint Themes — Negative Volume, Helpful Votes & H2 Surge
    # -------------------------------------------------------------------------
    issues_by_vol = sorted(issues, key=lambda x: x["negCountTotal"], reverse=True)
    t_names = [f"{i['issueId']}: {i['shortName']}" for i in issues_by_vol]
    t_neg = [i["negCountTotal"] for i in issues_by_vol]
    t_thumbs = [i["thumbsUpTotal"] for i in issues_by_vol]
    t_growth = [i["h2VsH1GrowthPct"] for i in issues_by_vol]
    t_colors = [MUTED if i["issueId"] == "ISS-08" else (BLUE if i["issueId"] == "ISS-01" else TEAL) for i in issues_by_vol]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.5, 3.15), dpi=220)
    fig.patch.set_facecolor("white")

    y = np.arange(len(t_names))
    b1 = ax1.barh(y, t_neg, color=t_colors, height=0.6)
    ax1.set_yticks(y)
    ax1.set_yticklabels(t_names, fontsize=7.5, fontweight="bold", color=NAVY)
    ax1.invert_yaxis()
    ax1.set_xlim(0, 545)
    ax1.set_xlabel("Negative (1–3★) Reviews in Corpus (n=1,177 total)", fontsize=7.8, color=SLATE)
    ax1.set_title("A. Negative Review Count & Helpful Votes\n(Gray = Confounded Ops; Blue/Teal = App Software)", fontsize=8.0, fontweight="bold", color=NAVY)
    ax1.grid(axis="x", linestyle=":", alpha=0.4)
    for bar, cnt, th in zip(b1, t_neg, t_thumbs):
        ax1.text(cnt + 6, bar.get_y() + bar.get_height() / 2, f"{cnt} rev (+{th} votes)", va="center", fontsize=7.0, fontweight="bold", color=NAVY)

    g_colors = [RED if g >= 40 else (AMBER if g > 0 else GREEN) for g in t_growth]
    b2 = ax2.barh(y, t_growth, color=g_colors, height=0.6)
    ax2.set_yticks(y)
    ax2.set_yticklabels([i["issueId"] for i in issues_by_vol], fontsize=7.5, fontweight="bold", color=NAVY)
    ax2.invert_yaxis()
    ax2.axvline(0, color=NAVY, linewidth=0.8)
    ax2.set_xlim(-35, 215)
    ax2.set_xlabel("H2 (Apr–Sep 2026) vs. H1 (Oct 2025–Mar 2026) Growth (%)", fontsize=7.8, color=SLATE)
    ax2.set_title("B. 6-Month Issue Trajectory (H2 vs. H1 Newest)\n(ISS-02 +178.6%, ISS-07 +60.0%, ISS-01 +43.6%)", fontsize=8.0, fontweight="bold", color=NAVY)
    ax2.grid(axis="x", linestyle=":", alpha=0.4)
    for bar, g in zip(b2, t_growth):
        offset = 4 if g >= 0 else -30
        ax2.text(g + offset, bar.get_y() + bar.get_height() / 2, f"{g:+.1f}%", va="center", fontsize=7.2, fontweight="bold", color=NAVY)

    plt.tight_layout()
    p3 = FIGURES_DIR / "fig3_theme_prevalence_velocity.png"
    plt.savefig(p3, bbox_inches="tight")
    plt.close(fig)
    paths["fig3"] = p3

    # -------------------------------------------------------------------------
    # FIG 4: Multi-Criteria Prioritization Matrix (Stacked Score Breakdown)
    # -------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(10.2, 3.05), dpi=220)
    fig.patch.set_facecolor("white")

    r_labels = [f"#{i['priorityRank']} {i['issueId']}: {i['shortName']} ({i['estimatedEffortSprints']}sp)" for i in issues]
    p_comp = [i["scoringBreakdown"]["prevalenceAndVisibility"] * 2.5 for i in issues]
    s_comp = [i["scoringBreakdown"]["severityAndImpact"] * 2.2 for i in issues]
    v_comp = [i["scoringBreakdown"]["temporalVelocity"] * 2.0 for i in issues]
    c_comp = [i["scoringBreakdown"]["confidenceAndAttributability"] * 2.3 for i in issues]
    f_comp = [i["scoringBreakdown"]["engineeringFeasibility"] * 1.0 for i in issues]
    totals = [i["priorityScore"] for i in issues]

    y = np.arange(len(r_labels))
    ax.barh(y, p_comp, label="Prevalence & Visibility (25%)", color="#1D4ED8", height=0.58)
    b_s = p_comp
    ax.barh(y, s_comp, left=b_s, label="Severity & Criticality (22%)", color="#DC2626", height=0.58)
    b_v = [a + b for a, b in zip(b_s, s_comp)]
    ax.barh(y, v_comp, left=b_v, label="Temporal Velocity (20%)", color="#D97706", height=0.58)
    b_c = [a + b for a, b in zip(b_v, v_comp)]
    ax.barh(y, c_comp, left=b_c, label="Software Attributability & Confidence (23%)", color="#0D9488", height=0.58)
    b_f = [a + b for a, b in zip(b_c, c_comp)]
    ax.barh(y, f_comp, left=b_f, label="Engineering Feasibility (10%)", color="#16A34A", height=0.58)

    ax.set_yticks(y)
    ax.set_yticklabels(r_labels, fontsize=7.8, fontweight="bold", color=NAVY)
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.set_xlabel("Composite Priority Score (0–100 Scale) = 10 × (0.25·P + 0.22·S + 0.20·V + 0.23·C + 0.10·F)", fontsize=7.8, color=SLATE)
    ax.set_title("Transparent Engineering Prioritization Score Breakdown (Oct 2026 Investigation Baseline, n=3,333 Reviews)", fontsize=8.6, fontweight="bold", color=NAVY, pad=6)
    ax.legend(loc="lower right", fontsize=6.9, ncol=3, frameon=True)
    ax.grid(axis="x", linestyle=":", alpha=0.4)

    for idx, tot in enumerate(totals):
        ax.text(tot + 0.8, y[idx], f"{tot:.2f}/100", va="center", fontsize=7.8, fontweight="bold", color=NAVY)

    plt.tight_layout()
    p4 = FIGURES_DIR / "fig4_priority_matrix.png"
    plt.savefig(p4, bbox_inches="tight")
    plt.close(fig)
    paths["fig4"] = p4

    # -------------------------------------------------------------------------
    # FIG 5: Version Regressions & Monthly Issue Share Shifts
    # -------------------------------------------------------------------------
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.5, 3.05), dpi=220)
    fig.patch.set_facecolor("white")

    vers = [v for v in baseline["versionAnalysis"] if v["version"] != "Unspecified / Missing"][:10]
    vers_sorted = sorted(vers, key=lambda x: x["firstSeenDate"])
    v_labels = [v["version"] + f"\n(n={v['reviewCount']})" for v in vers_sorted]
    v_neg_pct = [v["negative12Pct"] for v in vers_sorted]

    xv = np.arange(len(v_labels))
    v_bars = ax1.bar(xv, v_neg_pct, color=[RED if p >= 30 else (AMBER if p >= 25 else BLUE) for p in v_neg_pct], width=0.58)
    ax1.set_xticks(xv)
    ax1.set_xticklabels(v_labels, rotation=35, ha="right", fontsize=6.9, color=NAVY)
    ax1.set_ylim(0, 42)
    ax1.set_ylabel("1–2★ Negative Review Share (%)", fontsize=7.8, color=SLATE)
    ax1.set_title("A. Negative Review Share by App Version\n(Newest Stream, v12.5 to v12.19.0; v12.19.0 at 34.3% 1–2★)", fontsize=8.2, fontweight="bold", color=NAVY)
    ax1.grid(axis="y", linestyle=":", alpha=0.4)
    for bar, p in zip(v_bars, v_neg_pct):
        ax1.text(bar.get_x() + bar.get_width() / 2, p + 0.8, f"{p:.1f}%", ha="center", fontsize=6.7, fontweight="bold", color=NAVY)

    snaps = data["monthlyMonitoring"]["snapshots"]
    top_codes = ["LIVE_TRACKING_MAP_ETA", "UX_MODALS_NOTIFICATIONS", "CRASH_LAUNCH_INTEGRITY", "BOOKING_ROSTER_SYNC", "AUTH_OTP_SESSION"]
    short_labels = ["ISS-01\nTracking", "ISS-03\nModals/UX", "ISS-02\nCrashes", "ISS-05\nBooking", "ISS-04\nAuth/OTP"]

    def get_m_share(ym_key: str, code: str) -> float:
        for ic in snaps[ym_key]["issueComparisons"]:
            if ic["themeCode"] == code:
                return ic["currentShareOfNegPct"]
        return 0.0

    aug_s = [get_m_share("2026-08", c) for c in top_codes]
    sep_s = [get_m_share("2026-09", c) for c in top_codes]
    oct_s = [get_m_share("2026-10", c) for c in top_codes]

    xm = np.arange(len(short_labels))
    w = 0.25
    ax2.bar(xm - w, aug_s, w, label="2026-08 (n=86 neg)", color="#64748B")
    ax2.bar(xm, sep_s, w, label="2026-09 (n=72 neg)", color=BLUE)
    ax2.bar(xm + w, oct_s, w, label="2026-10 MTD (n=26 neg)", color=RED)
    ax2.set_xticks(xm)
    ax2.set_xticklabels(short_labels, fontsize=7.4, fontweight="bold", color=NAVY)
    ax2.set_ylabel("Share of Monthly 1–3★ Reviews (%)", fontsize=7.8, color=SLATE)
    ax2.set_title("B. Monthly Monitoring: Top Software Issues Share\n(Aug 2026 vs. Sep 2026 vs. Oct 2026 MTD v12.19.0)", fontsize=8.2, fontweight="bold", color=NAVY)
    ax2.legend(loc="upper right", fontsize=6.8, frameon=True)
    ax2.grid(axis="y", linestyle=":", alpha=0.4)

    plt.tight_layout()
    p5 = FIGURES_DIR / "fig5_version_and_monthly_monitoring.png"
    plt.savefig(p5, bbox_inches="tight")
    plt.close(fig)
    paths["fig5"] = p5

    return paths


class NumberedPageCanvas(canvas.Canvas):
    """Custom ReportLab canvas that draws executive headers and 'Page X of 8' footers."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self._draw_header_footer(num_pages)
            super().showPage()
        super().save()

    def _draw_header_footer(self, page_count: int):
        self.saveState()
        w, h = A4
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.6)
        self.line(13 * mm, h - 11.5 * mm, w - 13 * mm, h - 11.5 * mm)

        self.setFont(FONT_BOLD, 7.2)
        self.setFillColor(colors.HexColor(NAVY))
        self.drawString(13 * mm, h - 9.2 * mm, "MOVEINSYNC RATING INTELLIGENCE — EVIDENCE-FIRST FDE INVESTIGATION")
        self.setFont(FONT_REG, 7.2)
        self.setFillColor(colors.HexColor(MUTED))
        self.drawRightString(w - 13 * mm, h - 9.2 * mm, "Target: com.moveinsync.ets | Observed: Oct 13, 2026")

        self.line(13 * mm, 11 * mm, w - 13 * mm, 11 * mm)
        self.setFont(FONT_REG, 6.8)
        self.setFillColor(colors.HexColor(MUTED))
        self.drawString(
            13 * mm,
            7.2 * mm,
            "Source: Verified Google Play Public Evidence (n=3,333 deduplicated reviews; N=114,881 ratings)",
        )
        self.setFont(FONT_BOLD, 7.2)
        self.setFillColor(colors.HexColor(NAVY))
        self.drawRightString(w - 13 * mm, 7.2 * mm, f"Page {self._pageNumber} of {page_count}")
        self.restoreState()


def build_styles() -> Dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "TitleBanner": ParagraphStyle(
            "TitleBanner",
            parent=base["Title"],
            fontName=FONT_BOLD,
            fontSize=13.5,
            leading=16.5,
            textColor=colors.HexColor(NAVY),
            alignment=TA_LEFT,
            spaceAfter=1.2 * mm,
        ),
        "SubBanner": ParagraphStyle(
            "SubBanner",
            parent=base["Normal"],
            fontName=FONT_REG,
            fontSize=7.8,
            leading=10.5,
            textColor=colors.HexColor(SLATE),
            spaceAfter=2.0 * mm,
        ),
        "PageHeader": ParagraphStyle(
            "PageHeader",
            parent=base["Heading1"],
            fontName=FONT_BOLD,
            fontSize=11.8,
            leading=14.5,
            textColor=colors.HexColor(NAVY),
            spaceBefore=0,
            spaceAfter=1.5 * mm,
        ),
        "SectionH2": ParagraphStyle(
            "SectionH2",
            parent=base["Heading2"],
            fontName=FONT_BOLD,
            fontSize=8.9,
            leading=11.2,
            textColor=colors.HexColor(BLUE),
            spaceBefore=1.6 * mm,
            spaceAfter=0.8 * mm,
        ),
        "Body": ParagraphStyle(
            "Body",
            parent=base["Normal"],
            fontName=FONT_REG,
            fontSize=7.5,
            leading=10.1,
            textColor=colors.HexColor("#1E293B"),
            alignment=TA_JUSTIFY,
            spaceAfter=1.1 * mm,
        ),
        "BulletItem": ParagraphStyle(
            "BulletItem",
            parent=base["Normal"],
            fontName=FONT_REG,
            fontSize=7.4,
            leading=9.9,
            leftIndent=9,
            firstLineIndent=-5,
            textColor=colors.HexColor("#1E293B"),
            spaceAfter=0.8 * mm,
        ),
        "Callout": ParagraphStyle(
            "Callout",
            parent=base["Normal"],
            fontName=FONT_REG,
            fontSize=7.4,
            leading=10.0,
            textColor=colors.HexColor(NAVY),
        ),
        "Cell": ParagraphStyle(
            "Cell",
            parent=base["Normal"],
            fontName=FONT_REG,
            fontSize=6.6,
            leading=8.5,
            textColor=colors.HexColor("#1E293B"),
        ),
        "CellHeader": ParagraphStyle(
            "CellHeader",
            parent=base["Normal"],
            fontName=FONT_BOLD,
            fontSize=6.7,
            leading=8.6,
            textColor=colors.white,
        ),
        "Caption": ParagraphStyle(
            "Caption",
            parent=base["Normal"],
            fontName=FONT_ITALIC,
            fontSize=6.7,
            leading=8.5,
            textColor=colors.HexColor(MUTED),
            alignment=TA_CENTER,
            spaceBefore=0.6 * mm,
            spaceAfter=1.2 * mm,
        ),
    }


def make_callout_box(text_html: str, st: Dict[str, ParagraphStyle], bg_hex: str = "#EFF6FF", border_hex: str = BLUE) -> Table:
    p = Paragraph(text_html, st["Callout"])
    t = Table([[p]], colWidths=[184 * mm])
    t.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(bg_hex)),
            ("BOX", (0, 0), (-1, -1), 0.9, colors.HexColor(border_hex)),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ])
    )
    return t


def make_styled_table(rows: List[List[Any]], col_widths: List[float], st: Dict[str, ParagraphStyle], pad: float = 2.6) -> Table:
    formatted_rows = []
    for r_idx, row in enumerate(rows):
        f_row = []
        for cell in row:
            if isinstance(cell, Paragraph):
                f_row.append(cell)
            else:
                style = st["CellHeader"] if r_idx == 0 else st["Cell"]
                f_row.append(Paragraph(str(cell), style))
        formatted_rows.append(f_row)

    t = Table(formatted_rows, colWidths=col_widths, repeatRows=1)
    t.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(NAVY)),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
            ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#CBD5E1")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 3.8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3.8),
            ("TOPPADDING", (0, 0), (-1, -1), pad),
            ("BOTTOMPADDING", (0, 0), (-1, -1), pad),
        ])
    )
    return t


def generate_case_study_pdf() -> Path:
    """Build the exact 8-page MoveInSync Rating Intelligence Case Study PDF."""
    with open(ANALYTICS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    chart_paths = generate_all_charts(data)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(PDF_OUTPUT_PATH),
        pagesize=A4,
        leftMargin=13 * mm,
        rightMargin=13 * mm,
        topMargin=14 * mm,
        bottomMargin=13 * mm,
        title="MoveInSync Rating Intelligence — Evidence-First Investigation Case Study",
        author="Forward Deployed Engineering & Product Analytics Investigation",
    )

    st = build_styles()
    story: List[Any] = []
    issues = data["issuesRegister"]

    # =========================================================================
    # PAGE 1: EXECUTIVE SUMMARY
    # =========================================================================
    story.append(Paragraph("PAGE 1 — EXECUTIVE SUMMARY: MOVEINSYNC GOOGLE PLAY INVESTIGATION", st["TitleBanner"]))
    story.append(
        Paragraph(
            "<b>Target Application:</b> MoveInSync (<font name='Courier'>com.moveinsync.ets</font>) | "
            "<b>Developer:</b> MoveInSync: Enabling Hybrid Workplaces (ID: <font name='Courier'>7798917469890870335</font>) | "
            "<b>Observed:</b> Oct 13, 2026 | <b>Evidence Corpus:</b> n = 3,333 Verified Deduplicated Reviews",
            st["SubBanner"],
        )
    )

    story.append(
        make_callout_box(
            "<b>CORE INVESTIGATION VERDICT (THE STOREFRONT MASKING ILLUSION):</b><br/>"
            "While MoveInSync's India Google Play storefront displays a <b>4.64★</b> lifetime score (and <b>4.32★</b> on the US storefront "
            "across <b>114,881</b> ratings and <b>3,217,985</b> installs), <b>substantive written reviews reveal severe product dissatisfaction</b>. "
            "Across the <b>3,000 newest reviews</b> (Sep 2025–Oct 2026), <b>46.9% (n=1,407)</b> are 1–2 word micro-reviews (<i>'good'</i>, <i>'nice'</i>, "
            "averaging <b>4.64★</b>) generated by an un-skippable post-ride rating modal. Among commuters writing <b>substantive feedback (≥6 words, n=1,066)</b>, "
            "mean rating drops to <b>2.71★ (54.5% 1–2★)</b>; for <b>detailed reviews (≥15 words, n=483)</b>, it collapses to <b>2.19★ (67.1% 1–2★)</b>; "
            "and Google Play's default <b>'Most Relevant' storefront view (n=600) averages 2.11★ (67.7% 1–2★, 77.7% 1–3★)</b>.",
            st,
            bg_hex="#FEF2F2",
            border_hex=RED,
        )
    )
    story.append(Spacer(1, 1.5 * mm))

    story.append(Paragraph("1.1 The Business Problem & Verified Evidence Baseline", st["SectionH2"]))
    story.append(
        Paragraph(
            "MoveInSync powers daily office commutes for over 3.2 million enterprise employees. However, prospective enterprise buyers and "
            "employees visiting Google Play encounter a wall of 1-star complaints (averaging <b>2.11★</b> in <i>Most Relevant</i> and <b>2.30★</b> "
            "among substantive ≥6-word reviews in October 2026 MTD on <font name='Courier'>v12.19.0</font>). Moreover, MoveInSync ceased replying "
            "to Google Play reviews after <b>February 2, 2026</b> (>8 months of silence), and <b>38 long-time users</b> who previously left positive "
            "reviews edited their ratings down to <b>1★</b> in 2025–2026.",
            st["Body"],
        )
    )

    kpi_rows = [
        ["Metric / Cohort (Observed Oct 13, 2026)", "Value / Rating", "1–2★ Negative Share", "Evidence Classification & Diagnostic Role"],
        ["Storefront Aggregate — India (gl=in)", "4.64★ (114,881 ratings)", "7.1% (8,154 ratings)", "Verified Observation — Masked by 91,256 textless taps"],
        ["Storefront Aggregate — US (gl=us)", "4.32★ (114,881 ratings)", "12.6% (14,517 ratings)", "Verified Observation — Regional recency weighting"],
        ["Chronological Newest Sample (n=3,000)", "3.83★ (Sep '25–Oct '26)", "27.1% (814 reviews)", "Reproducible Result — 12.6-month full public window"],
        ["Micro-Reviews: 1–2 Words (n=1,407)", "4.64★ (46.9% of Newest)", "7.3% (103 reviews)", "Confounder — Driven by forced post-ride rating modal"],
        ["Substantive Reviews: ≥6 Words (n=1,066)", "2.71★ (35.5% of Newest)", "54.5% (581 reviews)", "Core Diagnostic Signal — Genuine user experience"],
        ["Detailed Reviews: ≥15 Words (n=483)", "2.19★ (16.1% of Newest)", "67.1% (324 reviews)", "Severe Workflow Failure — Multi-point bug reports"],
        ["Default Storefront 'Most Relevant' (n=600)", "2.11★ (2018–2026)", "67.7% (406 reviews)", "High Visibility Risk — Default visitor impression"],
    ]
    story.append(make_styled_table(kpi_rows, [53 * mm, 35 * mm, 33 * mm, 63 * mm], st, pad=2.2))

    story.append(Paragraph("1.2 First-Priority Engineering Decision & Immediate Next Action", st["SectionH2"]))
    story.append(
        Paragraph(
            "Ranking purely by raw complaint count would select <b>Fleet Operations &amp; Cab Delays (ISS-08, 429 negative reviews, 36.4%)</b>. "
            "However, fleet supply, driver conduct, and route-clubbing rules are governed by third-party vendors and client transport admins—not "
            "mobile app code. Our 5-factor prioritization model (<b>Prevalence 25%, Severity 22%, Velocity 20%, Software Attributability 23%, "
            "Feasibility 10%</b>) establishes a focused two-track engineering intervention:",
            st["Body"],
        )
    )
    story.append(
        Paragraph(
            "• <b>Primary Priority (#1 — ISS-01: Live Vehicle Tracking Freeze, Map Auto-Zoom Reset &amp; Offline Boarding Cache, Score 86.46/100):</b> "
            "Backed by <b>230 negative reviews (+882 helpful votes, #1 software complaint on the storefront)</b> plus <b>103 4–5★ caveat reviews</b> "
            "(+43.6% H2 growth). <i>Action:</i> Lock map camera state after user pinch-zoom (<font name='Courier'>REASON_GESTURE</font>), cache active "
            "trip + Boarding OTP in local Room/SQLite storage for zero-network basements, and display live GPS staleness badges.",
            st["BulletItem"],
        )
    )
    story.append(
        Paragraph(
            "• <b>Parallel Week-1 Hotfixes (#2 — ISS-03: Blocking Modals, 85.16/100 &amp; #3 — ISS-02: Launch Crashes / Play Store Block, 80.80/100, "
            "+178.6% H2 surge):</b> Unblock Boarding OTP from the <font name='Courier'>v12.19.0</font> seatbelt modal, add a <i>'Skip'</i> CTA to the "
            "forced ride-rating prompt, and whitelist Android 16/17 package installers in the Play Store integrity check.",
            st["BulletItem"],
        )
    )
    story.append(Image(str(chart_paths["fig1"]), width=182 * mm, height=54 * mm))
    story.append(
        Paragraph(
            "Figure 1: Verified Storefront vs. Written Review Cohorts and Review-Length Bifurcation (com.moveinsync.ets, Observed Oct 13, 2026).",
            st["Caption"],
        )
    )
    story.append(PageBreak())

    # =========================================================================
    # PAGE 2: INVESTIGATION METHODOLOGY & EVIDENCE VERIFICATION
    # =========================================================================
    story.append(Paragraph("PAGE 2 — INVESTIGATION METHODOLOGY & APPLICATION VERIFICATION", st["PageHeader"]))
    story.append(Paragraph("2.1 Official Application Identity & Ecosystem Disambiguation", st["SectionH2"]))
    story.append(
        Paragraph(
            "We verified all applications on Google Play published by <b>MoveInSync Technology Solutions Private Limited</b> "
            "(Developer Profile: <b>MoveInSync: Enabling Hybrid Workplaces</b>, ID <font name='Courier'>7798917469890870335</font>, "
            "<font name='Courier'>app@moveinsync.com</font>, <font name='Courier'>https://www.moveinsync.com/</font>). Across 7 published apps, "
            "<b>MoveInSync (<font name='Courier'>com.moveinsync.ets</font>)</b> represents <b>99.3% of all ratings (114,881)</b> and "
            "<b>94.8% of all installs (3,217,985)</b>, confirming it as the primary investigation target.",
            st["Body"],
        )
    )

    eco_rows = [
        ["Application Title", "Package Identifier (appId)", "Role in Ecosystem", "Real Installs", "IN Score (Ratings / Reviews)", "Latest Version (Updated)"],
        ["MoveInSync (PRIMARY TARGET)", "com.moveinsync.ets", "Employee Commute & Workplace", "3,217,985", "4.64★ (114,881 / 23,625)", "v12.19.0 (Oct 8, 2026)"],
        ["Moveinsync Partner - Lite", "com.moveinsync.driver.lite", "Driver Trip Execution & GPS", "143,072", "4.25★ (703 / 111)", "Varies with device"],
        ["MoveInSync - Driver Partner", "com.moveinsync.driver.dco", "Driver Onboarding & KYC", "19,905", "3.50★ (46 / 7)", "Varies with device"],
        ["MoveInSync - Field app", "field.moveinsync.ets", "Transport Supervisor / Admin", "6,774", "4.08★ (24 / 8)", "v1.0.92 (Sep 29, 2026)"],
        ["MoveInSync Workplace", "com.workinsync.meeting", "Meeting Room Kiosk Tablet", "5,583", "Unrated (0 / 0)", "Varies with device"],
        ["Driver Book / TransitInSync", "driverbook / publictransit", "Auxiliary Internal Tools", "442 combined", "Unrated (0 / 0)", "Varies with device"],
    ]
    story.append(make_styled_table(eco_rows, [38 * mm, 38 * mm, 35 * mm, 19 * mm, 31 * mm, 23 * mm], st, pad=2.0))

    story.append(Paragraph("2.2 Evidence Collection Protocol, Deduplication & Separation of Layers", st["SectionH2"]))
    story.append(
        Paragraph(
            "Public evidence was collected on <b>October 13, 2026 (03:20 UTC+05:30)</b> using legitimate, rate-limited requests via "
            "<font name='Courier'>google-play-scraper</font> (<font name='Courier'>hl=en&amp;gl=in</font> and <font name='Courier'>gl=us</font>). "
            "When live collection is restricted, the system provides a full CSV/JSON import workflow (<font name='Courier'>POST /api/import</font>).",
            st["Body"],
        )
    )
    story.append(
        Paragraph(
            "• <b>Stream A — Chronological Newest (<font name='Courier'>Sort.NEWEST</font>, n = 3,000):</b> Captures 100% of publicly accessible "
            "English reviews posted between <b>Sep 22, 2025 and Oct 11, 2026</b> (12.6 months) for unbiased temporal and version analysis.",
            st["BulletItem"],
        )
    )
    story.append(
        Paragraph(
            "• <b>Stream B — Storefront Most Relevant (<font name='Courier'>Sort.MOST_RELEVANT</font>, n = 600):</b> Captures the high-visibility "
            "reviews ranked first by Google Play's helpfulness algorithm (spanning <b>Sep 21, 2018 to Sep 19, 2026</b>).",
            st["BulletItem"],
        )
    )
    story.append(
        Paragraph(
            "• <b>Two-Tier Deduplication &amp; Data Separation:</b> Merging Streams A and B (3,600 raw records) removed <b>267 exact overlaps</b> "
            "via stable <font name='Courier'>reviewId</font> UUIDs, yielding <b>3,333 unique verified reviews</b>. For imported records without UUIDs, "
            "a fallback SHA-256 hash (<font name='Courier'>sha256(user|text|YYYY-MM-DD|score)</font>) prevents double-counting. Raw files (<font name='Courier'>data/raw/</font>), "
            "cleaned records (<font name='Courier'>data/processed/</font>), audit overrides (<font name='Courier'>data/validation/</font>), and analytics "
            "(<font name='Courier'>data/analytics/</font>, <font name='Courier'>movesync_intelligence.db</font>) are kept strictly separate.",
            st["BulletItem"],
        )
    )

    story.append(Paragraph("2.3 Classifier Validation Against Actual Reviews & Known Limitations", st["SectionH2"]))
    val = data["classifierValidation"]
    val_rows = [
        ["Theme Code & Short Name", "TP", "FP", "FN", "Precision", "Recall", "F1 Score", "Validation Audit Notes (n=120 Stratified Sample)"],
    ]
    for tcode, m in val["perThemeMetrics"].items():
        val_rows.append([
            f"{tcode} ({m['themeName']})",
            str(m["truePositives"]),
            str(m["falsePositives"]),
            str(m["falseNegatives"]),
            f"{m['precision']:.3f}",
            f"{m['recall']:.3f}",
            f"{m['f1Score']:.3f}",
            "Verified against actual review text; UI override supported",
        ])
    val_rows.append([
        "MICRO-AVERAGED BENCHMARK TOTAL",
        "—",
        "—",
        "—",
        f"{val['microPrecision']:.3f}",
        f"{val['microRecall']:.3f}",
        f"{val['microF1']:.3f}",
        f"Exact multi-label match on {val['exactSetMatchCount']}/{val['sampleSize']} ({val['exactSetMatchRate']*100:.1f}%) reviews",
    ])
    story.append(make_styled_table(val_rows, [52 * mm, 8 * mm, 8 * mm, 8 * mm, 15 * mm, 13 * mm, 14 * mm, 66 * mm], st, pad=1.9))
    story.append(Spacer(1, 1.5 * mm))
    story.append(
        make_callout_box(
            "<b>KEY METHODOLOGICAL LIMITATIONS &amp; HONESTY BOUNDARIES:</b><br/>"
            "1) <b>Sample vs. Population:</b> The 3,333 collected reviews represent <b>14.1%</b> of 23,625 lifetime written reviews and <b>2.9%</b> of "
            "114,881 total ratings. Findings apply to the verified 2025–2026 written cohort and storefront view, never extrapolated to silent tap raters.<br/>"
            "2) <b>Missing Version Field:</b> <b>9.7%</b> of newest reviews (291/3,000) and <b>12.6%</b> overall (419/3,333) omit <font name='Courier'>reviewCreatedVersion</font>.<br/>"
            "3) <b>Terminology Confounder:</b> Commuters frequently write <i>'login/logout'</i> to describe morning pickup and evening drop-off shifts rather "
            "than authentication; our sub-issue rules and manual overrides explicitly separate shift scheduling from auth failures.",
            st,
            bg_hex="#F8FAFC",
            border_hex=SLATE,
        )
    )
    story.append(PageBreak())

    # =========================================================================
    # PAGE 3: RATING BASELINE & TEMPORAL ANALYSIS
    # =========================================================================
    story.append(Paragraph("PAGE 3 — RATING BASELINE, DISTRIBUTION & TEMPORAL TRENDS", st["PageHeader"]))
    story.append(Paragraph("3.1 Storefront Lifetime Rating vs. Written Review Cohorts", st["SectionH2"]))
    story.append(
        Paragraph(
            "Because historical storefront aggregate snapshots prior to October 13, 2026 do not exist publicly, we establish the "
            "<b>first verified storefront baseline</b> (4.64★ IN / 4.32★ US) and measure temporal trends strictly from verified review "
            "timestamps (<font name='Courier'>at</font>). Comparing the storefront histogram to collected written cohorts exposes the polarization:",
            st["Body"],
        )
    )

    dist_rows = [
        ["Cohort / Dataset", "Total Count", "Mean ★", "5★ Share", "4★ Share", "3★ Share", "2★ Share", "1★ Share", "1–2★ Negative"],
        ["Play Store Lifetime — India (gl=in)", "114,881 ratings", "4.64★", "85.5%", "6.3%", "1.1%", "0.7%", "6.4%", "7.1% (8,154)"],
        ["Play Store Lifetime — US (gl=us)", "114,881 ratings", "4.32★", "72.0%", "12.9%", "1.9%", "0.8%", "11.8%", "12.6% (14,517)"],
        ["Newest Written Reviews (Sep '25–Oct '26)", "3,000 reviews", "3.83★", "63.8%", "6.4%", "2.6%", "2.9%", "24.2%", "27.1% (814)"],
        ["Substantive Newest (≥6 words)", "1,066 reviews", "2.71★", "33.1%", "6.8%", "5.6%", "7.1%", "47.4%", "54.5% (581)"],
        ["Storefront 'Most Relevant' Stream", "600 reviews", "2.11★", "14.2%", "8.2%", "10.0%", "9.8%", "57.8%", "67.7% (406)"],
    ]
    story.append(make_styled_table(dist_rows, [49 * mm, 22 * mm, 14 * mm, 15 * mm, 15 * mm, 15 * mm, 15 * mm, 15 * mm, 24 * mm], st, pad=2.2))
    story.append(Spacer(1, 1.5 * mm))

    story.append(Image(str(chart_paths["fig2"]), width=182 * mm, height=55 * mm))
    story.append(
        Paragraph(
            "Figure 2: Monthly Review Volume by Rating Tier and Mean Rating Trajectory (Sort.NEWEST, n=3,000, Sep 22, 2025 – Oct 11, 2026).",
            st["Caption"],
        )
    )

    story.append(Paragraph("3.2 Comparable Time-Period Trends, Version Regressions & Developer Silence", st["SectionH2"]))
    p_h1 = data["baseline"]["comparablePeriods"]["h1_2025_10_to_2026_03"]
    p_h2 = data["baseline"]["comparablePeriods"]["h2_2026_04_to_2026_09"]
    p_oct = data["baseline"]["comparablePeriods"]["oct_2026_mtd"]

    story.append(
        Paragraph(
            f"• <b>Comparable 6-Month Halves (H1 vs. H2):</b> Across the 12 complete calendar months, review volume rose <b>+24.9%</b> from "
            f"<b>H1 (Oct 2025–Mar 2026, n={p_h1['count']})</b> to <b>H2 (Apr 2026–Sep 2026, n={p_h2['count']})</b>. While overall mean rating "
            f"appeared steady ({p_h1['meanRating']}★ vs. {p_h2['meanRating']}★) due to 1-word ride ratings, software complaints accelerated "
            f"sharply in H2: <b>Startup Crashes &amp; Play Store Blocks (+178.6%)</b>, <b>Mobile Data Network Bugs (+60.0%)</b>, and "
            f"<b>Live Tracking/Map Bugs (+43.6%)</b>.",
            st["BulletItem"],
        )
    )
    story.append(
        Paragraph(
            f"• <b>Recent Release Regression (<font name='Courier'>v12.19.0</font>, Oct 2026 MTD):</b> In October 2026 (n={p_oct['count']} reviews "
            f"through Oct 11), overall mean rating fell to <b>{p_oct['meanRating']}★ (30.5% 1–2★)</b>, and substantive (≥6 words) mean rating hit an "
            f"all-year low of <b>2.30★ (66.7% 1–2★)</b>. Version <font name='Courier'>12.19.0</font> (n=105 reviews) averages <b>3.62★ (34.3% 1–2★)</b> "
            f"compared to <b>4.04★ (22.9% 1–2★)</b> on <font name='Courier'>v12.15.0</font> and <b>4.02★ (22.3% 1–2★)</b> on <font name='Courier'>v12.12.3</font>.",
            st["BulletItem"],
        )
    )
    story.append(
        Paragraph(
            "• <b>Forced Rating Confounder &amp; Support Abandonment:</b> Reviewers explicitly document why 1-word ratings flood the store: "
            "<i>'forcing me to give rating after every ride, so I came here to give you 1 star. because if I don't rate, I can't use the app as there is "
            "no skip option'</i> (<font name='Courier'>id=f9fce9fe</font>, Oct 8, 2026, <font name='Courier'>v12.19.0</font>). Meanwhile, MoveInSync's "
            "developer reply rate on 1–2★ newest reviews is <b>3.81% (31/814)</b>, with <b>zero new replies after February 2, 2026</b>.",
            st["BulletItem"],
        )
    )
    story.append(PageBreak())

    # =========================================================================
    # PAGE 4: ROOT-CAUSE COMPLAINT THEMES
    # =========================================================================
    story.append(Paragraph("PAGE 4 — ROOT-CAUSE INVESTIGATION OF DISSATISFACTION THEMES", st["PageHeader"]))
    story.append(
        Paragraph(
            "Analyzing all <b>1,177 negative/neutral (1–3★) reviews</b> (and cross-checking <b>2,156 positive 4–5★ reviews</b> for caveats and "
            "contradictory experiences) identifies <b>8 distinct themes</b>. Below, we distinguish <b>reported user symptoms</b> from "
            "<b>technical root-cause hypotheses</b> and isolate external operational confounders.",
            st["Body"],
        )
    )

    story.append(Image(str(chart_paths["fig3"]), width=182 * mm, height=53 * mm))
    story.append(
        Paragraph(
            "Figure 3: Negative Review Counts, Helpful Votes, and H2 vs. H1 Growth Across All 8 Investigation Themes (n=1,177 neg).",
            st["Caption"],
        )
    )

    # Ensure each theme displays a distinct signature review quote
    used_quote_ids = set()
    theme_table_rows = [
        ["ID & Theme (Trajectory)", "Neg Rev (Votes) & ★", "Reported Symptom vs. Technical Hypothesis & Representative Review Citation", "Contradictory Positives, Confounders & Confidence"],
    ]
    for iss in sorted(issues, key=lambda x: x["priorityRank"]):
        chosen_rep = iss["representativeReviews"][0]
        for cand in iss["representativeReviews"]:
            if cand["reviewId"] not in used_quote_ids:
                chosen_rep = cand
                used_quote_ids.add(cand["reviewId"])
                break
        excerpt = chosen_rep["content"][:98] + ("..." if len(chosen_rep["content"]) > 98 else "")
        theme_table_rows.append([
            f"<b>{iss['issueId']}: {iss['shortName']}</b><br/><i>{iss['trendStatus']}</i>",
            f"<b>{iss['negCountTotal']}</b> ({iss['negShareOfCorpusPct']}%)<br/>+{iss['thumbsUpTotal']} votes<br/>Avg: <b>{iss['avgScoreNeg']}★</b> ({iss['oneStarPctNeg']}% 1★)",
            f"<b>Symptom:</b> {iss['reportedSymptomVsRootCause']['reportedUserSymptom'][:92]}...<br/>"
            f"<b>Cite [{chosen_rep['reviewId'][:8]}, {chosen_rep['date']}]:</b> <i>\"{excerpt}\"</i>",
            f"<b>Positives:</b> {iss['posMentionCount']} (4–5★) | <b>Conf:</b> {iss['confidenceLevel']} (F1={iss['classifierValidation']['f1Score']:.2f})<br/>"
            f"<b>Confounder:</b> {iss['confoundersAndLimitations'][:82]}...",
        ])

    story.append(make_styled_table(theme_table_rows, [34 * mm, 25 * mm, 73 * mm, 52 * mm], st, pad=1.8))
    story.append(PageBreak())

    # =========================================================================
    # PAGE 5: ISSUE PRIORITIZATION & SCORING MODEL
    # =========================================================================
    story.append(Paragraph("PAGE 5 — TRANSPARENT ISSUE PRIORITIZATION MATRIX & RATIONALE", st["PageHeader"]))
    story.append(Paragraph("5.1 Multi-Criteria Scoring Formula, Weights & Assumptions", st["SectionH2"]))
    story.append(
        Paragraph(
            "To avoid ranking raw complaint frequency first, each issue is scored on a 0–100 composite index combining five dimensions (0–10): "
            "<b>PriorityScore = 10 × (0.25·P + 0.22·S + 0.20·V + 0.23·C + 0.10·F)</b>. "
            "<b>P (Prevalence &amp; Visibility, 25%)</b> combines total mentions (35%), helpful votes (40%), and Most Relevant presence (25%); "
            "<b>S (Severity, 22%)</b> combines commute critical-path blocking (55%), 1★ concentration (25%), and rating deficit (20%); "
            "<b>V (Velocity, 20%)</b> combines H2 vs. H1 growth (65%) and last-60-day density (35%); "
            "<b>C (Software Attributability &amp; Confidence, 23%)</b> weights direct MoveInSync software ownership vs. external operational confounding (70%) "
            "and classifier F1 (30%); and <b>F (Feasibility, 10%)</b> represents inverse sprint effort.",
            st["Body"],
        )
    )

    story.append(Image(str(chart_paths["fig4"]), width=182 * mm, height=52 * mm))
    story.append(
        Paragraph(
            "Figure 4: Weighted Component Breakdown of Composite Engineering Priority Scores Across All 8 Verified Issues (Oct 2026).",
            st["Caption"],
        )
    )

    prio_rows = [
        ["Rank & ID", "Issue Name", "P (25%)", "S (22%)", "V (20%)", "C (23%)", "F (10%)", "Score", "Effort & Owner", "Primary Recommended Action"],
    ]
    for iss in issues:
        sb = iss["scoringBreakdown"]
        prio_rows.append([
            f"<b>#{iss['priorityRank']} ({iss['issueId']})</b>",
            iss["shortName"],
            f"{sb['prevalenceAndVisibility']:.1f}",
            f"{sb['severityAndImpact']:.1f}",
            f"{sb['temporalVelocity']:.1f}",
            f"{sb['confidenceAndAttributability']:.1f}",
            f"{sb['engineeringFeasibility']:.1f}",
            f"<b>{iss['priorityScore']:.2f}</b>",
            f"{iss['estimatedEffortSprints']} sp | {iss['suggestedOwner'][:22]}...",
            iss["recommendedAction"][:95] + "...",
        ])
    story.append(make_styled_table(prio_rows, [17 * mm, 27 * mm, 11 * mm, 11 * mm, 11 * mm, 11 * mm, 11 * mm, 13 * mm, 26 * mm, 46 * mm], st, pad=1.9))
    story.append(Spacer(1, 1.5 * mm))

    story.append(
        make_callout_box(
            "<b>WHY #1 (ISS-01: LIVE TRACKING, MAP ZOOM &amp; ETA — 86.46/100) BEATS RAW-VOLUME LEADER ISS-08 (FLEET OPS — 74.17/100):</b><br/>"
            "1) <b>Ownership Boundary:</b> Although <b>ISS-08 (Fleet Ops)</b> has 429 negative reviews (36.4%), MoveInSync's own developer response "
            "(<font name='Courier'>2018-08-16</font>) states: <i>'Path planning is not done by app. It just publishes data. Planning is done by your company "
            "transport team.'</i> Mobile engineers cannot code away city traffic, vendor shortages, or client cost-clubbing rules (<b>C = 5.1/10</b>).<br/>"
            "2) <b>Storefront Impact &amp; Software Control:</b> <b>ISS-01</b> is the <b>#1 most-upvoted software complaint</b> on Google Play's default "
            "storefront view (<b>+882 helpful votes across 230 negative reviews + 103 4–5★ caveat reviews = 333 total mentions</b>, +43.6% in H2). Fixing "
            "map camera auto-zoom resets and caching active trip/OTP data locally is <b>100% software-controllable (C = 9.0/10)</b> within <b>2 sprints</b>.<br/>"
            "3) <b>Sequenced Execution:</b> Because <b>ISS-03 (Blocking Modals, 85.16/100, 1.0 sp)</b> and <b>ISS-02 (Launch Crashes / Play Store Block, "
            "80.80/100, +178.6% H2 surge)</b> require low-effort client patches, we schedule them as a <b>Week-1 Parallel Hotfix</b> while the core "
            "telemetry squad executes the 2-sprint <b>ISS-01</b> stabilization.",
            st,
            bg_hex="#EFF6FF",
            border_hex=BLUE,
        )
    )
    story.append(PageBreak())

    # =========================================================================
    # PAGE 6: ENGINEERING RECOMMENDATION & IMPLEMENTATION PLAN
    # =========================================================================
    story.append(Paragraph("PAGE 6 — PRIMARY ENGINEERING RECOMMENDATION & EXECUTION PLAN", st["PageHeader"]))
    story.append(Paragraph("6.1 Proposed Engineering Change: Commute Telemetry & Offline Boarding Pack", st["SectionH2"]))
    story.append(
        Paragraph(
            "Our primary recommendation targets <b>ISS-01 (Live Tracking, Map Auto-Zoom &amp; Offline Boarding Cache)</b> alongside the "
            "<b>Week-1 Hotfix for ISS-03/ISS-02</b>. Every engineering component maps directly to verified review evidence:",
            st["Body"],
        )
    )

    eng_rows = [
        ["Engineering Component", "Verified User Evidence & Citation IDs", "Proposed Technical Change", "First Implementation Step (Days 1–12)"],
        [
            "1. Map Camera Gesture Lock\n(ISS-01 Primary)\nMapTrackingFragment",
            "• id=fdc328ac (Nov 7, 2025, v12.6, +10 votes): 'poor logic of setting zoom level and automatically reset it every 30 seconds... keep one point at a time in focus'\n• id=8e9b5aa8 (+51 votes) & id=d291343a (+15 votes)",
            "Register GoogleMap.OnCameraMoveStartedListener. When REASON_GESTURE is detected, set isUserCameraLocked=true and suppress automatic animateCamera(LatLngBounds) on 5–30s GPS ticks. Add floating 'Re-center' button.",
            "Day 1–3: Patch onLocationTick() camera update guard and default active-boarding bounds to [UserPickup, CabLocation] rather than distant office destination."
        ],
        [
            "2. Offline-First Active Trip & Boarding OTP Cache\n(ISS-01 Primary)\nTripCacheRepository",
            "• id=e12ed49a (Sep 30, 2026, v12.11.2): 'Why is there not some cache wherein a user has their ride details stored? instead it needs a network call every time... underground'\n• id=138265c4 (+28 votes) & id=d980e749",
            "Persist active TripAssignment, driver masked contact, route stops, Boarding/Drop OTPs, and Metro QR payloads in encrypted local Room/SQLite storage upon trip allocation push/sync.",
            "Day 4–8: Implement ActiveTripLocalDao with local-first rendering (<150ms cold start in Airplane/basement mode) + 'Synced Xm ago' banner."
        ],
        [
            "3. Telemetry Staleness Pill & Pre-Trip Window\n(ISS-01 Primary)\nEtaEngine",
            "• id=2ce14584 (Oct 8, 2026, v12.19.0): 'google maps always shows 3x the time shown in moveinsync'\n• id=61a4a85f (Oct 7, 2026, v12.19.0): 'wont let you track the location of the van under an hour'",
            "Display live 'GPS updated Xs ago' badge on cab card; trigger SMS fallback if driver telemetry is stale >90s; restore pre-60-minute cab tracking visibility removed in v12.19.0.",
            "Day 9–12: Expose telemetry timestamp delta in trip sheet UI and revert v12.19.0 60-minute tracking gate."
        ],
        [
            "4. Parallel Week-1 Hotfix: Boarding Modal & Installer Guard\n(ISS-03 & ISS-02)",
            "• id=3d87f169 (Oct 9, 2026): 'click view otp, it pops up seat belt safely first'\n• id=f9fce9fe (Oct 8, 2026): 'no skip option' on rating\n• id=4f55dc55 & id=93d75126 (Sep 24, 2026): fake 'not downloaded from play store' error",
            "(a) Render Boarding OTP inline without seatbelt modal interception; (b) Add 'Skip' button to post-ride rating modal; (c) Whitelist Android 16/17 package installer in Play Integrity check + self-heal corrupted local cache.",
            "Day 1–5 (Hotfix Branch v12.20.1): Ship non-blocking OTP/Skip UI and wrap cold-start storage init in try/catch cache recovery."
        ],
    ]
    story.append(make_styled_table(eng_rows, [34 * mm, 49 * mm, 54 * mm, 47 * mm], st, pad=2.5))
    story.append(Spacer(1, 2.0 * mm))

    story.append(Paragraph("6.2 Required Internal Validation, Dependencies & Technical Risks", st["SectionH2"]))
    story.append(
        Paragraph(
            "• <b>Required Pre-Release Validation (Separating Symptom from Root Cause):</b> Because public Play Store reviews do not include "
            "server logs or stack traces, engineering must validate three internal questions before 100% rollout: "
            "(1) What proportion of frozen vehicle pins stems from driver smartphones throttling background GPS in <font name='Courier'>com.moveinsync.driver.lite</font> "
            "versus WebSocket consumer lag? (2) Which specific Android 16/17 OEM package installer string triggers the false "
            "<i>'not downloaded from Play Store'</i> dialog in <font name='Courier'>v12.18.1–v12.19.0</font>? (3) Do any enterprise client contracts "
            "mandate blocking OTP display behind seatbelt confirmation?",
            st["BulletItem"],
        )
    )
    story.append(
        Paragraph(
            "• <b>Technical Dependencies:</b> Google Maps Android SDK gesture listener refactor; Android Room encrypted storage migration; "
            "Driver Partner Lite location timestamp headers; InfoSec approval on Play Integrity API verdict rules.",
            st["BulletItem"],
        )
    )
    story.append(
        Paragraph(
            "• <b>Key Implementation Risk &amp; Mitigation:</b> Caching trip/OTP details offline introduces a risk that an employee in a basement "
            "views a cached cab plate number that was dynamically re-allocated 5 minutes prior. <i>Mitigation:</i> Display an amber "
            "<i>'Offline Mode — Showing cab assigned at HH:MM. Reconnect at surface to verify live changes'</i> badge whenever network is unreachable.",
            st["BulletItem"],
        )
    )
    story.append(PageBreak())

    # =========================================================================
    # PAGE 7: MEASUREMENT PLAN, GUARDRAILS & ACTION TRACKING
    # =========================================================================
    story.append(Paragraph("PAGE 7 — MEASUREMENT PLAN, TARGETS, GUARDRAILS & ACTION TRACKER", st["PageHeader"]))
    story.append(Paragraph("7.1 Baseline vs. Proposed Target Metrics & Evaluation Window", st["SectionH2"]))
    story.append(
        Paragraph(
            "All baselines below are <b>Verified Observations</b> from our October 13, 2026 investigation. All targets are explicitly "
            "labelled as <b>Proposed Targets</b> requiring post-deployment validation—we do not promise an immediate storefront headline "
            "rating jump because the 4.64★ lifetime average is anchored by 114,881 historical ratings.",
            st["Body"],
        )
    )

    meas_rows = [
        ["Metric Name & Scope", "Verified Baseline (Oct 13, 2026)", "Proposed Target (Post-Release)", "Measurement Method & Cohort Window"],
        [
            "1. Primary: ISS-01 Negative Share (LIVE_TRACKING_MAP_ETA)",
            "19.5% of 1–3★ corpus (11.4% Newest 1–3★; 29.3% Most Relevant 1–3★; 230 rev)",
            "≤ 6.0% of monthly 1–3★ reviews (Proposed Target: ≥45% relative reduction)",
            "Monthly classification run on Sort.NEWEST filtering for target release (v ≥ 12.21.0) at Day 30 & Day 60."
        ],
        [
            "2. Sub-Issue: Map Auto-Zoom & Offline OTP Complaints",
            "23 explicit reviews (+562 helpful votes) citing map zoom reset or no offline cache",
            "0 new reviews citing map auto-zoom reset or missing offline OTP on v ≥ 12.21.0",
            "Sub-issue regex detector (map_auto_zoom_reset, offline_trip_cache_missing) + manual analyst audit."
        ],
        [
            "3. Hotfix: False Play Store Block & Startup Crashes (ISS-02)",
            "8.5% of 1–3★ corpus (100 reviews; +178.6% H2 surge; 21 in last 60 days)",
            "0 'not downloaded from Play Store' reports; ≤ 3.0% monthly crash share within 30d",
            "Monthly review cohort check on v ≥ 12.20.1 paired with Play Console Android Vitals crash-free rate."
        ],
        [
            "4. Hotfix: Forced Rating & Seatbelt/OTP Friction (ISS-03)",
            "17.5% of 1–3★ corpus (206 reviews; 28 in last 60 days; 34.3% 1–2★ on v12.19.0)",
            "≤ 8.0% of monthly 1–3★ reviews; 0 retaliatory 1★ reviews citing 'no skip option'",
            "Sub-issue audit (otp_blocked_by_seatbelt_modal, forced_rating_no_skip) at Day 30 & Day 45."
        ],
        [
            "5. North-Star Quality: Substantive Review Mean Rating (≥6w)",
            "2.71★ (12m Newest baseline; 2.62★ in Sep 2026; 2.30★ in Oct 2026 MTD)",
            "≥ 3.25★ mean rating on substantive written reviews (≥6 words) within 60 days",
            "Stratified mean star score of reviews with wordCount ≥ 6 (eliminating 1-word micro-review distortion)."
        ],
        [
            "6. Operational SLA: Developer Review Response Rate",
            "3.81% on 1–2★ Newest (0% new replies since Feb 2, 2026; 8.3 months silent)",
            "≥ 80.0% response rate on substantive 1–2★ reviews within 48 hours",
            "Monthly audit of replyContent and (repliedAt - at) latency in monthly investigation pipeline."
        ],
    ]
    story.append(make_styled_table(meas_rows, [38 * mm, 44 * mm, 46 * mm, 56 * mm], st, pad=1.9))

    story.append(Paragraph("7.2 Guardrail Metrics & Continuation / Modification / Reversal Conditions", st["SectionH2"]))
    story.append(
        Paragraph(
            "• <b>Guardrail Effect on 5★ Tap Volume:</b> Adding a <i>'Skip'</i> button to the forced post-ride rating modal (ISS-03) will stop "
            "retaliatory 1★ written reviews, but may also reduce coerced 1-word 5★ ratings (<i>'good'</i>). Success must be evaluated via "
            "<b>Substantive Written Review Mean Rating (≥6 words)</b> and <b>Issue-Specific Negative Share</b> rather than raw 1-word 5★ count.",
            st["BulletItem"],
        )
    )
    story.append(
        Paragraph(
            "• <b>Decision Rules (Day 14 Canary / Day 30 / Day 60):</b> <b>(1) Continue:</b> ISS-01 negative share drops ≥40% on <font name='Courier'>v12.21+</font> "
            "with zero ANR/crash regression. <b>(2) Modify:</b> If map-zoom complaints cease but ETA inaccuracy remains >8% at Day 30, shift focus to Partner Lite "
            "background GPS wake-locks and routing ETA buffers. <b>(3) Reverse:</b> Immediate rollback if cold-start crashes rise >0.2% or cached OTPs cause >0.5% mismatch.",
            st["BulletItem"],
        )
    )

    story.append(Paragraph("7.3 Multi-Issue Action Tracking Register", st["SectionH2"]))
    act_rows = [
        ["Action ID & Issue", "Action Title & Suggested Owner", "Current Status (Verification)", "Target Window & Immediate Next Step"],
    ]
    for act in data["actionPlanAndTracking"]["actionTrackingRegister"]:
        act_rows.append([
            f"<b>{act['actionId']} ({act['issueId']})</b>",
            f"<b>{act['title']}</b> | Owner: {act['owner']}",
            f"{act['status']} <i>({act['verificationSource'][:28]})</i>",
            f"<b>{act['targetEvaluationDate'][:10]}:</b> {act['nextStep'][:78]}...",
        ])
    story.append(make_styled_table(act_rows, [25 * mm, 63 * mm, 42 * mm, 54 * mm], st, pad=1.8))
    story.append(PageBreak())

    # =========================================================================
    # PAGE 8: MONTHLY MONITORING WORKFLOW & SYSTEM ARCHITECTURE
    # =========================================================================
    story.append(Paragraph("PAGE 8 — REPEATABLE MONTHLY INVESTIGATION & SYSTEM ARCHITECTURE", st["PageHeader"]))
    story.append(Paragraph("8.1 Monthly Investigation Comparison (Aug 2026 vs. Sep 2026 vs. Oct 2026 MTD)", st["SectionH2"]))
    story.append(
        Paragraph(
            "The system is engineered for repeatable monthly execution (<font name='Courier'>python -m analysis.run_monthly --month YYYY-MM</font> "
            "or via the dashboard's <b>Run Monthly Investigation</b> workflow). Below is the verified comparison across the three most recent "
            "monthly cohorts against our 12-month baseline:",
            st["Body"],
        )
    )

    story.append(Image(str(chart_paths["fig5"]), width=182 * mm, height=51 * mm))
    story.append(
        Paragraph(
            "Figure 5: App Version Negative Review Share (v12.5–v12.19.0) and Monthly Issue Trajectory (Aug vs. Sep vs. Oct 2026 MTD).",
            st["Caption"],
        )
    )

    snaps = data["monthlyMonitoring"]["snapshots"]
    m_comp_rows = [
        ["Issue ID & Theme", "12m Baseline Share", "2026-08 Share (n=86 neg)", "2026-09 Share (n=72 neg)", "2026-10 MTD Share (n=26 neg)", "Oct vs. Sep Delta", "Automated Monthly Status"],
    ]
    for ic in snaps["2026-10"]["issueComparisons"]:
        code = ic["themeCode"]
        aug_ic = next(x for x in snaps["2026-08"]["issueComparisons"] if x["themeCode"] == code)
        sep_ic = next(x for x in snaps["2026-09"]["issueComparisons"] if x["themeCode"] == code)
        m_comp_rows.append([
            f"<b>{ic['issueId']}: {ic['shortName']}</b>",
            f"{ic['baseline12mSharePct']:.1f}%",
            f"{aug_ic['currentShareOfNegPct']:.1f}% ({aug_ic['currentCount']})",
            f"{sep_ic['currentShareOfNegPct']:.1f}% ({sep_ic['currentCount']})",
            f"<b>{ic['currentShareOfNegPct']:.1f}% ({ic['currentCount']})</b>",
            f"{ic['deltaMoMPts']:+.1f} pts",
            f"<b>{ic['monthlyStatus']}</b>",
        ])
    story.append(make_styled_table(m_comp_rows, [43 * mm, 22 * mm, 24 * mm, 24 * mm, 26 * mm, 20 * mm, 25 * mm], st, pad=2.0))
    story.append(Spacer(1, 1.5 * mm))

    story.append(Paragraph("8.2 Repeatable 10-Step Monthly Workflow & System Architecture", st["SectionH2"]))
    story.append(
        Paragraph(
            "• <b>10-Step Automated Monthly Pipeline:</b> (1) Record reporting period &amp; UTC timestamp; (2) Collect new public reviews via "
            "<font name='Courier'>google-play-scraper</font> or ingest CSV/JSON export; (3) Archive immutable raw snapshot in <font name='Courier'>data/raw/</font>; "
            "(4) Deduplicate via primary <font name='Courier'>reviewId</font> UUID and fallback SHA-256 fingerprint (<font name='Courier'>user|text|date|score</font>); "
            "(5) Re-run text cleaning, 8-theme classification, 18 sub-issue detectors, and analyst overrides; (6) Compute MoM and vs-baseline deltas; "
            "(7) Classify issues as <i>New/Emerging</i>, <i>Worsening</i>, <i>Persistent</i>, or <i>Improving</i>; (8) Re-score the 5-factor priority matrix; "
            "(9) Update Action Tracking with verified release notes; (10) Persist run to SQLite (<font name='Courier'>movesync_intelligence.db</font>) and regenerate exports + PDF.",
            st["BulletItem"],
        )
    )
    story.append(
        Paragraph(
            "• <b>Full-Stack Architecture &amp; Scheduling Honesty:</b> The system comprises a reproducible Python analytical core (<font name='Courier'>analysis/</font>), "
            "a FastAPI REST backend (<font name='Courier'>backend/app.py</font>) serving validated SQLite/JSON endpoints and an interactive dashboard "
            "(<font name='Courier'>frontend/</font>), and a Pytest verification suite (<font name='Courier'>tests/</font>). Manual execution is immediately active via "
            "UI button or CLI (<font name='Courier'>python -m analysis.run_monthly</font>); unattended monthly execution is documented via GitHub Actions cron / "
            "Windows Task Scheduler (<font name='Courier'>0 4 1 * *</font>) and is explicitly labelled <i>Manual / Configurable</i> until hosted credentials are attached.",
            st["BulletItem"],
        )
    )

    doc.build(story, canvasmaker=NumberedPageCanvas)
    return PDF_OUTPUT_PATH


if __name__ == "__main__":
    out = generate_case_study_pdf()
    print(f"Generated Case Study PDF at: {out} (size: {out.stat().st_size:,} bytes)")
