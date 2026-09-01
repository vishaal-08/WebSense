from typing import List, Dict, Tuple
from app.models.schemas import ClauseRisk, SeverityLevel, RiskLevel


SEVERITY_WEIGHTS: Dict[SeverityLevel, int] = {
    SeverityLevel.LOW: 10,
    SeverityLevel.MEDIUM: 25,
    SeverityLevel.HIGH: 45,
    SeverityLevel.CRITICAL: 65,
}


def calculate_individual_clause_score(
    severity: SeverityLevel,
    confidence: float,
    deviation_score: float = 0.0,
    has_mitigation: bool = False
) -> int:
    """Calculate 0-100 risk contribution for a single clause."""
    base = SEVERITY_WEIGHTS.get(severity, 20)
    weighted = base * confidence
    deviation_bonus = (deviation_score / 100.0) * 15.0
    mitigation_discount = 10.0 if has_mitigation else 0.0
    
    total = weighted + deviation_bonus - mitigation_discount
    return max(5, min(100, int(round(total))))


def calculate_overall_risk_score(clauses: List[ClauseRisk]) -> Tuple[int, RiskLevel, str]:
    """
    Calculate the overall document legal risk score (0-100) and risk level.
    
    Formula:
    - Sum top clause contributions with diminishing marginal impact.
    - Add category diversity bonus (breadth of different risk types).
    - Clamp strictly to [0, 100].
    """
    if not clauses:
        return 0, RiskLevel.LOW, "No high-risk or concerning legal clauses detected on this page."
        
    # Sort clauses by score descending
    sorted_clauses = sorted(clauses, key=lambda c: c.score, reverse=True)
    
    # Highest scoring clause provides anchor score
    top_score = sorted_clauses[0].score
    
    # Cumulative impact of remaining clauses with diminishing returns (decay factor 0.5^i)
    cumulative_additions = 0.0
    for i, clause in enumerate(sorted_clauses[1:], start=1):
        decay = 0.55 ** (i * 0.7)
        cumulative_additions += clause.score * 0.45 * decay
        
    # Category breadth bonus (distinct categories detected)
    distinct_categories = len(set(c.category for c in clauses))
    breadth_bonus = min(15, (distinct_categories - 1) * 4) if distinct_categories > 1 else 0
    
    raw_total = top_score + cumulative_additions + breadth_bonus
    final_score = max(0, min(100, int(round(raw_total))))
    
    # Determine Risk Level
    if final_score < 30:
        level = RiskLevel.LOW
        summary = f"Low risk detected ({final_score}/100). The agreement uses largely standard, balanced terms."
    elif final_score < 60:
        level = RiskLevel.MODERATE
        summary = f"Moderate risk detected ({final_score}/100). Found {len(clauses)} potentially concerning provisions."
    elif final_score < 80:
        level = RiskLevel.HIGH
        summary = f"High legal risk detected ({final_score}/100). Found {len(clauses)} material risk clauses that significantly favor the provider."
    else:
        level = RiskLevel.CRITICAL
        summary = f"CRITICAL legal risk detected ({final_score}/100). Contains severe clauses including broad IP assignment, perpetual rights, or liability shifts."
        
    return final_score, level, summary
