from pymongo import MongoClient
from config import MONGO_URI, DB_NAME
from bson.objectid import ObjectId
from datetime import datetime

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

def get_db():
    """Get database instance"""
    return db

# Default grade thresholds
DEFAULT_GRADE_THRESHOLDS = {
    "A": 85,
    "B": 70,
    "C": 55,
    "D": 40,
    "F": 0
}

def get_grade_thresholds(user_id=None):
    """Get current grade thresholds from database or return defaults"""
    try:
        if user_id:
            thresholds = db.settings.find_one({"type": "grade_thresholds", "user_id": user_id})
        else:
            thresholds = db.settings.find_one({"type": "grade_thresholds"})
        
        if thresholds:
            return thresholds.get("thresholds", DEFAULT_GRADE_THRESHOLDS)
        return DEFAULT_GRADE_THRESHOLDS
    except Exception as e:
        print(f"Error getting grade thresholds: {e}")
        return DEFAULT_GRADE_THRESHOLDS

def save_grade_thresholds(thresholds, user_id=None):
    """Save grade thresholds to database"""
    try:
        if not thresholds:
            return False, "No thresholds provided"
        
        filter_query = {"type": "grade_thresholds"}
        if user_id:
            filter_query["user_id"] = user_id
        
        db.settings.update_one(
            filter_query,
            {"$set": {"thresholds": thresholds, "user_id": user_id}},
            upsert=True
        )
        return True, "Grade thresholds saved successfully"
    except Exception as e:
        print(f"Error saving grade thresholds: {e}")
        return False, f"Error saving grade thresholds: {str(e)}"

def detect_rule_type(rule_text):
    """Dynamically detect rule type based on content analysis"""
    if not rule_text or not isinstance(rule_text, str):
        return "semantic"
    
    rule_lower = rule_text.lower()
    
    # Check for exact phrase indicators
    if any(word in rule_lower for word in ["formula", "equation", "mentions"]):
        return "exact_phrase"
    
    # Check for keyword matching indicators
    elif any(word in rule_lower for word in ["contains", "has", "includes"]):
        return "contains_keywords"
    
    # Default to semantic for conceptual understanding
    else:
        return "semantic"

def save_question(question_text, sample_answer, rules, user_id):
    """Save a question with validation"""
    try:
        if not question_text or not sample_answer:
            return False, "Question text and sample answer are required"
        
        if not user_id:
            return False, "User ID is required"
        
        # Convert simple rules to rule objects with types
        rule_objects = []
        if rules:
            for rule in rules:
                if rule and isinstance(rule, str):
                    # Auto-determine rule type based on content
                    rule_type = detect_rule_type(rule)
                    rule_objects.append({
                        "text": rule,
                        "type": rule_type
                    })
                elif isinstance(rule, dict) and rule.get("text"):
                    rule_objects.append(rule)
        
        question_data = {
            "question": question_text,
            "sample_answer": sample_answer,
            "marking_scheme": rule_objects,
            "user_id": user_id,
            "created_at": datetime.utcnow()
        }
        
        result = db.questions.insert_one(question_data)
        return True, f"Question saved successfully with ID: {result.inserted_id}"
    except Exception as e:
        print(f"Error saving question: {e}")
        return False, f"Error saving question: {str(e)}"

def save_student_answer(name, roll_no, answer, question_id, user_id):
    """Save a student answer with validation"""
    try:
        if not name or not roll_no or not answer:
            return False, "Student name, roll number, and answer are required"
        
        if not user_id:
            return False, "User ID is required"
        
        if not question_id:
            return False, "Question ID is required"
        
        answer_data = {
            "student_name": name,
            "student_roll_no": roll_no,
            "student_ans": answer,
            "question_id": question_id,
            "user_id": user_id,
            "created_at": datetime.utcnow()
        }
        
        result = db.answers.insert_one(answer_data)
        return True, f"Student answer saved successfully with ID: {result.inserted_id}"
    except Exception as e:
        print(f"Error saving student answer: {e}")
        return False, f"Error saving student answer: {str(e)}"

def get_questions(user_id):
    """Get questions for a specific user"""
    try:
        if not user_id:
            return []
        
        questions = list(db.questions.find({"user_id": user_id}))
        return questions
    except Exception as e:
        print(f"Error getting questions: {e}")
        return []

