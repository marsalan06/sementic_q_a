from sentence_transformers import SentenceTransformer, util
import re
from nltk.stem import WordNetLemmatizer

model = SentenceTransformer('all-MiniLM-L6-v2')
lemmatizer = WordNetLemmatizer()

def assign_grade(score):
    percent = score * 100
    if percent >= 85:
        return "A"
    elif percent >= 70:
        return "B"
    elif percent >= 55:
        return "C"
    elif percent >= 40:
        return "D"
    else:
        return "F"

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

def match_rule(student_answer, rule_text, rule_type="semantic", threshold=0.2):
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
        
        # Check overlap between rule and student words
        overlap = len(student_important.intersection(rule_important))
        score = overlap / len(rule_important) if rule_important else 0
        
        # More flexible matching: require at least 50% of important words
        # OR if we have a high overlap score (>= 0.6)
        required_words = max(1, len(rule_important) * 0.5)  # At least 50% of words
        words_present = overlap >= required_words
        
        # Also consider it a match if we have high semantic similarity
        if not words_present and score >= 0.6:
            words_present = True
        
        # Additional flexibility: if we have at least 2 words matching, consider it a match
        if not words_present and overlap >= 2:
            words_present = True
        
        return words_present, score
    
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
            if any(word in rule_lower for word in ["formula", "equation", "mentions"]):
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

def calculate_similarity_with_feedback(student_answer, sample, rules, threshold=0.2):
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
            if any(word in rule_lower for word in ["formula", "equation", "mentions"]):
                rule_type = "exact_phrase"
            elif any(word in rule_lower for word in ["contains", "has", "includes"]):
                rule_type = "contains_keywords"
        
        is_matched, rule_score = match_rule(student_answer, rule_text, rule_type, threshold)
        rule_scores.append(rule_score)
        
        if is_matched:
            matched.append(rule_text)
        else:
            missed.append(rule_text)

    sample_weight = 0.6
    rule_weight = 0.4 / len(rules) if rules else 0
    final_score = sample_score * sample_weight + sum(r * rule_weight for r in rule_scores)

    return {
        "score": final_score,
        "grade": assign_grade(final_score),
        "matched_rules": matched,
        "missed_rules": missed
    }
