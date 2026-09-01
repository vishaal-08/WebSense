import re
import uuid
from typing import List, Dict, Any, Optional
from app.models.schemas import ClauseRisk, RiskCategory, SeverityLevel
from app.scoring.risk_engine import calculate_individual_clause_score
from app.vector.lightweight_vector import vector_engine

CATEGORY_DEFINITIONS: Dict[RiskCategory, Dict[str, Any]] = {
    RiskCategory.IP_ASSIGNMENT: {
        "patterns": [
            r"assign(?:s|ed|ing)?\s+(?:all\s+)?(?:right[s]?|title|interest|ownership|intellectual\s+property|inventions|works)",
            r"sole\s+and\s+exclusive\s+property\s+of\s+(?:the\s+)?company",
            r"transfer\s+all\s+(?:ip|copyright|patent)\s+rights",
            r"work(?:s)?\s+made\s+for\s+hire",
            r"unconditionally\s+assign",
            r"irrevocably\s+assign"
        ],
        "severity": SeverityLevel.CRITICAL,
        "explanation": "This clause transfers or assigns your intellectual property, inventions, or created work to the company.",
        "why_it_matters": "You may permanently lose ownership over content, designs, code, or ideas created while using or working under this service/contract."
    },
    RiskCategory.PERPETUAL_RIGHTS: {
        "patterns": [
            r"perpetual(?:ly)?",
            r"irrevocable",
            r"worldwide\s+and\s+perpetual",
            r"survive\s+(?:indefinitely|in\s+perpetuity|termination\s+forever)",
            r"royalty-free,\s+perpetual",
            r"forever\s+and\s+ever"
        ],
        "severity": SeverityLevel.HIGH,
        "explanation": "This clause grants rights that continue indefinitely and can never be revoked, even if you delete your account or cancel the contract.",
        "why_it_matters": "Once granted, you can never take back these rights or force the company to stop using your content."
    },
    RiskCategory.BROAD_LICENSE: {
        "patterns": [
            r"transferable,\s+sub-?licensable,\s+royalty-free,\s+worldwide",
            r"use,\s+reproduce,\s+modify,\s+adapt,\s+publish,\s+translate,\s+create\s+derivative\s+works",
            r"unrestricted\s+right\s+to\s+use",
            r"for\s+any\s+purpose\s+(?:whatsoever|without\s+compensation)",
            r"worldwide,\s+non-exclusive,\s+royalty-free"
        ],
        "severity": SeverityLevel.HIGH,
        "explanation": "This clause grants the company broad, expansive rights to use, modify, distribute, and commercialize your uploaded content.",
        "why_it_matters": "The provider can reuse or relicense your uploads far beyond what is necessary to simply render the product service."
    },
    RiskCategory.DATA_SALE: {
        "patterns": [
            r"sell,\s+rent,\s+or\s+monetize\s+(?:your\s+)?(?:personal\s+)?data",
            r"sell\s+your\s+information",
            r"commercialize\s+user\s+data",
            r"share\s+(?:or\s+sell\s+)?data\s+with\s+data\s+brokers",
            r"monetize\s+user\s+(?:profiles|behavior|activity)"
        ],
        "severity": SeverityLevel.CRITICAL,
        "explanation": "This clause permits the company or its partners to sell or commercialize your personal data.",
        "why_it_matters": "Your private information and browsing behavior could be sold to data brokers, advertisers, or third-party entities."
    },
    RiskCategory.AI_TRAINING: {
        "patterns": [
            r"train\s+(?:our\s+)?(?:ai|artificial\s+intelligence|machine\s+learning|llm|models)",
            r"use\s+(?:your\s+)?(?:content|data|uploads|inputs)\s+to\s+improve\s+(?:our\s+)?algorithms",
            r"machine\s+learning\s+training",
            r"model\s+development\s+and\s+training",
            r"generative\s+ai\s+training"
        ],
        "severity": SeverityLevel.HIGH,
        "explanation": "This clause allows the provider to use your proprietary content, code, or personal data to train machine learning and AI models.",
        "why_it_matters": "Your private data, intellectual property, or confidential inputs could become embedded inside AI models."
    },
    RiskCategory.MANDATORY_ARBITRATION: {
        "patterns": [
            r"binding\s+arbitration",
            r"arbitrate\s+all\s+disputes",
            r"american\s+arbitration\s+association",
            r"jams\s+arbitration",
            r"waive\s+(?:your\s+)?right\s+to\s+go\s+to\s+court",
            r"waive\s+(?:a\s+)?jury\s+trial"
        ],
        "severity": SeverityLevel.HIGH,
        "explanation": "This clause forces you to resolve legal disputes through private arbitration rather than public court or jury trial.",
        "why_it_matters": "Arbitration proceedings often favor large corporations, are private, and restrict rights to appeal."
    },
    RiskCategory.CLASS_ACTION_WAIVER: {
        "patterns": [
            r"class\s+action\s+waiver",
            r"waive\s+(?:any\s+)?right\s+to\s+participate\s+in\s+a\s+class\s+action",
            r"individual\s+capacity\s+only",
            r"not\s+as\s+a\s+plaintiff\s+or\s+class\s+member",
            r"representative\s+proceeding"
        ],
        "severity": SeverityLevel.HIGH,
        "explanation": "This clause strips away your right to join class action lawsuits against the company.",
        "why_it_matters": "If the company commits widespread small-scale fraud or data breaches, users cannot band together to seek justice."
    },
    RiskCategory.AUTO_RENEWAL: {
        "patterns": [
            r"automatic(?:ally)?\s+renew",
            r"recurring\s+subscription",
            r"until\s+cancelled",
            r"auto-?renewal",
            r"charged\s+automatically",
            r"without\s+further\s+notice"
        ],
        "severity": SeverityLevel.MEDIUM,
        "explanation": "This clause automatically renews your paid subscription and charges your payment method unless proactively cancelled.",
        "why_it_matters": "You may be charged repeatedly if you forget to cancel before the billing cycle date."
    },
    RiskCategory.DIFFICULT_CANCELLATION: {
        "patterns": [
            r"cancel\s+at\s+least\s+(?:30|60|90)\s+days\s+prior",
            r"cancellation\s+fee",
            r"written\s+notice\s+by\s+certified\s+mail",
            r"non-refundable",
            r"no\s+refunds?\s+(?:under\s+any\s+circumstance|will\s+be\s+issued)"
        ],
        "severity": SeverityLevel.MEDIUM,
        "explanation": "This clause sets strict or burdensome requirements for cancelling your subscription or getting refunds.",
        "why_it_matters": "Cancelling may require advance notice periods or forfeiture of pre-paid fees."
    },
    RiskCategory.INDEMNIFICATION: {
        "patterns": [
            r"indemnify,\s+defend,\s+and\s+hold\s+harmless",
            r"user\s+shall\s+be\s+solely\s+responsible\s+for\s+all\s+claims",
            r"hold\s+company\s+harmless\s+from\s+any\s+(?:loss|liability|damage|attorney)"
        ],
        "severity": SeverityLevel.HIGH,
        "explanation": "This clause requires you to pay the company's legal fees and damages if a third party sues them because of your actions.",
        "why_it_matters": "You could face sudden, massive financial liabilities for third-party legal claims."
    },
    RiskCategory.UNILATERAL_LIABILITY: {
        "patterns": [
            r"disclaim\s+all\s+(?:liability|warranties)",
            r"maximum\s+aggregate\s+liability\s+shall\s+not\s+exceed\s+\$(?:0|50|100)",
            r"sole\s+discretion\s+to\s+modify",
            r"modify\s+these\s+terms\s+at\s+any\s+time\s+without\s+notice"
        ],
        "severity": SeverityLevel.HIGH,
        "explanation": "This clause limits the company's legal liability to zero or minimal amounts while reserving rights to change terms unilaterally.",
        "why_it_matters": "If the company causes financial damage or leaks data, you cannot recover significant compensation."
    },
    RiskCategory.DATA_HARVESTING: {
        "patterns": [
            r"collect(?:s|ing)?\s+(?:location|device|biometric|contacts|browsing|keystroke)",
            r"track\s+(?:your\s+)?activity\s+across\s+(?:third-party|other)\s+websites",
            r"harvest\s+personal\s+data",
            r"cross-site\s+tracking"
        ],
        "severity": SeverityLevel.MEDIUM,
        "explanation": "This clause outlines expansive automated data collection across your devices, activity, or outside websites.",
        "why_it_matters": "More telemetry and background data is collected than is required for basic app operation."
    },
    RiskCategory.DATA_SHARING: {
        "patterns": [
            r"share\s+(?:your\s+)?information\s+with\s+(?:affiliates|marketing\s+partners|third\s+parties)",
            r"disclose\s+personal\s+data\s+to\s+advertisers",
            r"third-party\s+service\s+providers\s+for\s+commercial\s+purposes"
        ],
        "severity": SeverityLevel.MEDIUM,
        "explanation": "This clause allows your data to be shared with marketing partners, advertisers, or third-party networks.",
        "why_it_matters": "Your contact info and behavior could be shared widely across external marketing ecosystems."
    },
    RiskCategory.THIRD_PARTY_SHARING: {
        "patterns": [
            r"unspecified\s+third\s+parties",
            r"business\s+partners\s+and\s+sponsors",
            r"third\s+party\s+ad\s+networks"
        ],
        "severity": SeverityLevel.MEDIUM,
        "explanation": "Allows broad data distribution to external third-party advertisers or commercial partners.",
        "why_it_matters": "Data privacy protections become fragmented once shared outside the primary provider."
    },
    RiskCategory.SURVEILLANCE: {
        "patterns": [
            r"monitor\s+(?:your\s+)?(?:screen|keystrokes|communications|files|clipboard)",
            r"record\s+session\s+activity",
            r"continuous\s+background\s+tracking"
        ],
        "severity": SeverityLevel.HIGH,
        "explanation": "Permits active monitoring or recording of your screen, session inputs, clipboard, or local device activity.",
        "why_it_matters": "Intrusive surveillance risks exposing confidential work or sensitive private input."
    },
    RiskCategory.TERMINATION_RIGHTS: {
        "patterns": [
            r"terminate\s+(?:your\s+)?account\s+at\s+any\s+time\s+for\s+any\s+reason\s+without\s+notice",
            r"suspend\s+access\s+in\s+our\s+sole\s+discretion\s+without\s+liability",
            r"immediate\s+termination\s+without\s+cause"
        ],
        "severity": SeverityLevel.MEDIUM,
        "explanation": "Grants the provider unilateral authority to delete your account or cut off service instantly without cause.",
        "why_it_matters": "You could lose access to critical files, data, or services abruptly with no recourse or backup time."
    },
    RiskCategory.RESTRICTIVE_TERMS: {
        "patterns": [
            r"non-?compete",
            r"shall\s+not\s+engage\s+in\s+any\s+competing\s+business",
            r"non-?solicitation\s+of\s+clients",
            r"restrain\s+(?:trade|employment)"
        ],
        "severity": SeverityLevel.HIGH,
        "explanation": "Includes restrictive covenants like non-compete clauses or client solicitation bans.",
        "why_it_matters": "Can restrict your future employment or business activities long after the relationship ends."
    },
    RiskCategory.CONTENT_OWNERSHIP: {
        "patterns": [
            r"company\s+retains\s+ownership\s+of\s+all\s+user-generated\s+content",
            r"you\s+waive\s+all\s+moral\s+rights",
            r"all\s+uploads\s+become\s+company\s+property"
        ],
        "severity": SeverityLevel.HIGH,
        "explanation": "Declares that uploaded content or user-generated material becomes the company's property.",
        "why_it_matters": "You lose explicit copyright and legal ownership of your original uploaded media or work."
    },
    RiskCategory.GOVERNING_LAW: {
        "patterns": [
            r"governed\s+by\s+the\s+laws\s+of\s+delaware",
            r"exclusive\s+jurisdiction\s+in\s+foreign\s+court",
            r"pay\s+all\s+attorney(?:'s)?\s+fees\s+if\s+company\s+prevails"
        ],
        "severity": SeverityLevel.LOW,
        "explanation": "Specifies legal jurisdiction or fee-shifting clauses for dispute litigation.",
        "why_it_matters": "Disputes must be litigated in potentially distant, unfamiliar legal jurisdictions."
    },
    RiskCategory.OTHER_MATERIAL_RISK: {
        "patterns": [
            r"unilateral\s+right\s+to\s+seize",
            r"forfeit\s+all\s+credits",
            r"penalty\s+fee"
        ],
        "severity": SeverityLevel.MEDIUM,
        "explanation": "Material clause imposing unusual terms or financial penalties.",
        "why_it_matters": "Contains specific non-standard legal exposure."
    }
}


