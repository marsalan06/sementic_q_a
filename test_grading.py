from core.grader import calculate_similarity_with_feedback, debug_grading

# Test with your specific example
question = "State and explain Newton's Second Law of Motion with an example."
sample_answer = "Newton's Second Law states that the force acting on an object is equal to the mass of the object multiplied by its acceleration (F = ma). It explains how an object will accelerate in the direction of the net force applied. For example, pushing a cart with more force causes it to accelerate faster."
rules = [
    "Mentions the formula F = ma.",
    "Explains the relationship between force, mass, and acceleration.",
    "Gives a real-world example of force causing acceleration."
]

student_answer = "Newton's Second Law states that the force acting on an object is the product of its mass and acceleration (F = ma). This means that if you push an object, it will accelerate in the direction of the force. For example, a heavier object needs more force to accelerate."

print("=== TESTING IMPROVED GRADING SYSTEM ===")
print(f"Question: {question}")
print(f"Student Answer: {student_answer}")
print(f"Rules: {rules}")

# Run debug analysis
debug_grading(student_answer, sample_answer, rules)

# Run actual grading
result = calculate_similarity_with_feedback(student_answer, sample_answer, rules)

print(f"\n=== FINAL RESULTS ===")
print(f"Score: {result['score']:.4f}")
print(f"Grade: {result['grade']}")
print(f"Matched Rules: {result['matched_rules']}")
print(f"Missed Rules: {result['missed_rules']}") 