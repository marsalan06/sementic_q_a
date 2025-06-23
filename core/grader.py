from sentence_transformers import SentenceTransformer, util

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

def calculate_similarity_with_feedback(student_answer, sample, rules, threshold=0.6):
    student_emb = model.encode(student_answer, convert_to_tensor=True)
    sample_emb = model.encode(sample, convert_to_tensor=True)
    sample_score = util.cos_sim(student_emb, sample_emb).item()

    matched, missed, rule_scores = [], [], []

    for rule in rules:
        rule_emb = model.encode(rule, convert_to_tensor=True)
        rule_score = util.cos_sim(student_emb, rule_emb).item()
        rule_scores.append(rule_score)
        if rule_score >= threshold:
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
