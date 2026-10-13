/* ==========================================================================
   MoveInSync Rating Intelligence — User-Friendly Frontend Application Logic
   ========================================================================== */

const STATE = {
  investigation: null,
  facets: null,
  explorerPage: 1,
  explorerPageSize: 20,
  selectedMonthlyPeriod: "2026-10",
  activeLensKey: null,
};

const FRIENDLY_THEME_LABELS = {
  LIVE_TRACKING_MAP_ETA: "ISS-01: Live Map Tracking & ETA",
  CRASH_LAUNCH_INTEGRITY: "ISS-02: App Crash & Play Store Block",
  UX_MODALS_NOTIFICATIONS: "ISS-03: Blocking Popups & Forced Rating",
  AUTH_OTP_SESSION: "ISS-04: Login OTP & Session Logout",
  BOOKING_ROSTER_SYNC: "ISS-05: Booking, Roster & Auto-Cancel",
  SUPPORT_HELPDESK_CALLING: "ISS-06: Driver Calling & Helpdesk",
  NETWORK_SYNC_PERFORMANCE: "ISS-07: Slow Loading & False 'No Network'",
  CAB_ROUTING_DISPATCH_OPS: "ISS-08: Cab Delays, Routing & Drivers (Ops)",
};

const FRIENDLY_SUBISSUE_LABELS = {
  map_auto_zoom_reset: "🗺️ Map Auto-Zoom Reset",
  stale_gps_eta_divergence: "📍 Stale GPS / Inaccurate ETA",
  tracking_window_restriction: "⏱️ 60-Min Tracking Block (v12.19)",
  offline_trip_cache_missing: "🚇 No Offline Trip/OTP Cache",
  false_playstore_integrity_block: "🛑 Fake 'Not From Play Store' Error",
  post_update_launch_crash: "💥 Cold-Start Crash After Update",
  blank_screen_or_webview_fallback: "⬛ Blank Screen / Freeze",
  otp_blocked_by_seatbelt_modal: "💺 Seatbelt Popup Hides OTP",
  forced_rating_no_skip: "⭐ Forced Rating (No Skip Button)",
  repeated_policy_consent_popup: "📜 Repeated Policy Consent Popup",
  notification_spam_or_missing_alerts: "🔔 Missing or Spam Alerts",
  qr_scanner_or_ui_regression: "📷 QR Scanner / UI Regression",
  login_otp_delivery_failure: "📩 Login OTP Not Received",
  session_auto_logout_loop: "🔄 Auto-Logout Loop",
  trip_otp_mismatch_or_change: "🔢 Boarding OTP Mismatch",
  morning_noshow_cancels_evening_logout: "🚕 Morning No-Show Cancels Evening Cab",
  waitlist_or_slot_sync_bug: "⏳ Unclear Waitlist / Slot Sync Bug",
  night_shift_date_order_confusion: "🌙 Night-Shift Date Confusion",
  workplace_desk_or_metro_qr_bug: "🏢 Desk Booking / Metro QR Issue",
  driver_masked_call_failure: "📞 Masked Driver Call Fails",
  helpdesk_unreachable: "🎧 Helpdesk Unreachable",
  broken_inapp_feedback_input: "⌨️ Broken Feedback Text Box",
  sos_button_obstruction: "🚨 SOS Button Blocked",
  false_no_network_error: "📶 False 'No Network' on 5G/WiFi",
  severe_ui_lag_and_multi_tap: "🐌 Severe Lag (Needs 4 Taps)",
  cab_delay_or_unassigned_trip: "⏰ Cab Late / Unassigned (Ops)",
  route_clubbing_excessive_detour: "🛣️ Long Route Clubbing Detour (Ops)",
  driver_behavior_or_vehicle_ac: "🧑‍✈️ Driver Conduct / AC Issue (Ops)",
};

const QUICK_LENS_PRESETS = {
  all: {
    filters: {},
    banner: "Showing all 3,333 verified, deduplicated Google Play reviews sorted by community helpfulness (👍).",
  },
  map_zoom: {
    filters: { sub_issue: "map_auto_zoom_reset" },
    banner: "🗺️ Inspecting Map Auto-Zoom Reset (#1 Priority Sub-Issue): While commuters pinch-zoom to see which street their cab is on, the map resets to full route bounds every 3–30 seconds.",
  },
  seatbelt_otp: {
    filters: { sub_issue: "otp_blocked_by_seatbelt_modal" },
    banner: "🛑 Inspecting v12.19.0 Seatbelt Popup Blocking Boarding OTP: Tapping 'View OTP' while boarding triggers a full-screen seatbelt alert that hides the OTP needed by the driver.",
  },
  forced_rating: {
    filters: { sub_issue: "forced_rating_no_skip" },
    banner: "⭐ Inspecting Forced Post-Ride Rating Modal: Commuters cannot use the app without rating their previous trip (no 'Skip' button), causing both 1-word 5★ taps and angry 1★ reviews.",
  },
  playstore_block: {
    filters: { sub_issue: "false_playstore_integrity_block" },
    banner: "💥 Inspecting Fake 'Not Downloaded from Play Store' Lockout: Official Play Store users are blocked every 2–3 days and forced to uninstall and reinstall the app.",
  },
  noshow_cancel: {
    filters: { sub_issue: "morning_noshow_cancels_evening_logout" },
    banner: "🚕 Inspecting Silent Evening Logout Cancellation: If a commuter misses their morning cab (No-Show), the system silently cancels their evening ride home without a warning notification.",
  },
  edited_reply: {
    filters: { special: "edited_after_reply" },
    banner: "📉 Inspecting 55 Reviews Edited After Developer Reply: Users who previously got a generic 'Thank you very much for your review!!!' reply in 2021–2024 later edited their review to report new bugs.",
  },
  pos_caveat: {
    filters: { special: "positive_with_caveat", theme: "LIVE_TRACKING_MAP_ETA" },
    banner: "💡 Inspecting 4–5★ Supporters Requesting Tracking Fixes: Even commuters who rate MoveInSync 4★ or 5★ overall explicitly ask engineering to fix live cab tracking and map zoom.",
  },
  human_overrides: {
    filters: { special: "has_override" },
    banner: "✏️ Inspecting Human Analyst Classification Overrides: Edge-case reviews (such as a 1★ rating with the text 'good') verified and overridden by a human auditor.",
  },
};

function escapeHtml(str) {
  if (str === null || str === undefined) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function friendlyTheme(code) {
  return FRIENDLY_THEME_LABELS[code] || code;
}

function friendlySubIssue(code) {
  return FRIENDLY_SUBISSUE_LABELS[code] || code;
}

function showToast(msg) {
  const el = document.getElementById("toast-notification");
  if (!el) return;
  el.textContent = msg;
  el.classList.remove("hidden");
  setTimeout(() => el.classList.add("hidden"), 4200);
}

function switchTab(tabName) {
  document.querySelectorAll(".nav-tab").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.tab === tabName);
  });
  document.querySelectorAll(".tab-panel").forEach((panel) => {
    panel.classList.toggle("active", panel.id === `tab-${tabName}`);
  });
  window.scrollTo({ top: 0, behavior: "smooth" });
}

/* --------------------------------------------------------------------------
   Initialization & Data Loading
   -------------------------------------------------------------------------- */
async function initApp() {
  bindNavigationAndModals();
  await Promise.all([loadInvestigationData(), loadFacetsData(), loadMonthlyHistory()]);
  await fetchExplorerReviews(1);
}

async function loadInvestigationData() {
  const res = await fetch("/api/investigation");
  const data = await res.json();
  STATE.investigation = data;

  const totalUnique = data.baseline.dataCompletenessAndLimitations.totalUniqueVerifiedReviews;
  document.getElementById("nav-review-count").textContent = totalUnique.toLocaleString();
  document.getElementById("hdr-date").textContent = data.baseline.observationDate;
  document.getElementById("hdr-version").textContent = `v${data.baseline.storefrontSnapshots.india.currentVersion} Verified`;

  renderOverviewTab(data);
  renderPrioritizationTab(data);
  renderActionsTab(data);
  renderMonthlyTab(data);
}