def get_student_answers(user_id):
    """Get student answers for a specific user"""
    try:
        if not user_id:
            return []
        
        answers = list(db.answers.find({"user_id": user_id}))
        return answers
    except Exception as e:
        print(f"Error getting student answers: {e}")
        return []

def get_grades(user_id):
    """Get grades for a specific user"""
    try:
        if not user_id:
            return []
        
        grades = list(db.grades.find({"user_id": user_id}))
        return grades
    except Exception as e:
        print(f"Error getting grades: {e}")
        return []

def save_grades(grades, user_id):
    """Save grades with validation"""
    try:
        if not grades or not isinstance(grades, list):
            return False, "No grades to save"
        
        if not user_id:
            return False, "User ID is required"
        
        if len(grades) == 0:
            return True, "No grades to save (empty list)"
        
        # Add user_id to each grade record
        for grade in grades:
            if isinstance(grade, dict):
                grade["user_id"] = user_id
                grade["created_at"] = datetime.utcnow()
        
        result = db.grades.insert_many(grades)
        return True, f"Saved {len(result.inserted_ids)} grades successfully"
    except Exception as e:
        print(f"Error saving grades: {e}")
        return False, f"Error saving grades: {str(e)}"

def clear_grades(user_id):
    """Clear grades for a specific user"""
    try:
        if not user_id:
            return False, "User ID is required"
        
        result = db.grades.delete_many({"user_id": user_id})
        return True, f"Cleared {result.deleted_count} grades"
    except Exception as e:
        print(f"Error clearing grades: {e}")
        return False, f"Error clearing grades: {str(e)}"

def get_question_by_id(qid, user_id):
    """Get a specific question by ID for a user"""
    try:
        if not qid or not user_id:
            return None
        
        question = db.questions.find_one({"_id": ObjectId(qid), "user_id": user_id})
        return question
    except Exception as e:
        print(f"Error getting question by ID: {e}")
        return None

def update_question(question_id, question_text, sample_answer, rules, user_id):
    """Update a question with validation"""
    try:
        if not question_id or not question_text or not sample_answer:
            return False, "Question ID, text, and sample answer are required"
        
        if not user_id:
            return False, "User ID is required"
        
        # Check if question exists and belongs to user
        existing_question = db.questions.find_one({"_id": ObjectId(question_id), "user_id": user_id})
        if not existing_question:
            return False, "Question not found or doesn't belong to you"
        
        # Convert simple rules to rule objects with types
        rule_objects = []
        if rules:
            for rule in rules:
                if rule and isinstance(rule, str):
                    # Auto-determine rule type based on content
                    rule_type = detect_rule_type(rule)
                    rule_objects.append({
                        "text": rule,
                        "type": rule_type
                    })
                elif isinstance(rule, dict) and rule.get("text"):
                    rule_objects.append(rule)
        
        # Update question data
        update_data = {
            "question": question_text,
            "sample_answer": sample_answer,
            "marking_scheme": rule_objects,
            "updated_at": datetime.utcnow()
        }
        
        result = db.questions.update_one(
            {"_id": ObjectId(question_id), "user_id": user_id},
            {"$set": update_data}
        )
        
        if result.modified_count > 0:
            return True, "Question updated successfully"
        else:
            return False, "No changes made to question"
    except Exception as e:
        print(f"Error updating question: {e}")
        return False, f"Error updating question: {str(e)}"

def delete_question(question_id, user_id):
    """Delete a question and all related data"""
    try:
        if not question_id or not user_id:
            return False, "Question ID and user ID are required"
        
        # Check if question exists and belongs to user
        existing_question = db.questions.find_one({"_id": ObjectId(question_id), "user_id": user_id})
        if not existing_question:
            return False, "Question not found or doesn't belong to you"
        
        # Delete related student answers
        answers_deleted = db.answers.delete_many({"question_id": question_id, "user_id": user_id})
        
        # Delete related grades
        grades_deleted = db.grades.delete_many({"question_id": question_id, "user_id": user_id})
        
        # Delete the question
        question_deleted = db.questions.delete_one({"_id": ObjectId(question_id), "user_id": user_id})
        
        if question_deleted.deleted_count > 0:
            return True, f"Question deleted successfully. Also deleted {answers_deleted.deleted_count} answers and {grades_deleted.deleted_count} grades"
        else:
            return False, "Failed to delete question"
    except Exception as e:
        print(f"Error deleting question: {e}")
        return False, f"Error deleting question: {str(e)}"

