from sentence_transformers import SentenceTransformer, util
import re
import nltk
from nltk.stem import WordNetLemmatizer
from core.math_utils import is_math_expression, compare_math_expressions

# Download NLTK data if not available
try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet')

try:
    lemmatizer = WordNetLemmatizer()
except Exception as e:
    print(f"Warning: Could not initialize WordNet lemmatizer: {e}")
    # Fallback lemmatizer
    class FallbackLemmatizer:
        def lemmatize(self, word):
            return word.lower()
    lemmatizer = FallbackLemmatizer()

# Replace with SciBERT model optimized for math/scientific context
model = SentenceTransformer('allenai/scibert_scivocab_uncased')

def assign_grade(score, grade_thresholds=None):
    """
    Assign grade based on score and custom thresholds
    Args:
        score: float between 0 and 1
        grade_thresholds: dict with grade letters as keys and percentage thresholds as values
    """
    if grade_thresholds is None:
        # Default thresholds
        grade_thresholds = {
            "A": 85,
            "B": 70,
            "C": 55,
            "D": 40,
            "F": 0
        }
    
    percent = score * 100
    
    # Sort thresholds in descending order to check from highest to lowest
    sorted_thresholds = sorted(grade_thresholds.items(), key=lambda x: x[1], reverse=True)
    
    for grade, threshold in sorted_thresholds:
        if percent >= threshold:
            return grade
    
    # Fallback to lowest grade if no threshold is met
    return sorted_thresholds[-1][0] if sorted_thresholds else "F"

def normalize(text):
    """Basic lemmatization and lowercasing"""
    words = re.findall(r'\b\w+\b', text.lower())
    return set(lemmatizer.lemmatize(word) for word in words)

def extract_key_concepts(text):
    """Extract key concepts from text using simple NLP techniques"""
    # Remove common stop words and punctuation
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can'}
    
    # Clean and tokenize
    text = re.sub(r'[^\w\s]', ' ', text.lower())
    words = text.split()
    
    # Filter out stop words and short words
    key_words = [word for word in words if word not in stop_words and len(word) > 2]
    
    return key_words

def calculate_semantic_similarity(student_answer, rule_text, threshold=0.2):
    """Calculate semantic similarity between student answer and rule"""
    # Direct semantic similarity
    student_emb = model.encode(student_answer, convert_to_tensor=True)
    rule_emb = model.encode(rule_text, convert_to_tensor=True)
    direct_similarity = util.cos_sim(student_emb, rule_emb).item()
    
    # Key concept overlap
    student_concepts = set(extract_key_concepts(student_answer))
    rule_concepts = set(extract_key_concepts(rule_text))
    
    if rule_concepts:
        concept_overlap = len(student_concepts.intersection(rule_concepts)) / len(rule_concepts)
    else:
        concept_overlap = 0
    
    # Weighted combination
    final_similarity = direct_similarity * 0.7 + concept_overlap * 0.3
    
    return final_similarity >= threshold, final_similarity

def extract_important_content(text):
    """Extract important content words from text dynamically"""
    # Remove common function words that don't carry content meaning
    function_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 
        'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 
        'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those',
        'mentions', 'contains', 'has', 'includes', 'explains', 'describes', 'shows', 'demonstrates',
        'student', 'mentions', 'mention', 'contains', 'contain', 'includes', 'include', 'has', 'have',
        'shows', 'show', 'demonstrates', 'demonstrate', 'explains', 'explain', 'describes', 'describe'
    }
    
    normalized = normalize(text)
    important_words = normalized - function_words
    
    # Filter out very short words and common verbs
    important_words = {word for word in important_words if len(word) > 2}
    
    return important_words

