"""
MoveInSync Rating Intelligence — Reproducible Theme Taxonomy & Issue Definitions
================================================================================
Defines the 8 evidence-backed root-cause themes, 18 fine-grained sub-issue symptom
detectors, sentiment scoring rules, and structured engineering metadata.
"""

import re
from typing import Dict, List, Any

THEME_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    "LIVE_TRACKING_MAP_ETA": {
        "id": "ISS-01",
        "code": "LIVE_TRACKING_MAP_ETA",
        "name": "Live Vehicle Tracking Freeze, Map Auto-Zoom Reset & ETA Divergence",
        "shortName": "Live Tracking, Map Zoom & ETA",
        "category": "Mobile Client & Telemetry Engineering",
        "plainLanguageSummary": (
            "Commuters waiting for assigned cabs experience frozen vehicle pins on the route map, "
            "automatic map camera zoom-outs every 3 to 30 seconds that undo manual pinch-zooming, "
            "wildly inaccurate ETAs (e.g., jumping from 3 mins to 20 mins or diverging 3x from Google Maps), "
            "a v12.19.0 restriction blocking live tracking >60 minutes before trip time, and total loss of "
            "trip/OTP details when opening the app in low-signal basements or metro stations."
        ),
        "reportedSymptomVsRootCause": {
            "reportedUserSymptom": (
                "Map zooms out automatically every few seconds while tracking; cab icon stays stuck while "
                "driver is already at pickup; ETA shows 20 mins when cab is outside (or 15 mins when it takes 60 mins); "
                "opening app in basement loses ride details and boarding OTP."
            ),
            "technicalRootCauseHypothesis": (
                "1) MapView camera bounds listener (`LatLngBounds` including pickup + vehicle + office destination) "
                "is re-triggered on every GPS websocket/polling tick (every 5-30s) without checking if the user has "
                "manually panned/zoomed (`isUserGesture`). 2) Driver GPS telemetry lacks dead-reckoning/staleness "
                "indicators when driver Partner Lite app is background-throttled. 3) Active trip card and boarding/drop "
                "OTP are fetched synchronously on cold start without a local Room/SQLite offline cache."
            ),
        },
        "patterns": [
            r"\b(gps|track|tracking|tracker|map|maps|eta|location|locate|zoom|zooming|zooms|route map|pin|navigation|live location|where is the cab|distance|kilometer|km|under an hour)\b"
        ],
        "subIssues": {
            "map_auto_zoom_reset": r"\b(zoom|zooming|zooms|reset|destination also in the view|focus)\b",
            "stale_gps_eta_divergence": r"\b(eta|gps|track|tracking|tracker|wrong location|different location|incorrect location|distance|google maps|minutes away|mins away|stuck)\b",
            "tracking_window_restriction": r"\b(under an hour|before 1 hour|1 hr|one hour)\b",
            "offline_trip_cache_missing": r"\b(cache|underground|internet|network call every time|offline)\b",
        },
        "workflowCriticality": 9.2,
        "softwareAttributability": 9.0,
        "effortSprints": 2.0,
        "feasibilityScore": 8.2,
        "confidenceLevel": "High",
        "confidenceRationale": (
            "Supported by 230 negative (1-3★) reviews (882 👍 thumbs-up, #1 in Google Play's Most Relevant stream) "
            "plus 103 4-5★ reviews explicitly requesting map/tracking fixes. Users across multiple versions "
            "(v11.4 through v12.19.0) describe identical, reproducible UI mechanics (e.g., map camera resetting "
            "to full-route bounds every 3-30 seconds)."
        ),
        "confoundersAndLimitations": (
            "Stale vehicle coordinates can be partially confounded by driver phone cellular dead zones or drivers "
            "disabling background location on the Partner Lite app (`com.moveinsync.driver.lite`). However, map "
            "auto-zoom resets and missing offline trip/OTP caching are 100% client-side MoveInSync app behaviors."
        ),
        "contradictoryPositiveEvidence": (
            "103 reviews rated 4-5★ mention tracking positively when network and GPS telemetry are stable "
            "(e.g., 'It is very easy to use and cab tracking is very helpful to know the cab location', id=ee0f8cee; "
            "'good app with real time cab movements and useful alerts', id=38ab0372), confirming high user value when functional."
        ),
        "recommendedAction": (
            "Ship Commute Telemetry & Offline Boarding Stabilization Pack: (1) Lock map camera state after user "
            "pinch/pan gesture with an explicit 'Re-center' FAB; (2) Cache active trip details, driver info, and "
            "boarding/drop OTPs in local device storage (Room/SQLite) immediately upon allocation; (3) Add telemetry "
            "'Last updated Xs ago' badge and Google Maps/traffic-calibrated ETA smoothing."
        ),
        "suggestedOwner": "Mobile Core & Location Telemetry Squad (Android + Backend Routing API)",
        "firstImplementationStep": (
            "Disable automatic `animateCamera(CameraUpdateFactory.newLatLngBounds(...))` on periodic location ticks "
            "once user gesture flag `hasUserMovedCamera` is true, and persist active `TripAssignment` + `OTP` payload "
            "in encrypted local storage with 24h TTL."
        ),
        "dependencies": [
            "Google Maps Android SDK camera-idle/gesture listener refactor",
            "Local Room/SQLite persistence schema for active trip & OTP cards",
            "Telemetry timestamp header from Driver Partner Lite location ingestion service"
        ],
        "risks": [
            "Caching stale OTP if a trip is dynamically re-allocated to a new cab while employee is offline (mitigate via push-triggered cache invalidation + 'Last synced' timestamp)."
        ],
        "successMetric": (
            "Reduce `LIVE_TRACKING_MAP_ETA` share of monthly negative (1-3★) reviews from 19.5% baseline to <=10.0% "
            "(proposed target) and eliminate map auto-zoom complaints within 60 days of release."
        ),
        "evaluationWindow": "30-day & 60-day post-release cohorts across >=200 new reviews",
    },
    "CRASH_LAUNCH_INTEGRITY": {
        "id": "ISS-02",
        "code": "CRASH_LAUNCH_INTEGRITY",
        "name": "App Launch Crashes, Post-Update State Corruption & False Play Store Integrity Block",
        "shortName": "Launch Crashes & Play Store Block",
        "category": "Android Platform & Release Engineering",
        "plainLanguageSummary": (
            "Following recent updates (v12.17.0 to v12.19.0), users experience immediate cold-start crashes, "
            "indefinite blank/splash screens (especially on Android 16/17, Pixel 8, OnePlus 12, Vivo), or a false "
            "blocking security dialog stating 'MoveInSync application cannot be opened as it was not downloaded from "
            "Play Store' every 2-3 days, forcing employees to repeatedly uninstall and reinstall the app."
        ),
        "reportedSymptomVsRootCause": {
            "reportedUserSymptom": (
                "App closes immediately upon opening; freezes on blank white/black screen after update; displays fake "
                "'not installed/downloaded from Play Store' error despite official Play Store installation; requires "
                "uninstalling and reinstalling every 2-3 days to work."
            ),
            "technicalRootCauseHypothesis": (
                "1) Custom installer-package verification (`PackageManager.getInstallSourceInfo` / Play Integrity check) "
                "misidentifies background Play Store auto-updates, Android 16/17 package installer sessions, or OEM/work-profile "
                "containers as sideloaded APKs. 2) Unhandled schema migration or corrupted WebView/SharedPreferences state "
                "across rapid v12.17->v12.18->v12.19 updates causes fatal startup exception until app data is wiped via reinstall."
            ),
        },
        "patterns": [
            r"\b(crash|crashes|crashing|crashed|hang|hangs|hanging|freeze|freezes|stuck|blank|black screen|white screen|not opening|won't open|wont open|doesn't open|does not open|unable to open|closes automatically|open and close|keeps stopping|stopped working|force close|uninstall|reinstall|play store|playstore|webview|web page|android 1[4567]|pixel|oneplus|vivo)\b"
        ],
        "subIssues": {
            "false_playstore_integrity_block": r"\b(play store|playstore|not installed from|not downloaded from)\b",
            "post_update_launch_crash": r"\b(not opening|won't open|wont open|doesn't open|unable to open|closes as soon as|open and close|keeps stopping|stopped working|crash|crashes|crashed|crashing|uninstall|reinstall)\b",
            "blank_screen_or_webview_fallback": r"\b(blank|black screen|white screen|splash|stuck|web page|webview)\b",
        },
        "workflowCriticality": 9.8,
        "softwareAttributability": 9.8,
        "effortSprints": 1.5,
        "feasibilityScore": 9.0,
        "confidenceLevel": "High",
        "confidenceRationale": (
            "100 negative reviews (438 👍) with an acute +207.1% surge in H2 2026 (14 in H1 -> 43 in H2, 21 in the last "
            "60 days). Multiple independent users quote the exact verbatim error string ('move in synch application can "
            "not be installed/opened as it was not downloaded from play store') and confirm that wiping app data via "
            "uninstall/reinstall temporarily restores functionality."
        ),
        "confoundersAndLimitations": (
            "Device-specific OEM battery/background restrictions or enterprise MDM work profiles may trigger the installer "
            "check differently across devices, and Play Store reviews do not attach stack traces. Needs verification against "
            "Firebase Crashlytics / Play Console Android Vitals."
        ),
        "contradictoryPositiveEvidence": (
            "Only 9 positive (4-5★) reviews mention crash/glitch keywords (primarily saying 'nice user friendly app with no "
            "glitch or slowness', id=64167d30), confirming that when launch succeeds, stability is acceptable."
        ),
        "recommendedAction": (
            "Fix Installer-Source Verification & Add Self-Healing Startup State Guard: (1) Replace brittle `getInstallerPackageName` "
            "check with official Google Play Integrity API standard verdict (or allow `com.google.android.packageinstaller` / "
            "enterprise MDM installers); (2) Wrap cold-start cache/database initialization in a try-catch recovery block that "
            "clears corrupted local cache without requiring app uninstallation."
        ),
        "suggestedOwner": "Android Platform & Release Engineering Lead",
        "firstImplementationStep": (
            "Audit the `not downloaded from Play Store` security check in v12.18/v12.19 startup flow, whitelist valid Android 16/17 "
            "auto-update installer package names, and add automated cache-reset fallback on startup exception."
        ),
        "dependencies": [
            "Play Console Android Vitals / Crashlytics ANR & crash logs by Android OS version (14-17)",
            "Security/InfoSec sign-off on Play Integrity API verdict policy"
        ],
        "risks": [
            "Relaxing installer check too broadly could permit modified APKs if not backed by Play Integrity API cryptographic token."
        ],
        "successMetric": (
            "Eliminate 'not downloaded from Play Store' review complaints (target: 0 new reports) and reduce `CRASH_LAUNCH_INTEGRITY` "
            "negative review share from 8.5% (and 13.7% in last 60d) to <3.0% within 30 days."
        ),
        "evaluationWindow": "30-day post-hotfix evaluation window",
    },
    "UX_MODALS_NOTIFICATIONS": {
        "id": "ISS-03",
        "code": "UX_MODALS_NOTIFICATIONS",
        "name": "Critical-Path Modal Friction: Seatbelt Blocking OTP, Forced Rating & Policy Pop-ups",
        "shortName": "Blocking Modals, Forced Rating & Alerts",
        "category": "Product UX & Notification Service",
        "plainLanguageSummary": (
            "Recent UI updates (v12.18.x-v12.19.0) introduced blocking modal dialogs right on the boarding critical path: "
            "(1) clicking 'View OTP' triggers a mandatory seatbelt safety pop-up that hides the boarding OTP; "
            "(2) opening the app forces a prior-ride rating dialog with no 'Skip' option, directly provoking angry users "
            "to leave 1-star reviews on Google Play; (3) Terms/Policy acceptance prompts appear repeatedly on every button click "
            "or launch; and (4) un-closable delay pop-ups block access to the emergency SOS button while push notifications arrive "
            "late or repeat endlessly."
        ),
        "reportedSymptomVsRootCause": {
            "reportedUserSymptom": (
                "Seatbelt check hides OTP when boarding; cannot use app without rating previous ride (no skip button); "
                "policy acceptance pops up on every button click; notification pop-ups cannot be closed and block SOS button; "
                "false 'trip not booked' push alerts sent even after booking."
            ),
            "technicalRootCauseHypothesis": (
                "1) Seatbelt compliance prompt is bound to the OTP reveal action rather than post-boarding trip-start state. "
                "2) Post-ride feedback modal sets `isCancelable(false)` with no dismiss CTA. 3) Policy consent boolean flag is "
                "not persisted cleanly in local user profile state. 4) In-app alert dialog queue stacks multiple delay modals "
                "above the main scaffold (obscuring the SOS button)."
            ),
        },
        "patterns": [
            r"\b(notification|notifications|notify|alert|alerts|pop up|popup|pop-up|popups|pop-ups|modal|seat belt|seatbelt|buckle|skip option|skip rating|forcing|asking for rating|terms and conditions|policy acceptance|permission|permissions|ui|ux|interface|confusing|complicated|user friendly|minimalist|feedback|qr|scan|scanner|brightness|ads|new update|latest update)\b"
        ],
        "subIssues": {
            "otp_blocked_by_seatbelt_modal": r"\b(seat belt|seatbelt|buckle|view otp)\b",
            "forced_rating_no_skip": r"\b(skip option|skip rating|forcing me to give rating|asking for rating|rate the trip|provide feedback upon opening)\b",
            "repeated_policy_consent_popup": r"\b(policy acceptance|terms and conditions|permission|permissions)\b",
            "notification_spam_or_missing_alerts": r"\b(notification|notifications|pop up|popup|pop-up|popups|pop-ups|alert|alerts)\b",
            "qr_scanner_or_ui_regression": r"\b(qr|scan|scanner|brightness|ui|ux|interface|confusing|minimalist|new update|latest update)\b",
        },
        "workflowCriticality": 8.6,
        "softwareAttributability": 9.6,
        "effortSprints": 1.0,
        "feasibilityScore": 9.4,
        "confidenceLevel": "High",
        "confidenceRationale": (
            "206 negative reviews (697 👍), up +46.8% in H2 2026 (47 -> 69) with 28 in the last 60 days. Reviewers in Oct 2026 "
            "explicitly trace their 1★ Play Store review to the un-skippable rating modal (id=f9fce9fe) and the v12.19.0 seatbelt "
            "modal hiding the boarding OTP (id=3d87f169, id=e12ed49a)."
        ),
        "confoundersAndLimitations": (
            "Some compliance prompts (e.g., seatbelt confirmation or company transport policy acceptance) may be mandated by "
            "enterprise client EHS (Environment, Health & Safety) policies, but their blocking placement over the OTP and SOS "
            "buttons and the failure to persist consent are pure UX/engineering implementation choices."
        ),
        "contradictoryPositiveEvidence": (
            "146 positive (4-5★) reviews praise the general UI simplicity and helpful trip notifications when modals do not "
            "obstruct the flow (e.g., 'easy and simple to use quite quick to navigate', id=0ef84db1)."
        ),
        "recommendedAction": (
            "De-block Boarding Critical Path & Modal Queue: (1) Render Boarding OTP inline on the trip card and move seatbelt "
            "confirmation to a non-blocking banner after trip start; (2) Add a prominent 'Skip / Remind Later' button to post-ride "
            "rating modals; (3) Persist policy consent per policy version ID; (4) Ensure emergency SOS FAB is always rendered above "
            "any notification banner."
        ),
        "suggestedOwner": "Mobile Product UX & Commuter Experience Squad",
        "firstImplementationStep": (
            "Decouple seatbelt modal trigger from `onViewOtpClicked()`, add a dismiss/skip CTA to `RideFeedbackDialog`, and cache "
            "`policy_accepted_vHash` in local storage + user profile."
        ),
        "dependencies": [
            "Enterprise EHS compliance sign-off on inline/banner seatbelt confirmation",
            "Push notification deduplication check on backend scheduler"
        ],
        "risks": [
            "Making post-ride rating skippable may reduce raw volume of 1-word 5★ ride ratings, which could temporarily lower "
            "the 5★ tap volume while genuinely reducing retaliatory 1★ written reviews."
        ],
        "successMetric": (
            "Reduce `UX_MODALS_NOTIFICATIONS` negative review share from 17.5% (and 18.3% in last 60d) to <=8.0% (proposed target) "
            "and eliminate complaints about seatbelt/OTP blocking and forced ratings within 45 days."
        ),
        "evaluationWindow": "30-day & 45-day post-release windows",
    },
    "AUTH_OTP_SESSION": {
        "id": "ISS-04",
        "code": "AUTH_OTP_SESSION",
        "name": "Authentication Failures, Missing Login OTPs & Forced Session Logout Loops",
        "shortName": "Login OTP & Session Logout Loops",
        "category": "Identity, Auth & Session Management",
        "plainLanguageSummary": (
            "Employees are frequently logged out of the app unexpectedly ('it logs out every time') and then locked out "
            "because login verification OTPs fail to arrive via SMS, Email, or WhatsApp, or the login screen returns "
            "'Empty response body' / 'Something went wrong', preventing users from viewing their assigned cab or boarding OTP."
        ),
        "reportedSymptomVsRootCause": {
            "reportedUserSymptom": (
                "App automatically logs out; login OTP is never received on mobile SMS, email, or WhatsApp; OTP text box "
                "fails to appear and shows 'Empty response body'; trip start/end OTP changes mid-ride or is rejected."
            ),
            "technicalRootCauseHypothesis": (
                "1) Short-lived access tokens or aggressive token-refresh invalidation on transient network errors logs users out "
                "during commute hours. 2) Single-vendor SMS/Email OTP gateway throttling during peak shift login windows (7-9 AM, "
                "5-7 PM IST) without automatic multi-provider failover. 3) Null-body HTTP 200/500 responses from auth endpoint "
                "not handled gracefully by the client parser."
            ),
        },
        "patterns": [
            r"\b(otp|otps|login|log in|logged out|log out|logs out|sign in|signin|verify|verifying|verification|password|session|authenticate|authentication|empty response body|registered mobile|email otp)\b"
        ],
        "subIssues": {
            "login_otp_delivery_failure": r"\b(not receiving the otp|not sending otp|not sending any otp|no otp|otp not received|doesn't send otp|both mobile otp and email otp|verify|verifying|verification)\b",
            "session_auto_logout_loop": r"\b(logs out every time|automatically logged out|logged out|empty response body)\b",
            "trip_otp_mismatch_or_change": r"\b(end otp|same otp|otp changed|otp keeps)\b",
        },
        "workflowCriticality": 9.4,
        "softwareAttributability": 8.8,
        "effortSprints": 2.0,
        "feasibilityScore": 8.0,
        "confidenceLevel": "High",
        "confidenceRationale": (
            "173 negative reviews (14.7% of negative corpus, 307 👍, 78.0% 1-star average 1.32★). Consistent reports across "
            "both H1 (62) and H2 (55) and last 60 days (17) specifically citing simultaneous failure of SMS, Email, and WhatsApp "
            "OTP channels plus unexpected session termination."
        ),
        "confoundersAndLimitations": (
            "SMS OTP delivery can be partially confounded by telecom DLT/carrier congestion in India or enterprise email spam "
            "filters, and some users say 'login/logout' to refer to morning/evening commute shifts rather than app authentication. "
            "Our sub-issue classifier isolates true authentication/OTP failures (`login_otp_delivery_failure`, `session_auto_logout_loop`)."
        ),
        "contradictoryPositiveEvidence": (
            "18 positive (4-5★) reviews mention login/OTP (mostly suggesting static/reusable rider passcodes like Uber PIN: "
            "'could we use one same OTP for every ride/trip', id=2c37f903)."
        ),
        "recommendedAction": (
            "Extend Session Refresh Resilience & Multi-Gateway OTP Failover: (1) Prevent automatic logout on transient 5xx/network "
            "timeouts by retaining encrypted refresh tokens for 90 days; (2) Implement automatic SMS->WhatsApp->Email OTP failover "
            "across secondary CPaaS providers when delivery receipt is not confirmed within 15s; (3) Support persistent static "
            "4-digit rider Boarding PIN per employee."
        ),
        "suggestedOwner": "Identity & Authentication Backend + Mobile Auth Squad",
        "firstImplementationStep": (
            "Audit auth token refresh interceptor on Android to eliminate forced logout on non-401 network errors, and add "
            "automated CPaaS provider fallback for unacknowledged OTP dispatches >15 seconds."
        ),
        "dependencies": [
            "Secondary SMS/WhatsApp CPaaS gateway integration",
            "Enterprise SSO / OAuth2 refresh token TTL policy review"
        ],
        "risks": [
            "Extending session TTL requires strict adherence to enterprise client MDM revocation hooks when an employee offboards."
        ],
        "successMetric": (
            "Reduce `AUTH_OTP_SESSION` negative review share from 14.7% baseline to <=6.0% (proposed target) and cut OTP delivery "
            "failure complaints by >=60% over 60 days."
        ),
        "evaluationWindow": "60-day post-deployment window",
    },
    "BOOKING_ROSTER_SYNC": {
        "id": "ISS-05",
        "code": "BOOKING_ROSTER_SYNC",
        "name": "Commute Scheduling, Roster Sync, Silent Evening Auto-Cancel & Night-Shift UX",
        "shortName": "Scheduling, Roster & Auto-Cancel",
        "category": "Roster & Booking Engine",
        "plainLanguageSummary": (
            "Employees face scheduling and roster synchronization failures: (1) being marked 'No-Show' on a morning login trip "
            "silently cancels the evening logout trip without any warning notification; (2) ad-hoc bookings place medically "
            "vulnerable or regular employees on a waitlist without clear waitlist confirmation; (3) night-shift schedules display "
            "'Logout and Login' under the same calendar date in a confusing order that causes accidental missed bookings; "
            "(4) workplace seat/desk allocations disappear after booking; and (5) Metro QR tickets lack offline caching and force "
            "100% screen brightness that fails on certain station scanners."
        ),
        "reportedSymptomVsRootCause": {
            "reportedUserSymptom": (
                "Evening logout trip cancelled automatically without reminder after morning No-Show; app shows no slots while "
                "web portal allows booking; books onto waitlist without informing user; night-shift Logout/Login date order is "
                "confusing; desk number disappears from workplace booking; Metro ticket has no offline QR and forces max brightness."
            ),
            "technicalRootCauseHypothesis": (
                "1) Backend 'Consecutive/Linked No-Show' rule cancels paired return trips silently without firing a push/SMS "
                "confirmation prompt. 2) Roster calendar UI groups shifts by UTC/midnight boundary rather than shift-workday "
                "grouping, confusing overnight shifts. 3) Mobile slot availability cache lags web portal state."
            ),
        },
        "patterns": [
            r"\b(book|booking|bookings|schedule|scheduling|roster|rostering|slot|slots|cancel|cancellation|cancelled|canceled|reschedule|no show|noshow|no-show|waitlist|cutoff|cut off|modify|shift|calendar|date selector|monthly view|seat|desk|workplace|metro)\b"
        ],
        "subIssues": {
            "morning_noshow_cancels_evening_logout": r"\b(no show|noshow|no-show|default cancellation of logout)\b",
            "waitlist_or_slot_sync_bug": r"\b(waitlist|no slots|website|unable to book|unable to schedule|saturday)\b",
            "night_shift_date_order_confusion": r"\b(night shift|logout and login|login and logout|calendar|date selector|monthly view)\b",
            "workplace_desk_or_metro_qr_bug": r"\b(metro|seat number|desk allocation|floor|parking)\b",
        },
        "workflowCriticality": 8.4,
        "softwareAttributability": 7.8,
        "effortSprints": 2.5,
        "feasibilityScore": 7.4,
        "confidenceLevel": "High",
        "confidenceRationale": (
            "235 negative reviews (20.0% of negative corpus, 585 👍), increasing +35.3% from H1 (51) to H2 (69) with 24 in the "
            "last 60 days. Detailed multi-point bug reports document silent logout-trip cancellation (id=0b1041ae), unannounced "
            "waitlist booking (id=387a67a5), workplace seat removal (id=da4ad9ad), and Metro QR bugs (id=d980e749)."
        ),
        "confoundersAndLimitations": (
            "Booking cutoff windows (e.g., 12h prior login / 4h prior logout) and No-Show penalty rules are configured by "
            "individual enterprise employers. However, silent cancellation without a warning notification, waitlist state opacity, "
            "night-shift UI ordering, and Metro QR caching are MoveInSync product/engineering defects."
        ),
        "contradictoryPositiveEvidence": (
            "67 positive (4-5★) reviews praise day-to-day scheduling convenience when rosters are static ('it's a great app for "
            "the night shift employees', id=d1e2d42b; 'makes our office routes so easy and convenient', id=6ccadce7)."
        ),
        "recommendedAction": (
            "Add Linked-Trip Cancellation Alert, Explicit Waitlist Badge & Offline Metro QR: (1) Send an actionable push/SMS "
            "'Keep My Evening Ride' confirmation whenever a morning No-Show triggers a linked logout-trip cancellation rule; "
            "(2) Display an explicit amber 'WAITLISTED' confirmation modal before finalizing ad-hoc bookings; (3) Cache Metro QR "
            "tickets locally and add a brightness toggle."
        ),
        "suggestedOwner": "Roster, Scheduling & Workplace Product Squad",
        "firstImplementationStep": (
            "Hook into the backend `NoShowCascadeCancelEvent` to dispatch a high-priority push notification with a 1-tap "
            "'Retain Evening Logout Trip' action link."
        ),
        "dependencies": [
            "Enterprise policy flag for linked No-Show auto-cancellation",
            "Metro ticketing partner QR payload offline validity window"
        ],
        "risks": [
            "Allowing 1-tap retention of evening trips after morning No-Show must respect employer transport admin override rules."
        ],
        "successMetric": (
            "Reduce `BOOKING_ROSTER_SYNC` negative review share from 20.0% baseline to <=11.0% (proposed target) over 60 days."
        ),
        "evaluationWindow": "60-day post-release window",
    },
    "SUPPORT_HELPDESK_CALLING": {
        "id": "ISS-06",
        "code": "SUPPORT_HELPDESK_CALLING",
        "name": "Driver Call-Masking Failures, Helpdesk Unreachability & Broken In-App Feedback",
        "shortName": "Driver Calling, Helpdesk & Feedback Box",
        "category": "Communications, Telephony & Support Workflow",
        "plainLanguageSummary": (
            "When a pickup goes wrong, every escalation channel inside the app fails simultaneously: (1) the masked driver "
            "call button fails to connect ('9 out of 10 times'), hides the mobile number, or blocks calls on shuttle buses; "
            "(2) the transport helpdesk button is missing or disconnects immediately; (3) the built-in feedback text box "
            "erases words on autocorrect or rejects input ('can't even write in built in feedback text box'); and "
            "(4) MoveInSync has replied to 0 new Google Play reviews since February 2, 2026."
        ),
        "reportedSymptomVsRootCause": {
            "reportedUserSymptom": (
                "Cannot call driver at critical pickup time; driver mobile number hidden after booking; helpdesk call disconnects "
                "or option is missing; built-in feedback text box deletes words when typing; zero response to Play Store complaints."
            ),
            "technicalRootCauseHypothesis": (
                "1) Cloud telephony DID/virtual-number bridge for masked driver calling runs out of concurrent channels during "
                "peak shift changeovers or lacks fallback when policy blocks direct display. 2) In-app feedback `EditText` "
                "overrides `onTextChanged` improperly, breaking Android IME autocorrect/composition spans. 3) Developer Play Console "
                "support workflow has been inactive since Feb 2, 2026."
            ),
        },
        "patterns": [
            r"\b(helpdesk|help desk|support|customer care|customer service|call|calling|dial|dialing|contact|helpline|complaint|complaints|escalate|escalation|sos|emergency|number is not visible|not allowed to call|feedback text box|autocorrect)\b"
        ],
        "subIssues": {
            "driver_masked_call_failure": r"\b(call|calling|dial|dialing|number is not visible|contact details|not allowed to call)\b",
            "helpdesk_unreachable": r"\b(helpdesk|help desk|support|customer care|customer service|helpline|disconnects)\b",
            "broken_inapp_feedback_input": r"\b(feedback text box|autocorrect|autocomplete|feedback link|meaningful)\b",
            "sos_button_obstruction": r"\b(sos|emergency)\b",
        },
        "workflowCriticality": 8.9,
        "softwareAttributability": 7.6,
        "effortSprints": 2.0,
        "feasibilityScore": 7.8,
        "confidenceLevel": "High",
        "confidenceRationale": (
            "158 negative reviews (13.4% of negative corpus, 505 👍) with the lowest average star rating of any theme (1.25★, "
            "81.6% 1-star) and +42.9% growth in H2 2026 (35 -> 50). Moreover, metadata audit proves 0 developer replies on "
            "Google Play since 2026-02-02."
        ),
        "confoundersAndLimitations": (
            "Helpdesk staffing and phone pickup rates depend on the employer's dedicated transport desk or third-party fleet "
            "control room. However, masked-call telephony bridge reliability, in-app chat/location sharing, the broken `EditText` "
            "feedback input, and Play Store review response SLAs are directly owned by MoveInSync."
        ),
        "contradictoryPositiveEvidence": (
            "34 positive (4-5★) reviews praise safety and assistance when helpdesk and driver coordination work ('the way to take "
            "care of sharing instructions and assistance all the way', id=9e51a63f)."
        ),
        "recommendedAction": (
            "Fix In-App Feedback IME Bug, Add Driver-Rider In-App Chat & Restore Play Store Support SLA: (1) Fix the broken "
            "feedback `EditText` IME composition bug immediately so complaints are captured in-app rather than on Google Play; "
            "(2) Add 1-tap templated in-app rider-to-driver chat + live pickup pin sharing when masked voice calls fail; "
            "(3) Re-establish a 48-hour SLA for Google Play review responses."
        ),
        "suggestedOwner": "Telephony/Comms Engineering & Customer Success Operations",
        "firstImplementationStep": (
            "Remove custom text-watcher state mutation on the in-app feedback `EditText` that breaks Android keyboard autocorrect, "
            "and add cloud-telephony bridge health monitoring during peak shift hours."
        ),
        "dependencies": [
            "Cloud telephony (Exotel/Knowlarity/Twilio) virtual number pool capacity",
            "Customer support Play Console response workflow reactivation"
        ],
        "risks": [
            "Direct driver phone number exposure violates privacy policies; must use masked bridge or in-app VoIP/chat."
        ],
        "successMetric": (
            "Reduce `SUPPORT_HELPDESK_CALLING` negative review share from 13.4% to <=7.0% (proposed target) and increase "
            "developer reply rate on substantive 1-2★ reviews from 0% (post-Feb 2026) to >=80%."
        ),
        "evaluationWindow": "30-day & 60-day evaluation windows",
    },
    "NETWORK_SYNC_PERFORMANCE": {
        "id": "ISS-07",
        "code": "NETWORK_SYNC_PERFORMANCE",
        "name": "False 'No Network' Errors on Mobile Data (5G/LTE) & UI Navigation Lag",
        "shortName": "Mobile Data 'No Network' Bug & Lag",
        "category": "Mobile Networking & Performance",
        "plainLanguageSummary": (
            "The app frequently displays false 'No network' or server unreachable errors when the phone is on a stable "
            "5G/LTE mobile data connection (working only on Wi-Fi), and suffers from multi-second UI freezes, slow loading "
            "spinners, and duplicate screen pushes (e.g., 'Show Address is navigating 4 times to the same screen'; passenger "
            "list requires multiple clicks to open or go back)."
        ),
        "reportedSymptomVsRootCause": {
            "reportedUserSymptom": (
                "App says 'no network' even though mobile data is stable and all other apps work; works only on Wi-Fi; "
                "very slow loading; clicking Show Address or Passenger List opens 4 duplicate screens or takes multiple taps."
            ),
            "technicalRootCauseHypothesis": (
                "1) Custom Android `ConnectivityManager` check inspects deprecated network type flags or fails on IPv6-only "
                "indian 5G/LTE carrierAPN configurations (Jio/Airtel IPv6) where DNS/socket binding prefers IPv4. "
                "2) Missing click-debounce (`throttleFirst`) on navigation actions causes 3-4 identical fragments/activities "
                "to be pushed onto the backstack when the main thread lags."
            ),
        },
        "patterns": [
            r"\b(no network|network issue|network error|mobile data|wifi|wi-fi|internet|offline|server|slow|slowness|lag|lags|lagging|loading|sync|synchronize|synchronized|cache|response|multiple clicks|4 times)\b"
        ],
        "subIssues": {
            "mobile_data_false_no_network": r"\b(no network|mobile data|wifi|wi-fi|network is stable|network issue)\b",
            "navigation_stack_lag_and_multi_click": r"\b(slow|slowness|lag|lags|lagging|loading|multiple clicks|4 times)\b",
        },
        "workflowCriticality": 8.2,
        "softwareAttributability": 9.2,
        "effortSprints": 1.5,
        "feasibilityScore": 8.6,
        "confidenceLevel": "High",
        "confidenceRationale": (
            "113 negative reviews (9.6% of negative corpus, 286 👍, avg 1.32★, 77.0% 1-star), surging +64.0% from H1 (25) "
            "to H2 (41). Reviewers explicitly isolate the Wi-Fi vs. mobile data discrepancy ('not working on mobile data "
            "anymore from last few days. works only on wifi', id=c8818d4d; 'app keeps showing no network even though the "
            "network is stable', id=2b0213c8)."
        ),
        "confoundersAndLimitations": (
            "Commuters often use the app in office basements with genuinely weak cellular signal, which can confound general "
            "network complaints. However, reports where other apps work fine on mobile data or where the app works only on Wi-Fi "
            "point to client connectivity-check or IPv6 DNS resolution bugs."
        ),
        "contradictoryPositiveEvidence": (
            "14 positive (4-5★) reviews note fast navigation on well-connected devices ('nice user friendly app with no glitch "
            "or slowness', id=64167d30)."
        ),
        "recommendedAction": (
            "Fix Android Connectivity Validation, Enable Dual-Stack IPv6/IPv4 & Debounce Navigation: (1) Replace custom "
            "connectivity pre-check with actual OkHttp request execution + Happy Eyeballs (IPv6/IPv4 fallback); (2) Add 500ms "
            "click debouncing (`launchSingleTop`) on all navigation buttons to prevent 4x duplicate screen pushes."
        ),
        "suggestedOwner": "Android Networking & Performance Engineering",
        "firstImplementationStep": (
            "Audit `NetworkUtils.isNetworkAvailable()` for false negatives on cellular 5G/IPv6 networks and add `launchSingleTop` "
            "to `ShowAddress` and `PassengerList` navigation intents."
        ),
        "dependencies": [
            "OkHttp DNS / Happy Eyeballs configuration",
            "Android Navigation Component backstack audit"
        ],
        "risks": [
            "Removing pre-flight connectivity checks requires clean timeout/retry error handling in OkHttp interceptors."
        ],
        "successMetric": (
            "Reduce `NETWORK_SYNC_PERFORMANCE` negative review share from 9.6% to <=4.0% (proposed target) within 45 days."
        ),
        "evaluationWindow": "45-day post-release window",
    },
    "CAB_ROUTING_DISPATCH_OPS": {
        "id": "ISS-08",
        "code": "CAB_ROUTING_DISPATCH_OPS",
        "name": "Fleet Operations: Multi-Zone Clubbing Delays, Cab Punctuality & Driver Conduct",
        "shortName": "Fleet Ops, Routing & Driver Conduct",
        "category": "Fleet Operations & Routing Algorithm (Confounded)",
        "plainLanguageSummary": (
            "The largest raw volume of negative reviews complains about physical commute execution: (1) routing algorithms "
            "clubbing passengers from opposite directions or different states into a single cab, turning a 20-minute commute "
            "into a 1.5-2 hour journey; (2) cabs not being assigned on time or arriving 1 hour late (or 1 hour too early); "
            "and (3) unprofessional, rude, or rash driver behavior and unannounced driver cancellations."
        ),
        "reportedSymptomVsRootCause": {
            "reportedUserSymptom": (
                "Cabs arrive 1 hour late or are not assigned at shift time; routing clubs passengers from opposite directions; "
                "pickup time changes every day; drivers are rude, refuse pickup, or mark false boarding."
            ),
            "technicalRootCauseHypothesis": (
                "1) Enterprise employer transport admins configure aggressive vehicle-occupancy/clubbing parameters to reduce "
                "per-seat transport cost, trading off detour time. 2) Third-party fleet vendor shortages and urban traffic cause "
                "dispatch delays. 3) App lacks transparent in-app route-detour feedback and driver-behavior escalation tracking, "
                "causing employees to blame the MoveInSync app on Google Play for vendor/employer operational failures."
            ),
        },
        "patterns": [
            r"\b(driver|drivers|cab|cabs|bus|shuttle|vehicle|punctual|punctuality|delay|delayed|late|on time|ontime|routing|clubbing|clubbed|route|routes|rude|arrogant|behavior|behaviour|professional|assign|assigned|allocation|allocated|pickup time|drop time|wait time|missed|vendor|transport team|transport management)\b"
        ],
        "subIssues": {
            "multi_zone_route_clubbing": r"\b(routing|clubbing|clubbed|opposite|route|routes|2 hours|two different states|detour)\b",
            "late_dispatch_or_unassigned_cab": r"\b(late|delay|delayed|on time|ontime|punctual|punctuality|not assigning|assign|assigned|pickup time|wait time|missed)\b",
            "driver_conduct_or_refusal": r"\b(rude|arrogant|behavior|behaviour|professional|professionalism|abusive|left me|vendor|transport management)\b",
        },
        "workflowCriticality": 8.5,
        "softwareAttributability": 3.5,
        "effortSprints": 5.0,
        "feasibilityScore": 3.5,
        "confidenceLevel": "High (Symptom) / Low (Pure App Defect)",
        "confidenceRationale": (
            "429 negative reviews (36.4% of all negative reviews, 1,248 👍). While user dissatisfaction with cab delays and "
            "driver conduct is indisputably real, MoveInSync's own developer reply (id=eb3230a8 / 2018-08-16) and B2B SaaS "
            "architecture confirm that fleet supply, driver hiring, and clubbing cost rules are controlled by employer transport "
            "teams and fleet vendors—making this a heavily confounded operational issue rather than the #1 mobile engineering fix."
        ),
        "confoundersAndLimitations": (
            "Severe external confounding: employees use the Google Play Store as a public grievance board against their "
            "employer's transport vendor (e.g., citing specific site operations like 'CNX Gurugram' or 'Synchrony Financial'). "
            "A mobile code change alone cannot fix physical cab shortages or driver conduct."
        ),
        "contradictoryPositiveEvidence": (
            "188 positive (4-5★) reviews praise safe, punctual cab rides and cooperative drivers ('full safety and cooperation "
            "on their part of helping us reach our destination', id=7ac55c75; 'never had a problem with your ride services', id=8aa00331)."
        ),
        "recommendedAction": (
            "Channel Operational Grievances into Structured In-App Escalation & Route Detour Guardrails: (1) Add a dedicated "
            "in-app 'Report Route Detour / Driver Conduct' ticket workflow routed directly to the employer's Transport Admin "
            "SLA dashboard with status tracking; (2) Surface max-detour-ratio alerts to enterprise transport admins in the "
            "MoveInSync ETS routing console."
        ),
        "suggestedOwner": "Enterprise Routing Engine & Client Transport Operations Team",
        "firstImplementationStep": (
            "Add structured post-ride 'Route / Driver / Timing' issue tags with visible ticket SLA status inside the app so "
            "employees see their employer transport desk acting on vendor complaints instead of venting on Google Play."
        ),
        "dependencies": [
            "Enterprise client transport admin SLA ticket webhook integration",
            "Routing engine max-detour threshold configuration per tenant"
        ],
        "risks": [
            "Mobile changes alone will not reduce physical cab delays if enterprise clients maintain strict cost-minimizing clubbing constraints."
        ],
        "successMetric": (
            "Divert >=35% of vendor/driver complaints from public Play Store reviews into tracked in-app transport desk tickets "
            "over 90 days (proposed target)."
        ),
        "evaluationWindow": "90-day operational evaluation window",
    },
}

