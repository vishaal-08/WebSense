from typing import Dict, Any

LEGAL_BASELINES: Dict[str, Dict[str, Any]] = {
    "Generic TOS": {
        "title": "Standard Fair Terms of Service Baseline",
        "description": "Standard balanced consumer/business service agreement with limited license grants and standard disclaimers.",
        "standard_clauses": {
            "BROAD_LICENSE": "User grants Service Provider a non-exclusive, revocable, royalty-free license solely to host and process content necessary to operate the service for User.",
            "IP_ASSIGNMENT": "User retains all right, title, and interest, including intellectual property rights, in and to all content and materials provided by User.",
            "DATA_SHARING": "Service Provider will not share or sell user personal data with third parties except as strictly necessary to fulfill the requested service or comply with applicable law.",
            "MANDATORY_ARBITRATION": "Disputes shall be resolved through good-faith negotiation, with optional binding arbitration or local small claims court jurisdiction.",
            "AUTO_RENEWAL": "Subscriptions renew automatically at standard non-promotional rates with prior written notice provided 30 days before renewal.",
            "INDEMNIFICATION": "User agrees to indemnify Service Provider against third-party claims arising directly from User's intentional illegal acts or material breach of terms.",
            "UNILATERAL_LIABILITY": "Liability is limited to direct proven damages and capped at amounts paid by User in the preceding 12 months."
        }
    },
    "SaaS Terms": {
        "title": "Standard SaaS Subscription Agreement Baseline",
        "description": "Enterprise-friendly SaaS terms emphasizing data confidentiality, uptime SLAs, and customer ownership of input/output content.",
        "standard_clauses": {
            "BROAD_LICENSE": "Customer grants SaaS Provider a limited, non-transferable license to access Customer Data solely to perform the SaaS services.",
            "DATA_SALE": "SaaS Provider explicitly covenants never to sell, monetize, or rent Customer Data to external third parties.",
            "CONTENT_OWNERSHIP": "Customer owns all data, inputs, uploads, outputs, and derivative work produced through Customer's use of the SaaS platform.",
            "AUTO_RENEWAL": "Annual subscriptions renew automatically unless either party gives written notice of non-renewal at least 30 days prior.",
            "AI_TRAINING": "Provider will not use Customer confidential data or uploads to train public foundation machine learning models without express consent."
        }
    },
    "Privacy Policy": {
        "title": "Standard Privacy Policy Baseline (GDPR/CCPA compliant)",
        "description": "Standard privacy baseline requiring clear consent, data minimization, right to delete, and restricted data transfers.",
        "standard_clauses": {
            "DATA_HARVESTING": "We collect only data necessary for account functionality, performance telemetry, and security validation.",
            "DATA_SALE": "We do not sell, trade, or rent personal identification information to data brokers or third parties.",
            "SURVEILLANCE": "Tracking technologies are limited to session cookies required for authentication and aggregated privacy-preserving analytics.",
            "THIRD_PARTY_SHARING": "Data is shared only with verified service subprocessors under strict data protection agreements."
        }
    },
    "NDA": {
        "title": "Mutual Non-Disclosure Agreement Baseline",
        "description": "Balanced NDA protecting confidential information with standard 2-3 year term limits and customary exclusions.",
        "standard_clauses": {
            "PERPETUAL_RIGHTS": "Confidentiality obligations persist for a period of three (3) years following disclosure, except for trade secrets.",
            "IP_ASSIGNMENT": "No license or ownership transfer of any IP or confidential information is granted or implied by disclosure under this Agreement.",
            "GOVERNING_LAW": "Disputes under this NDA shall be governed by the mutually agreed domestic jurisdiction without asymmetric fee shifting."
        }
    },
    "Freelancer Agreement": {
        "title": "Standard Independent Contractor Agreement Baseline",
        "description": "Fair contractor agreement with work-for-hire provisions triggered only upon full payment.",
        "standard_clauses": {
            "IP_ASSIGNMENT": "Contractor assigns deliverables to Client upon receipt of full payment for services rendered.",
            "RESTRICTIVE_TERMS": "Contractor remains free to perform services for other clients, provided no confidential information of Client is misused.",
            "TERMINATION_RIGHTS": "Either party may terminate this agreement upon 14 days written notice, with payment due for work completed."
        }
    },
    "Employment Agreement": {
        "title": "Fair Employment Agreement Baseline",
        "description": "Standard employment contract balancing employer IP rights with reasonable scope and geographic bounds.",
        "standard_clauses": {
            "IP_ASSIGNMENT": "Inventions created by Employee during work hours using Company equipment within Company business scope belong to Company.",
            "RESTRICTIVE_TERMS": "Non-compete provisions are strictly limited in time (max 1 year) and geographic region directly tied to Employee's role."
        }
    },
    "SAFE Agreement": {
        "title": "Simple Agreement for Future Equity (Y Combinator Standard Baseline)",
        "description": "Standard investment SAFE agreement without predatory liquidation preferences or side-letter traps.",
        "standard_clauses": {
            "UNILATERAL_LIABILITY": "Standard post-money SAFE provisions converting automatically upon qualified equity financing event without arbitrary penalty multipliers."
        }
    }
}


def get_baseline_for_document_type(doc_type: str) -> Dict[str, Any]:
    """Retrieve baseline definition for a given document type, falling back to Generic TOS."""
    return LEGAL_BASELINES.get(doc_type, LEGAL_BASELINES["Generic TOS"])