def match_rule(student_answer, rule_text, rule_type="semantic", threshold=0.2, debug=False):
    """Match a rule based on its type with completely dynamic matching"""
    
    if rule_type == "exact_phrase":
        # For exact phrase matching, extract the key content from the rule
        rule_lower = rule_text.lower()
        student_lower = student_answer.lower()
        
        # Extract the main content phrase (after common instruction words)
        instruction_patterns = [
            r'mentions?\s+(?:the\s+)?(.+)',
            r'contains?\s+(?:the\s+)?(.+)',
            r'has\s+(?:the\s+)?(.+)',
            r'includes?\s+(?:the\s+)?(.+)',
            r'formula\s+(.+)',
            r'equation\s+(.+)'
        ]
        
        key_phrases = []
        for pattern in instruction_patterns:
            matches = re.findall(pattern, rule_lower)
            for match in matches:
                # Clean up the extracted phrase
                phrase = match.strip().rstrip('.')
                if len(phrase) > 2:  # Only meaningful phrases
                    key_phrases.append(phrase)
        
        # If no pattern matched, try to extract meaningful content
        if not key_phrases:
            # Extract words that seem like content (not instruction words)
            important_words = extract_important_content(rule_text)
            if important_words:
                key_phrases.extend(list(important_words))
        
        # Check if any key phrase is present
        for phrase in key_phrases:
            if phrase in student_lower:
                return True, 1.0
        
        return False, 0.0
    
    elif rule_type == "contains_keywords":
        # Extract important content words from both rule and answer
        rule_important = extract_important_content(rule_text)
        student_important = extract_important_content(student_answer)
        
        if not rule_important:
            # If no important words found, fall back to semantic matching
            return calculate_semantic_similarity(student_answer, rule_text, threshold)
        
        # First, try exact phrase matching for multi-word terms
        rule_lower = rule_text.lower()
        student_lower = student_answer.lower()
        
        # Extract key phrases from the rule (after instruction words)
        instruction_patterns = [
            r'contains?\s+(?:the\s+)?(.+)',
            r'has\s+(?:the\s+)?(.+)',
            r'includes?\s+(?:the\s+)?(.+)',
            r'keywords?\s+(?:are\s+)?(.+)',
            r'terms?\s+(?:are\s+)?(.+)'
        ]
        
        key_phrases = []
        for pattern in instruction_patterns:
            matches = re.findall(pattern, rule_lower)
            for match in matches:
                phrase = match.strip().rstrip('.')
                if len(phrase) > 2:
                    key_phrases.append(phrase)
        
        # If we found specific phrases, check for exact matches first
        if key_phrases:
            for phrase in key_phrases:
                if phrase in student_lower:
                    return True, 1.0
        
        # Debug: Print what we're looking for
        if debug:
            print(f"  Keyword rule '{rule_text}' extracted phrases: {key_phrases}")
            print(f"  Student answer: '{student_lower}'")
            print(f"  No exact phrase match found")
        
        # If no exact phrase match, fall back to word-level matching
        # But be more strict - require higher overlap
        overlap = len(student_important.intersection(rule_important))
        score = overlap / len(rule_important) if rule_important else 0
        
        # Debug: Print word-level matching info
        if debug:
            print(f"  Word-level matching - Rule words: {rule_important}")
            print(f"  Word-level matching - Student words: {student_important}")
            print(f"  Overlap: {student_important.intersection(rule_important)}")
            print(f"  Overlap score: {score:.2f}")
        
        # More strict matching: require at least 80% of important words
        # OR if we have a very high overlap score (>= 0.8)
        required_words = max(1, len(rule_important) * 0.8)  # At least 80% of words
        words_present = overlap >= required_words
        
        # Also consider it a match if we have very high semantic similarity
        if not words_present and score >= 0.8:
            words_present = True
        
        # Additional flexibility: if we have at least 3 words matching, consider it a match
        if not words_present and overlap >= 3:
            words_present = True
        
        return words_present, score
    
    elif rule_type == "math_equation":
        try:
            return compare_math_expressions(rule_text, student_answer)
        except Exception as e:
            # If math parsing fails, fall back to semantic matching
            print(f"Math parsing failed for '{rule_text}', falling back to semantic matching: {e}")
            return calculate_semantic_similarity(student_answer, rule_text, threshold)
    
    elif rule_type == "semantic":
        return calculate_semantic_similarity(student_answer, rule_text, threshold)
    
    else:
        # Default to semantic if unspecified
        return calculate_semantic_similarity(student_answer, rule_text, threshold)

