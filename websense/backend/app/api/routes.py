from typing import List
from fastapi import APIRouter, HTTPException, status
from app.models.schemas import (
    AnalysisRequest,
    AnalysisResponse,
    BatchAnalysisRequest,
    BatchAnalysisResponse,
    BaselineCompareRequest,
    BaselineCompareResponse,
    CategoryInfo,
    HealthResponse,
    RiskCategory,
    SeverityLevel
)
from app.analyzers.hybrid_analyzer import hybrid_analyzer
from app.analyzers.local_analyzer import CATEGORY_DEFINITIONS, local_analyzer
from app.analyzers.llm_analyzer import llm_analyzer
from app.vector.lightweight_vector import vector_engine

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def get_health():
    """Health check endpoint indicating system operational status."""
    return HealthResponse(
        status="ok",
        version="1.0.0",
        analyzer="hybrid",
        llm_available=llm_analyzer.is_available()
    )


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_agreement(request: AnalysisRequest):
    """Analyze an agreement or set of clauses for legal risks."""
    if not request.clauses and not request.full_text:
        # Return clean low-risk response for empty payload rather than throwing error
        import datetime
        return AnalysisResponse(
            risk_score=0,
            risk_level=SeverityLevel.LOW,
            summary="No document content provided for analysis.",
            total_clauses_analyzed=0,
            detected_risks_count=0,
            clauses=[],
            analyzer_used="local",
            baseline_document_type=request.document_type or "Generic TOS",
            timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
        )
        
    try:
        return await hybrid_analyzer.analyze(request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error performing risk analysis: {str(e)}"
        )


@router.post("/analyze/batch", response_model=BatchAnalysisResponse)
async def analyze_batch(request: BatchAnalysisRequest):
    """Batch analyze multiple document requests concurrently."""
    results = []
    for doc_req in request.documents:
        res = await hybrid_analyzer.analyze(doc_req)
        results.append(res)
    return BatchAnalysisResponse(results=results)


@router.post("/baseline/compare", response_model=BaselineCompareResponse)
async def compare_baseline(request: BaselineCompareRequest):
    """Compare a single clause against baseline standards and compute deviation score."""
    if not request.clause_text or len(request.clause_text.strip()) < 5:
        raise HTTPException(status_code=400, detail="clause_text must be at least 5 characters.")
        
    category_str = request.expected_category.value if request.expected_category else "OTHER_MATERIAL_RISK"
    dev_score, baseline_std, summary = vector_engine.calculate_clause_deviation(
        request.clause_text, category_str, request.document_type
    )
    
    # Simple local classification for single clause
    local_risks = local_analyzer.analyze_clauses([request.clause_text], request.document_type)
    cat = local_risks[0].category if local_risks else RiskCategory.OTHER_MATERIAL_RISK
    sev = local_risks[0].severity if local_risks else SeverityLevel.MEDIUM
    
    return BaselineCompareResponse(
        clause_text=request.clause_text,
        baseline_standard=baseline_std,
        deviation_score=dev_score,
        analysis_summary=summary,
        category=cat,
        severity=sev
    )


@router.get("/risk-categories", response_model=List[CategoryInfo])
async def get_risk_categories():
    """Retrieve listing of all 20 legal risk categories monitored by WebSense."""
    categories_list = []
    for cat, info in CATEGORY_DEFINITIONS.items():
        categories_list.append(
            CategoryInfo(
                category=cat,
                display_name=cat.value.replace("_", " ").title(),
                default_severity=info["severity"],
                description=info["explanation"]
            )
        )
    return categories_list