POSITIVE_WORDS = {
    "good", "nice", "great", "excellent", "awesome", "super", "best", "helpful", "easy",
    "smooth", "convenient", "safe", "safety", "accurate", "wonderful", "amazing", "love",
    "thank", "thanks", "kudos", "fantastic", "reliable", "fast", "quick", "useful", "fine"
}

NEGATIVE_WORDS = {
    "worst", "bad", "pathetic", "horrible", "terrible", "useless", "waste", "rubbish",
    "garbage", "poor", "annoying", "frustrating", "disappointing", "disappointed",
    "bug", "bugs", "buggy", "crash", "crashes", "crashing", "crashed", "stuck", "hang",
    "hangs", "slow", "lag", "error", "fail", "fails", "failed", "unable", "wrong",
    "inaccurate", "misleading", "rude", "late", "delay", "delayed", "bekar", "bakwas",
    "third class", "filthy", "stupid", "ridiculous", "unprofessional", "broken", "fake"
}


def compute_sentiment(text: str, score: int) -> Dict[str, Any]:
    """
    Reproducible lexicon + star-discrepancy sentiment analyzer.
    Distinguishes genuine positive/negative text from star-text mismatches
    (e.g., 1★ review saying 'good' or 5★ review reporting a bug).
    """
    cleaned = (text or "").strip().lower()
    tokens = re.findall(r"[a-z]+", cleaned)
    pos_hits = sum(1 for t in tokens if t in POSITIVE_WORDS)
    neg_hits = sum(1 for t in tokens if t in NEGATIVE_WORDS)
    if "not good" in cleaned or "not working" in cleaned or "not nice" in cleaned or "not easy" in cleaned:
        pos_hits = max(0, pos_hits - 1)
        neg_hits += 1

    raw_lex = (pos_hits - neg_hits) / max(1, pos_hits + neg_hits) if (pos_hits + neg_hits) > 0 else 0.0
    star_norm = (score - 3.0) / 2.0  # -1.0 for 1★, +1.0 for 5★
    composite = round(0.6 * star_norm + 0.4 * raw_lex, 3)

    is_mismatch = False
    mismatch_type = None
    if score == 1 and len(tokens) <= 3 and pos_hits >= 1 and neg_hits == 0:
        is_mismatch = True
        mismatch_type = "1star_positive_text"
    elif score >= 4 and (neg_hits >= 1 or any(w in cleaned for w in ["but ", "improve", "issue", "problem", "sometimes", "wrong", "late"])):
        is_mismatch = True
        mismatch_type = "high_star_with_complaint_caveat"

    if is_mismatch:
        category = "mixed_or_mismatch"
    elif score <= 2 or composite < -0.2:
        category = "negative"
    elif score == 3 or (-0.2 <= composite <= 0.2):
        category = "neutral"
    else:
        category = "positive"

    return {
        "sentimentScore": composite,
        "lexicalPolarity": round(raw_lex, 3),
        "sentimentCategory": category,
        "isStarTextMismatch": is_mismatch,
        "mismatchType": mismatch_type,
    }


