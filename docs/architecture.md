# WebSense Technical Architecture Document

## System Overview

WebSense is an autonomous browser safety system that operates directly at the moment of legal consent. It continuously monitors the browser DOM for legal agreements (Terms of Service, Privacy Policies, NDAs, SaaS Contracts), performs fast local extraction, computes risk scores via a deterministic semantic backend, and pre-emptively intercepts submission when high-risk clauses are present.

---

## Component Architecture Diagram

```mermaid
flowchart TD
    subgraph Browser Environment
        A[Webpage DOM] -->|MutationObserver| B[Chrome Extension Detector]
        B -->|Candidate Text| C[Local Keyword Pre-Filter]
        C -->|Filtered Clauses| D[Background Service Worker]
    end

    subgraph Backend Analysis Engine
        D -->|POST /analyze| E[FastAPI REST API]
        E --> F[Hybrid Risk Analyzer]
        
        F --> G{LLM Key Available?}
        G -->|Yes| H[LLM Semantic Classifier]
        G -->|No / Offline| I[Deterministic Legal Pattern Classifier]
        
        F --> J[Lightweight Vector Engine]
        J -->|Cosine N-Gram Similarity| K[Legal Baselines DB]
        
        H --> L[Risk Engine Formula]
        I --> L
        K --> L
        
        L -->|Structured Risk JSON| E
    end

    subgraph Visual & Interception Layer
        E -->|Response| D
        D --> M[Content Script Coordinator]
        M --> N[Shadow DOM Isolated UI]
        N --> O[Floating Risk Status Indicator]
        N --> P[In-Page Heatmap & Popover Tooltips]
        N --> Q[Pre-Emptive Consent Interception Modal]
        Q -->|Explicit Checkbox Ack| R[Form Lock Released / Continue Allowed]
    end
```

---

## Risk Engine Mathematical Model

$$\text{Document Risk Score} = \text{clamp}\left(\text{Top Clause Score} + \sum_{i=1}^{n} (\text{Clause}_i \times 0.45 \times 0.55^{0.7i}) + \text{Breadth Bonus}, 0, 100\right)$$

Where each individual clause score is computed as:

$$\text{Clause Score} = (\text{Severity Weight} \times \text{Confidence}) + \left(\frac{\text{Deviation Score}}{100} \times 15\right) - \text{Mitigation Discount}$$

### Risk Level Ranges
- **0 – 29**: `LOW RISK` (Calm Green)
- **30 – 59**: `MODERATE RISK` (Warning Amber)
- **60 – 79**: `HIGH RISK` (Orange/Red)
- **80 – 100**: `CRITICAL RISK` (Urgent Red)

---

## Data Privacy Architecture

```
User Web Browsing
   │
   ▼
Local DOM Extraction (Extension)
   │
   ▼
Local Regex Pre-Filtering (Only agreement snippets extracted)
   │
   ▼
FastAPI Backend (No raw page logging / Stateless)
   │
   ▼
Structured Risk Signals Returned to Browser
```

WebSense enforces local-first filtering. It **never** sends full raw web page HTML or un-related DOM content to external services.
