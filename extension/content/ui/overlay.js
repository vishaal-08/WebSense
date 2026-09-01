// WebSense Shadow DOM UI Encapsulator
window.WebSenseShadowUI = (function () {
  let hostEl = null;
  let shadowRoot = null;
  let widgetEl = null;
  let tooltipEl = null;
  let modalBackdropEl = null;
  let onContinueHandler = null;

  function initUI() {
    if (hostEl) return;

    // Create host element on body
    hostEl = document.createElement("div");
    hostEl.id = "websense-root-container";
    hostEl.setAttribute("data-websense-ui", "true");
    document.body.appendChild(hostEl);

    // Attach Shadow DOM
    shadowRoot = hostEl.attachShadow({ mode: "open" });

    // Inject Isolated Stylesheet
    const styleLink = document.createElement("link");
    styleLink.rel = "stylesheet";
    styleLink.href = chrome.runtime.getURL("content/ui/styles.css");
    shadowRoot.appendChild(styleLink);

    // Build Floating Widget
    widgetEl = document.createElement("div");
    widgetEl.className = "websense-floating-widget";
    widgetEl.innerHTML = `
      <div class="websense-status-dot dot-scanning" id="statusDot"></div>
      <span class="websense-widget-title">WebSense</span>
      <span class="websense-widget-score" id="widgetScore">Scanning...</span>
    `;
    shadowRoot.appendChild(widgetEl);

    // Build Hover Tooltip Popover
    tooltipEl = document.createElement("div");
    tooltipEl.className = "websense-tooltip-popover";
    shadowRoot.appendChild(tooltipEl);

    // Build Consent Interception Modal
    modalBackdropEl = document.createElement("div");
    modalBackdropEl.className = "websense-modal-backdrop";
    modalBackdropEl.innerHTML = `
      <div class="websense-modal-card">
        <div class="websense-modal-header">
          <div class="websense-warning-icon">🛡️</div>
          <div class="websense-modal-title">WebSense Protection</div>
          <div class="websense-score-banner" id="modalScoreBanner">⚠ HIGH RISK DETECTED</div>
        </div>

        <p style="font-size: 13px; color: #94a3b8; margin-bottom: 14px; text-align: center;">
          We detected material legal risks in this agreement before you accept:
        </p>

        <div class="websense-clause-list" id="modalClauseList">
          <!-- Dynamically populated clauses -->
        </div>

        <div class="websense-ack-group">
          <label class="websense-ack-label">
            <input type="checkbox" id="ackCheckbox">
            <span>I understand these automated risk signals and want to continue anyway.</span>
          </label>
        </div>

        <div class="websense-btn-row">
          <button id="btnGoBack" class="websense-btn websense-btn-back">Go Back & Review</button>
          <button id="btnContinue" class="websense-btn websense-btn-continue" disabled>Continue Anyway</button>
        </div>

        <div class="websense-disclaimer-note">
          WebSense provides automated risk signals, not formal legal advice.
        </div>
      </div>
    `;
    shadowRoot.appendChild(modalBackdropEl);

    // Attach Event Listeners inside Shadow DOM
    const ackCheckbox = shadowRoot.querySelector("#ackCheckbox");
    const btnContinue = shadowRoot.querySelector("#btnContinue");
    const btnGoBack = shadowRoot.querySelector("#btnGoBack");

    ackCheckbox.addEventListener("change", (e) => {
      btnContinue.disabled = !e.target.checked;
    });

    btnGoBack.addEventListener("click", () => {
      hideConsentModal();
    });

    btnContinue.addEventListener("click", () => {
      if (onContinueHandler) {
        onContinueHandler();
      }
      hideConsentModal();
    });
  }

  function updateStatus(score, level) {
    if (!shadowRoot) initUI();

    const dot = shadowRoot.querySelector("#statusDot");
    const scoreEl = shadowRoot.querySelector("#widgetScore");

    dot.className = "websense-status-dot";
    if (level === "CRITICAL" || score >= 80) {
      dot.classList.add("dot-critical");
      scoreEl.innerText = `CRITICAL (${score}/100)`;
    } else if (level === "HIGH" || score >= 60) {
      dot.classList.add("dot-high");
      scoreEl.innerText = `HIGH RISK (${score}/100)`;
    } else if (level === "MODERATE" || score >= 30) {
      dot.classList.add("dot-moderate");
      scoreEl.innerText = `Risk: Moderate (${score})`;
    } else {
      dot.classList.add("dot-low");
      scoreEl.innerText = `Safe (${score}/100)`;
    }
  }

  function showTooltip(event, clause) {
    if (!tooltipEl) return;

    const categoryName = (clause.category || 'RISK').replace(/_/g, ' ');
    const severity = (clause.severity || 'MEDIUM').toLowerCase();
    const devScore = clause.deviation_score || 0;

    tooltipEl.innerHTML = `
      <div class="websense-popover-header">
        <span class="websense-badge ${severity}">${clause.severity || 'MEDIUM'} RISK</span>
        <span style="font-size: 11px; font-weight: 700; color: #94a3b8;">${categoryName}</span>
      </div>
      <div class="websense-popover-body">
        <div class="websense-popover-exp">${escapeHTML(clause.explanation)}</div>
        <div class="websense-popover-why">${escapeHTML(clause.why_it_matters)}</div>
      </div>
      <div class="websense-popover-meta">
        <span>Deviation: <strong>${devScore}%</strong></span>
        <span>Confidence: <strong>${Math.round((clause.confidence || 0.9) * 100)}%</strong></span>
      </div>
    `;

    // Position popover near mouse target
    const x = event.clientX;
    const y = event.clientY;
    tooltipEl.style.left = `${Math.min(x + 10, window.innerWidth - 360)}px`;
    tooltipEl.style.top = `${Math.max(y - 120, 20)}px`;
    tooltipEl.classList.add("visible");
  }

  function hideTooltip() {
    if (tooltipEl) tooltipEl.classList.remove("visible");
  }

  function showConsentModal(analysis, callback) {
    if (!modalBackdropEl) initUI();

    onContinueHandler = callback;
    const scoreBanner = shadowRoot.querySelector("#modalScoreBanner");
    const listEl = shadowRoot.querySelector("#modalClauseList");
    const ackCheckbox = shadowRoot.querySelector("#ackCheckbox");
    const btnContinue = shadowRoot.querySelector("#btnContinue");

    ackCheckbox.checked = false;
    btnContinue.disabled = true;

    scoreBanner.innerText = `⚠ ${analysis.risk_level} RISK DETECTED (${analysis.risk_score}/100)`;

    let clausesHTML = "";
    const clauses = analysis.clauses || [];

    if (clauses.length === 0) {
      clausesHTML = `<div style="text-align: center; color: #94a3b8; font-size: 12px;">Significant legal terms found on page.</div>`;
    } else {
      clauses.forEach(c => {
        const cat = (c.category || 'RISK').replace(/_/g, ' ');
        clausesHTML += `
          <div class="websense-clause-item">
            <span style="color: #ef4444;">⚠</span>
            <div>
              <strong style="color: #f8fafc;">${escapeHTML(cat)}:</strong>
              <span style="color: #cbd5e1;"> ${escapeHTML(c.explanation)}</span>
            </div>
          </div>
        `;
      });
    }

    listEl.innerHTML = clausesHTML;
    modalBackdropEl.classList.add("visible");
  }

  function hideConsentModal() {
    if (modalBackdropEl) modalBackdropEl.classList.remove("visible");
  }

  function escapeHTML(str) {
    if (!str) return '';
    return str.replace(/[&<>"']/g, match => {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[match];
    });
  }

  return {
    initUI,
    updateStatus,
    showTooltip,
    hideTooltip,
    showConsentModal,
    hideConsentModal
  };
})();
