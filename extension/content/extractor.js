// WebSense Clause Text Extractor
window.WebSenseExtractor = (function () {
  const FILTER_KEYWORDS = [
    "assign", "intellectual property", "perpetual", "irrevocable", "data broker",
    "sell your data", "rent your data", "monetize", "train", "ai model", "machine learning",
    "arbitration", "class action", "jury trial", "renew", "recurring", "non-refundable",
    "indemnify", "hold harmless", "disclaim", "liability", "sole discretion", "terminate",
    "non-compete", "ownership", "surveillance", "monitor"
  ];

  function extractClausesFromContainers(containers) {
    const extractedClauses = [];
    const seenHashes = new Set();

    containers.forEach(container => {
      // Find paragraphs, list items, or sentence blocks
      const textBlocks = container.querySelectorAll("p, li, div > p, span, td");
      
      let elementsToScan = Array.from(textBlocks);
      if (elementsToScan.length === 0) {
        elementsToScan = [container];
      }

      elementsToScan.forEach(el => {
        const rawText = el.innerText || "";
        if (rawText.length < 15) return;

        // Split text by sentence boundaries
        const sentences = rawText.split(/(?<=[.!?])\s+/);
        
        sentences.forEach(sentence => {
          const cleanSentence = sentence.trim();
          if (cleanSentence.length < 15) return;

          const lower = cleanSentence.toLowerCase();
          const hash = simpleHash(cleanSentence);

          if (seenHashes.has(hash)) return;

          // Local pre-filtering: check if sentence contains any legal risk keyword
          const matchesKeyword = FILTER_KEYWORDS.some(kw => lower.includes(kw));
          
          if (matchesKeyword) {
            seenHashes.add(hash);
            extractedClauses.push({
              text: cleanSentence,
              element: el
            });
          }
        });
      });
    });

    return extractedClauses;
  }

  function simpleHash(str) {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      hash = ((hash << 5) - hash) + str.charCodeAt(i);
      hash |= 0;
    }
    return hash;
  }

  return {
    extractClausesFromContainers
  };
})();
