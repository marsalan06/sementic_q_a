from core.grader import calculate_similarity_with_feedback, debug_grading, match_rule, extract_important_content

# Test the improved chemistry example
print("=== TEST IMPROVED CHEMISTRY EXAMPLE ===")
chemistry_rules = [
    {"text": "Student mentions the center or core is a nucleus", "type": "contains_keywords"},
    {"text": "it has protons, neutrons and electrons", "type": "contains_keywords"},
    {"text": "atom has subatomic particles in its nucleus", "type": "contains_keywords"}
]

chemistry_answer = "An atom has a nucleus at its center. The nucleus contains protons and neutrons. Electrons orbit around the nucleus."

print("Rules:", chemistry_rules)
print("Answer:", chemistry_answer)

# Test individual rules with debug info
for i, rule in enumerate(chemistry_rules):
    print(f"\n--- Rule {i+1} Analysis ---")
    rule_important = extract_important_content(rule["text"])
    student_important = extract_important_content(chemistry_answer)
    overlap = student_important.intersection(rule_important)
    
    print(f"Rule: {rule['text']}")
    print(f"Important Rule Words: {rule_important}")
    print(f"Important Student Words: {student_important}")
    print(f"Overlap: {overlap}")
    print(f"Overlap Count: {len(overlap)}/{len(rule_important)} = {len(overlap)/len(rule_important):.2f}")
    
    is_matched, score = match_rule(chemistry_answer, rule["text"], rule["type"])
    print(f"Final Result: Score: {score:.4f}, Matched: {is_matched}")

print("\n" + "="*50)

# Test auto-detection with improved system
print("=== TEST AUTO-DETECTION WITH IMPROVED SYSTEM ===")
auto_rules = [
    "Student mentions the center or core is a nucleus",  # Should auto-detect as contains_keywords
    "it has protons, neutrons and electrons",           # Should auto-detect as contains_keywords
    "atom has subatomic particles in its nucleus"       # Should auto-detect as contains_keywords
]

result = calculate_similarity_with_feedback(chemistry_answer, "Sample chemistry answer", auto_rules)
print(f"Final Score: {result['score']:.4f}")
print(f"Grade: {result['grade']}")
print(f"Matched: {result['matched_rules']}")
print(f"Missed: {result['missed_rules']}") 