def debug_grading(student_answer, sample, rules):
    """Debug function to analyze grading process"""
    print(f"\n=== DEBUG GRADING ===")
    print(f"Student Answer: {student_answer}")
    print(f"Sample Answer: {sample}")
    print(f"Rules: {rules}")
    
    student_emb = model.encode(student_answer, convert_to_tensor=True)
    sample_emb = model.encode(sample, convert_to_tensor=True)
    sample_score = util.cos_sim(student_emb, sample_emb).item()
    
    print(f"\nSample Answer Similarity: {sample_score:.4f}")
    
    for i, rule in enumerate(rules):
        # Determine rule type based on content
        rule_text = rule if isinstance(rule, str) else rule.get("text", rule)
        rule_type = rule.get("type", "semantic") if isinstance(rule, dict) else "semantic"
        
        # Auto-detect rule type if not specified
        if rule_type == "semantic":
            rule_lower = rule_text.lower()
            # Be more conservative about math detection - only if it's clearly a mathematical expression
            if is_math_expression(rule_text) and not any(word in rule_lower for word in ["formula for", "equation for", "could not parse"]):
                rule_type = "math_equation"
            elif any(word in rule_lower for word in ["formula", "equation", "mentions"]):
                rule_type = "exact_phrase"
            elif any(word in rule_lower for word in ["contains", "has", "includes"]):
                rule_type = "contains_keywords"
        
        is_matched, rule_score = match_rule(student_answer, rule_text, rule_type, 0.2)
        
        print(f"\nRule {i+1}: {rule_text}")
        print(f"  Type: {rule_type}")
        print(f"  Final Score: {rule_score:.4f}")
        print(f"  Matched: {is_matched}")
        
        # Show key concepts for semantic rules
        if rule_type == "semantic":
            student_concepts = set(extract_key_concepts(student_answer))
            rule_concepts = set(extract_key_concepts(rule_text))
            overlap = student_concepts.intersection(rule_concepts)
            
            print(f"  Key Concepts in Rule: {rule_concepts}")
            print(f"  Key Concepts in Answer: {student_concepts}")
            print(f"  Overlap: {overlap}")
        
        # Show important words for keyword rules
        elif rule_type == "contains_keywords":
            rule_important = extract_important_content(rule_text)
            student_important = extract_important_content(student_answer)
            
            print(f"  Important Rule Words: {rule_important}")
            print(f"  Important Student Words: {student_important}")
            print(f"  Overlap: {student_important.intersection(rule_important)}")

def calculate_similarity_with_feedback(student_answer, sample, rules, threshold=0.2, grade_thresholds=None, debug=False):
    student_emb = model.encode(student_answer, convert_to_tensor=True)
    sample_emb = model.encode(sample, convert_to_tensor=True)
    sample_score = util.cos_sim(student_emb, sample_emb).item()

    matched, missed, rule_scores = [], [], []

    for rule in rules:
        # Determine rule type based on content
        rule_text = rule if isinstance(rule, str) else rule.get("text", rule)
        rule_type = rule.get("type", "semantic") if isinstance(rule, dict) else "semantic"
        
        # Auto-detect rule type if not specified
        if rule_type == "semantic":
            rule_lower = rule_text.lower()
            # Be more conservative about math detection - only if it's clearly a mathematical expression
            if is_math_expression(rule_text) and not any(word in rule_lower for word in ["formula for", "equation for", "could not parse"]):
                rule_type = "math_equation"
            elif any(word in rule_lower for word in ["formula", "equation", "mentions"]):
                rule_type = "exact_phrase"
            elif any(word in rule_lower for word in ["contains", "has", "includes"]):
                rule_type = "contains_keywords"
        
        is_matched, rule_score = match_rule(student_answer, rule_text, rule_type, threshold, debug)
        rule_scores.append(rule_score)
        
        if is_matched:
            matched.append(rule_text)
        else:
            missed.append(rule_text)

    # Calculate rule-based score (primary scoring method)
    if rules:
        rule_score = len(matched) / len(rules)  # Percentage of rules matched
    else:
        rule_score = 0
    
    # Use sample similarity as a bonus/penalty (secondary scoring method)
    sample_bonus = max(0, (sample_score - 0.5) * 0.2)  # Small bonus for good sample similarity
    
    # Final score: primarily rule-based with small sample bonus
    final_score = rule_score + sample_bonus
    
    # Cap the score at 1.0
    final_score = min(1.0, final_score)

    return {
        "score": final_score,
        "grade": assign_grade(final_score, grade_thresholds),
        "matched_rules": matched,
        "missed_rules": missed
    }
