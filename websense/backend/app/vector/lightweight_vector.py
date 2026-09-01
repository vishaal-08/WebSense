import re
import math
from typing import Dict, List, Set, Tuple
from app.baselines.legal_baselines import get_baseline_for_document_type


def _tokenize_ngram(text: str, n: int = 3) -> Dict[str, int]:
    """Extract character n-grams and word tokens for lightweight TF representation."""
    clean_text = re.sub(r'[^a-z0-9\s]', '', text.lower())
    words = clean_text.split()
    counts: Dict[str, int] = {}
    
    # Word unigrams and bigrams
    for word in words:
        counts[word] = counts.get(word, 0) + 2
    for i in range(len(words) - 1):
        bigram = f"{words[i]}_{words[i+1]}"
        counts[bigram] = counts.get(bigram, 0) + 3
        
    # Character n-grams for typo/variation robustness
    for i in range(len(clean_text) - n + 1):
        ngram = clean_text[i:i+n]
        counts[ngram] = counts.get(ngram, 0) + 1
        
    return counts


def calculate_cosine_similarity(vec1: Dict[str, int], vec2: Dict[str, int]) -> float:
    """Calculate cosine similarity between two frequency vector dictionaries."""
    intersection = set(vec1.keys()) & set(vec2.keys())
    dot_product = sum(vec1[k] * vec2[k] for k in intersection)
    
    mag1 = math.sqrt(sum(val ** 2 for val in vec1.values()))
    mag2 = math.sqrt(sum(val ** 2 for val in vec2.values()))
    
    if mag1 == 0 or mag2 == 0:
        return 0.0
        
    return dot_product / (mag1 * mag2)


class LightweightVectorEngine:
    """Lightweight vector similarity engine for baseline clause comparison."""
    
    def calculate_clause_deviation(
        self, clause_text: str, category: str, document_type: str = "Generic TOS"
    ) -> Tuple[float, str, str]:
        """
        Compare clause_text against the category baseline standard for document_type.
        Returns: (deviation_score [0-100], baseline_standard_text, deviation_explanation)
        """
        baseline_info = get_baseline_for_document_type(document_type)
        standard_clauses = baseline_info.get("standard_clauses", {})
        
        baseline_standard = standard_clauses.get(
            category,
            "The service provider maintains standard fair practices without unmitigated unilateral burdens."
        )
        
        vec_clause = _tokenize_ngram(clause_text)
        vec_baseline = _tokenize_ngram(baseline_standard)
        
        similarity = calculate_cosine_similarity(vec_clause, vec_baseline)
        
        # Deviation is inverse of similarity, scaled 0-100
        # If clause contains extreme language (e.g. "perpetual", "irrevocable", "sole discretion", "no refund"), amplify deviation
        extreme_triggers = [
            "perpetual", "irrevocable", "unfettered", "sole discretion", "worldwide",
            "waive all", "sell your", "train model", "no liability", "indemnify and hold harmless"
        ]
        extreme_multiplier = 1.0
        for trigger in extreme_triggers:
            if trigger in clause_text.lower():
                extreme_multiplier += 0.08
                
        raw_deviation = (1.0 - (similarity * 0.7)) * 100 * extreme_multiplier
        deviation_score = max(0.0, min(100.0, round(raw_deviation, 1)))
        
        explanation = (
            f"Compared against the standard {document_type} baseline for {category.replace('_', ' ')}, "
            f"this clause exhibits a {deviation_score}% structural deviation from customary terms."
        )
        
        return deviation_score, baseline_standard, explanation


# Global singleton instance
vector_engine = LightweightVectorEngine()