# Test Management Functions
def save_test(test_name, test_description, question_ids, user_id):
    """Save a test with validation"""
    try:
        if not test_name or not question_ids:
            return False, "Test name and question IDs are required"
        
        if not user_id:
            return False, "User ID is required"
        
        if not isinstance(question_ids, list) or len(question_ids) == 0:
            return False, "At least one question must be selected"
        
        # Validate that all questions exist and belong to the user
        for qid in question_ids:
            question = db.questions.find_one({"_id": ObjectId(qid), "user_id": user_id})
            if not question:
                return False, f"Question with ID {qid} not found or doesn't belong to you"
        
        test_data = {
            "test_name": test_name,
            "test_description": test_description or "",
            "question_ids": question_ids,
            "user_id": user_id,
            "created_at": datetime.utcnow(),
            "is_active": True
        }
        
        result = db.tests.insert_one(test_data)
        return True, f"Test saved successfully with ID: {result.inserted_id}"
    except Exception as e:
        print(f"Error saving test: {e}")
        return False, f"Error saving test: {str(e)}"

def update_test(test_id, test_name, test_description, question_ids, user_id):
    """Update a test with validation"""
    try:
        if not test_id or not test_name or not question_ids:
            return False, "Test ID, name, and question IDs are required"
        
        if not user_id:
            return False, "User ID is required"
        
        if not isinstance(question_ids, list) or len(question_ids) == 0:
            return False, "At least one question must be selected"
        
        # Check if test exists and belongs to user
        existing_test = db.tests.find_one({"_id": ObjectId(test_id), "user_id": user_id})
        if not existing_test:
            return False, "Test not found or doesn't belong to you"
        
        # Validate that all questions exist and belong to the user
        for qid in question_ids:
            question = db.questions.find_one({"_id": ObjectId(qid), "user_id": user_id})
            if not question:
                return False, f"Question with ID {qid} not found or doesn't belong to you"
        
        # Update test data
        update_data = {
            "test_name": test_name,
            "test_description": test_description or "",
            "question_ids": question_ids,
            "updated_at": datetime.utcnow()
        }
        
        result = db.tests.update_one(
            {"_id": ObjectId(test_id), "user_id": user_id},
            {"$set": update_data}
        )
        
        if result.modified_count > 0:
            return True, "Test updated successfully"
        else:
            return False, "No changes made to test"
    except Exception as e:
        print(f"Error updating test: {e}")
        return False, f"Error updating test: {str(e)}"

def get_tests(user_id):
    """Get all tests for a specific user"""
    try:
        if not user_id:
            return []
        
        tests = list(db.tests.find({"user_id": user_id}).sort("created_at", -1))
        return tests
    except Exception as e:
        print(f"Error getting tests: {e}")
        return []

def get_test_by_id(test_id, user_id):
    """Get a specific test by ID for a user"""
    try:
        if not test_id or not user_id:
            return None
        
        test = db.tests.find_one({"_id": ObjectId(test_id), "user_id": user_id})
        return test
    except Exception as e:
        print(f"Error getting test by ID: {e}")
        return None

def delete_test(test_id, user_id):
    """Delete a test and its associated data"""
    try:
        if not test_id or not user_id:
            return False, "Test ID and User ID are required"
        
        print(f"Attempting to delete test {test_id} for user {user_id}")
        
        # Check if test exists and belongs to user
        test = db.tests.find_one({"_id": ObjectId(test_id), "user_id": user_id})
        if not test:
            print(f"Test {test_id} not found for user {user_id}")
            return False, "Test not found or doesn't belong to you"
        
        print(f"Found test: {test.get('test_name', 'Unknown')}")
        
        # Delete test
        result = db.tests.delete_one({"_id": ObjectId(test_id), "user_id": user_id})
        print(f"Test deletion result: {result.deleted_count} documents deleted")
        
        # Delete associated test answers and grades
        try:
            test_answers_result = db.test_answers.delete_many({"test_id": test_id})
            print(f"Test answers deletion result: {test_answers_result.deleted_count} documents deleted")
        except Exception as e:
            print(f"Warning: Could not delete test answers: {e}")
        
        try:
            test_grades_result = db.test_grades.delete_many({"test_id": test_id})
            print(f"Test grades deletion result: {test_grades_result.deleted_count} documents deleted")
        except Exception as e:
            print(f"Warning: Could not delete test grades: {e}")
        
        return True, f"Test and associated data deleted successfully"
    except Exception as e:
        print(f"Error deleting test: {e}")
        return False, f"Error deleting test: {str(e)}"

