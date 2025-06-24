from core.grader import calculate_similarity_with_feedback, debug_grading, match_rule
from core.db import get_questions, get_student_answers
from bson.objectid import ObjectId

def grade_all(debug=False):
    questions = get_questions()
    answers = get_student_answers()
    results = []

    for q in questions:
        qid = str(q["_id"])
        sample = q["sample_answer"]
        rules = q["marking_scheme"]

        for student in filter(lambda a: a["question_id"] == qid, answers):
            if debug:
                debug_grading(student["student_ans"], sample, rules)
                
            feedback = calculate_similarity_with_feedback(
                student["student_ans"], sample, rules
            )
            results.append({
                "student_name": student["student_name"],
                "student_roll_no": student["student_roll_no"],
                "student_answer": student["student_ans"],
                "question_id": qid,
                "correct_%": f"{feedback['score'] * 100:.2f}%",
                "grade": feedback['grade'],
                "matched_rules": feedback["matched_rules"],
                "missed_rules": feedback["missed_rules"]
            })

    return results
