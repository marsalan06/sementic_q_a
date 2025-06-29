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