async function loadFacetsData() {
  const res = await fetch("/api/reviews/facets");
  const facets = await res.json();
  STATE.facets = facets;

  const themeSelect = document.getElementById("flt-theme");
  themeSelect.innerHTML = `<option value="all">All 8 Problem Categories</option>`;
  facets.themes.forEach((t) => {
    themeSelect.innerHTML += `<option value="${t.themeCode}">[${t.issueId}] ${escapeHtml(t.shortName)}</option>`;
  });
  themeSelect.innerHTML += `<option value="UNTHEMED">No Specific Bug Mentioned (Generic 1-Word Praise)</option>`;

  const subSelect = document.getElementById("flt-subissue");
  subSelect.innerHTML = `<option value="all">All 18 Specific Symptoms</option>`;
  facets.subIssues.forEach((s) => {
    subSelect.innerHTML += `<option value="${s.subIssue}">${escapeHtml(friendlySubIssue(s.subIssue))} (${s.count})</option>`;
  });

  const verSelect = document.getElementById("flt-version");
  verSelect.innerHTML = `<option value="all">All App Versions</option>`;
  facets.versions.forEach((v) => {
    verSelect.innerHTML += `<option value="${escapeHtml(v.version)}">${escapeHtml(v.version)} (${v.count})</option>`;
  });

  // Populate override modal checkboxes
  const ovrBox = document.getElementById("ovr-themes-checkboxes");
  ovrBox.innerHTML = facets.themes
    .map(
      (t) => `
      <label class="checkbox-item">
        <input type="checkbox" name="ovr-theme" value="${t.themeCode}" />
        <span><strong>${t.issueId}</strong>: ${escapeHtml(t.shortName)}</span>
      </label>`
    )
    .join("");
}

/* --------------------------------------------------------------------------
   TAB 1: Investigation Overview Rendering
   -------------------------------------------------------------------------- */
