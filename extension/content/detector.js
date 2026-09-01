// WebSense Autonomous Agreement & Submit Button Detector
window.WebSenseDetector = (function () {
  const AGREEMENT_KEYWORDS = [
    "terms of service", "terms & conditions", "terms of use", "privacy policy",
    "user agreement", "service agreement", "non-disclosure agreement", "nda",
    "license agreement", "consent form", "data processing agreement",
    "i agree", "accept terms", "contractor agreement", "employment agreement"
  ];

  const BUTTON_KEYWORDS = [
    "accept", "i agree", "agree & continue", "agree and continue", "sign",
    "submit", "continue", "create account", "accept terms", "confirm", "proceed"
  ];

  function isAgreementPageOrSection() {
    const pageText = document.body ? document.body.innerText.toLowerCase() : "";
    const title = document.title ? document.title.toLowerCase() : "";
    
    // Check page title and headings
    const titleMatch = AGREEMENT_KEYWORDS.some(kw => title.includes(kw));
    if (titleMatch) return true;

    // Check containers explicitly tagged or containing heading terms
    const containers = document.querySelectorAll("[data-websense-container], .terms-content, .agreement-box, article, main, form");
    for (let c of containers) {
      const text = c.innerText ? c.innerText.toLowerCase() : "";
      if (AGREEMENT_KEYWORDS.some(kw => text.includes(kw))) {
        return true;
      }
    }

    // Check text density of agreement keywords
    let matchCount = 0;
    for (let kw of AGREEMENT_KEYWORDS) {
      if (pageText.includes(kw)) matchCount++;
    }
    return matchCount >= 2;
  }

  function findAgreementContainers() {
    const containers = [];
    const elements = document.querySelectorAll("div, section, article, form, [data-websense-container]");
    
    elements.forEach(el => {
      if (el.hasAttribute("data-websense-processed") || el.hasAttribute("data-websense-ui")) {
        return;
      }
      const text = el.innerText || "";
      if (text.length > 80 && text.length < 50000) {
        const lower = text.toLowerCase();
        const matches = AGREEMENT_KEYWORDS.filter(kw => lower.includes(kw));
        if (matches.length >= 1) {
          containers.push(el);
        }
      }
    });

    return containers.length > 0 ? containers : [document.body];
  }

  function findSubmitButtons() {
    const buttons = [];
    const candidates = document.querySelectorAll("button, input[type='submit'], input[type='button'], a.btn, [role='button']");
    
    candidates.forEach(btn => {
      if (btn.hasAttribute("data-websense-ui")) return;
      
      const label = (btn.innerText || btn.value || btn.getAttribute("aria-label") || "").toLowerCase().trim();
      const isMatch = BUTTON_KEYWORDS.some(kw => label.includes(kw));
      
      if (isMatch) {
        buttons.push(btn);
      }
    });
    
    return buttons;
  }

  function observeDOMChanges(callback) {
    let timer = null;
    const observer = new MutationObserver(mutations => {
      let shouldScan = false;
      for (let mut of mutations) {
        // Ignore nodes injected by WebSense Shadow DOM or UI
        if (mut.target && mut.target.id === "websense-root-container") continue;
        if (mut.addedNodes.length > 0) {
          shouldScan = true;
          break;
        }
      }
      if (shouldScan) {
        if (timer) clearTimeout(timer);
        timer = setTimeout(() => {
          callback();
        }, 500);
      }
    });

    if (document.body) {
      observer.observe(document.body, { childList: true, subtree: true });
    }
  }

  return {
    isAgreementPageOrSection,
    findAgreementContainers,
    findSubmitButtons,
    observeDOMChanges
  };
})();
