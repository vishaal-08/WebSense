// WebSense Pre-Emptive Consent Interceptor
window.WebSenseInterceptor = (function () {
  let isIntercepting = false;
  let currentAnalysis = null;
  let currentTargetButton = null;

  function attachInterception(analysis) {
    currentAnalysis = analysis;
    if (!analysis || analysis.risk_score < 45) {
      return; // Safe or low risk: allow normal submission flow
    }

    const currentUrl = window.location.href;

    // Check if user has already acknowledged risk for this page
    chrome.storage.local.get(["acknowledgedUrls", "protectionEnabled"], (res) => {
      const ackMap = res.acknowledgedUrls || {};
      const protectionEnabled = res.protectionEnabled !== false;

      if (!protectionEnabled || ackMap[currentUrl]) {
        console.log("WebSense: Protection disabled or URL already acknowledged by user.");
        return;
      }

      activateInterceptionListeners();
    });
  }

  function activateInterceptionListeners() {
    if (isIntercepting) return;
    isIntercepting = true;

    // Capture phase click listener on detected agreement submit buttons
    document.addEventListener("click", handleCaptureClick, true);
    document.addEventListener("submit", handleCaptureSubmit, true);
  }

  function handleCaptureClick(e) {
    if (e.defaultPrevented || e.__websense_bypassed) return;

    const target = e.target.closest("button, input[type='submit'], input[type='button'], a.btn, [role='button']");
    if (!target || target.hasAttribute("data-websense-ui")) return;

    const label = (target.innerText || target.value || "").toLowerCase();
    const isAgreementBtn = ["accept", "agree", "sign", "submit", "continue"].some(kw => label.includes(kw));

    if (isAgreementBtn && currentAnalysis && currentAnalysis.risk_score >= 45) {
      e.preventDefault();
      e.stopPropagation();
      e.stopImmediatePropagation();

      currentTargetButton = target;

      // Trigger Consent Interception Modal
      window.WebSenseShadowUI.showConsentModal(currentAnalysis, () => {
        // User acknowledged modal! Save state and re-trigger click.
        acknowledgeAndProceed(target);
      });
    }
  }

  function handleCaptureSubmit(e) {
    if (e.defaultPrevented || e.__websense_bypassed) return;

    if (currentAnalysis && currentAnalysis.risk_score >= 45) {
      e.preventDefault();
      e.stopPropagation();
      e.stopImmediatePropagation();

      const form = e.target;
      window.WebSenseShadowUI.showConsentModal(currentAnalysis, () => {
        acknowledgeAndProceed(null, form);
      });
    }
  }

  function acknowledgeAndProceed(buttonEl, formEl) {
    const currentUrl = window.location.href;

    // Send acknowledgment message to background script
    chrome.runtime.sendMessage({
      type: "SET_ACKNOWLEDGED",
      url: currentUrl
    }, () => {
      // Re-dispatch bypassed event to allow normal site progression
      if (buttonEl) {
        buttonEl.__websense_bypassed = true;
        buttonEl.click();
      } else if (formEl) {
        formEl.__websense_bypassed = true;
        formEl.submit();
      }
    });
  }

  return {
    attachInterception
  };
})();
