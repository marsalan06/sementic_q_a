from core.grader import calculate_similarity_with_feedback, debug_grading, match_rule
from core.db import get_questions, get_student_answers, get_grade_thresholds
from bson.objectid import ObjectId

def grade_all(debug=False, user_id=None):
    """Grade all student answers for a user with proper error handling"""
    try:
        if not user_id:
            return []
        
        questions = get_questions(user_id)
        answers = get_student_answers(user_id)
        grade_thresholds = get_grade_thresholds(user_id)
        
        if not questions:
            print("No questions found for user")
            return []
        
        if not answers:
            print("No student answers found for user")
            return []
        
        results = []

        for q in questions:
            try:
                qid = str(q["_id"])
                sample = q.get("sample_answer", "")
                rules = q.get("marking_scheme", [])
                
                if not sample:
                    print(f"Warning: No sample answer for question {qid}")
                    continue

                # Filter answers for this question
                question_answers = [a for a in answers if str(a.get("question_id")) == qid]
                
                if debug:
                    print(f"Question {qid}: Found {len(question_answers)} answers")
                    for a in question_answers:
                        print(f"  - {a.get('student_name', 'Unknown')}: {a.get('student_ans', a.get('student_answer', 'No answer'))[:50]}...")
                
                for student in question_answers:
                    try:
                        # Handle both field name variations in the database
                        student_answer = student.get("student_ans", student.get("student_answer", ""))
                        if not student_answer:
                            print(f"Warning: Empty student answer for {student.get('student_name', 'Unknown')}")
                            continue
                        
                        if debug:
                            debug_grading(student_answer, sample, rules)
                            
                        feedback = calculate_similarity_with_feedback(
                            student_answer, sample, rules, grade_thresholds=grade_thresholds, debug=debug
                        )
                        
                        results.append({
                            "student_name": student.get("student_name", "Unknown"),
                            "student_roll_no": student.get("student_roll_no", "Unknown"),
                            "student_answer": student_answer,
                            "question_id": qid,
                            "correct_%": f"{feedback['score'] * 100:.2f}%",
                            "grade": feedback['grade'],
                            "matched_rules": feedback["matched_rules"],
                            "missed_rules": feedback["missed_rules"]
                        })
                    except Exception as e:
                        print(f"Error grading student {student.get('student_name', 'Unknown')}: {e}")
                        continue
                        
            except Exception as e:
                print(f"Error processing question {q.get('_id', 'Unknown')}: {e}")
                continue

        return results
        
    except Exception as e:
        print(f"Error in grade_all: {e}")
        return []
