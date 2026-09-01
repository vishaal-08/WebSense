// WebSense Background Service Worker (Manifest V3)
const BACKEND_URL = "http://localhost:8000";

// Default extension settings
chrome.runtime.onInstalled.addListener(() => {
  chrome.storage.local.set({
    protectionEnabled: true,
    backendUrl: BACKEND_URL,
    acknowledgedUrls: {},
    pageAnalyses: {}
  });
  console.log("WebSense Service Worker installed and initialized.");
});

// Handle incoming messages from Content Script and Popup UI
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "ANALYZE_DOCUMENT") {
    handleDocumentAnalysis(message.payload, sender)
      .then(response => sendResponse(response))
      .catch(error => {
        console.warn("Backend request error, initiating local fallback:", error);
        sendResponse({ success: false, error: error.message });
      });
    return true; // Keep channel open for async response
  }

  if (message.type === "UPDATE_BADGE") {
    updateBadge(sender.tab?.id, message.score, message.level);
    sendResponse({ success: true });
    return false;
  }

  if (message.type === "SET_ACKNOWLEDGED") {
    const url = message.url;
    chrome.storage.local.get(["acknowledgedUrls"], (res) => {
      const ackMap = res.acknowledgedUrls || {};
      ackMap[url] = true;
      chrome.storage.local.set({ acknowledgedUrls: ackMap }, () => {
        sendResponse({ success: true });
      });
    });
    return true;
  }
});

async function handleDocumentAnalysis(payload, sender) {
  const tabId = sender.tab?.id;
  const currentUrl = payload.url || sender.tab?.url || "";

  try {
    const res = await fetch(`${BACKEND_URL}/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      throw new Error(`Server returned status ${res.status}`);
    }

    const data = await res.json();
    
    // Save tab analysis state
    if (tabId && currentUrl) {
      chrome.storage.local.get(["pageAnalyses"], (result) => {
        const pageAnalyses = result.pageAnalyses || {};
        pageAnalyses[currentUrl] = data;
        chrome.storage.local.set({ pageAnalyses });
      });
      updateBadge(tabId, data.risk_score, data.risk_level);
    }

    return { success: true, data };
  } catch (err) {
    console.warn("WebSense Backend offline or unreachable. Using fallback.", err);
    return { success: false, isOffline: true, error: err.message };
  }
}

function updateBadge(tabId, score, level) {
  if (!tabId) return;

  let color = "#10b981"; // Safe Green
  let text = `${score}`;

  if (score >= 80 || level === "CRITICAL") {
    color = "#ef4444"; // Red
    text = `${score}`;
  } else if (score >= 60 || level === "HIGH") {
    color = "#f97316"; // Orange
    text = `${score}`;
  } else if (score >= 30 || level === "MODERATE") {
    color = "#f59e0b"; // Yellow/Amber
    text = `${score}`;
  }

  chrome.action.setBadgeText({ tabId, text });
  chrome.action.setBadgeBackgroundColor({ tabId, color });
}
