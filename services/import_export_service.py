import csv
import json
import pandas as pd
import io
from datetime import datetime
from bson.objectid import ObjectId
from core.db import get_db, get_questions, get_student_answers, get_grades, get_tests, get_test_answers, get_test_by_id, get_test_grades
from services.auth_service import get_user_by_id

class ImportExportService:
    def __init__(self, user_id):
        self.user_id = user_id
        self.db = get_db()
    
    def export_questions_to_csv(self):
        """Export all questions to CSV format"""
        try:
            questions = get_questions(self.user_id)
            if not questions:
                return False, "No questions found to export"
            csv_data = []
            for q in questions:
                csv_data.append({
                    'question_id': str(q.get('_id', '')),
                    'question_text': q.get('question', ''),
                    'sample_answer': q.get('sample_answer', ''),
                    'rules': '; '.join([r.get('text', '') for r in q.get('marking_scheme', [])]),
                    'created_at': q.get('created_at', '').strftime('%Y-%m-%d %H:%M:%S') if q.get('created_at') else '',
                    'total_answers': len(q.get('student_answers', []))
                })
            output = io.StringIO()
            if csv_data:
                fieldnames = csv_data[0].keys()
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(csv_data)
            return True, output.getvalue()
        except Exception as e:
            return False, f"Error exporting questions: {str(e)}"
    
    def export_questions_to_json(self):
        """Export all questions to JSON format"""
        try:
            questions = get_questions(self.user_id)
            if not questions:
                return False, "No questions found to export"
            json_data = []
            for q in questions:
                question_data = {
                    'question_id': str(q.get('_id', '')),
                    'question_text': q.get('question', ''),
                    'sample_answer': q.get('sample_answer', ''),
                    'rules': [r.get('text', '') for r in q.get('marking_scheme', [])],
                    'created_at': q.get('created_at', '').isoformat() if q.get('created_at') else '',
                    'total_answers': len(q.get('student_answers', []))
                }
                json_data.append(question_data)
            return True, json.dumps(json_data, indent=2)
        except Exception as e:
            return False, f"Error exporting questions: {str(e)}"
    
    def export_student_answers_to_csv(self, question_id=None):
        """Export student answers to CSV format"""
        try:
            if question_id:
                question = self.db.questions.find_one({'_id': ObjectId(question_id), 'user_id': self.user_id})
                if not question:
                    return False, "Question not found"
                answers = question.get('student_answers', [])
            else:
                answers = get_student_answers(self.user_id)
            if not answers:
                return False, "No student answers found to export"
            csv_data = []
            for answer in answers:
                csv_data.append({
                    'answer_id': str(answer.get('_id', '')),
                    'question_id': str(answer.get('question_id', '')),
                    'student_name': answer.get('student_name', ''),
                    'student_roll_no': answer.get('student_roll_no', ''),
                    'answer_text': answer.get('student_ans', answer.get('student_answer', answer.get('answer', ''))),
                    'submitted_at': answer.get('created_at', answer.get('submitted_at')).strftime('%Y-%m-%d %H:%M:%S') if answer.get('created_at', answer.get('submitted_at')) else ''
                })
            output = io.StringIO()
            if csv_data:
                fieldnames = csv_data[0].keys()
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(csv_data)
            return True, output.getvalue()
        except Exception as e:
            return False, f"Error exporting student answers: {str(e)}"
    
    def export_student_answers_to_json(self, question_id=None):
        """Export student answers to JSON format"""
        try:
            if question_id:
                question = self.db.questions.find_one({'_id': ObjectId(question_id), 'user_id': self.user_id})
                if not question:
                    return False, "Question not found"
                answers = question.get('student_answers', [])
            else:
                answers = get_student_answers(self.user_id)
            if not answers:
                return False, "No student answers found to export"
            json_data = []
            for answer in answers:
                answer_data = {
                    'answer_id': str(answer.get('_id', '')),
                    'question_id': str(answer.get('question_id', '')),
                    'student_name': answer.get('student_name', ''),
                    'student_roll_no': answer.get('student_roll_no', ''),
                    'answer_text': answer.get('student_ans', answer.get('student_answer', answer.get('answer', ''))),
                    'submitted_at': answer.get('created_at', answer.get('submitted_at')).isoformat() if answer.get('created_at', answer.get('submitted_at')) else ''
                }
                json_data.append(answer_data)
            return True, json.dumps(json_data, indent=2)
        except Exception as e:
            return False, f"Error exporting student answers: {str(e)}"
    
    def export_grades_to_csv(self):
        """Export grading results to CSV format"""
        try:
            grades = get_grades(self.user_id)
            if not grades:
                return False, "No grading results found to export"
            csv_data = []
            for grade in grades:
                csv_data.append({
                    'grade_id': str(grade.get('_id', '')),
                    'question_id': str(grade.get('question_id', '')),
                    'student_name': grade.get('student_name', ''),
                    'student_roll_no': grade.get('student_roll_no', ''),
                    'answer_text': grade.get('student_answer', ''),
                    'score': grade.get('score', ''),
                    'grade': grade.get('grade', ''),
                    'correct_percentage': grade.get('correct_%', ''),
                    'matched_rules': '; '.join(grade.get('matched_rules', [])),
                    'missed_rules': '; '.join(grade.get('missed_rules', [])),
                    'graded_at': grade.get('graded_at', '').strftime('%Y-%m-%d %H:%M:%S') if grade.get('graded_at') else ''
                })
            output = io.StringIO()
            if csv_data:
                fieldnames = csv_data[0].keys()
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(csv_data)
            return True, output.getvalue()
        except Exception as e:
            return False, f"Error exporting grades: {str(e)}"
    
    def export_grades_to_json(self):
        """Export grading results to JSON format"""
        try:
            grades = get_grades(self.user_id)
            if not grades:
                return False, "No grading results found to export"
            json_data = []
            for grade in grades:
                grade_data = {
                    'grade_id': str(grade.get('_id', '')),
                    'question_id': str(grade.get('question_id', '')),
                    'student_name': grade.get('student_name', ''),
                    'student_roll_no': grade.get('student_roll_no', ''),
                    'answer_text': grade.get('student_answer', ''),
                    'score': grade.get('score', ''),
                    'grade': grade.get('grade', ''),
                    'correct_percentage': grade.get('correct_%', ''),
                    'matched_rules': grade.get('matched_rules', []),
                    'missed_rules': grade.get('missed_rules', []),
                    'graded_at': grade.get('graded_at', '').isoformat() if grade.get('graded_at') else ''
                }
                json_data.append(grade_data)
            return True, json.dumps(json_data, indent=2)
        except Exception as e:
            return False, f"Error exporting grades: {str(e)}"
    
    def import_questions_from_csv(self, csv_content):
        """Import questions from CSV format"""
        try:
            # Parse CSV content
            csv_reader = csv.DictReader(csv_content.splitlines())
            
            imported_count = 0
            errors = []
            
            for row in csv_reader:
                try:
                    # Validate required fields
                    if not row.get('question_text') or not row.get('sample_answer'):
                        errors.append(f"Row {imported_count + 1}: Missing required fields")
                        continue
                    
                    # Parse rules (semicolon-separated)
                    rules = [rule.strip() for rule in row.get('rules', '').split(';') if rule.strip()]
                    
                    # Create question
                    question_data = {
                        'question': row['question_text'],
                        'sample_answer': row['sample_answer'],
                        'rules': rules,
                        'user_id': self.user_id,
                        'created_at': datetime.utcnow()
                    }
                    
                    result = self.db.questions.insert_one(question_data)
                    if result.inserted_id:
                        imported_count += 1
                    else:
                        errors.append(f"Row {imported_count + 1}: Failed to insert question")
                        
                except Exception as e:
                    errors.append(f"Row {imported_count + 1}: {str(e)}")
            
            return True, f"Successfully imported {imported_count} questions", errors
            
        except Exception as e:
            return False, f"Error importing questions: {str(e)}", []
    
    def import_questions_from_json(self, json_content):
        """Import questions from JSON format"""
        try:
            # Parse JSON content
            questions_data = json.loads(json_content)
            
            if not isinstance(questions_data, list):
                return False, "Invalid JSON format: expected array of questions", []
            
            imported_count = 0
            errors = []
            
            for i, question_data in enumerate(questions_data):
                try:
                    # Validate required fields
                    if not question_data.get('question_text') or not question_data.get('sample_answer'):
                        errors.append(f"Question {i + 1}: Missing required fields")
                        continue
                    
                    # Get rules
                    rules = question_data.get('rules', [])
                    if isinstance(rules, str):
                        rules = [rule.strip() for rule in rules.split(';') if rule.strip()]
                    
                    # Create question
                    question = {
                        'question': question_data['question_text'],
                        'sample_answer': question_data['sample_answer'],
                        'rules': rules,
                        'user_id': self.user_id,
                        'created_at': datetime.utcnow()
                    }
                    
                    result = self.db.questions.insert_one(question)
                    if result.inserted_id:
                        imported_count += 1
                    else:
                        errors.append(f"Question {i + 1}: Failed to insert question")
                        
                except Exception as e:
                    errors.append(f"Question {i + 1}: {str(e)}")
            
            return True, f"Successfully imported {imported_count} questions", errors
            
        except Exception as e:
            return False, f"Error importing questions: {str(e)}", []
    
    def import_student_answers_from_csv(self, csv_content, question_id=None):
        """Import student answers from CSV format"""
        try:
            # Parse CSV content
            csv_reader = csv.DictReader(csv_content.splitlines())
            
            imported_count = 0
            errors = []
            
            for row in csv_reader:
                try:
                    # Validate required fields
                    if not row.get('student_name') or not row.get('student_roll_no') or not row.get('answer_text'):
                        errors.append(f"Row {imported_count + 1}: Missing required fields")
                        continue
                    
                    # Use provided question_id or get from row
                    target_question_id = question_id or row.get('question_id')
                    if not target_question_id:
                        errors.append(f"Row {imported_count + 1}: No question ID specified")
                        continue
                    
                    # Validate question exists
                    question = self.db.questions.find_one({'_id': ObjectId(target_question_id), 'user_id': self.user_id})
                    if not question:
                        errors.append(f"Row {imported_count + 1}: Question not found")
                        continue
                    
                    # Create answer
                    answer_data = {
                        'question_id': ObjectId(target_question_id),
                        'student_name': row['student_name'],
                        'student_roll_no': row['student_roll_no'],
                        'student_ans': row['answer_text'],
                        'user_id': self.user_id,
                        'created_at': datetime.utcnow()
                    }
                    
                    result = self.db.answers.insert_one(answer_data)
                    if result.inserted_id:
                        imported_count += 1
                    else:
                        errors.append(f"Row {imported_count + 1}: Failed to insert answer")
                        
                except Exception as e:
                    errors.append(f"Row {imported_count + 1}: {str(e)}")
            
            return True, f"Successfully imported {imported_count} answers", errors
            
        except Exception as e:
            return False, f"Error importing answers: {str(e)}", []
    
    def import_student_answers_from_json(self, json_content, question_id=None):
        """Import student answers from JSON format"""
        try:
            # Parse JSON content
            answers_data = json.loads(json_content)
            
            if not isinstance(answers_data, list):
                return False, "Invalid JSON format: expected array of answers", []
            
            imported_count = 0
            errors = []
            
            for i, answer_data in enumerate(answers_data):
                try:
                    # Validate required fields
                    if not answer_data.get('student_name') or not answer_data.get('student_roll_no') or not answer_data.get('answer_text'):
                        errors.append(f"Answer {i + 1}: Missing required fields")
                        continue
                    
                    # Use provided question_id or get from answer data
                    target_question_id = question_id or answer_data.get('question_id')
                    if not target_question_id:
                        errors.append(f"Answer {i + 1}: No question ID specified")
                        continue
                    
                    # Validate question exists
                    question = self.db.questions.find_one({'_id': ObjectId(target_question_id), 'user_id': self.user_id})
                    if not question:
                        errors.append(f"Answer {i + 1}: Question not found")
                        continue
                    
                    # Create answer
                    answer = {
                        'question_id': ObjectId(target_question_id),
                        'student_name': answer_data['student_name'],
                        'student_roll_no': answer_data['student_roll_no'],
                        'student_ans': answer_data['answer_text'],
                        'user_id': self.user_id,
                        'created_at': datetime.utcnow()
                    }
                    
                    result = self.db.answers.insert_one(answer)
                    if result.inserted_id:
                        imported_count += 1
                    else:
                        errors.append(f"Answer {i + 1}: Failed to insert answer")
                        
                except Exception as e:
                    errors.append(f"Answer {i + 1}: {str(e)}")
            
            return True, f"Successfully imported {imported_count} answers", errors
            
        except Exception as e:
            return False, f"Error importing answers: {str(e)}", []
    
    def get_export_templates(self):
        """Get export templates for different data types"""
        return {
            'student_answers': {
                'headers': ['student_name', 'student_roll_no', 'answer_text'],
                'example': ['John Doe', '2023001', 'The answer to the question is...']
            },
            'test_answers': {
                'headers': ['student_name', 'student_roll_no', 'question_1_answer', 'question_2_answer', 'question_3_answer'],
                'example': ['John Doe', '2023001', 'Answer to question 1...', 'Answer to question 2...', 'Answer to question 3...']
            }
        }

    def export_tests_to_csv(self):
        """Export all tests to CSV format"""
        try:
            tests = get_tests(self.user_id)
            if not tests:
                return False, "No tests found to export"
            
            csv_data = []
            for test in tests:
                # Get question details for this test
                question_details = []
                for qid in test.get('question_ids', []):
                    question = self.db.questions.find_one({'_id': ObjectId(qid), 'user_id': self.user_id})
                    if question:
                        question_details.append(question.get('question', '')[:50] + '...')
                
                csv_data.append({
                    'test_id': str(test.get('_id', '')),
                    'test_name': test.get('test_name', ''),
                    'test_description': test.get('test_description', ''),
                    'questions': '; '.join(question_details),
                    'total_questions': len(test.get('question_ids', [])),
                    'created_at': test.get('created_at', '').strftime('%Y-%m-%d %H:%M:%S') if test.get('created_at') else '',
                    'is_active': test.get('is_active', True)
                })
            
            output = io.StringIO()
            if csv_data:
                fieldnames = csv_data[0].keys()
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(csv_data)
            return True, output.getvalue()
        except Exception as e:
            return False, f"Error exporting tests: {str(e)}"

    def export_test_answers_to_csv(self, test_id=None):
        """Export test answers to CSV format"""
        try:
            test_answers = get_test_answers(self.user_id, test_id)
            if not test_answers:
                return False, "No test answers found to export"
            
            csv_data = []
            for answer in test_answers:
                # Get test details
                test = get_test_by_id(answer.get('test_id'), self.user_id)
                if not test:
                    continue
                
                # Create row with test info and question answers
                row = {
                    'test_id': str(answer.get('test_id', '')),
                    'test_name': test.get('test_name', ''),
                    'student_name': answer.get('student_name', ''),
                    'student_roll_no': answer.get('student_roll_no', ''),
                    'submitted_at': answer.get('created_at', '').strftime('%Y-%m-%d %H:%M:%S') if answer.get('created_at') else ''
                }
                
                # Add question answers
                question_answers = answer.get('question_answers', {})
                for qid in test.get('question_ids', []):
                    question = self.db.questions.find_one({'_id': ObjectId(qid), 'user_id': self.user_id})
                    if question:
                        question_text = question.get('question', '')[:30] + '...'
                        answer_text = question_answers.get(qid, '')
                        row[f'Q_{question_text}'] = answer_text
                
                csv_data.append(row)
            
            output = io.StringIO()
            if csv_data:
                fieldnames = csv_data[0].keys()
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(csv_data)
            return True, output.getvalue()
        except Exception as e:
            return False, f"Error exporting test answers: {str(e)}"

    def export_test_grades_to_csv(self, test_id=None):
        """Export test grades to CSV format"""
        try:
            test_grades = get_test_grades(self.user_id, test_id)
            if not test_grades:
                return False, "No test grades found to export"
            
            csv_data = []
            for grade in test_grades:
                # Get test details
                test = get_test_by_id(grade.get('test_id'), self.user_id)
                if not test:
                    continue
                
                row = {
                    'test_id': str(grade.get('test_id', '')),
                    'test_name': test.get('test_name', ''),
                    'student_name': grade.get('student_name', ''),
                    'student_roll_no': grade.get('student_roll_no', ''),
                    'overall_score': grade.get('overall_score', 0),
                    'overall_percentage': grade.get('overall_percentage', '0%'),
                    'overall_grade': grade.get('overall_grade', 'F'),
                    'total_questions': grade.get('total_questions', 0),
                    'answered_questions': grade.get('answered_questions', 0),
                    'graded_at': grade.get('created_at', '').strftime('%Y-%m-%d %H:%M:%S') if grade.get('created_at') else ''
                }
                
                # Add question-wise scores
                question_details = grade.get('question_details', [])
                for i, q_detail in enumerate(question_details, 1):
                    row[f'Q{i}_score'] = f"{q_detail.get('score', 0) * 100:.2f}%"
                    row[f'Q{i}_grade'] = q_detail.get('grade', 'F')
                
                csv_data.append(row)
            
            output = io.StringIO()
            if csv_data:
                fieldnames = csv_data[0].keys()
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(csv_data)
            return True, output.getvalue()
        except Exception as e:
            return False, f"Error exporting test grades: {str(e)}"

    def import_test_answers_from_csv(self, csv_content, test_id):
        """Import test answers from CSV format"""
        try:
            # Validate test exists
            test = get_test_by_id(test_id, self.user_id)
            if not test:
                return False, "Test not found or doesn't belong to you", []
            
            # Parse CSV content
            csv_reader = csv.DictReader(csv_content.splitlines())
            
            imported_count = 0
            errors = []
            
            for row in csv_reader:
                try:
                    # Validate required fields
                    if not row.get('student_name') or not row.get('student_roll_no'):
                        errors.append(f"Row {imported_count + 1}: Missing student name or roll number")
                        continue
                    
                    # Extract question answers from the row
                    question_answers = {}
                    question_ids = test.get('question_ids', [])
                    
                    for qid in question_ids:
                        # Look for answer in the row (could be named Q1, Q2, etc. or question text)
                        answer_found = False
                        for key, value in row.items():
                            if key.lower().startswith('q') and value.strip():
                                # This is a question answer
                                question_answers[qid] = value.strip()
                                answer_found = True
                                break
                        
                        if not answer_found:
                            # Try to find by question text
                            question = self.db.questions.find_one({'_id': ObjectId(qid), 'user_id': self.user_id})
                            if question:
                                question_text = question.get('question', '')[:30] + '...'
                                for key, value in row.items():
                                    if question_text in key and value.strip():
                                        question_answers[qid] = value.strip()
                                        break
                    
                    # Check if we have answers for all questions
                    if len(question_answers) != len(question_ids):
                        errors.append(f"Row {imported_count + 1}: Missing answers for some questions")
                        continue
                    
                    # Save test answer
                    from core.db import save_test_answer
                    success, message = save_test_answer(
                        row['student_name'],
                        row['student_roll_no'],
                        test_id,
                        question_answers,
                        self.user_id
                    )
                    
                    if success:
                        imported_count += 1
                    else:
                        errors.append(f"Row {imported_count + 1}: {message}")
                        
                except Exception as e:
                    errors.append(f"Row {imported_count + 1}: {str(e)}")
            
            return True, f"Successfully imported {imported_count} test answers", errors
            
        except Exception as e:
            return False, f"Error importing test answers: {str(e)}", [] 