class LocalRiskAnalyzer:
    """Deterministic, offline-capable legal risk analyzer."""
    
    def analyze_clauses(
        self, clauses: List[str], document_type: str = "Generic TOS"
    ) -> List[ClauseRisk]:
        """Analyze extracted clauses using deterministic legal pattern matching."""
        detected_risks: List[ClauseRisk] = []
        seen_texts = set()
        
        for raw_clause in clauses:
            clause_text = raw_clause.strip()
            if not clause_text or len(clause_text) < 15 or clause_text in seen_texts:
                continue
                
            seen_texts.add(clause_text)
            
            # Check against all risk category patterns
            for category, info in CATEGORY_DEFINITIONS.items():
                patterns = info["patterns"]
                for pattern in patterns:
                    match = re.search(pattern, clause_text, re.IGNORECASE)
                    if match:
                        matched_text = match.group(0)
                        severity = info["severity"]
                        
                        # Confidence score based on length and exact match clarity
                        confidence = 0.88 if len(matched_text) > 10 else 0.78
                        if "sole discretion" in clause_text.lower() or "perpetual" in clause_text.lower():
                            confidence = min(0.98, confidence + 0.1)
                            
                        # Compute deviation score against vector baseline
                        dev_score, _, dev_explanation = vector_engine.calculate_clause_deviation(
                            clause_text, category.value, document_type
                        )
                        
                        has_mitigating = any(
                            m in clause_text.lower()
                            for m in ["subject to applicable law", "with prior notice", "except as required"]
                        )
                        
                        clause_score = calculate_individual_clause_score(
                            severity, confidence, dev_score, has_mitigating
                        )
                        
                        clause_obj = ClauseRisk(
                            id=f"clause-{uuid.uuid4().hex[:8]}",
                            category=category,
                            severity=severity,
                            confidence=round(confidence, 2),
                            score=clause_score,
                            text=clause_text,
                            explanation=info["explanation"],
                            why_it_matters=info["why_it_matters"],
                            matched_evidence=f"Matched trigger: '{matched_text}'",
                            deviation_score=dev_score,
                            mitigating_factors=["Contains qualification clause"] if has_mitigating else None
                        )
                        
                        detected_risks.append(clause_obj)
                        break  # Match highest priority pattern for this category on this sentence
                        
        return detected_risks


# Global singleton instance
local_analyzer = LocalRiskAnalyzer()
