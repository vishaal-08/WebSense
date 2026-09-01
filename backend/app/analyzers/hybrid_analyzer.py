import datetime
import logging
from typing import List, Optional
from app.models.schemas import AnalysisRequest, AnalysisResponse, ClauseRisk
from app.analyzers.local_analyzer import local_analyzer
from app.analyzers.llm_analyzer import llm_analyzer
from app.scoring.risk_engine import calculate_overall_risk_score

logger = logging.getLogger(__name__)


class HybridRiskAnalyzer:
    """Combines LLM semantic analysis with local deterministic classifier fail-safe fallback."""
    
    async def analyze(self, request: AnalysisRequest) -> AnalysisResponse:
        clauses_to_scan: List[str] = list(request.clauses or [])
        
        # If full text provided without pre-split clauses, split into sentences
        if not clauses_to_scan and request.full_text:
            import re
            sentences = re.split(r'(?<=[.!?])\s+', request.full_text)
            clauses_to_scan = [s.strip() for s in sentences if len(s.strip()) > 15]
            
        doc_type = request.document_type or "Generic TOS"
        detected_clauses: List[ClauseRisk] = []
        analyzer_used = "local"
        
        # 1. Try LLM semantic analysis if API key is present
        if llm_analyzer.is_available():
            llm_results = await llm_analyzer.analyze_clauses(clauses_to_scan, doc_type)
            if llm_results is not None:
                detected_clauses = llm_results
                analyzer_used = "hybrid (llm+local)"
                
        # 2. Fall back or supplement with local deterministic analyzer
        local_results = local_analyzer.analyze_clauses(clauses_to_scan, doc_type)
        
        if not detected_clauses:
            detected_clauses = local_results
            analyzer_used = "local (deterministic)"
        else:
            # Merge and deduplicate by text similarity
            existing_texts = set(c.text.lower() for c in detected_clauses)
            for loc in local_results:
                if loc.text.lower() not in existing_texts:
                    detected_clauses.append(loc)
                    existing_texts.add(loc.text.lower())
                    
        # 3. Calculate overall score and summary
        risk_score, risk_level, summary = calculate_overall_risk_score(detected_clauses)
        
        return AnalysisResponse(
            risk_score=risk_score,
            risk_level=risk_level,
            summary=summary,
            total_clauses_analyzed=len(clauses_to_scan),
            detected_risks_count=len(detected_clauses),
            clauses=detected_clauses,
            analyzer_used=analyzer_used,
            baseline_document_type=doc_type,
            timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
        )


# Global singleton instance
hybrid_analyzer = HybridRiskAnalyzer()
