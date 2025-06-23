from pymongo import MongoClient
from config import MONGO_URI, DB_NAME
from bson.objectid import ObjectId

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

def save_question(question_text, sample_answer, rules):
    db.questions.insert_one({
        "question": question_text,
        "sample_answer": sample_answer,
        "marking_scheme": rules
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
