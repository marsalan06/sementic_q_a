from core.grader import calculate_similarity_with_feedback, debug_grading, match_rule

# Test 1: Physics example (original)
print("=== TEST 1: PHYSICS EXAMPLE ===")
physics_rules = [
    {"text": "Mentions the formula F = ma.", "type": "exact_phrase"},
    {"text": "Explains the relationship between force, mass, and acceleration.", "type": "semantic"},
    {"text": "Gives a real-world example of force causing acceleration.", "type": "semantic"}
]

physics_answer = "Newton's Second Law states that the force acting on an object is the product of its mass and acceleration (F = ma). This means that if you push an object, it will accelerate in the direction of the force. For example, a heavier object needs more force to accelerate."

print("Rules:", physics_rules)
print("Answer:", physics_answer)

for i, rule in enumerate(physics_rules):
    is_matched, score = match_rule(physics_answer, rule["text"], rule["type"])
    print(f"Rule {i+1}: {rule['text']} ({rule['type']}) - Score: {score:.4f}, Matched: {is_matched}")

print("\n" + "="*50)

# Test 2: Chemistry example (new keyword matching)
print("=== TEST 2: CHEMISTRY EXAMPLE ===")
chemistry_rules = [
    {"text": "Student mentions the center or core is a nucleus", "type": "contains_keywords"},
    {"text": "it has protons, neutrons and electrons", "type": "contains_keywords"},
    {"text": "atom has subatomic particles in its nucleus", "type": "semantic"}
]

chemistry_answer = "An atom has a nucleus at its center. The nucleus contains protons and neutrons. Electrons orbit around the nucleus."

print("Rules:", chemistry_rules)
print("Answer:", chemistry_answer)

for i, rule in enumerate(chemistry_rules):
    is_matched, score = match_rule(chemistry_answer, rule["text"], rule["type"])
    print(f"Rule {i+1}: {rule['text']} ({rule['type']}) - Score: {score:.4f}, Matched: {is_matched}")

print("\n" + "="*50)

# Test 3: Biology example (lemmatization test)
print("=== TEST 3: BIOLOGY EXAMPLE (LEMMATIZATION) ===")
biology_rules = [
    {"text": "contains mitochondria", "type": "contains_keywords"},
    {"text": "has ribosomes", "type": "contains_keywords"},
    {"text": "explains cellular respiration", "type": "semantic"}
]

biology_answer = "The cell contains many mitochondria. It also has numerous ribosomes. The mitochondria produce energy through cellular respiration."

print("Rules:", biology_rules)
print("Answer:", biology_answer)

for i, rule in enumerate(biology_rules):
    is_matched, score = match_rule(biology_answer, rule["text"], rule["type"])
    print(f"Rule {i+1}: {rule['text']} ({rule['type']}) - Score: {score:.4f}, Matched: {is_matched}")

print("\n" + "="*50)

# Test 4: Auto-detection test
print("=== TEST 4: AUTO-DETECTION TEST ===")
auto_rules = [
    "Mentions the formula E = mc²",  # Should auto-detect as exact_phrase
    "contains DNA and RNA",          # Should auto-detect as contains_keywords
    "explains the process of photosynthesis"  # Should auto-detect as semantic
]

auto_answer = "Einstein's famous formula is E = mc². The cell contains DNA and RNA molecules. Photosynthesis is the process where plants make food."

print("Rules:", auto_rules)
print("Answer:", auto_answer)

# Test auto-detection
from core.grader import calculate_similarity_with_feedback
result = calculate_similarity_with_feedback(auto_answer, "Sample answer", auto_rules)
print(f"Final Score: {result['score']:.4f}")
print(f"Grade: {result['grade']}")
print(f"Matched: {result['matched_rules']}")
print(f"Missed: {result['missed_rules']}")

print("\n" + "="*50)

# Test 5: Debug analysis
print("=== TEST 5: DEBUG ANALYSIS ===")
debug_grading(chemistry_answer, "Sample chemistry answer", chemistry_rules) 