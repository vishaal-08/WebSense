from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class SeverityLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RiskCategory(str, Enum):
    DATA_HARVESTING = "DATA_HARVESTING"
    DATA_SHARING = "DATA_SHARING"
    DATA_SALE = "DATA_SALE"
    BROAD_LICENSE = "BROAD_LICENSE"
    IP_ASSIGNMENT = "IP_ASSIGNMENT"
    PERPETUAL_RIGHTS = "PERPETUAL_RIGHTS"
    UNILATERAL_LIABILITY = "UNILATERAL_LIABILITY"
    INDEMNIFICATION = "INDEMNIFICATION"
    MANDATORY_ARBITRATION = "MANDATORY_ARBITRATION"
    CLASS_ACTION_WAIVER = "CLASS_ACTION_WAIVER"
    AUTO_RENEWAL = "AUTO_RENEWAL"
    DIFFICULT_CANCELLATION = "DIFFICULT_CANCELLATION"
    TERMINATION_RIGHTS = "TERMINATION_RIGHTS"
    GOVERNING_LAW = "GOVERNING_LAW"
    RESTRICTIVE_TERMS = "RESTRICTIVE_TERMS"
    CONTENT_OWNERSHIP = "CONTENT_OWNERSHIP"
    AI_TRAINING = "AI_TRAINING"
    THIRD_PARTY_SHARING = "THIRD_PARTY_SHARING"
    SURVEILLANCE = "SURVEILLANCE"
    OTHER_MATERIAL_RISK = "OTHER_MATERIAL_RISK"


class ClauseRisk(BaseModel):
    id: str
    category: RiskCategory
    severity: SeverityLevel
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0")
    score: int = Field(..., ge=0, le=100, description="Individual clause risk score contribution (0-100)")
    text: str
    explanation: str
    why_it_matters: str
    matched_evidence: Optional[str] = None
    deviation_score: float = Field(default=0.0, ge=0.0, le=100.0)
    mitigating_factors: Optional[List[str]] = None


class AnalysisRequest(BaseModel):
    url: Optional[str] = None
    title: Optional[str] = None
    document_type: Optional[str] = "Generic TOS"  # e.g., TOS, Privacy Policy, NDA, Freelancer, SAFE
    clauses: List[str] = Field(default_factory=list, description="List of extracted candidate clauses or text snippets")
    full_text: Optional[str] = None


class AnalysisResponse(BaseModel):
    risk_score: int = Field(..., ge=0, le=100)
    risk_level: RiskLevel
    summary: str
    total_clauses_analyzed: int
    detected_risks_count: int
    clauses: List[ClauseRisk]
    analyzer_used: str = "hybrid"  # "local", "llm", "hybrid"
    baseline_document_type: str = "Generic TOS"
    timestamp: str
    disclaimer: str = "WebSense provides automated risk signals, not formal legal advice."


class BatchAnalysisRequest(BaseModel):
    documents: List[AnalysisRequest]


class BatchAnalysisResponse(BaseModel):
    results: List[AnalysisResponse]


class BaselineCompareRequest(BaseModel):
    clause_text: str
    document_type: str = "Generic TOS"
    expected_category: Optional[RiskCategory] = None


class BaselineCompareResponse(BaseModel):
    clause_text: str
    baseline_standard: str
    deviation_score: float
    analysis_summary: str
    category: RiskCategory
    severity: SeverityLevel


class CategoryInfo(BaseModel):
    category: RiskCategory
    display_name: str
    default_severity: SeverityLevel
    description: str


class HealthResponse(BaseModel):
    status: str
    version: str
    analyzer: str
    llm_available: bool
