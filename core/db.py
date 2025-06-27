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
    if user_id:
        thresholds = db.settings.find_one({"type": "grade_thresholds", "user_id": user_id})
    else:
        thresholds = db.settings.find_one({"type": "grade_thresholds"})
    
    if thresholds:
        return thresholds.get("thresholds", DEFAULT_GRADE_THRESHOLDS)
    return DEFAULT_GRADE_THRESHOLDS

def save_grade_thresholds(thresholds, user_id=None):
    """Save grade thresholds to database"""
    filter_query = {"type": "grade_thresholds"}
    if user_id:
        filter_query["user_id"] = user_id
    
    db.settings.update_one(
        filter_query,
        {"$set": {"thresholds": thresholds, "user_id": user_id}},
        upsert=True
    )

def detect_rule_type(rule_text):
    """Dynamically detect rule type based on content analysis"""
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
    # Convert simple rules to rule objects with types
    rule_objects = []
    for rule in rules:
        if isinstance(rule, dict):
            rule_objects.append(rule)
        else:
            # Auto-determine rule type based on content
            rule_type = detect_rule_type(rule)
            
            rule_objects.append({
                "text": rule,
                "type": rule_type
            })
    
    db.questions.insert_one({
        "question": question_text,
        "sample_answer": sample_answer,
        "marking_scheme": rule_objects,
        "user_id": user_id,
        "created_at": datetime.utcnow()
    })

def save_student_answer(name, roll_no, answer, question_id, user_id):
    db.answers.insert_one({
        "student_name": name,
        "student_roll_no": roll_no,
        "student_ans": answer,
        "question_id": question_id,
        "user_id": user_id,
        "created_at": datetime.utcnow()
    })

def get_questions(user_id):
    return list(db.questions.find({"user_id": user_id}))

def get_student_answers(user_id):
    return list(db.answers.find({"user_id": user_id}))

def save_grades(grades, user_id):
    # Add user_id to each grade record
    for grade in grades:
        grade["user_id"] = user_id
        grade["created_at"] = datetime.utcnow()
    
    db.grades.insert_many(grades)

def clear_grades(user_id):
    db.grades.delete_many({"user_id": user_id})

def get_question_by_id(qid, user_id):
    return db.questions.find_one({"_id": ObjectId(qid), "user_id": user_id})
