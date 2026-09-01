// WebSense In-Page Heatmap & Clause Highlighter
window.WebSenseHighlighter = (function () {
  
  function applyHighlights(clauseRisks, shadowUI) {
    if (!clauseRisks || clauseRisks.length === 0) return;

    clauseRisks.forEach(clause => {
      highlightClauseText(clause, shadowUI);
    });
  }

  function highlightClauseText(clause, shadowUI) {
    const searchText = clause.text.trim();
    if (!searchText) return;

    // Search text nodes across agreement containers
    const walker = document.createTreeWalker(
      document.body,
      NodeFilter.SHOW_TEXT,
      {
        acceptNode: function(node) {
          if (!node.nodeValue || node.nodeValue.trim().length < 10) {
            return NodeFilter.FILTER_SKIP;
          }
          if (node.parentElement && (
            node.parentElement.hasAttribute("data-websense-highlight") ||
            node.parentElement.hasAttribute("data-websense-ui") ||
            node.parentElement.tagName === "SCRIPT" ||
            node.parentElement.tagName === "STYLE"
          )) {
            return NodeFilter.FILTER_SKIP;
          }
          return NodeFilter.FILTER_ACCEPT;
        }
      }
    );

    let currentNode;
    while (currentNode = walker.nextNode()) {
      const nodeText = currentNode.nodeValue;
      const index = nodeText.indexOf(searchText.substring(0, Math.min(30, searchText.length)));
      
      if (index !== -1) {
        const parent = currentNode.parentElement;
        if (!parent) continue;

        const mark = document.createElement("mark");
        const severityClass = `websense-risk-${(clause.severity || 'MEDIUM').toLowerCase()}`;
        mark.className = `websense-highlight ${severityClass}`;
        mark.setAttribute("data-websense-highlight", "true");
        mark.setAttribute("data-clause-id", clause.id);

        // Attach hover popover events
        mark.addEventListener("mouseenter", (e) => {
          shadowUI.showTooltip(e, clause);
        });

        mark.addEventListener("mouseleave", () => {
          shadowUI.hideTooltip();
        });

        try {
          const range = document.createRange();
          range.setStart(currentNode, 0);
          range.setEnd(currentNode, nodeText.length);
          range.surroundContents(mark);
        } catch (e) {
          // If range surrounding fails due to HTML boundary, wrap parent styling safely
          parent.classList.add("websense-highlight", severityClass);
          parent.setAttribute("data-websense-highlight", "true");
          parent.addEventListener("mouseenter", (evt) => shadowUI.showTooltip(evt, clause));
          parent.addEventListener("mouseleave", () => shadowUI.hideTooltip());
        }
        break; // Match highlighted once
      }
    }
  }

  function clearHighlights() {
    const highlights = document.querySelectorAll("[data-websense-highlight]");
    highlights.forEach(el => {
      if (el.tagName === "MARK") {
        const parent = el.parentNode;
        while (el.firstChild) parent.insertBefore(el.firstChild, el);
        parent.removeChild(el);
      } else {
        el.removeAttribute("data-websense-highlight");
        el.className = el.className.replace(/websense-highlight\s+websense-risk-\w+/g, "");
      }
    });
  }

  return {
    applyHighlights,
    clearHighlights
  };
})();
