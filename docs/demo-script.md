# WebSense Hackathon Demo Script & Presentation Guide

## 🎯 High-Impact 3-Minute Demo Walkthrough

### Part 1: The Problem (0:00 - 0:30)
> *"Every single day, millions of users click 'I Agree' on legal terms without reading a single word. Existing AI tools force you to copy-paste giant 50-page PDFs into ChatGPT. WebSense brings real-time, autonomous protection directly to the moment of consent inside your browser."*

### Part 2: Passive Scanning & In-Page Heatmap (0:30 - 1:15)
1. Open Chrome and navigate to the **CloudFlow AI Demo Page** (`http://localhost:8080/risky.html`).
2. Point out the **Floating WebSense Indicator** in the bottom right corner updating automatically from `Scanning...` to `HIGH RISK (82/100)`.
3. Scroll through the CloudFlow Terms section to show the **In-Page Heatmap Highlights**:
   - Highlighted in Red: *Broad IP Assignment* & *Data Sale*.
   - Highlighted in Amber: *Mandatory Arbitration* & *Auto-Renewal*.
4. **Hover over a highlighted red clause** to display the plain-English tooltip popover showing the explanation, why it matters, and confidence score.

### Part 3: The WOW Moment — Consent Interception (1:15 - 2:15)
1. Check the `[ ] I agree to the CloudFlow Terms` checkbox.
2. Click **[ Accept Terms & Create Account ]**.
3. **WATCH WEBSENSE INTERCEPT THE ACTION**:
   - The form submit is blocked pre-emptively.
   - The **Consent Interception Modal** renders over the page with `⚠ HIGH RISK DETECTED (82/100)`.
   - The modal lists the exact detected clauses (*Broad IP Assignment*, *Data Sale*, *Mandatory Arbitration*).
   - Point out that the **[ Continue Anyway ]** button is disabled until explicit acknowledgment.
4. Check the acknowledgment box: *"I understand these automated risk signals..."*
5. Click **[ Continue Anyway ]**. The form submits cleanly!

### Part 4: Deterministic Accuracy & Low Risk Demo (2:15 - 3:00)
1. Navigate to the **Simple Notes App Demo Page** (`http://localhost:8080/safe.html`).
2. Show that WebSense automatically evaluates the safe terms to **LOW RISK (18/100)**.
3. Click **Accept** on the safe page — point out that WebSense does NOT block safe agreements, eliminating false alarm friction.
