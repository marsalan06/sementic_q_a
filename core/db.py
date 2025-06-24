from pymongo import MongoClient
from config import MONGO_URI, DB_NAME
from bson.objectid import ObjectId

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

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

def save_question(question_text, sample_answer, rules):
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
        "marking_scheme": rule_objects
    })

def save_student_answer(name, roll_no, answer, question_id):
    db.answers.insert_one({
        "student_name": name,
        "student_roll_no": roll_no,
        "student_ans": answer,
        "question_id": question_id
    })

def get_questions():
    return list(db.questions.find())

def get_student_answers():
    return list(db.answers.find())

def save_grades(grades):
    db.grades.insert_many(grades)

def clear_grades():
    db.grades.delete_many({})

def get_question_by_id(qid):
    return db.questions.find_one({"_id": ObjectId(qid)})
