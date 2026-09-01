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


def test_all_20_categories_detection():
    """Verify that every single one of the 20 legal risk categories is detected by local analyzer."""
    category_samples = {
        RiskCategory.IP_ASSIGNMENT: "You irrevocably assign all intellectual property and inventions to the company.",
        RiskCategory.PERPETUAL_RIGHTS: "The granted rights are royalty-free, perpetual and survive indefinitely.",
        RiskCategory.BROAD_LICENSE: "You grant an unrestricted right to use, reproduce, modify, adapt, publish, translate, create derivative works.",
        RiskCategory.DATA_SALE: "We may sell, rent, or monetize your personal data to third parties.",
        RiskCategory.AI_TRAINING: "We use your uploads and content to train our AI and generative machine learning models.",
        RiskCategory.MANDATORY_ARBITRATION: "All disputes must be resolved by binding arbitration under American Arbitration Association rules.",
        RiskCategory.CLASS_ACTION_WAIVER: "You agree to proceed in an individual capacity only and waive any right to participate in a class action.",
        RiskCategory.AUTO_RENEWAL: "Your credit card will be charged automatically every billing cycle on an auto-renewal basis.",
        RiskCategory.DIFFICULT_CANCELLATION: "All subscriptions are strictly non-refundable and no refunds under any circumstance will be issued.",
        RiskCategory.INDEMNIFICATION: "You agree to indemnify, defend, and hold harmless the company against all third-party claims and liabilities.",
        RiskCategory.UNILATERAL_LIABILITY: "The company's maximum aggregate liability shall not exceed $0 and we disclaim all warranties.",
        RiskCategory.DATA_HARVESTING: "We collect location, device, biometric, contacts, browsing and keystroke data across sessions.",
        RiskCategory.DATA_SHARING: "We may disclose personal data to advertisers and third-party commercial marketing partners.",
        RiskCategory.THIRD_PARTY_SHARING: "Information may be provided to unspecified third parties and business partners and sponsors.",
        RiskCategory.SURVEILLANCE: "The software may monitor your screen, keystrokes and record session activity during use.",
        RiskCategory.TERMINATION_RIGHTS: "We reserve the right to terminate your account at any time for any reason without notice.",
        RiskCategory.RESTRICTIVE_TERMS: "You agree to a 24-month non-compete and shall not engage in any competing business.",
        RiskCategory.CONTENT_OWNERSHIP: "The company retains ownership of all user-generated content and uploads become company property.",
        RiskCategory.GOVERNING_LAW: "All disputes are governed by the laws of Delaware with exclusive jurisdiction in foreign court.",
        RiskCategory.OTHER_MATERIAL_RISK: "The company reserves a unilateral right to seize your digital balance with a penalty fee."
    }

    for expected_cat, sample_clause in category_samples.items():
        results = local_analyzer.analyze_clauses([sample_clause], "Generic TOS")
        matched_categories = [r.category for r in results]
        assert expected_cat in matched_categories, (
            f"Failed to detect expected category {expected_cat} for clause: '{sample_clause}'"
        )


def test_false_positive_and_clean_clauses():
    """Verify that safe, standard clauses do not trigger critical or predatory risk alarms."""
    safe_clauses = [
        "Welcome to our service. We hope you enjoy using our productivity app.",
        "Please select a secure password containing at least eight characters.",
        "You can contact customer support Monday through Friday during business hours."
    ]
    results = local_analyzer.analyze_clauses(safe_clauses, "Generic TOS")
    assert len(results) == 0

    score, level, summary = calculate_overall_risk_score(results)
    assert score == 0
    assert level == RiskLevel.LOW


