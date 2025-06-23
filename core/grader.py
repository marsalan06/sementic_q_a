from sentence_transformers import SentenceTransformer, util
import re

model = SentenceTransformer('all-MiniLM-L6-v2')

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

def calculate_rule_similarity(student_answer, rule, threshold=0.2):
    """Calculate similarity between student answer and a specific rule using fast approaches"""
    
    # Approach 1: Direct semantic similarity (single embedding - most important)
    student_emb = model.encode(student_answer, convert_to_tensor=True)
    rule_emb = model.encode(rule, convert_to_tensor=True)
    direct_similarity = util.cos_sim(student_emb, rule_emb).item()
    
    # Approach 2: Key concept overlap (no embeddings needed - very fast)
    student_concepts = set(extract_key_concepts(student_answer))
    rule_concepts = set(extract_key_concepts(rule))
    
    if rule_concepts:
        concept_overlap = len(student_concepts.intersection(rule_concepts)) / len(rule_concepts)
    else:
        concept_overlap = 0
    
    # Simple weighted combination
    final_similarity = direct_similarity * 0.7 + concept_overlap * 0.3
    
    return final_similarity >= threshold, final_similarity

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
        is_matched, rule_score = calculate_rule_similarity(student_answer, rule, 0.2)
        
        print(f"\nRule {i+1}: {rule}")
        print(f"  Final Score: {rule_score:.4f}")
        print(f"  Matched: {is_matched}")
        
        # Show key concepts
        student_concepts = set(extract_key_concepts(student_answer))
        rule_concepts = set(extract_key_concepts(rule))
        overlap = student_concepts.intersection(rule_concepts)
        
        print(f"  Key Concepts in Rule: {rule_concepts}")
        print(f"  Key Concepts in Answer: {student_concepts}")
        print(f"  Overlap: {overlap}")

def calculate_similarity_with_feedback(student_answer, sample, rules, threshold=0.2):
    student_emb = model.encode(student_answer, convert_to_tensor=True)
    sample_emb = model.encode(sample, convert_to_tensor=True)
    sample_score = util.cos_sim(student_emb, sample_emb).item()

    matched, missed, rule_scores = [], [], []

    for rule in rules:
        is_matched, rule_score = calculate_rule_similarity(student_answer, rule, threshold)
        rule_scores.append(rule_score)
        
        if is_matched:
            matched.append(rule)
        else:
            missed.append(rule)

    sample_weight = 0.5
    rule_weight = 0.5 / len(rules) if rules else 0
    final_score = sample_score * sample_weight + sum(r * rule_weight for r in rule_scores)

    return {
        "score": final_score,
        "grade": assign_grade(final_score),
        "matched_rules": matched,
        "missed_rules": missed
    }
