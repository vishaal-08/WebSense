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
    """Vector similarity engine for baseline clause comparison with ChromaDB and built-in cosine fallback."""
    
    def __init__(self):
        self._chroma_client = None
        self._chroma_collection = None
        self._init_chromadb()

    def _init_chromadb(self):
        """Optionally initialize ChromaDB vector collection if installed."""
        try:
            import chromadb
            # Use in-memory or ephemeral ChromaDB client for instant startup
            self._chroma_client = chromadb.Client()
            self._chroma_collection = self._chroma_client.get_or_create_collection(
                name="websense_legal_baselines",
                metadata={"description": "Standard fair legal clauses across NDAs, SAFEs, and TOS"}
            )
            self._seed_chroma_baselines()
        except Exception:
            self._chroma_client = None
            self._chroma_collection = None

    def _seed_chroma_baselines(self):
        """Seed ChromaDB with standard baseline clauses."""
        if not self._chroma_collection:
            return
        from app.baselines.legal_baselines import LEGAL_BASELINES
        docs = []
        ids = []
        metadatas = []
        for doc_type, info in LEGAL_BASELINES.items():
            for cat, clause in info.get("standard_clauses", {}).items():
                docs.append(clause)
                ids.append(f"{doc_type}_{cat}")
                metadatas.append({"document_type": doc_type, "category": cat})
        if docs:
            self._chroma_collection.upsert(
                documents=docs,
                ids=ids,
                metadatas=metadatas
            )

    @property
    def is_chromadb_active(self) -> bool:
        return self._chroma_collection is not None

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

        similarity = 0.0
        used_vector_db = False

        # Try ChromaDB query if active
        if self._chroma_collection is not None:
            try:
                results = self._chroma_collection.query(
                    query_texts=[clause_text],
                    n_results=1,
                    where={"$and": [{"document_type": document_type}, {"category": category}]}
                )
                if results and results.get("distances") and results["distances"][0]:
                    distance = results["distances"][0][0]
                    similarity = max(0.0, min(1.0, 1.0 - (distance / 2.0)))
                    used_vector_db = True
            except Exception:
                used_vector_db = False

        # Built-in lightweight cosine similarity fallback
        if not used_vector_db:
            vec_clause = _tokenize_ngram(clause_text)
            vec_baseline = _tokenize_ngram(baseline_standard)
            similarity = calculate_cosine_similarity(vec_clause, vec_baseline)
        
        # Deviation is inverse of similarity, scaled 0-100
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
        
        engine_name = "ChromaDB vector embedding" if used_vector_db else "baseline vector similarity"
        explanation = (
            f"Compared against the standard {document_type} baseline for {category.replace('_', ' ')} via {engine_name}, "
            f"this clause exhibits a {deviation_score}% structural deviation from customary terms."
        )
        
        return deviation_score, baseline_standard, explanation


# Global singleton instance
vector_engine = LightweightVectorEngine()