def test_batch_analysis_api_endpoint():
    """Test the batch analysis endpoint with multiple agreement requests."""
    payload = {
        "documents": [
            {
                "document_type": "NDA",
                "clauses": [
                    "Confidentiality obligations survive in perpetuity forever and ever."
                ]
            },
            {
                "document_type": "Privacy Policy",
                "clauses": [
                    "We collect location, device, and keystroke data across other websites."
                ]
            }
        ]
    }
    response = client.post("/analyze/batch", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert len(data["results"]) == 2
    assert data["results"][0]["detected_risks_count"] >= 1
    assert data["results"][1]["detected_risks_count"] >= 1


def test_empty_and_whitespace_requests():
    """Test that empty or whitespace payloads return clean zero-risk responses gracefully."""
    response = client.post("/analyze", json={"clauses": []})
    assert response.status_code == 200
    data = response.json()
    assert data["risk_score"] == 0
    assert data["risk_level"] == "LOW"

    response2 = client.post("/analyze", json={"clauses": ["   ", "short"]})
    assert response2.status_code == 200
    data2 = response2.json()
    assert data2["risk_score"] == 0


def test_vector_engine_deviation_logic():
    """Test that the vector deviation calculation returns valid bounds and explanations."""
    clause = "We will monetize your personal data and commercialize user profiles."
    dev_score, baseline_std, explanation = vector_engine.calculate_clause_deviation(
        clause, "DATA_SALE", "Privacy Policy"
    )
    assert 0.0 <= dev_score <= 100.0
    assert isinstance(baseline_std, str)
    assert len(baseline_std) > 10
    assert "Privacy Policy" in explanation
    assert hasattr(vector_engine, "is_chromadb_active")


@pytest.mark.anyio
async def test_llm_analyzer_missing_key_graceful(monkeypatch):
    """Verify that missing API keys return None without error."""
    from app.analyzers.llm_analyzer import LLMRiskAnalyzer
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    analyzer = LLMRiskAnalyzer()
    assert analyzer.is_available() is False
    result = await analyzer.analyze_clauses(["Some clause text"])
    assert result is None


@pytest.mark.anyio
async def test_llm_analyzer_openai_mocked_success(monkeypatch):
    """Verify that OpenAI chat completions request is correctly constructed and parsed."""
    import httpx
    import json
    from app.analyzers.llm_analyzer import LLMRiskAnalyzer

    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-mock-test-key-for-unit-testing-only")

    mock_llm_output = [
        {
            "text": "We sell your personal data to advertisers.",
            "category": "DATA_SALE",
            "severity": "CRITICAL",
            "confidence": 0.95,
            "explanation": "This allows selling user data.",
            "why_it_matters": "Your privacy is exposed.",
            "evidence": "sell your personal data"
        }
    ]

    mock_response_data = {
        "id": "chatcmpl-mock123",
        "object": "chat.completion",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": json.dumps(mock_llm_output)
                },
                "finish_reason": "stop"
            }
        ]
    }

    recorded_requests = []

    async def mock_post(self, url, *args, **kwargs):
        recorded_requests.append({"url": str(url), "headers": kwargs.get("headers"), "json": kwargs.get("json")})
        return httpx.Response(
            status_code=200,
            json=mock_response_data,
            request=httpx.Request("POST", url)
        )

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    analyzer = LLMRiskAnalyzer()
    assert analyzer.is_available() is True

    clauses = ["We sell your personal data to advertisers."]
    results = await analyzer.analyze_clauses(clauses, "Privacy Policy")

    # Verify request construction
    assert len(recorded_requests) == 1
    req = recorded_requests[0]
    assert "api.openai.com/v1/chat/completions" in req["url"]
    assert req["headers"]["Authorization"] == "Bearer sk-mock-test-key-for-unit-testing-only"
    assert req["json"]["model"] == "gpt-4o-mini"
    assert req["json"]["temperature"] == 0.1

    # Verify response parsing
    assert results is not None
    assert len(results) == 1
    assert results[0].category == RiskCategory.DATA_SALE
    assert results[0].severity == SeverityLevel.CRITICAL
    assert results[0].confidence == 0.95


@pytest.mark.anyio
async def test_llm_analyzer_openai_markdown_code_fences(monkeypatch):
    """Verify that OpenAI outputs wrapped in ```json ... ``` code fences are parsed properly."""
    import httpx
    import json
    from app.analyzers.llm_analyzer import LLMRiskAnalyzer

    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-mock-test-key-for-unit-testing-only")

    raw_json = json.dumps([
        {
            "text": "Arbitration is mandatory.",
            "category": "MANDATORY_ARBITRATION",
            "severity": "HIGH",
            "confidence": 0.9,
            "explanation": "Mandatory arbitration.",
            "why_it_matters": "Waives court trial."
        }
    ])
    fenced_content = f"```json\n{raw_json}\n```"

    async def mock_post(self, url, *args, **kwargs):
        return httpx.Response(
            status_code=200,
            json={"choices": [{"message": {"content": fenced_content}}]},
            request=httpx.Request("POST", url)
        )

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    analyzer = LLMRiskAnalyzer()
    results = await analyzer.analyze_clauses(["Arbitration is mandatory."])
    assert results is not None
    assert len(results) == 1
    assert results[0].category == RiskCategory.MANDATORY_ARBITRATION


@pytest.mark.anyio
async def test_llm_analyzer_gemini_mocked_success(monkeypatch):
    """Verify that Gemini request and response format continues to function properly."""
    import httpx
    import json
    from app.analyzers.llm_analyzer import LLMRiskAnalyzer

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "mock-gemini-key-for-testing")

    mock_gemini_response = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": json.dumps([
                                {
                                    "text": "You assign all inventions to company.",
                                    "category": "IP_ASSIGNMENT",
                                    "severity": "CRITICAL",
                                    "confidence": 0.98,
                                    "explanation": "Assigns all IP.",
                                    "why_it_matters": "Loss of inventions."
                                }
                            ])
                        }
                    ]
                }
            }
        ]
    }

    recorded_urls = []

    async def mock_post(self, url, *args, **kwargs):
        recorded_urls.append(str(url))
        return httpx.Response(
            status_code=200,
            json=mock_gemini_response,
            request=httpx.Request("POST", url)
        )

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    analyzer = LLMRiskAnalyzer()
    assert analyzer.is_available() is True
    results = await analyzer.analyze_clauses(["You assign all inventions to company."])

    assert len(recorded_urls) == 1
    assert "generativelanguage.googleapis.com" in recorded_urls[0]
    assert results is not None
    assert len(results) == 1
    assert results[0].category == RiskCategory.IP_ASSIGNMENT


@pytest.mark.anyio
async def test_llm_analyzer_timeout_and_errors_graceful(monkeypatch):
    """Verify that timeouts and HTTP 500 errors gracefully return None without unhandled exceptions."""
    import httpx
    from app.analyzers.llm_analyzer import LLMRiskAnalyzer

    monkeypatch.setenv("OPENAI_API_KEY", "sk-mock-test-key")

    # Simulate network timeout
    async def mock_post_timeout(self, url, *args, **kwargs):
        raise httpx.ReadTimeout("Request timed out")

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post_timeout)

    analyzer = LLMRiskAnalyzer()
    result = await analyzer.analyze_clauses(["Some clause."])
    assert result is None

    # Simulate HTTP 500 server error
    async def mock_post_500(self, url, *args, **kwargs):
        return httpx.Response(500, request=httpx.Request("POST", url))

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post_500)
    result500 = await analyzer.analyze_clauses(["Some clause."])
    assert result500 is None