def save_test_answer(student_name, student_roll_no, test_id, question_answers, user_id):
    """Save a student's answers for an entire test"""
    try:
        if not student_name or not student_roll_no or not test_id or not question_answers:
            return False, "Student name, roll number, test ID, and answers are required"
        
        if not user_id:
            return False, "User ID is required"
        
        # Validate test exists and belongs to user
        test = db.tests.find_one({"_id": ObjectId(test_id), "user_id": user_id})
        if not test:
            return False, "Test not found or doesn't belong to you"
        
        # Validate that all questions in the test have answers
        test_question_ids = set(test.get("question_ids", []))
        answer_question_ids = set(question_answers.keys())
        
        if test_question_ids != answer_question_ids:
            missing_questions = test_question_ids - answer_question_ids
            extra_questions = answer_question_ids - test_question_ids
            error_msg = []
            if missing_questions:
                error_msg.append(f"Missing answers for questions: {', '.join(missing_questions)}")
            if extra_questions:
                error_msg.append(f"Extra answers for questions not in test: {', '.join(extra_questions)}")
            return False, "; ".join(error_msg)
        
        # Check if student already has answers for this test
        existing_answer = db.test_answers.find_one({
            "test_id": test_id,
            "student_roll_no": student_roll_no,
            "user_id": user_id
        })
        
        if existing_answer:
            return False, f"Student {student_roll_no} already has answers for this test"
        
        # Create test answer record
        test_answer_data = {
            "test_id": test_id,
            "student_name": student_name,
            "student_roll_no": student_roll_no,
            "question_answers": question_answers,
            "user_id": user_id,
            "created_at": datetime.utcnow()
        }
        
        result = db.test_answers.insert_one(test_answer_data)
        return True, f"Test answers saved successfully with ID: {result.inserted_id}"
    except Exception as e:
        print(f"Error saving test answer: {e}")
        return False, f"Error saving test answer: {str(e)}"

def get_test_answers(user_id, test_id=None):
    """Get test answers for a specific user and optionally a specific test"""
    try:
        if not user_id:
            return []
        
        query = {"user_id": user_id}
        if test_id:
            query["test_id"] = test_id
        
        answers = list(db.test_answers.find(query).sort("created_at", -1))
        return answers
    except Exception as e:
        print(f"Error getting test answers: {e}")
        return []

def save_test_grades(test_grades, user_id):
    """Save test grades with validation"""
    try:
        if not test_grades or not isinstance(test_grades, list):
            return False, "No test grades to save"
        
        if not user_id:
            return False, "User ID is required"
        
        if len(test_grades) == 0:
            return True, "No test grades to save (empty list)"
        
        # Add user_id to each grade record
        for grade in test_grades:
            if isinstance(grade, dict):
                grade["user_id"] = user_id
                grade["created_at"] = datetime.utcnow()
        
        result = db.test_grades.insert_many(test_grades)
        return True, f"Saved {len(result.inserted_ids)} test grades successfully"
    except Exception as e:
        print(f"Error saving test grades: {e}")
        return False, f"Error saving test grades: {str(e)}"

def get_test_grades(user_id, test_id=None):
    """Get test grades for a specific user and optionally a specific test"""
    try:
        if not user_id:
            return []
        
        query = {"user_id": user_id}
        if test_id:
            query["test_id"] = test_id
        
        grades = list(db.test_grades.find(query).sort("created_at", -1))
        return grades
    except Exception as e:
        print(f"Error getting test grades: {e}")
        return []

def clear_test_grades(user_id, test_id=None):
    """Clear test grades for a specific user and optionally a specific test"""
    try:
        if not user_id:
            return False, "User ID is required"
        
        query = {"user_id": user_id}
        if test_id:
            query["test_id"] = test_id
        
        result = db.test_grades.delete_many(query)
        return True, f"Cleared {result.deleted_count} test grades"
    except Exception as e:
        print(f"Error clearing test grades: {e}")
        return False, f"Error clearing test grades: {str(e)}"
