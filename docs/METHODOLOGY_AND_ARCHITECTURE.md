# MoveInSync Rating Intelligence — Methodology, Data Separation & Architecture

## 1. Epistemic Discipline & Separation of Evidence Layers

A core engineering principle of **MoveInSync Rating Intelligence** is strict separation between raw public evidence, reproducible analytical outputs, and engineering hypotheses/recommendations:

| Layer | Storage Location | Contents | Mutability |
| :--- | :--- | :--- | :--- |
| **1. Raw Public Evidence** | `data/raw/` | Unmodified Google Play Store metadata (`app_metadata_snapshot_2026_10_13.json`), chronological `Sort.NEWEST` stream (`reviews_newest_3000_2026_10_13.json`), default storefront `Sort.MOST_RELEVANT` stream (`reviews_most_relevant_600_2026_10_13.json`), and raw imported batches (`data/raw/imports/`). | **Immutable** (Read-only baseline snapshots) |
| **2. Human Audit & Overrides** | `data/validation/` | Stratified 120-review ground-truth audit benchmark (`classification_audit_120.json`), analyst classification overrides (`analyst_overrides.json`), and action-tracker status overrides (`action_overrides.json`). | **Audited Append/Update** (Tracks auditor ID & UTC timestamp) |
| **3. Cleaned & Enriched Corpus** | `data/processed/` | Deduplicated 3,333-review corpus (`reviews_cleaned_enriched.json`, `reviews_export.csv`) and ranked issue register (`issues_register.csv`). | **Reproducibly Generated** by `analysis/engine.py` |
| **4. Analytical & Historical Store** | `data/analytics/` & `data/movesync_intelligence.db` | Complete JSON analytical payload (`investigation_results.json`) and SQLite relational tables (`reviews`, `investigation_runs`). | **Reproducibly Generated** on pipeline or monthly runs |
| **5. Executive & Monthly Reports** | `reports/` | Standalone 8-page PDF Case Study (`MoveInSync_Case_Study.pdf`), high-DPI figures (`reports/figures/`), and dated monthly investigation reports (`reports/monthly/`). | **Reproducibly Generated** by `generate_report.py` & `run_monthly.py` |

---

## 2. Two-Tier Deduplication Architecture

To ensure no review is ever double-counted across streams (`Sort.NEWEST` vs. `Sort.MOST_RELEVANT`) or across consecutive monthly runs:

1. **Primary Key (`reviewId` UUID)**: Every review fetched from Google Play carries a globally unique UUID (e.g., `fdc328ac-...`). During ingestion, `load_and_deduplicate_reviews()` indexes records by `reviewId`. When a review appears in both `newest` (`3,000`) and `most_relevant` (`600`), the record is merged once and its `streams` array records `["newest", "most_relevant"]` (`267` overlaps removed, yielding `3,333` unique verified reviews).
2. **Secondary Fallback Fingerprint (`dedupHash`)**: For manual CSV/JSON imports where `reviewId` may be missing, `compute_fallback_hash()` computes a 24-character SHA-256 hex digest over normalized fields:
   $$\text{dedupHash} = \text{SHA256}\big(\text{lower}(\text{trim}(\text{userName})) \;\|\; \text{lower}(\text{collapse\_ws}(\text{content})) \;\|\; \text{YYYY-MM-DD} \;\|\; \text{score}\big)_{[0:24]}$$

---

## 3. Reproducible Theme & Sub-Issue Classification

`analysis/taxonomy.py` defines 8 root-cause themes (`ISS-01` through `ISS-08`) and 18 fine-grained sub-issue regex detectors:

- **Context-Aware Disambiguation**: In Indian enterprise commute terminology, employees frequently refer to their morning pickup as their *"login cab"* and their evening drop as their *"logout trip"*. A naive keyword classifier would misclassify *"my evening logout cab was delayed"* as an authentication logout bug (`AUTH_OTP_SESSION`). Our classifier explicitly disambiguates shift schedule terms (`logout trip`, `login cab`, `evening logout`) from authentication failures unless accompanied by authentication tokens (`otp`, `unable to login`, `automatically logged out`, `session`).
- **Star-Text Mismatch Detection**: `compute_sentiment()` cross-checks lexical polarity against the numeric star rating. Reviews where a user selects `1★` but writes only `"good"` or `"ok"` are flagged as `mixed_or_mismatch` (`1star_positive_text`), while `4–5★` reviews containing defect clauses (`"good app but map keeps zooming out"`) are flagged as `high_star_with_complaint_caveat` and tracked separately under `posMentionCount`.
- **120-Review Stratified Validation Benchmark**: Validated against a deterministic 120-review sample (`data/validation/classification_audit_120.json`), achieving **Micro-Precision = `0.858`**, **Micro-Recall = `0.889`**, **Micro-F1 = `0.873`**, and **Exact Multi-Label Set Match = `79.2%`**.

---

## 4. Transparent 5-Factor Prioritization Formula

Each issue is scored on a $0\text{–}100$ scale using five explicit dimensions ($0\text{–}10$ each):

$$\text{PriorityScore} = 10 \times \left(0.25 \cdot P + 0.22 \cdot S + 0.20 \cdot V + 0.23 \cdot C + 0.10 \cdot F\right)$$

1. **$P$ — Prevalence & Storefront Visibility (`25%`)**: $0.35 \cdot \text{TotalMentionsNorm} + 0.40 \cdot \text{ThumbsUpNorm} + 0.25 \cdot \text{MostRelevantPresenceNorm}$ (normalized against the software issue ceiling so operational volume does not distort software visibility).
2. **$S$ — Severity & Journey Criticality (`22%`)**: $0.55 \cdot \text{WorkflowCriticality} + 0.25 \cdot \text{OneStarIntensity} + 0.20 \cdot \text{MeanRatingDeficit}$.
3. **$V$ — Temporal Velocity / H2 Surge (`20%`)**: Maps H2 (Apr–Sep 2026) vs. H1 (Oct 2025–Mar 2026) growth rate and recent 60-day density onto $[0, 10]$.
4. **$C$ — Evidence Confidence & Software Attributability (`23%`)**: $0.75 \cdot \text{SoftwareControllability} + 0.25 \cdot (10 \cdot \text{ClassifierF1})$. This prevents heavily confounded third-party fleet/driver delays (`ISS-08`, $C=5.1$) from outranking pure MoveInSync mobile software defects (`ISS-01`, $C=9.0$; `ISS-03`, $C=9.4$; `ISS-02`, $C=9.7$).
5. **$F$ — Engineering Feasibility (`10%`)**: Inverse implementation effort ($1.0\text{–}2.5$ sprints).
