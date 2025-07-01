from core.grader import calculate_similarity_with_feedback, debug_grading
from core.db import get_questions, get_test_answers, get_grade_thresholds, get_test_by_id
from bson.objectid import ObjectId

def grade_test(test_id, user_id, debug=False):
    """Grade all student answers for a specific test"""
    try:
        if not test_id or not user_id:
            return []
        
        # Get test details
        test = get_test_by_id(test_id, user_id)
        if not test:
            print(f"Test {test_id} not found for user {user_id}")
            return []
        
        # Get test answers
        test_answers = get_test_answers(user_id, test_id)
        if not test_answers:
            print(f"No test answers found for test {test_id}")
            return []
        
        # Get questions for this test
        question_ids = test.get("question_ids", [])
        questions = []
        for qid in question_ids:
            question = get_questions(user_id)
            question = next((q for q in question if str(q["_id"]) == qid), None)
            if question:
                questions.append(question)
        
        if not questions:
            print(f"No questions found for test {test_id}")
            return []
        
        # Get grade thresholds
        grade_thresholds = get_grade_thresholds(user_id)
        
        results = []
        
        for test_answer in test_answers:
            try:
                student_name = test_answer.get("student_name", "Unknown")
                student_roll_no = test_answer.get("student_roll_no", "Unknown")
                question_answers = test_answer.get("question_answers", {})
                
                if debug:
                    print(f"Grading test for student: {student_name} ({student_roll_no})")
                
                # Grade each question in the test
                question_scores = []
                question_grades = []
                question_details = []
                
                for question in questions:
                    question_id = str(question["_id"])
                    student_answer = question_answers.get(question_id, "")
                    
                    if not student_answer:
                        print(f"Warning: No answer for question {question_id} by student {student_roll_no}")
                        question_scores.append(0.0)
                        question_grades.append("F")
                        question_details.append({
                            "question_id": question_id,
                            "score": 0.0,
                            "grade": "F",
                            "matched_rules": [],
                            "missed_rules": question.get("marking_scheme", [])
                        })
                        continue
                    
                    sample_answer = question.get("sample_answer", "")
                    rules = question.get("marking_scheme", [])
                    
                    if debug:
                        debug_grading(student_answer, sample_answer, rules)
                    
                    feedback = calculate_similarity_with_feedback(
                        student_answer, sample_answer, rules, 
                        grade_thresholds=grade_thresholds, debug=debug
                    )
                    
                    score = feedback['score']
                    grade = feedback['grade']
                    
                    question_scores.append(score)
                    question_grades.append(grade)
                    question_details.append({
                        "question_id": question_id,
                        "score": score,
                        "grade": grade,
                        "matched_rules": feedback["matched_rules"],
                        "missed_rules": feedback["missed_rules"]
                    })
                
                # Calculate overall test score
                if question_scores:
                    overall_score = sum(question_scores) / len(question_scores)
                    overall_percentage = overall_score * 100
                    
                    # Determine overall grade based on average score
                    overall_grade = "F"
                    for grade, threshold in grade_thresholds.items():
                        if overall_percentage >= threshold:
                            overall_grade = grade
                            break
                else:
                    overall_score = 0.0
                    overall_percentage = 0.0
                    overall_grade = "F"
                
                # Create test grade record
                test_grade = {
                    "test_id": test_id,
                    "student_name": student_name,
                    "student_roll_no": student_roll_no,
                    "overall_score": overall_score,
                    "overall_percentage": f"{overall_percentage:.2f}%",
                    "overall_grade": overall_grade,
                    "question_scores": question_scores,
                    "question_grades": question_grades,
                    "question_details": question_details,
                    "total_questions": len(questions),
                    "answered_questions": len([s for s in question_scores if s > 0])
                }
                
                results.append(test_grade)
                
                if debug:
                    print(f"Student {student_roll_no} - Overall: {overall_percentage:.2f}% ({overall_grade})")
                
            except Exception as e:
                print(f"Error grading test for student {test_answer.get('student_roll_no', 'Unknown')}: {e}")
                continue
        
        return results
        
    except Exception as e:
        print(f"Error in grade_test: {e}")
        return []

def get_test_statistics(test_id, user_id):
    """Get statistics for a specific test"""
    try:
        from core.db import get_test_grades
        
        test_grades = get_test_grades(user_id, test_id)
        if not test_grades:
            return None
        
        # Calculate statistics
        total_students = len(test_grades)
        scores = [grade.get("overall_score", 0) for grade in test_grades]
        
        if not scores:
            return None
        
        avg_score = sum(scores) / len(scores)
        max_score = max(scores)
        min_score = min(scores)
        
        # Grade distribution
        grade_distribution = {}
        for grade in test_grades:
            grade_letter = grade.get("overall_grade", "F")
            grade_distribution[grade_letter] = grade_distribution.get(grade_letter, 0) + 1
        
        # Question-wise statistics
        question_stats = {}
        for grade in test_grades:
            question_details = grade.get("question_details", [])
            for q_detail in question_details:
                question_id = q_detail.get("question_id")
                if question_id not in question_stats:
                    question_stats[question_id] = {
                        "scores": [],
                        "grades": []
                    }
                question_stats[question_id]["scores"].append(q_detail.get("score", 0))
                question_stats[question_id]["grades"].append(q_detail.get("grade", "F"))
        
        # Calculate averages for each question
        for q_id, stats in question_stats.items():
            if stats["scores"]:
                stats["avg_score"] = sum(stats["scores"]) / len(stats["scores"])
                stats["avg_percentage"] = stats["avg_score"] * 100
        
        return {
            "total_students": total_students,
            "average_score": avg_score,
            "average_percentage": avg_score * 100,
            "max_score": max_score,
            "min_score": min_score,
            "grade_distribution": grade_distribution,
            "question_statistics": question_stats
        }
        
    except Exception as e:
        print(f"Error getting test statistics: {e}")
        return None 