function renderOverviewTab(data) {
  const b = data.baseline;
  const topIssue = data.issuesRegister[0];
  const sfIn = b.storefrontSnapshots.india;
  const sfUs = b.storefrontSnapshots.unitedStates;
  const cNewest = b.sampleCohorts.newest3000;
  const cSub = b.sampleCohorts.substantiveNewest;
  const cDet = b.sampleCohorts.detailedNewest15Plus;
  const cRel = b.sampleCohorts.mostRelevant600;
  const devAudit = b.developerResponseAudit;

  document.getElementById("btn-explore-top-issue").onclick = () => {
    jumpToExplorerWithFilters({ theme: topIssue.themeCode, score: "1-3" }, "🗺️ Viewing all 230 negative (1–3★) reviews for #1 Priority Issue: Live Tracking, Map Auto-Zoom & ETA.");
  };

  // Render 6 Friendly KPI Cards
  const kpiGrid = document.getElementById("overview-kpi-grid");
  kpiGrid.innerHTML = `
    <div class="kpi-card">
      <div class="kpi-label">Play Store Headline</div>
      <div class="kpi-value">${sfIn.exactScore.toFixed(2)}★ <span style="font-size:13px;color:#64748b;">IN</span> / ${sfUs.exactScore.toFixed(2)}★ <span style="font-size:13px;color:#64748b;">US</span></div>
      <div class="kpi-sub">${sfIn.totalRatings.toLocaleString()} total ratings (79% silent taps)</div>
    </div>
    <div class="kpi-card kpi-amber">
      <div class="kpi-label">Newest 3,000 Written</div>
      <div class="kpi-value">${cNewest.meanRating.toFixed(2)}★</div>
      <div class="kpi-sub"><strong>${cNewest.negative12Pct}% are 1–2★</strong> (${cNewest.negative12Count} unhappy users)</div>
    </div>
    <div class="kpi-card kpi-red">
      <div class="kpi-label">Real Sentences (&ge;6 Words)</div>
      <div class="kpi-value">${cSub.meanRating.toFixed(2)}★</div>
      <div class="kpi-sub"><strong>${cSub.negative12Pct}% are 1–2★</strong> (15+ words: <strong>${cDet.meanRating.toFixed(2)}★</strong>)</div>
    </div>
    <div class="kpi-card kpi-red">
      <div class="kpi-label">Default Storefront View</div>
      <div class="kpi-value">${cRel.meanRating.toFixed(2)}★</div>
      <div class="kpi-sub"><strong>${cRel.negative12Pct}% 1–2★</strong> in "Most Relevant" (n=600)</div>
    </div>
    <div class="kpi-card kpi-purple">
      <div class="kpi-label">Developer Support Replies</div>
      <div class="kpi-value">0 <span style="font-size:13px;font-weight:600;color:#64748b;">since Feb '26</span></div>
      <div class="kpi-sub">Only ${devAudit.newest12StarReplyRatePct}% of 1–2★ reviews ever got a reply</div>
    </div>
    <div class="kpi-card kpi-green">
      <div class="kpi-label">#1 Recommended Fix</div>
      <div class="kpi-value">${topIssue.issueId} <span style="font-size:14px;color:#047857;">(${topIssue.priorityScore}/100)</span></div>
      <div class="kpi-sub">Live Map Zoom &amp; Offline OTP (${topIssue.estimatedEffortSprints} Sprints)</div>
    </div>
  `;

  // Render Review-Length Bifurcation Chart & Table
  const bifBox = document.getElementById("bifurcation-chart-container");
  const bifTbody = document.querySelector("#bifurcation-table tbody");
  bifBox.innerHTML = "";
  bifTbody.innerHTML = "";

  const friendlyBucketNames = {
    "1-2 words (tap/micro)": "1–2 words (Forced 'good' taps)",
    "3-5 words": "3–5 words (Short comments)",
    "6-14 words": "6–14 words (Real sentences)",
    "15+ words (substantive)": "15+ words (Detailed stories)",
  };

  b.ratingBifurcationExplanation.lengthStratification.forEach((row) => {
    const midPct = Math.max(0, 100 - row.negative12Pct - row.positive45Pct).toFixed(1);
    const niceName = friendlyBucketNames[row.bucket] || row.bucket;
    const barEl = document.createElement("div");
    barEl.className = "bif-row";
    barEl.title = `Click to read ${row.count} reviews in '${niceName}'`;
    barEl.innerHTML = `
      <div class="bif-label">${escapeHtml(niceName)}</div>
      <div class="bif-bar-track">
        <div class="bif-seg-neg" style="width:${row.negative12Pct}%">${row.negative12Pct >= 10 ? row.negative12Pct + "% Unhappy" : ""}</div>
        <div class="bif-seg-mid" style="width:${midPct}%"></div>
        <div class="bif-seg-pos" style="width:${row.positive45Pct}%">${row.positive45Pct >= 14 ? row.positive45Pct + "% Happy" : ""}</div>
      </div>
      <div class="bif-stat">${row.meanRating.toFixed(2)}★ <span style="color:#64748b;font-weight:500;">(${row.count})</span></div>
    `;
    barEl.onclick = () => jumpToExplorerWithFilters({ length_bucket: row.bucket }, `Filtering by Review Length: ${niceName} (Average: ${row.meanRating.toFixed(2)}★).`);
    bifBox.appendChild(barEl);

    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><strong>${escapeHtml(niceName)}</strong></td>
      <td class="num">${row.count.toLocaleString()}</td>
      <td class="num">${row.shareOfNewestPct}%</td>
      <td class="num"><strong>${row.meanRating.toFixed(2)}★</strong></td>
      <td class="num" style="color:#e11d48;font-weight:700;">${row.negative12Pct}% (${row.negative12Count})</td>
      <td class="num" style="color:#047857;font-weight:700;">${row.positive45Pct}% (${row.positive45Count})</td>
      <td><button class="btn btn-xs btn-outline">Read &rarr;</button></td>
    `;
    tr.querySelector("button").onclick = () => jumpToExplorerWithFilters({ length_bucket: row.bucket }, `Filtering by Review Length: ${niceName} (Average: ${row.meanRating.toFixed(2)}★).`);
    bifTbody.appendChild(tr);
  });

  // Render Monthly SVG Trend Chart (2025-10 to 2026-10)
  renderMonthlyTrendSvg(b.monthlySeries);

  // Render Version Regression Table
  const verTbody = document.querySelector("#version-regression-table tbody");
  verTbody.innerHTML = "";
  b.versionAnalysis.slice(0, 10).forEach((v) => {
    const tr = document.createElement("tr");
    tr.className = "clickable-row";
    const isRecentBad = v.negative12Pct >= 30.0;
    tr.innerHTML = `
      <td class="nowrap"><code>${escapeHtml(v.version)}</code></td>
      <td class="nowrap">${v.firstSeenDate} &rarr; ${v.lastSeenDate}</td>
      <td class="num nowrap">${v.reviewCount}</td>
      <td class="num nowrap"><strong>${v.meanRating.toFixed(2)}★</strong></td>
      <td class="num nowrap" style="${isRecentBad ? "color:#e11d48;font-weight:700;" : ""}">${v.negative12Pct}%</td>
      <td class="num nowrap">${v.trackingNegCount}</td>
      <td class="num nowrap">${v.uxModalNegCount}</td>
      <td class="num nowrap">${v.crashLaunchNegCount}</td>
    `;
    tr.onclick = () => {
      const verParam = v.version.startsWith("Unspecified") ? "Unspecified" : v.version;
      jumpToExplorerWithFilters({ version: verParam }, `Inspecting reviews posted on App Version ${v.version} (Avg: ${v.meanRating.toFixed(2)}★).`);
    };
    verTbody.appendChild(tr);
  });

  // Render Developer Response Audit Box
  document.getElementById("dev-response-audit-box").innerHTML = `
    <div class="audit-stat-box">
      <div class="kpi-label">Last Developer Reply</div>
      <div class="kpi-value" style="font-size:17px;color:#e11d48;">${devAudit.latestDeveloperReplyDate}</div>
      <div class="kpi-sub">8.3+ months with 0 replies</div>
    </div>
    <div class="audit-stat-box">
      <div class="kpi-label">1–2★ Reply Rate</div>
      <div class="kpi-value" style="font-size:17px;">${devAudit.newest12StarReplyRatePct}%</div>
      <div class="kpi-sub">Only ${devAudit.newest12StarReplied} of ${devAudit.newest12StarTotal} unhappy users</div>
    </div>
    <div class="audit-stat-box">
      <div class="kpi-label">Edited After Reply</div>
      <div class="kpi-value" style="font-size:17px;color:#d97706;">${devAudit.editedAfterReplyCount} Users</div>
      <div class="kpi-sub">33 are now 1–3★ complaints</div>
    </div>
  `;

  document.getElementById("btn-inspect-edited-replies").onclick = () => {
    applyQuickLens("edited_reply");
  };

  // Render Ecosystem Apps Table
  const ecoTbody = document.querySelector("#ecosystem-apps-table tbody");
  ecoTbody.innerHTML = "";
  data.ecosystemApps.forEach((app) => {
    const tr = document.createElement("tr");
    const isPrimary = app.appId === "com.moveinsync.ets";
    tr.innerHTML = `
      <td class="nowrap"><strong>${escapeHtml(app.title)}</strong> ${isPrimary ? '<span class="badge badge-blue">Primary App</span>' : ""}</td>
      <td class="nowrap"><code>${escapeHtml(app.appId)}</code></td>
      <td class="num nowrap">${(app.realInstalls || 0).toLocaleString()}</td>
      <td class="num nowrap">${app.score ? app.score.toFixed(2) + "★" : "—"}</td>
      <td class="num nowrap">${(app.ratings || 0).toLocaleString()}</td>
      <td class="nowrap"><code>${escapeHtml(app.version || "—")}</code></td>
    `;
    ecoTbody.appendChild(tr);
  });
}

function renderMonthlyTrendSvg(monthlySeries) {
  const container = document.getElementById("monthly-trend-svg-container");
  const series = monthlySeries.filter((m) => m.yearMonth >= "2025-10");
  if (!series.length) return;

  const width = 640;
  const height = 225;
  const padL = 42;
  const padR = 42;
  const padT = 22;
  const padB = 36;
  const plotW = width - padL - padR;
  const plotH = height - padT - padB;

  const xFor = (i) => padL + (i / Math.max(1, series.length - 1)) * plotW;
  const yForStar = (star) => padT + ((4.5 - star) / 3.0) * plotH;
  const yForPct = (pct) => padT + ((80 - pct) / 80.0) * plotH;

  let allPath = "";
  let subPath = "";
  let barsHtml = "";
  let pointsHtml = "";
  let labelsHtml = "";

  series.forEach((m, i) => {
    const x = xFor(i);
    const yAll = yForStar(m.meanRatingAll);
    const ySub = yForStar(m.meanRatingSubstantive);
    const yPct = yForPct(m.substantiveNegative12Pct);
    const barH = padT + plotH - yPct;
    const tipText = `${m.yearMonth}: All Avg ${m.meanRatingAll.toFixed(2)}★ | Written (≥6w) Avg ${m.meanRatingSubstantive.toFixed(2)}★ (${m.substantiveNegative12Pct}% 1-2★) | Click to filter ${m.reviewCount} reviews`;

    allPath += `${i === 0 ? "M" : "L"}${x.toFixed(1)},${yAll.toFixed(1)} `;
    subPath += `${i === 0 ? "M" : "L"}${x.toFixed(1)},${ySub.toFixed(1)} `;

    barsHtml += `<rect class="svg-month-hit" data-ym="${m.yearMonth}" x="${(x - 12).toFixed(1)}" y="${yPct.toFixed(1)}" width="24" height="${barH.toFixed(1)}" fill="rgba(217,119,6,0.18)" stroke="rgba(217,119,6,0.45)" rx="4" style="cursor:pointer;"><title>${tipText}</title></rect>`;

    pointsHtml += `
      <g class="svg-month-hit" data-ym="${m.yearMonth}" style="cursor:pointer;">
        <title>${tipText}</title>
        <circle cx="${x.toFixed(1)}" cy="${yAll.toFixed(1)}" r="5" fill="#2563eb" stroke="#ffffff" stroke-width="1.5" />
        <text x="${x.toFixed(1)}" y="${(yAll - 8).toFixed(1)}" text-anchor="middle" font-size="9.5" font-weight="700" fill="#1d4ed8">${m.meanRatingAll.toFixed(2)}★</text>
        <circle cx="${x.toFixed(1)}" cy="${ySub.toFixed(1)}" r="5.5" fill="#e11d48" stroke="#ffffff" stroke-width="1.5" />
        <text x="${x.toFixed(1)}" y="${(ySub + 15).toFixed(1)}" text-anchor="middle" font-size="9.5" font-weight="700" fill="#be123c">${m.meanRatingSubstantive.toFixed(2)}★</text>
      </g>
    `;

    const shortYm = m.yearMonth.slice(2);
    labelsHtml += `<text class="svg-month-hit" data-ym="${m.yearMonth}" x="${x.toFixed(1)}" y="${height - 12}" text-anchor="middle" font-size="10" font-weight="700" fill="#334155" style="cursor:pointer;">${shortYm}${m.isPartialMonth ? "*" : ""}</text>`;
  });

  let gridHtml = "";
  [2.0, 3.0, 4.0].forEach((s) => {
    const y = yForStar(s);
    gridHtml += `
      <line x1="${padL}" y1="${y.toFixed(1)}" x2="${width - padR}" y2="${y.toFixed(1)}" stroke="#cbd5e1" stroke-dasharray="3,3" />
      <text x="${padL - 6}" y="${(y + 3).toFixed(1)}" text-anchor="end" font-size="10" fill="#64748b">${s.toFixed(1)}★</text>
    `;
  });

  container.innerHTML = `
    <svg viewBox="0 0 ${width} ${height}" width="100%" height="225" role="img" aria-label="12-Month Rating Trajectory">
      ${gridHtml}
      ${barsHtml}
      <path d="${allPath}" fill="none" stroke="#2563eb" stroke-width="2.5" />
      <path d="${subPath}" fill="none" stroke="#e11d48" stroke-width="2.8" />
      ${pointsHtml}
      ${labelsHtml}
    </svg>
  `;

  container.querySelectorAll(".svg-month-hit").forEach((el) => {
    el.addEventListener("click", () => {
      const ym = el.dataset.ym;
      if (ym === "2026-08" || ym === "2026-09" || ym === "2026-10") {
        document.getElementById("sel-monthly-period").value = ym;
        if (STATE.investigation && STATE.investigation.monthlyMonitoring.snapshots[ym]) {
          renderMonthlySnapshotView(STATE.investigation.monthlyMonitoring.snapshots[ym]);
        }
        switchTab("monthly");
        showToast(`Switched Monthly Monitor to ${ym} snapshot.`);
      } else {
        jumpToExplorerWithFilters({ q: ym }, `Showing reviews from month ${ym}.`);
      }
    });
  });
}

/* --------------------------------------------------------------------------
   TAB 2: Evidence Explorer & Quick Lenses
   -------------------------------------------------------------------------- */
function applyQuickLens(lensKey) {
  const preset = QUICK_LENS_PRESETS[lensKey] || QUICK_LENS_PRESETS.all;
  STATE.activeLensKey = lensKey;
  document.querySelectorAll(".lens-chip").forEach((c) => {
    c.classList.toggle("active", c.dataset.lens === lensKey);
  });
  jumpToExplorerWithFilters(preset.filters, preset.banner);
}

function jumpToExplorerWithFilters(filters, bannerText = null) {
  document.getElementById("flt-q").value = filters.q || "";
  document.getElementById("flt-score").value = filters.score || "all";
  document.getElementById("flt-theme").value = filters.theme || "all";
  document.getElementById("flt-subissue").value = filters.sub_issue || "all";
  document.getElementById("flt-version").value = filters.version || "all";
  document.getElementById("flt-length").value = filters.length_bucket || "all";
  document.getElementById("flt-stream").value = filters.stream || "all";
  document.getElementById("flt-special").value = filters.special || "all";

  const bannerEl = document.getElementById("active-lens-banner");
  if (bannerText) {
    bannerEl.innerHTML = `<span>${escapeHtml(bannerText)}</span><button class="btn btn-xs btn-outline" id="btn-dismiss-banner">Reset View</button>`;
    bannerEl.classList.remove("hidden");
    document.getElementById("btn-dismiss-banner").onclick = () => {
      bannerEl.classList.add("hidden");
      jumpToExplorerWithFilters({});
    };
  } else {
    bannerEl.classList.add("hidden");
  }

  switchTab("explorer");
  fetchExplorerReviews(1);
}

async function fetchExplorerReviews(page = 1) {
  STATE.explorerPage = page;
  const params = new URLSearchParams({
    page: String(page),
    page_size: String(STATE.explorerPageSize),
    q: document.getElementById("flt-q").value.trim(),
    score: document.getElementById("flt-score").value,
    theme: document.getElementById("flt-theme").value,
    sub_issue: document.getElementById("flt-subissue").value,
    version: document.getElementById("flt-version").value,
    length_bucket: document.getElementById("flt-length").value,
    stream: document.getElementById("flt-stream").value,
    special: document.getElementById("flt-special").value,
    sort_by: document.getElementById("flt-sort").value,
  });

  const res = await fetch(`/api/reviews?${params.toString()}`);
  const payload = await res.json();

  document.getElementById("explorer-summary-pill").innerHTML = `
    Found <strong>${payload.totalMatching.toLocaleString()}</strong> reviews &bull;
    Avg Rating: <strong>${payload.filteredSummary.meanRating.toFixed(2)}★</strong> &bull;
    1–2★ Unhappy: <strong>${payload.filteredSummary.negative12Pct}%</strong>
  `;

  const listEl = document.getElementById("reviews-list-container");
  if (!payload.reviews.length) {
    listEl.innerHTML = `<div class="card"><p>No reviews match these filters. Click <strong>Clear All Filters</strong> to reset.</p></div>`;
    document.getElementById("reviews-pagination").innerHTML = "";
    return;
  }

  listEl.innerHTML = payload.reviews.map((r) => renderReviewCardHtml(r)).join("");
  listEl.querySelectorAll(".btn-audit-review").forEach((btn) => {
    btn.onclick = () => openOverrideModal(btn.dataset.revid);
  });

  // Render pagination
  const pagEl = document.getElementById("reviews-pagination");
  pagEl.innerHTML = `
    <div>
      Showing page <strong>${payload.page}</strong> of <strong>${payload.totalPages}</strong>
      (${payload.totalMatching.toLocaleString()} matching reviews)
    </div>
    <div style="display:flex;gap:8px;">
      <button class="btn btn-sm btn-outline" id="pg-prev" ${payload.page <= 1 ? "disabled" : ""}>&larr; Previous Page</button>
      <button class="btn btn-sm btn-outline" id="pg-next" ${payload.page >= payload.totalPages ? "disabled" : ""}>Next Page &rarr;</button>
    </div>
  `;
  const prevBtn = document.getElementById("pg-prev");
  const nextBtn = document.getElementById("pg-next");
  if (prevBtn) prevBtn.onclick = () => fetchExplorerReviews(payload.page - 1);
  if (nextBtn) nextBtn.onclick = () => fetchExplorerReviews(payload.page + 1);
}

function renderReviewCardHtml(r) {
  const starSymbols = "★".repeat(r.score) + "☆".repeat(5 - r.score);
  const starsHtml = `<span class="star-pill star-${r.score}">${r.score}.0 ${starSymbols}</span>`;
  const verText = r.reviewCreatedVersion ? `v${escapeHtml(r.reviewCreatedVersion)}` : "Web / No Version";
  const streamBadges = r.streams
    .map((s) => `<span class="badge badge-gray">${s === "most_relevant" ? "Storefront Featured" : "Newest Feed"}</span>`)
    .join(" ");

  const editedBadge = r.isEditedAfterReply
    ? `<span class="badge badge-red" title="User edited their review rating AFTER receiving a generic developer reply">⚠️ User Edited Rating to ${r.score}★ After Dev Reply</span>`
    : "";

  const replyHtml = r.replyContent
    ? `<div class="dev-reply-box">
         <strong>💬 MoveInSync Developer Reply (${escapeHtml(r.replyDate || "N/A")}):</strong>
         <div>"${escapeHtml(r.replyContent)}"</div>
       </div>`
    : "";

  const themePills = r.themes.length
    ? r.themes.map((t) => `<span class="badge badge-blue">${escapeHtml(friendlyTheme(t))}</span>`).join(" ")
    : `<span class="badge badge-gray">No Bug Reported (${escapeHtml(r.lengthBucket)})</span>`;

  const subIssuePills = r.subIssues.length
    ? r.subIssues.map((s) => `<span class="badge badge-purple">${escapeHtml(friendlySubIssue(s))}</span>`).join(" ")
    : `<span style="font-size:12px;color:#64748b;">No specific sub-issue triggered</span>`;

  const sentBadgeClass =
    r.sentimentCategory === "negative"
      ? "badge-red"
      : r.sentimentCategory === "positive"
      ? "badge-green"
      : "badge-amber";

  const sentFriendly =
    r.sentimentCategory === "mixed_or_mismatch"
      ? "Mixed / Star-Text Mismatch"
      : r.sentimentCategory.charAt(0).toUpperCase() + r.sentimentCategory.slice(1);

  const overrideHtml = r.manualOverride
    ? `<div class="override-banner">
         <strong>✓ Verified by Human Auditor (${escapeHtml(r.manualOverride.auditor)})</strong>
         <div>${escapeHtml(r.manualOverride.analystNote)}</div>
       </div>`
    : "";

  const rawQuery = (document.getElementById("flt-q")?.value || "").trim();
  const formattedContent = highlightReviewTerms(r.content, rawQuery, r.subIssues || []);

  return `
    <article class="review-card">
      <!-- Left: Commuter Review (Source Evidence) -->
      <div class="review-source-pane">
        <div class="review-meta-row">
          ${starsHtml}
          <strong>${escapeHtml(r.date)}</strong>
          <code>${verText}</code>
          <span class="badge badge-amber" title="Helpful votes on Google Play">👍 ${r.thumbsUpCount} Helpful</span>
          ${streamBadges}
          ${editedBadge}
        </div>
        <div class="review-text">"${formattedContent}"</div>
        ${replyHtml}
        <details class="tech-provenance-details">
          <summary>View Technical Provenance (UUID &amp; SHA-256 Dedup Hash)</summary>
          <div style="margin-top:4px;">
            Google Play Review ID: <code>${escapeHtml(r.reviewId)}</code> &bull;
            SHA-256 Fingerprint: <code>${escapeHtml(r.dedupHash)}</code> &bull;
            Word Count: <strong>${r.wordCount} words</strong> (${escapeHtml(r.lengthBucket)})
          </div>
        </details>
      </div>

      <!-- Right: Automated Diagnosis & Human Audit -->
      <div class="review-interp-pane">
        <div>
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
            <span class="epistemic-tag ${r.manualOverride ? "tag-decision" : "tag-analytical"}" style="margin:0;">
              ${r.manualOverride ? "✓ HUMAN-AUDITED DIAGNOSIS" : "🤖 AUTOMATED ROOT-CAUSE TAGS"}
            </span>
            <span class="badge ${sentBadgeClass}">${escapeHtml(sentFriendly)}</span>
          </div>
          <div style="margin-top:6px;font-size:12px;">
            <strong>Problem Category:</strong>
            <div class="interp-tags">${themePills}</div>
          </div>
          <div style="margin-top:10px;font-size:12px;">
            <strong>Specific Symptoms Detected:</strong>
            <div class="interp-tags">${subIssuePills}</div>
          </div>
        </div>
        ${overrideHtml}
        <div style="display:flex;justify-content:flex-end;margin-top:4px;">
          <button class="btn btn-xs btn-outline btn-audit-review" data-revid="${escapeHtml(r.reviewId)}">
            &#9998; Edit / Audit Tags
          </button>
        </div>
      </div>
    </article>
  `;
}

/* --------------------------------------------------------------------------
   TAB 3: Issue Prioritization & Root Causes
   -------------------------------------------------------------------------- */
function renderPrioritizationTab(data) {
  renderPrioritizationMatrix(data.issuesRegister);
  renderIssueDossiers(data.issuesRegister);
}

function renderPrioritizationMatrix(issuesList) {
  const wp = Number(document.getElementById("rng-wp").value);
  const ws = Number(document.getElementById("rng-ws").value);
  const wv = Number(document.getElementById("rng-wv").value);
  const wc = Number(document.getElementById("rng-wc").value);
  const wf = Number(document.getElementById("rng-wf").value);
  const sumW = Math.max(1, wp + ws + wv + wc + wf);

  const nwP = wp / sumW;
  const nwS = ws / sumW;
  const nwV = wv / sumW;
  const nwC = wc / sumW;
  const nwF = wf / sumW;

  document.getElementById("lbl-wp").textContent = `${Math.round(nwP * 100)}%`;
  document.getElementById("lbl-ws").textContent = `${Math.round(nwS * 100)}%`;
  document.getElementById("lbl-wv").textContent = `${Math.round(nwV * 100)}%`;
  document.getElementById("lbl-wc").textContent = `${Math.round(nwC * 100)}%`;
  document.getElementById("lbl-wf").textContent = `${Math.round(nwF * 100)}%`;

  const simulated = issuesList.map((iss) => {
    const sb = iss.scoringBreakdown;
    const simScore =
      10.0 *
      (nwP * sb.prevalenceAndVisibility +
        nwS * sb.severityAndImpact +
        nwV * sb.temporalVelocity +
        nwC * sb.confidenceAndAttributability +
        nwF * sb.engineeringFeasibility);
    return {
      ...iss,
      simulatedScore: Number(simScore.toFixed(2)),
    };
  });

  simulated.sort((a, b) => b.simulatedScore - a.simulatedScore);

  const tbody = document.querySelector("#prioritization-matrix-table tbody");
  tbody.innerHTML = "";
  simulated.forEach((iss, idx) => {
    const rank = idx + 1;
    const sb = iss.scoringBreakdown;
    const growthColor = iss.h2VsH1GrowthPct >= 30 ? "#e11d48" : iss.h2VsH1GrowthPct < 0 ? "#047857" : "#d97706";
    const isSoftware = iss.themeCode !== "CAB_ROUTING_DISPATCH_OPS";
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td class="nowrap">
        <span class="badge ${rank === 1 ? "badge-red" : rank <= 3 ? "badge-blue" : "badge-gray"}">#${rank}</span>
        ${rank !== iss.priorityRank ? `<div style="font-size:10.5px;color:#64748b;">(base #${iss.priorityRank})</div>` : ""}
      </td>
      <td style="min-width:190px;">
        <strong><span class="nowrap">${iss.issueId}:</span> ${escapeHtml(iss.shortName)}</strong>
        <div style="font-size:11.5px;color:#64748b;">Avg ${iss.avgScoreNeg.toFixed(2)}★ (${iss.oneStarPctNeg}% 1★)</div>
      </td>
      <td class="nowrap"><span class="badge ${isSoftware ? "badge-blue" : "badge-amber"}">${isSoftware ? "💻 App Software" : "🚕 Fleet Ops"}</span></td>
      <td class="num nowrap"><strong>${iss.negCountTotal}</strong> <span style="color:#64748b;font-size:11.5px;">(${iss.negShareOfCorpusPct}%)</span></td>
      <td class="num nowrap">+${iss.posMentionCount}</td>
      <td class="num nowrap">${iss.thumbsUpTotal.toLocaleString()}</td>
      <td class="num nowrap" style="color:${growthColor};font-weight:700;">${iss.h2VsH1GrowthPct >= 0 ? "+" : ""}${iss.h2VsH1GrowthPct}%</td>
      <td class="num nowrap">${sb.prevalenceAndVisibility.toFixed(1)}</td>
      <td class="num nowrap">${sb.severityAndImpact.toFixed(1)}</td>
      <td class="num nowrap">${sb.temporalVelocity.toFixed(1)}</td>
      <td class="num nowrap"><strong>${sb.confidenceAndAttributability.toFixed(1)}</strong></td>
      <td class="num nowrap">${sb.engineeringFeasibility.toFixed(1)}</td>
      <td class="nowrap">
        <div class="score-bar-cell">
          <div class="score-bar-track"><div class="score-bar-fill" style="width:${iss.simulatedScore}%"></div></div>
          <strong style="font-size:13px;color:#0f172a;">${iss.simulatedScore.toFixed(1)}</strong>
        </div>
      </td>
      <td class="num nowrap">${iss.estimatedEffortSprints} sp</td>
      <td class="nowrap"><button class="btn btn-xs btn-outline nowrap">Read &rarr;</button></td>
    `;
    tr.querySelector("button").onclick = () =>
      jumpToExplorerWithFilters(
        { theme: iss.themeCode, score: "1-3" },
        `Inspecting ${iss.negCountTotal} negative reviews for ${iss.issueId}: ${iss.shortName}.`
      );
    tbody.appendChild(tr);
  });
}

function renderIssueDossiers(issuesList) {
  const container = document.getElementById("issue-dossiers-container");
  container.innerHTML = issuesList
    .map((iss) => {
      const rankClass = iss.priorityRank <= 3 ? `rank-${iss.priorityRank}` : "";
      const subBadges = Object.entries(iss.subIssueCounts || {})
        .map(([k, v]) => `<span class="badge badge-purple">${escapeHtml(friendlySubIssue(k))}: <strong>${v}</strong></span>`)
        .join(" ");

      const negQuotesHtml = (iss.representativeReviews || [])
        .slice(0, 3)
        .map(
          (q) => `
          <div class="quote-item">
            <div style="font-size:11.5px;color:#64748b;margin-bottom:3px;">
              <strong>${q.score}★ Review &bull; ${escapeHtml(q.date)} &bull; v${escapeHtml(q.version)} &bull; 👍 ${q.thumbsUpCount} Helpful</strong>
              <code>id=${escapeHtml(q.reviewId.slice(0, 8))}</code>
            </div>
            <div>"${escapeHtml(q.content.slice(0, 260))}${q.content.length > 260 ? "..." : ""}"</div>
          </div>`
        )
        .join("");

      const posQuotesHtml = (iss.positiveRepresentativeReviews || [])
        .slice(0, 2)
        .map(
          (q) => `
          <div class="quote-item quote-pos">
            <div style="font-size:11.5px;color:#047857;margin-bottom:3px;">
              <strong>${q.score}★ Happy User w/ Suggestion &bull; ${escapeHtml(q.date)} &bull; v${escapeHtml(q.version)}</strong>
              <code>id=${escapeHtml(q.reviewId.slice(0, 8))}</code>
            </div>
            <div>"${escapeHtml(q.content.slice(0, 220))}${q.content.length > 220 ? "..." : ""}"</div>
          </div>`
        )
        .join("");

      return `
        <div class="dossier-card ${rankClass}">
          <div class="card-header">
            <div>
              <span class="epistemic-tag ${iss.themeCode !== "CAB_ROUTING_DISPATCH_OPS" ? "tag-verified" : "tag-warning"}">
                PRIORITY RANK #${iss.priorityRank} (SCORE ${iss.priorityScore}/100) &bull; ${escapeHtml(iss.category)} &bull; CLASSIFIER ACCURACY F1=${iss.classifierValidation.f1Score}
              </span>
              <h3>${iss.issueId}: ${escapeHtml(iss.title)}</h3>
            </div>
            <div style="display:flex;gap:6px;flex-wrap:wrap;">
              <span class="badge badge-red">${iss.negCountTotal} Unhappy Reviews (${iss.negShareOfCorpusPct}%)</span>
              <span class="badge badge-green">+${iss.posMentionCount} 4–5★ Mentions</span>
              <span class="badge badge-amber">${escapeHtml(iss.trendStatus)}</span>
            </div>
          </div>

          <p class="card-desc">${escapeHtml(iss.plainLanguageSummary)}</p>
          <div style="margin-bottom:12px;"><strong>Specific Bugs Detected:</strong> ${subBadges}</div>

          <div class="dossier-grid-2">
            <div class="subcard">
              <h4>🔍 What Users Experience vs. Likely Code Cause</h4>
              <p style="font-size:13px;margin-bottom:10px;">
                <strong>🗣️ What Commuters Report (Verified Symptom):</strong><br/>
                ${escapeHtml(iss.reportedSymptomVsRootCause.reportedUserSymptom)}
              </p>
              <p style="font-size:13px;margin-bottom:10px;">
                <strong>🔧 Likely Engineering Root Cause (Hypothesis to Validate):</strong><br/>
                ${escapeHtml(iss.reportedSymptomVsRootCause.technicalRootCauseHypothesis || iss.reportedSymptomVsRootCause.technicalHypothesis)}
              </p>
              <p style="font-size:12.5px;color:#475569;">
                <strong>⚖️ Confounders &amp; Context:</strong><br/>
                ${escapeHtml(iss.confoundersAndLimitations)}
              </p>
            </div>

            <div class="subcard">
              <h4>💬 Real Commuter Quotes &amp; Positive Counter-Evidence</h4>
              ${negQuotesHtml}
              <div style="margin-top:8px;margin-bottom:6px;font-size:12.5px;color:#047857;">
                <strong>✓ Positive / Contradictory Evidence (${iss.posMentionCount} 4–5★ reviews):</strong>
                ${escapeHtml(iss.contradictoryPositiveEvidence)}
              </div>
              ${posQuotesHtml}
            </div>
          </div>

          <div class="subcard top-gap" style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;">
            <div style="font-size:13px;flex:1;">
              <strong>🚀 Recommended Engineering Fix (${escapeHtml(iss.suggestedOwner)}, ${iss.estimatedEffortSprints} Sprints):</strong>
              ${escapeHtml(iss.recommendedAction)}
              <div style="color:#475569;margin-top:4px;">
                <strong>First Step:</strong> ${escapeHtml(iss.firstImplementationStep)} &bull;
                <strong>Success Target:</strong> ${escapeHtml(iss.successMetric)}
              </div>
            </div>
            <button class="btn btn-sm btn-primary btn-dossier-explore" data-theme="${iss.themeCode}" data-name="${escapeHtml(iss.shortName)}">
              Read All ${iss.totalMentionsAllStars} Reviews &rarr;
            </button>
          </div>
        </div>
      `;
    })
    .join("");

  container.querySelectorAll(".btn-dossier-explore").forEach((btn) => {
    btn.onclick = () =>
      jumpToExplorerWithFilters(
        { theme: btn.dataset.theme },
        `Exploring all reviews mentioning ${btn.dataset.name}.`
      );
  });
}

/* --------------------------------------------------------------------------
   TAB 4: Action Plan & Tracking
   -------------------------------------------------------------------------- */
function renderActionsTab(data) {
  const ap = data.actionPlanAndTracking.primaryRecommendation;
  const register = data.actionPlanAndTracking.actionTrackingRegister;

  document.getElementById("ap-title").textContent = `${ap.selectedIssueId}: ${ap.proposedEngineeringChange.summary}`;
  document.getElementById("ap-rationale").textContent = ap.selectionRationale;
  document.getElementById("ap-parallel-note").innerHTML = `<strong>⚡ Parallel Week-1 Quick-Win Hotfixes:</strong> ${escapeHtml(ap.parallelHotfixNote)}`;

  document.getElementById("ap-components-grid").innerHTML = ap.proposedEngineeringChange.components
    .map(
      (c) => `
      <div class="component-box">
        <h4>${escapeHtml(c.component)}</h4>
        <p style="font-size:13px;color:#334155;margin-bottom:10px;">${escapeHtml(c.change)}</p>
        <div style="font-size:11.5px;color:#64748b;">
          <strong>Backed by Reviews:</strong> ${c.supportingEvidenceIds.map((id) => `<code>${escapeHtml(id)}</code>`).join(" ")}
        </div>
      </div>`
    )
    .join("");

  document.getElementById("ap-first-steps").innerHTML = ap.firstEngineeringSteps
    .map((s) => `<li>${escapeHtml(s)}</li>`)
    .join("");

  const valItems = ap.validationAndDependencies.requiredInternalValidation
    .map((v) => `<li><strong>QA Check:</strong> ${escapeHtml(v)}</li>`)
    .concat(
      ap.validationAndDependencies.dependencies.map((d) => `<li><strong>Dependency:</strong> ${escapeHtml(d)}</li>`)
    );
  document.getElementById("ap-validation-list").innerHTML = valItems.join("");

  // Measurement Plan Metrics
  document.getElementById("ap-metrics-cards").innerHTML = ap.measurementPlan.metrics
    .map(
      (m) => `
      <div class="metric-plan-card">
        <div style="font-weight:800;font-size:14px;margin-bottom:8px;">${escapeHtml(m.metricName)}</div>
        <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:8px;">
          <span class="badge badge-red">Today (${escapeHtml(m.baselineType)}): ${escapeHtml(m.baselineValue)}</span>
          <span class="badge badge-green">Goal (${escapeHtml(m.targetLabel)}): ${escapeHtml(m.proposedTarget)}</span>
        </div>
        <div style="font-size:12.5px;color:#475569;"><strong>How We Measure It:</strong> ${escapeHtml(m.measurementMethod)}</div>
      </div>`
    )
    .join("");

  // Guardrails & Decision Rules
  const dc = ap.measurementPlan.decisionConditions;
  document.getElementById("ap-guardrails-box").innerHTML = `
    <div class="subcard" style="margin-bottom:12px;">
      <h4>⏱️ Check-In Schedule</h4>
      <p style="font-size:13px;"><strong>Day 14 Canary Check:</strong> ${escapeHtml(ap.measurementPlan.evaluationTiming.canaryCheck)}</p>
      <p style="font-size:13px;"><strong>Day 30 &amp; Day 60 Review:</strong> ${escapeHtml(ap.measurementPlan.evaluationTiming.primaryEvaluation)}</p>
    </div>
    <div class="subcard" style="margin-bottom:12px;">
      <h4>🛡️ Safety Guardrails</h4>
      <ul class="step-list">
        ${ap.measurementPlan.risksAndGuardrails.map((g) => `<li>${escapeHtml(g)}</li>`).join("")}
      </ul>
    </div>
    <div class="subcard">
      <h4>🚦 Go / No-Go Decision Rules</h4>
      <p style="font-size:12.5px;margin-bottom:6px;"><span class="badge badge-green">Scale to 100%</span> ${escapeHtml(dc.continueAndScale)}</p>
      <p style="font-size:12.5px;margin-bottom:6px;"><span class="badge badge-amber">Adjust Fix</span> ${escapeHtml(dc.modifyIntervention)}</p>
      <p style="font-size:12.5px;"><span class="badge badge-red">Roll Back Immediately</span> ${escapeHtml(dc.reverseOrRollback)}</p>
    </div>
  `;

  renderActionTrackingTable(register);
}

function renderActionTrackingTable(register) {
  const tbody = document.querySelector("#action-tracking-table tbody");
  tbody.innerHTML = "";
  register.forEach((act) => {
    const isVerified = act.status.startsWith("Deployed") || act.status.startsWith("Verified");

    // Split status into crisp single-line badge + clean subtitle so it never forms a multi-line oval
    const statusParts = (act.status || "").split(/\s*[—–-]\s*/);
    const statusMain = statusParts[0] || act.status;
    const statusSub = statusParts.slice(1).join(" — ");

    // Split verification into clean badge + subtitle (no multi-line jagged <code> box)
    const verifRaw = act.verificationSource || "";
    const verifIdx = verifRaw.indexOf("(");
    const verifMain = verifIdx > 0 ? verifRaw.slice(0, verifIdx).trim() : verifRaw;
    const verifSub = verifIdx > 0 ? verifRaw.slice(verifIdx).replace(/^\(|\)$/g, "").trim() : "";

    // Split evaluation date into date + window subtitle
    const evalRaw = act.targetEvaluationDate || "";
    const evalIdx = evalRaw.indexOf("(");
    const evalMain = evalIdx > 0 ? evalRaw.slice(0, evalIdx).trim() : evalRaw;
    const evalSub = evalIdx > 0 ? evalRaw.slice(evalIdx).replace(/^\(|\)$/g, "").trim() : "";

    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td class="nowrap"><span class="id-pill">${escapeHtml(act.actionId)}</span></td>
      <td class="nowrap"><span class="id-pill id-pill-blue">${escapeHtml(act.issueId)}</span></td>
      <td style="min-width:280px;max-width:420px;">
        <strong style="display:block;color:#0f172a;margin-bottom:4px;">${escapeHtml(act.title)}</strong>
        <div style="font-size:12px;color:#475569;line-height:1.45;"><strong>Next Step:</strong> ${escapeHtml(act.nextStep)}</div>
        <div style="font-size:11.5px;color:#b45309;margin-top:4px;line-height:1.45;"><strong>Open Question:</strong> ${escapeHtml(act.unresolvedQuestions)}</div>
      </td>
      <td style="min-width:135px;font-weight:600;color:#334155;">${escapeHtml(act.owner)}</td>
      <td class="nowrap">
        <span class="badge ${isVerified ? "badge-green" : "badge-amber"}">● ${escapeHtml(statusMain)}</span>
        ${statusSub ? `<div class="cell-subtext">${escapeHtml(statusSub)}</div>` : ""}
      </td>
      <td style="min-width:165px;">
        <span class="badge ${isVerified ? "badge-green" : "badge-gray"}">${escapeHtml(verifMain)}</span>
        ${verifSub ? `<div class="cell-subtext">${escapeHtml(verifSub)}</div>` : ""}
      </td>
      <td style="min-width:210px;">
        <div style="font-size:11.5px;line-height:1.45;"><strong>Now:</strong> ${escapeHtml(act.baselineMetric)}</div>
        <div style="font-size:11.5px;color:#047857;margin-top:3px;line-height:1.45;"><strong>Goal:</strong> ${escapeHtml(act.proposedTarget)}</div>
      </td>
      <td class="nowrap">
        <strong style="color:#0f172a;">${escapeHtml(evalMain)}</strong>
        ${evalSub ? `<div class="cell-subtext">${escapeHtml(evalSub)}</div>` : ""}
      </td>
      <td class="nowrap"><button class="btn btn-xs btn-outline nowrap" data-actid="${escapeHtml(act.actionId)}">Update Status</button></td>
    `;
    tr.querySelector("button").onclick = () => openActionUpdateModal(act);
    tbody.appendChild(tr);
  });
}

/* --------------------------------------------------------------------------
   TAB 5: Monthly Monitoring, Classifier Validation & Exports
   -------------------------------------------------------------------------- */
function renderMonthlyTab(data) {
  const mm = data.monthlyMonitoring;
  document.getElementById("monthly-dedup-guarantee").textContent = mm.deduplicationGuarantee;

  const selPeriod = document.getElementById("sel-monthly-period").value || "2026-10";
  renderMonthlySnapshotView(mm.snapshots[selPeriod]);

  // Render Classifier Validation Table
  const val = data.classifierValidation;
  document.getElementById("val-f1-badge").textContent = `Accuracy (Micro-F1): ${val.microF1} | Exact Match: ${(val.exactSetMatchRate * 100).toFixed(1)}%`;

  const valTbody = document.querySelector("#validation-benchmark-table tbody");
  valTbody.innerHTML = "";
  Object.entries(val.perThemeMetrics).forEach(([themeCode, m]) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><strong>${escapeHtml(friendlyTheme(themeCode))}</strong></td>
      <td class="num nowrap">${m.truePositives}</td>
      <td class="num nowrap">${m.falsePositives}</td>
      <td class="num nowrap">${m.falseNegatives}</td>
      <td class="num nowrap">${(m.precision * 100).toFixed(1)}%</td>
      <td class="num nowrap">${(m.recall * 100).toFixed(1)}%</td>
      <td class="num nowrap"><strong>${(m.f1Score * 100).toFixed(1)}%</strong></td>
    `;
    valTbody.appendChild(tr);
  });
}

function renderMonthlySnapshotView(snap) {
  if (!snap) return;
  document.getElementById("btn-download-monthly-md").href = `/api/export/monthly/${snap.reportingPeriod}.md`;

  document.getElementById("monthly-kpi-strip").innerHTML = `
    <div class="kpi-card">
      <div class="kpi-label">Month Analyzed</div>
      <div class="kpi-value">${escapeHtml(snap.reportingPeriod)}</div>
      <div class="kpi-sub">Compared vs ${escapeHtml(snap.previousPeriodCompared)} &amp; 12m Avg</div>
    </div>
    <div class="kpi-card kpi-amber">
      <div class="kpi-label">Reviews in Month</div>
      <div class="kpi-value">${snap.totalReviews} Reviews</div>
      <div class="kpi-sub">Overall Avg: <strong>${snap.meanRating.toFixed(2)}★</strong> (${snap.negative12Pct}% 1–2★)</div>
    </div>
    <div class="kpi-card kpi-red">
      <div class="kpi-label">Real Written (&ge;6 Words)</div>
      <div class="kpi-value">${snap.substantiveMeanRating.toFixed(2)}★</div>
      <div class="kpi-sub">${snap.substantiveCount} detailed reviews in month</div>
    </div>
    <div class="kpi-card kpi-purple">
      <div class="kpi-label">Top Software Issue in Month</div>
      <div class="kpi-value" style="font-size:16px;">${escapeHtml(snap.topSoftwareIssueInMonth.issueId)}: ${escapeHtml(snap.topSoftwareIssueInMonth.shortName)}</div>
      <div class="kpi-sub">${snap.topSoftwareIssueInMonth.currentShareOfNegPct}% of unhappy reviews this month</div>
    </div>
  `;

  const tbody = document.querySelector("#monthly-comparison-table tbody");
  tbody.innerHTML = "";
  snap.issueComparisons.forEach((ic) => {
    const statusBadgeClass =
      ic.monthlyStatus === "Worsening"
        ? "badge-red"
        : ic.monthlyStatus === "Improving"
        ? "badge-green"
        : ic.monthlyStatus === "New / Emerging"
        ? "badge-purple"
        : "badge-amber";

    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td class="nowrap"><span class="id-pill id-pill-blue">${escapeHtml(ic.issueId)}</span></td>
      <td><strong>${escapeHtml(ic.shortName)}</strong></td>
      <td class="num nowrap">${ic.currentCount}</td>
      <td class="num nowrap"><strong>${ic.currentShareOfNegPct}%</strong></td>
      <td class="num nowrap">${ic.previousMonthSharePct}% (${ic.previousMonthCount})</td>
      <td class="num nowrap" style="font-weight:700;color:${ic.deltaMoMPts > 0 ? "#e11d48" : "#047857"};">
        ${ic.deltaMoMPts >= 0 ? "+" : ""}${ic.deltaMoMPts} pts
      </td>
      <td class="num nowrap">${ic.baseline12mSharePct}%</td>
      <td class="num nowrap">${ic.deltaVsBaselinePts >= 0 ? "+" : ""}${ic.deltaVsBaselinePts} pts</td>
      <td class="nowrap"><span class="badge ${statusBadgeClass}">${escapeHtml(ic.monthlyStatus)}</span></td>
    `;
    tbody.appendChild(tr);
  });
}

