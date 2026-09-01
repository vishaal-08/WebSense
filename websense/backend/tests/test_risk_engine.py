import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.analyzers.local_analyzer import local_analyzer
from app.models.schemas import RiskCategory, SeverityLevel, RiskLevel
from app.scoring.risk_engine import calculate_overall_risk_score
from app.vector.lightweight_vector import vector_engine

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "analyzer" in data


def test_risk_categories_endpoint():
    response = client.get("/risk-categories")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 15
    categories = [item["category"] for item in data]
    assert "IP_ASSIGNMENT" in categories
    assert "MANDATORY_ARBITRATION" in categories


def test_local_classifier_detection():
    sample_clauses = [
        "The user hereby assigns all right, title, and intellectual property to the company irrevocably.",
        "Any dispute arising out of this agreement shall be submitted to binding arbitration under AAA rules.",
        "We automatically renew your subscription every month without further notice."
    ]
    results = local_analyzer.analyze_clauses(sample_clauses, "SaaS Terms")
    assert len(results) >= 3
    
    categories = [r.category for r in results]
    assert RiskCategory.IP_ASSIGNMENT in categories
    assert RiskCategory.MANDATORY_ARBITRATION in categories
    assert RiskCategory.AUTO_RENEWAL in categories


def test_scoring_clamping_and_levels():
    clauses = local_analyzer.analyze_clauses([
        "The user assigns all intellectual property to the company forever.",
        "We sell your data to data brokers for commercial monetization.",
        "You waive all rights to a jury trial or class action lawsuit."
    ], "Generic TOS")
    
    score, level, summary = calculate_overall_risk_score(clauses)
    assert 0 <= score <= 100
    assert score >= 60  # High or Critical risk
    assert level in [RiskLevel.HIGH, RiskLevel.CRITICAL]


def test_analyze_api_endpoint():
    payload = {
        "document_type": "SaaS Terms",
        "clauses": [
            "You grant us a perpetual, worldwide, sublicensable license to use your content for any purpose without compensation.",
            "We reserve the right to modify these terms at any time in our sole discretion."
        ]
    }
    response = client.post("/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["risk_score"] > 50
    assert data["risk_level"] in ["HIGH", "CRITICAL"]
    assert len(data["clauses"]) >= 2


def test_baseline_compare_endpoint():
    payload = {
        "clause_text": "Company retains sole ownership of all customer uploads and derivative works.",
        "document_type": "SaaS Terms",
        "expected_category": "IP_ASSIGNMENT"
    }
    response = client.post("/baseline/compare", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["deviation_score"] > 30.0
    assert "baseline_standard" in data
