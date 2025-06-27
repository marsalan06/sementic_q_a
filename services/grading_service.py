from core.grader import calculate_similarity_with_feedback, debug_grading, match_rule
from core.db import get_questions, get_student_answers, get_grade_thresholds
from bson.objectid import ObjectId

def grade_all(debug=False, user_id=None):
    questions = get_questions(user_id)
    answers = get_student_answers(user_id)
    grade_thresholds = get_grade_thresholds(user_id)
    results = []

    for q in questions:
        qid = str(q["_id"])
        sample = q["sample_answer"]
        rules = q["marking_scheme"]

        for student in filter(lambda a: a["question_id"] == qid, answers):
            if debug:
                debug_grading(student["student_ans"], sample, rules)
                
            feedback = calculate_similarity_with_feedback(
                student["student_ans"], sample, rules, grade_thresholds=grade_thresholds
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