async function loadMonthlyHistory() {
  const res = await fetch("/api/monthly/history");
  const hist = await res.json();
  const tbody = document.querySelector("#monthly-history-table tbody");
  tbody.innerHTML = "";
  (hist.runs || []).slice(0, 8).forEach((r) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td class="nowrap"><code>${escapeHtml(r.runId)}</code></td>
      <td class="nowrap"><strong>${escapeHtml(r.reportingPeriod)}</strong></td>
      <td class="nowrap">${escapeHtml((r.executedAt || "").slice(0, 19).replace("T", " "))}</td>
      <td class="num nowrap">${(r.totalUniqueReviews || 0).toLocaleString()}</td>
      <td class="num nowrap"><strong>${Number(r.substantiveMeanRating || 0).toFixed(2)}★</strong></td>
      <td class="nowrap"><span class="badge badge-blue">${escapeHtml(r.topPriorityIssueId)}</span></td>
    `;
    tbody.appendChild(tr);
  });
}

/* --------------------------------------------------------------------------
   Modals & Interactive Workflows
   -------------------------------------------------------------------------- */
async function openOverrideModal(reviewId) {
  const res = await fetch(`/api/reviews/${encodeURIComponent(reviewId)}`);
  if (!res.ok) return;
  const rev = await res.json();

  document.getElementById("ovr-review-id").value = rev.reviewId;
  document.getElementById("override-review-preview").innerHTML = `
    <div><strong>Review:</strong> ${rev.score}★ on ${escapeHtml(rev.date)} (<code>${escapeHtml(rev.reviewId.slice(0, 8))}</code>)</div>
    <div style="margin-top:4px;font-weight:500;">"${escapeHtml(rev.content)}"</div>
    <div style="margin-top:6px;font-size:12px;color:#475569;">
      <strong>Current Automated Tags:</strong> ${(rev.automatedClassification.themes || []).map(friendlyTheme).join(", ") || "None"} (${escapeHtml(rev.automatedClassification.sentimentCategory)})
    </div>
  `;

  const activeThemes = new Set(rev.themes || []);
  document.querySelectorAll('input[name="ovr-theme"]').forEach((cb) => {
    cb.checked = activeThemes.has(cb.value);
  });
  document.getElementById("ovr-sentiment").value = rev.sentimentCategory || "negative";
  document.getElementById("ovr-note").value = rev.manualOverride ? rev.manualOverride.analystNote : "";
  document.getElementById("modal-override").classList.remove("hidden");
}

function openActionUpdateModal(act) {
  document.getElementById("act-edit-id").value = act.actionId;
  document.getElementById("act-modal-title").textContent = `Update ${act.actionId} (${act.issueId})`;
  document.getElementById("act-edit-status").value = act.status;
  document.getElementById("act-edit-verification").value = act.verificationSource;
  document.getElementById("act-edit-nextstep").value = act.nextStep;
  document.getElementById("act-edit-questions").value = act.unresolvedQuestions;
  document.getElementById("modal-action-update").classList.remove("hidden");
}

function setWeightSliders(wp, ws, wv, wc, wf) {
  document.getElementById("rng-wp").value = wp;
  document.getElementById("rng-ws").value = ws;
  document.getElementById("rng-wv").value = wv;
  document.getElementById("rng-wc").value = wc;
  document.getElementById("rng-wf").value = wf;
  if (STATE.investigation) {
    renderPrioritizationMatrix(STATE.investigation.issuesRegister);
  }
}

function bindNavigationAndModals() {
  // Tab switching
  document.querySelectorAll(".nav-tab").forEach((btn) => {
    btn.addEventListener("click", () => switchTab(btn.dataset.tab));
  });
  document.querySelectorAll("[data-goto-tab]").forEach((btn) => {
    btn.addEventListener("click", () => switchTab(btn.dataset.gotoTab));
  });

  // Quick Evidence Lens chips
  document.querySelectorAll(".lens-chip").forEach((chip) => {
    chip.addEventListener("click", () => applyQuickLens(chip.dataset.lens));
  });

  // Explorer filters
  const filterIds = ["flt-score", "flt-theme", "flt-subissue", "flt-version", "flt-length", "flt-stream", "flt-special", "flt-sort"];
  filterIds.forEach((id) => {
    document.getElementById(id).addEventListener("change", () => fetchExplorerReviews(1));
  });

  let searchTimer = null;
  document.getElementById("flt-q").addEventListener("input", () => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => fetchExplorerReviews(1), 260);
  });

  document.getElementById("btn-reset-filters").addEventListener("click", () => {
    document.querySelectorAll(".lens-chip").forEach((c) => c.classList.remove("active"));
    jumpToExplorerWithFilters({});
  });

  // Weight sensitivity sliders & presets
  ["rng-wp", "rng-ws", "rng-wv", "rng-wc", "rng-wf"].forEach((id) => {
    document.getElementById(id).addEventListener("input", () => {
      if (STATE.investigation) {
        renderPrioritizationMatrix(STATE.investigation.issuesRegister);
      }
    });
  });

  document.getElementById("btn-reset-weights").addEventListener("click", () => {
    setWeightSliders(25, 22, 20, 23, 10);
    showToast("Applied Recommended Balanced Prioritization Model (ISS-01 Ranks #1).");
  });

  const btnSoft = document.getElementById("btn-preset-software");
  if (btnSoft) {
    btnSoft.addEventListener("click", () => {
      setWeightSliders(15, 20, 20, 30, 15);
      showToast("Applied Pure Software Quick-Win Weights (High Software Controllability & Speed).");
    });
  }

  const btnVol = document.getElementById("btn-preset-volume");
  if (btnVol) {
    btnVol.addEventListener("click", () => {
      setWeightSliders(60, 20, 20, 0, 0);
      showToast("Simulating Naive Volume-Only Ranking: Notice how 3rd-party Cab Delays (ISS-08) jumps to #1 when Software Controllability is ignored!");
    });
  }

  // Monthly selector & execution
  document.getElementById("sel-monthly-period").addEventListener("change", (e) => {
    const ym = e.target.value;
    if (STATE.investigation && STATE.investigation.monthlyMonitoring.snapshots[ym]) {
      renderMonthlySnapshotView(STATE.investigation.monthlyMonitoring.snapshots[ym]);
    }
  });

  const triggerMonthlyRun = async () => {
    const ym = document.getElementById("sel-monthly-period").value || "2026-10";
    showToast(`Running monthly investigation for ${ym}...`);
    const res = await fetch("/api/monthly/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ reportingMonth: ym }),
    });
    const report = await res.json();
    await loadInvestigationData();
    await loadMonthlyHistory();
    switchTab("monthly");
    showToast(`Monthly Audit (${report.reportingPeriod}) completed! Run ID: ${report.runId}`);
  };

  document.getElementById("btn-execute-monthly").addEventListener("click", triggerMonthlyRun);
  document.getElementById("btn-quick-monthly").addEventListener("click", triggerMonthlyRun);

  // Override Modal handlers
  const closeOvr = () => document.getElementById("modal-override").classList.add("hidden");
  document.getElementById("btn-close-override").onclick = closeOvr;
  document.getElementById("btn-cancel-override").onclick = closeOvr;

  document.getElementById("form-override").addEventListener("submit", async (e) => {
    e.preventDefault();
    const revId = document.getElementById("ovr-review-id").value;
    const themes = Array.from(document.querySelectorAll('input[name="ovr-theme"]:checked')).map((c) => c.value);
    const sentiment = document.getElementById("ovr-sentiment").value;
    const auditor = document.getElementById("ovr-auditor").value;
    const note = document.getElementById("ovr-note").value;

    const res = await fetch(`/api/reviews/${encodeURIComponent(revId)}/override`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ themes, sentiment, auditor, note }),
    });
    if (res.ok) {
      closeOvr();
      await loadInvestigationData();
      await fetchExplorerReviews(STATE.explorerPage);
      showToast(`Saved human audit for review ${revId.slice(0, 8)} and updated metrics.`);
    }
  });

  // Action Update Modal handlers
  const closeAct = () => document.getElementById("modal-action-update").classList.add("hidden");
  document.getElementById("btn-close-action-modal").onclick = closeAct;
  document.getElementById("btn-cancel-action-modal").onclick = closeAct;

  document.getElementById("form-action-update").addEventListener("submit", async (e) => {
    e.preventDefault();
    const actId = document.getElementById("act-edit-id").value;
    const body = {
      status: document.getElementById("act-edit-status").value,
      verificationSource: document.getElementById("act-edit-verification").value,
      nextStep: document.getElementById("act-edit-nextstep").value,
      unresolvedQuestions: document.getElementById("act-edit-questions").value,
    };
    const res = await fetch(`/api/actions/${encodeURIComponent(actId)}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (res.ok) {
      closeAct();
      await loadInvestigationData();
      showToast(`Updated ${actId} status in the Action Tracker.`);
    }
  });

  // Import Reviews Modal handlers
  const closeImp = () => document.getElementById("modal-import").classList.add("hidden");
  document.getElementById("btn-open-import").onclick = () => {
    document.getElementById("imp-result-box").classList.add("hidden");
    document.getElementById("modal-import").classList.remove("hidden");
  };
  document.getElementById("btn-close-import").onclick = closeImp;
  document.getElementById("btn-cancel-import").onclick = closeImp;

  document.getElementById("btn-load-sample-import").onclick = () => {
    document.getElementById("imp-format").value = "json";
    document.getElementById("imp-payload").value = JSON.stringify(
      [
        {
          reviewId: "026c2e2a-7197-4609-85cf-94611b36a788",
          userName: "ExistingCommuter",
          content: "The map keeps zooming out automatically every few seconds while tracking the cab.",
          score: 1,
          at: "2026-10-11T10:00:00",
          reviewCreatedVersion: "12.19.0",
        },
        {
          reviewId: "sample-new-audit-2026-10-13",
          userName: "BengaluruUser",
          content: "Map auto zoom resets every 5 seconds and seatbelt popup hides the boarding OTP when in basement.",
          score: 1,
          at: "2026-10-12T09:15:00",
          reviewCreatedVersion: "12.19.0",
        },
      ],
      null,
      2
    );
  };

  document.getElementById("form-import").addEventListener("submit", async (e) => {
    e.preventDefault();
    const format = document.getElementById("imp-format").value;
    const persistBatch = document.getElementById("imp-mode").value === "persist";
    const payload = document.getElementById("imp-payload").value;

    const res = await fetch("/api/import", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ format, payload, persistBatch }),
    });
    const out = await res.json();
    const resBox = document.getElementById("imp-result-box");
    resBox.classList.remove("hidden");
    if (!res.ok) {
      resBox.className = "alert-banner alert-amber";
      resBox.textContent = `Import Error: ${out.detail || "Invalid format"}`;
      return;
    }
    resBox.className = "alert-banner alert-green";
    resBox.innerHTML = `
      <strong>✓ Duplicate Check Complete (${out.persisted ? "Saved to Database" : "Safe Test Mode"}):</strong><br/>
      Reviews Checked: <strong>${out.recordsSubmitted}</strong> &bull;
      Duplicates Blocked by ID: <strong>${out.duplicatesPreventedByReviewId}</strong> &bull;
      Duplicates Blocked by Fingerprint: <strong>${out.duplicatesPreventedByFallbackHash}</strong> &bull;
      New Unique Reviews Accepted: <strong>${out.newUniqueReviewsAccepted}</strong>
    `;
    if (out.persisted) {
      await loadInvestigationData();
      await fetchExplorerReviews(1);
    }
  });
}

