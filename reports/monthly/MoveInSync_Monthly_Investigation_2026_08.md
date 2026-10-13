# MoveInSync Rating Intelligence — Monthly Investigation Report (2026-08)

- **Run ID:** `monthly-2026-08-20261012222251`
- **Execution Timestamp (UTC):** `2026-10-12T22:22:51.112555+00:00`
- **Reporting Period:** `2026-08` (Complete Calendar Month)
- **Compared Against Prior Month:** `2026-07` and 12-Month Verified Baseline
- **Total Deduplicated Corpus Size:** `3,333` unique reviews (`267` cross-stream duplicates removed)

## 1. Monthly Rating & Volume Summary

| Metric | Value |
| :--- | :--- |
| **Written Reviews Collected in `2026-08`** | `242` |
| **All-Review Mean Rating (`2026-08`)** | `3.65★` |
| **1–2★ Negative Review Share (`2026-08`)** | `31.8%` (`77` reviews) |
| **Substantive Reviews ($\ge 6$ words) Mean Rating** | `2.47★` (`n = 99`) |

## 2. Month-over-Month Issue Trajectory (`vs Prior Month & 12m Baseline`)

| Issue ID | Theme | Month Neg Count | Month Share (%) | Prior Month (%) | MoM Delta (pts) | 12m Baseline (%) | Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| `ISS-08` | Fleet Ops, Routing & Driver Conduct | 25 | **29.1%** | 30.6% | `-1.5` | 27.2% | **Persistent** |
| `ISS-02` | Launch Crashes & Play Store Block | 14 | **16.3%** | 8.3% | `+8.0` | 6.5% | **Worsening** |
| `ISS-05` | Scheduling, Roster & Auto-Cancel | 13 | **15.1%** | 19.4% | `-4.3` | 13.9% | **Persistent** |
| `ISS-03` | Blocking Modals, Forced Rating & Alerts | 12 | **14.0%** | 19.4% | `-5.4` | 13.5% | **Persistent** |
| `ISS-01` | Live Tracking, Map Zoom & ETA | 11 | **12.8%** | 11.1% | `+1.7` | 11.4% | **Persistent** |
| `ISS-06` | Driver Calling, Helpdesk & Feedback Box | 7 | **8.1%** | 8.3% | `-0.2` | 9.9% | **Persistent** |
| `ISS-04` | Login OTP & Session Logout Loops | 5 | **5.8%** | 4.2% | `+1.6` | 13.4% | **Persistent** |
| `ISS-07` | Mobile Data 'No Network' Bug & Lag | 5 | **5.8%** | 4.2% | `+1.6` | 7.8% | **Persistent** |

## 3. Priority Reassessment & Next-Month Engineering Plan

- **Primary Architectural Priority (`#1` Overall):** `ISS-01` — *Live Vehicle Tracking Freeze, Map Auto-Zoom Reset & ETA Divergence* (`86.46/100`)
- **Highest Software Spike in `2026-08`:** `ISS-02` — *Launch Crashes & Play Store Block* (`16.3%` of negative reviews in `2026-08`)
- **Decision:** Maintain ISS-01 (Live Tracking, Map Zoom & ETA, score 86.46/100) as Primary 2-Sprint Architectural Initiative while executing urgent Week-1 Hotfixes for month-specific spikes in ISS-02 (Launch Crashes & Play Store Block, 16.3% of 2026-08 negative reviews).

## 4. Verified Action Tracking Register

| Action ID | Issue | Owner | Current Status | Verification | Target Evaluation |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `ACT-01` | `ISS-01` | Mobile Core & Location Telemetry Squad | **Proposed — Ready for Sprint Planning** | Unverified (Pending Engineering Implementation) | 2026-12-13 (60-Day Cohort Window) |
| `ACT-02` | `ISS-02` | Android Platform & Release Engineering Lead | **Proposed — Urgent P0 Hotfix** | Unverified (Pending Crashlytics & Play Integrity Audit) | 2026-11-13 (30-Day Hotfix Window) |
| `ACT-03` | `ISS-03` | Mobile Product UX Squad | **Proposed — Sprint Candidate** | Unverified (Pending Product & EHS Sign-off) | 2026-11-27 (45-Day Window) |
| `ACT-04` | `ISS-04` | Identity & Auth Backend Squad | **Proposed — Backlog Prioritized** | Unverified | 2026-12-13 (60-Day Window) |
| `ACT-05` | `ISS-05` | Roster & Scheduling Product Squad | **Proposed — Backlog Prioritized** | Unverified | 2026-12-13 (60-Day Window) |
| `ACT-06` | `ISS-06` | Telephony Engineering & Customer Support Ops | **Proposed — Immediate Operational + UI Fix** | Unverified | 2026-11-13 (30-Day Window) |
