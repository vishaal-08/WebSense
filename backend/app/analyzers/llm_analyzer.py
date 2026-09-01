import os
import json
import logging
from typing import List, Optional
import httpx
from app.models.schemas import ClauseRisk, RiskCategory, SeverityLevel
from app.vector.lightweight_vector import vector_engine

logger = logging.getLogger(__name__)


class LLMRiskAnalyzer:
    """Optional LLM semantic analyzer for deep clause interpretation when API key is available."""
    
    @property
    def api_key(self) -> Optional[str]:
        return os.environ.get("GEMINI_API_KEY") or os.environ.get("OPENAI_API_KEY")
        
    def is_available(self) -> bool:
        key = self.api_key
        return bool(key and len(key.strip()) > 5)
        
    async def analyze_clauses(
        self, clauses: List[str], document_type: str = "Generic TOS"
    ) -> Optional[List[ClauseRisk]]:
        """Call LLM API for structured risk JSON if configured, returning None on failure/missing key."""
        if not self.is_available():
            return None
            
        # We enforce structured prompt returning valid JSON
        prompt = f"""You are WebSense Legal AI. Analyze the following legal clauses from a {document_type}.
Return ONLY a valid JSON list of objects for any clauses that contain material risk.

JSON Format required:
[
  {{
    "text": "original text snippet",
    "category": "IP_ASSIGNMENT|BROAD_LICENSE|DATA_SALE|DATA_HARVESTING|PERPETUAL_RIGHTS|MANDATORY_ARBITRATION|CLASS_ACTION_WAIVER|AUTO_RENEWAL|INDEMNIFICATION|UNILATERAL_LIABILITY|AI_TRAINING|SURVEILLANCE|TERMINATION_RIGHTS|RESTRICTIVE_TERMS",
    "severity": "LOW|MEDIUM|HIGH|CRITICAL",
    "confidence": 0.95,
    "explanation": "Plain english explanation of the risk",
    "why_it_matters": "Why this matters to the user",
    "evidence": "matched key term"
  }}
]

Clauses to analyze:
{json.dumps(clauses[:15], indent=2)}
"""

        try:
            async with httpx.AsyncClient(timeout=6.0) as client:
                if os.environ.get("GEMINI_API_KEY"):
                    # Gemini REST API Endpoint
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.api_key}"
                    payload = {
                        "contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": {"response_mime_type": "application/json", "temperature": 0.1}
                    }
                    resp = await client.post(url, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        text_content = data['candidates'][0]['content']['parts'][0]['text']
                        parsed = json.loads(text_content)
                        if isinstance(parsed, dict):
                            parsed = parsed.get("clauses", parsed.get("risks", []))
                        return self._parse_llm_results(parsed, document_type)
                elif os.environ.get("OPENAI_API_KEY"):
                    # OpenAI REST API Endpoint
                    url = "https://api.openai.com/v1/chat/completions"
                    headers = {
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    }
                    payload = {
                        "model": "gpt-4o-mini",
                        "messages": [
                            {"role": "system", "content": "You are WebSense Legal AI. Return only valid JSON."},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.1
                    }
                    resp = await client.post(url, headers=headers, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        raw_text = data['choices'][0]['message']['content'].strip()
                        # Extract JSON if wrapped in markdown code fences
                        if "```" in raw_text:
                            parts = raw_text.split("```")
                            raw_text = parts[1] if len(parts) > 1 else raw_text
                            if raw_text.startswith("json"):
                                raw_text = raw_text[4:].strip()
                        parsed = json.loads(raw_text.strip())
                        if isinstance(parsed, dict):
                            parsed = parsed.get("clauses", parsed.get("risks", []))
                        return self._parse_llm_results(parsed, document_type)
        except Exception as e:
            logger.warning(f"LLM semantic analysis failed: {e}. Falling back to local classifier.")
            
        return None
        
    def _parse_llm_results(self, raw_list: List[dict], document_type: str) -> List[ClauseRisk]:
        if not isinstance(raw_list, list):
            return []
        results = []
        for item in raw_list:
            try:
                category = RiskCategory(item.get("category", "OTHER_MATERIAL_RISK"))
                severity = SeverityLevel(item.get("severity", "MEDIUM"))
                text = item.get("text", "")
                
                dev_score, _, _ = vector_engine.calculate_clause_deviation(
                    text, category.value, document_type
                )
                
                results.append(
                    ClauseRisk(
                        id=f"llm-clause-{len(results)+1}",
                        category=category,
                        severity=severity,
                        confidence=float(item.get("confidence", 0.9)),
                        score=int(item.get("score", 30)),
                        text=text,
                        explanation=item.get("explanation", "Detected risk clause."),
                        why_it_matters=item.get("why_it_matters", "Contains risk."),
                        matched_evidence=item.get("evidence"),
                        deviation_score=dev_score
                    )
                )
            except Exception:
                continue
        return results


# Global singleton instance
llm_analyzer = LLMRiskAnalyzer()