/* --------------------------------------------------------------------------
   INTERACTIVE MODULE A: Live Keyword & Symptom Highlighting in Review Cards
   -------------------------------------------------------------------------- */
function highlightReviewTerms(text, searchQuery, subIssues) {
  let safe = escapeHtml(text || "");
  const terms = new Set();
  if (searchQuery && searchQuery.length >= 2) {
    terms.add(searchQuery.toLowerCase());
  }
  const subMap = {
    map_auto_zoom_reset: ["zoom", "zooming", "map", "reset"],
    otp_blocked_by_seatbelt_modal: ["seatbelt", "seat belt", "otp", "popup", "pop up"],
    forced_rating_no_skip: ["rating", "rate", "feedback", "skip", "force"],
    false_playstore_integrity_block: ["play store", "playstore", "reinstall", "uninstall"],
    morning_noshow_cancels_evening_logout: ["no show", "noshow", "evening", "logout", "cancel"],
  };
  (subIssues || []).forEach((s) => {
    (subMap[s] || []).forEach((kw) => terms.add(kw));
  });
  terms.forEach((kw) => {
    const escapedKw = kw.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    const regex = new RegExp(`(${escapedKw})`, "gi");
    safe = safe.replace(regex, '<mark class="kw-highlight">$1</mark>');
  });
  return safe;
}


document.addEventListener('DOMContentLoaded', initApp);
