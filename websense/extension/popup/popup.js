document.addEventListener('DOMContentLoaded', () => {
  const siteUrlEl = document.getElementById('siteUrl');
  const scoreNumberEl = document.getElementById('scoreNumber');
  const riskBadgeEl = document.getElementById('riskBadge');
  const docTypeEl = document.getElementById('docType');
  const summaryBoxEl = document.getElementById('summaryBox');
  const riskListEl = document.getElementById('riskList');
  const riskCountEl = document.getElementById('riskCount');
  const rescanBtn = document.getElementById('rescanBtn');
  const protectionToggle = document.getElementById('protectionToggle');

  // Load active tab details
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    if (!tabs || tabs.length === 0) return;
    const currentTab = tabs[0];
    const url = currentTab.url || "";
    
    try {
      const hostname = new URL(url).hostname;
      siteUrlEl.innerText = hostname || url;
    } catch (e) {
      siteUrlEl.innerText = url;
    }

    // Retrieve cached analysis from local storage
    chrome.storage.local.get(["pageAnalyses", "protectionEnabled"], (res) => {
      if (res.protectionEnabled !== undefined) {
        protectionToggle.checked = res.protectionEnabled;
      }

      const pageAnalyses = res.pageAnalyses || {};
      const analysis = pageAnalyses[url];

      if (analysis) {
        renderAnalysis(analysis);
      } else {
        scoreNumberEl.innerText = "0";
        riskBadgeEl.innerText = "CLEAN / UNKNOWN";
        riskBadgeEl.className = "risk-badge low";
        summaryBoxEl.innerText = "No legal agreement context detected on this page.";
      }
    });
  });

  protectionToggle.addEventListener('change', (e) => {
    chrome.storage.local.set({ protectionEnabled: e.target.checked });
  });

  rescanBtn.addEventListener('click', () => {
    rescanBtn.innerText = "Scanning...";
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (tabs[0]?.id) {
        chrome.tabs.sendMessage(tabs[0].id, { type: "MANUAL_RESCAN" }, () => {
          setTimeout(() => {
            rescanBtn.innerText = "🔄 Scan This Page";
            window.location.reload();
          }, 1000);
        });
      }
    });
  });

  function renderAnalysis(analysis) {
    scoreNumberEl.innerText = analysis.risk_score;
    docTypeEl.innerText = analysis.baseline_document_type || "Generic TOS";
    summaryBoxEl.innerText = analysis.summary || "Legal analysis complete.";

    const level = (analysis.risk_level || "LOW").toLowerCase();
    riskBadgeEl.innerText = analysis.risk_level;
    riskBadgeEl.className = `risk-badge ${level}`;

    const clauses = analysis.clauses || [];
    riskCountEl.innerText = clauses.length;

    if (clauses.length === 0) {
      riskListEl.innerHTML = `<div class="empty-state">No high-risk clauses detected.</div>`;
      return;
    }

    let html = "";
    clauses.forEach(c => {
      const cat = (c.category || "RISK").replace(/_/g, " ");
      const sev = (c.severity || "MEDIUM").toLowerCase();
      html += `
        <div class="risk-item">
          <span class="risk-dot ${sev}"></span>
          <div style="flex-grow: 1;">
            <strong style="color: #f8fafc;">${cat}</strong>
            <div style="font-size: 0.75rem; color: #94a3b8;">${c.explanation}</div>
          </div>
        </div>
      `;
    });
    riskListEl.innerHTML = html;
  }
});