def classify_review_text(text: str, score: int) -> Dict[str, Any]:
    """
    Reproducible multi-label classifier mapping a review to its matching
    investigation themes and fine-grained technical sub-issues.
    """
    cleaned = (text or "").strip().lower()
    words = cleaned.split()
    word_count = len(words)

    if word_count <= 2:
        length_bucket = "1-2 words (tap/micro)"
    elif word_count <= 5:
        length_bucket = "3-5 words"
    elif word_count <= 14:
        length_bucket = "6-14 words"
    else:
        length_bucket = "15+ words (substantive)"

    matched_themes: List[str] = []
    matched_sub_issues: List[str] = []

    for theme_code, tdef in THEME_DEFINITIONS.items():
        if any(re.search(p, cleaned) for p in tdef["patterns"]):
            # Disambiguate shift schedule 'login trip / logout cab' from app authentication login failure
            if theme_code == "AUTH_OTP_SESSION":
                if any(s in cleaned for s in ["logout trip", "logout cab", "login trip", "login cab", "evening logout", "morning login"]):
                    if not any(a in cleaned for a in ["otp", "unable to login", "can't login", "cannot login", "automatically logged out", "logs out", "session"]):
                        continue
            matched_themes.append(theme_code)
            for sub_code, sub_pat in tdef["subIssues"].items():
                if re.search(sub_pat, cleaned):
                    matched_sub_issues.append(sub_code)

    sentiment = compute_sentiment(text, score)

    return {
        "wordCount": word_count,
        "lengthBucket": length_bucket,
        "isSubstantive": word_count >= 6,
        "isShortTapReview": word_count <= 2,
        "themes": matched_themes,
        "subIssues": matched_sub_issues,
        **sentiment,
    }
