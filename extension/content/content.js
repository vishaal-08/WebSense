// WebSense Main Content Script Orchestrator
(function () {
  let isScanning = false;
  let hasAnalyzed = false;

  console.log("WebSense Autonomous Legal Protection active on tab.");

  function initWebSense() {
    window.WebSenseShadowUI.initUI();

    if (!window.WebSenseDetector.isAgreementPageOrSection()) {
      console.log("WebSense: No agreement context detected on initial scan.");
      return;
    }

    runFullScan();

    // Observe dynamic SPA / DOM updates
    window.WebSenseDetector.observeDOMChanges(() => {
      if (!hasAnalyzed) {
        runFullScan();
      }
    });

    // Listen for manual re-scan requests from extension popup
    chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
      if (msg && msg.type === "MANUAL_RESCAN") {
        hasAnalyzed = false;
        runFullScan();
        sendResponse({ success: true });
        return true;
      }
    });
  }

  function runFullScan() {
    if (isScanning) return;
    isScanning = true;

    console.log("WebSense: Scanning page DOM for legal risk clauses...");

    const containers = window.WebSenseDetector.findAgreementContainers();
    const extractedClauses = window.WebSenseExtractor.extractClausesFromContainers(containers);

    const clauseTexts = extractedClauses.map(c => c.text);
    const documentType = inferDocumentType();

    const payload = {
      url: window.location.href,
      title: document.title,
      document_type: documentType,
      clauses: clauseTexts
    };

    // Send payload to background script for analysis
    chrome.runtime.sendMessage({
      type: "ANALYZE_DOCUMENT",
      payload: payload
    }, (response) => {
      isScanning = false;
      hasAnalyzed = true;

      if (!response || !response.success) {
        console.warn("WebSense: Backend analysis response failed or offline.");
        return;
      }

      const analysis = response.data;
      console.log("WebSense Analysis Complete:", analysis);

      // 1. Update Shadow DOM Status Widget
      window.WebSenseShadowUI.updateStatus(analysis.risk_score, analysis.risk_level);

      // 2. Apply In-Page Heatmap Highlights
      window.WebSenseHighlighter.applyHighlights(analysis.clauses, window.WebSenseShadowUI);

      // 3. Attach Consent Submission Interceptor
      window.WebSenseInterceptor.attachInterception(analysis);
    });
  }

  function inferDocumentType() {
    const text = (document.title + " " + (document.body ? document.body.innerText : "")).toLowerCase();
    if (text.includes("non-disclosure") || text.includes("nda")) return "NDA";
    if (text.includes("privacy policy")) return "Privacy Policy";
    if (text.includes("freelancer") || text.includes("contractor")) return "Freelancer Agreement";
    if (text.includes("employment")) return "Employment Agreement";
    if (text.includes("safe") || text.includes("equity")) return "SAFE Agreement";
    if (text.includes("saas") || text.includes("subscription")) return "SaaS Terms";
    return "Generic TOS";
  }

  // Initialize on document ready
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initWebSense);
  } else {
    initWebSense();
  }
})();
