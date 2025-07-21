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
        """Export all questions to CSV format with proper formatting"""
        try:
            questions = get_questions(self.user_id)
            if not questions:
                return False, "No questions found to export"
            
            csv_data = []
            for i, q in enumerate(questions, 1):
                # Clean and format the data
                question_text = q.get('question', '').strip()
                sample_answer = q.get('sample_answer', '').strip()
                
                # Format rules properly
                rules = q.get('marking_scheme', [])
                rules_text = []
                for rule in rules:
                    rule_text = rule.get('text', '').strip()
                    if rule_text:
                        rules_text.append(rule_text)
                
                # Format creation date
                created_at = q.get('created_at')
                if created_at:
                    try:
                        formatted_date = created_at.strftime('%Y-%m-%d %H:%M:%S')
                    except:
                        formatted_date = str(created_at)
                else:
                    formatted_date = ''
                
                csv_data.append({
                    'Question Number': f"Q{i:03d}",
                    'Question ID': str(q.get('_id', '')),
                    'Question Text': question_text,
                    'Sample Answer': sample_answer,
                    'Marking Rules': ' | '.join(rules_text),
                    'Number of Rules': len(rules_text),
                    'Created Date': formatted_date,
                    'Total Answers': len(q.get('student_answers', []))
                })
            
            if not csv_data:
                return False, "No valid questions found to export"
            
            # Create CSV with proper formatting
            output = io.StringIO()
            fieldnames = [
                'Question Number', 'Question ID', 'Question Text', 'Sample Answer',
                'Marking Rules', 'Number of Rules', 'Created Date', 'Total Answers'
            ]
            
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(csv_data)
            
            return True, output.getvalue()
            
        except Exception as e:
            return False, f"Error exporting questions: {str(e)}"

    def export_questions_to_csv_with_custom_ids(self, question_ids=None):
        """Export specific questions to CSV format with custom identifiers"""
        try:
            if question_ids:
                # Get specific questions
                questions = []
                for qid in question_ids:
                    question = self.db.questions.find_one({'_id': ObjectId(qid), 'user_id': self.user_id})
                    if question:
                        questions.append(question)
            else:
                questions = get_questions(self.user_id)
            
            if not questions:
                return False, "No questions found to export"
            
            csv_data = []
            for i, q in enumerate(questions, 1):
                csv_data.append({
                    'question_id': str(q.get('_id', '')),
                    'question_number': f"Q{i:03d}",
                    'question_identifier': f"Q{i:03d}_{str(q.get('_id', ''))[-6:]}",
                    'question_text': q.get('question', ''),
                    'sample_answer': q.get('sample_answer', ''),
                    'rules': '; '.join([r.get('text', '') for r in q.get('marking_scheme', [])]),
                    'rule_count': len(q.get('marking_scheme', [])),
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
        """Import questions from CSV format with improved error handling"""
        try:
            # Parse CSV content
            csv_reader = csv.DictReader(csv_content.splitlines())
            
            # Validate CSV structure
            required_fields = ['question_text', 'sample_answer']
            optional_fields = ['rules']
            
            if not csv_reader.fieldnames:
                return False, "Invalid CSV file: No headers found", []
            
            missing_fields = [field for field in required_fields if field not in csv_reader.fieldnames]
            if missing_fields:
                return False, f"Invalid CSV format: Missing required columns: {', '.join(missing_fields)}", []
            
            imported_count = 0
            errors = []
            
            for row_num, row in enumerate(csv_reader, 1):
                try:
                    # Validate required fields
                    question_text = row.get('question_text', '').strip()
                    sample_answer = row.get('sample_answer', '').strip()
                    
                    if not question_text:
                        errors.append(f"Row {row_num}: Missing question text")
                        continue
                    
                    if not sample_answer:
                        errors.append(f"Row {row_num}: Missing sample answer")
                        continue
                    
                    # Parse rules (semicolon or pipe separated)
                    rules_text = row.get('rules', '').strip()
                    rules = []
                    if rules_text:
                        # Try different separators
                        if ';' in rules_text:
                            rules = [rule.strip() for rule in rules_text.split(';') if rule.strip()]
                        elif '|' in rules_text:
                            rules = [rule.strip() for rule in rules_text.split('|') if rule.strip()]
                        else:
                            # Single rule
                            rules = [rules_text] if rules_text else []
                    
                    # Create question
                    question_data = {
                        'question': question_text,
                        'sample_answer': sample_answer,
                        'marking_scheme': [{'text': rule, 'type': 'semantic'} for rule in rules],
                        'user_id': self.user_id,
                        'created_at': datetime.utcnow()
                    }
                    
                    result = self.db.questions.insert_one(question_data)
                    if result.inserted_id:
                        imported_count += 1
                    else:
                        errors.append(f"Row {row_num}: Failed to insert question")
                        
                except Exception as e:
                    errors.append(f"Row {row_num}: {str(e)}")
            
            if imported_count == 0:
                return False, "No questions were imported. Please check your CSV format.", errors
            
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
                        'question': question_data.get('question_text', ''),
                        'sample_answer': question_data.get('sample_answer', ''),
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
                        'student_name': row.get('student_name', ''),
                        'student_roll_no': row.get('student_roll_no', ''),
                        'student_ans': row.get('answer_text', ''),
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
                        'student_name': answer_data.get('student_name', ''),
                        'student_roll_no': answer_data.get('student_roll_no', ''),
                        'student_ans': answer_data.get('answer_text', ''),
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
                question_identifiers = []
                for i, qid in enumerate(test.get('question_ids', []), 1):
                    question = self.db.questions.find_one({'_id': ObjectId(qid), 'user_id': self.user_id})
                    if question:
                        question_text = question.get('question', '')[:50] + '...'
                        question_details.append(question_text)
                        question_identifiers.append(f"Q{i:03d}_{str(qid)[-6:]}")
                
                csv_data.append({
                    'test_id': str(test.get('_id', '')),
                    'test_name': test.get('test_name', ''),
                    'test_description': test.get('test_description', ''),
                    'questions': '; '.join(question_details),
                    'question_identifiers': '; '.join(question_identifiers),
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

    def export_test_with_questions_to_csv(self, test_id):
        """Export a specific test with detailed question information"""
        try:
            test = get_test_by_id(test_id, self.user_id)
            if not test:
                return False, "Test not found"
            
            # Get all questions for this test
            questions = []
            for qid in test.get('question_ids', []):
                question = self.db.questions.find_one({'_id': ObjectId(qid), 'user_id': self.user_id})
                if question:
                    questions.append(question)
            
            if not questions:
                return False, "No questions found for this test"
            
            # Create CSV with test info and question details
            csv_data = []
            
            # Test header row
            csv_data.append({
                'type': 'TEST_INFO',
                'test_id': str(test.get('_id', '')),
                'test_name': test.get('test_name', ''),
                'test_description': test.get('test_description', ''),
                'total_questions': len(questions),
                'created_at': test.get('created_at', '').strftime('%Y-%m-%d %H:%M:%S') if test.get('created_at') else ''
            })
            
            # Question rows
            for i, question in enumerate(questions, 1):
                csv_data.append({
                    'type': 'QUESTION',
                    'question_number': f"Q{i:03d}",
                    'question_identifier': f"Q{i:03d}_{str(question.get('_id', ''))[-6:]}",
                    'question_id': str(question.get('_id', '')),
                    'question_text': question.get('question', ''),
                    'sample_answer': question.get('sample_answer', ''),
                    'rules': '; '.join([r.get('text', '') for r in question.get('marking_scheme', [])]),
                    'rule_count': len(question.get('marking_scheme', [])),
                    'created_at': question.get('created_at', '').strftime('%Y-%m-%d %H:%M:%S') if question.get('created_at') else ''
                })
            
            output = io.StringIO()
            if csv_data:
                fieldnames = csv_data[0].keys()
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(csv_data)
            return True, output.getvalue()
        except Exception as e:
            return False, f"Error exporting test with questions: {str(e)}"

    def export_test_answers_to_csv(self, test_id=None):
        """Export test answers to CSV format with proper formatting"""
        try:
            test_answers = get_test_answers(self.user_id, test_id)
            if not test_answers:
                return False, "No test answers found to export"
            
            # Get test details if test_id provided
            test_name = "All Tests"
            test_questions = []
            if test_id:
                test = get_test_by_id(test_id, self.user_id)
                if test:
                    test_name = test.get('test_name', 'Unknown Test')
                    # Get questions for this test
                    for qid in test.get('question_ids', []):
                        question = self.db.questions.find_one({'_id': ObjectId(qid), 'user_id': self.user_id})
                        if question:
                            test_questions.append(question)
            
            csv_data = []
            for answer in test_answers:
                # Clean and format the data
                student_name = answer.get('student_name', '').strip()
                student_roll = answer.get('student_roll_no', '').strip()
                
                # Format creation date
                created_at = answer.get('created_at')
                if created_at:
                    try:
                        formatted_date = created_at.strftime('%Y-%m-%d %H:%M:%S')
                    except:
                        formatted_date = str(created_at)
                else:
                    formatted_date = ''
                
                row = {
                    'Test Name': test_name,
                    'Student Name': student_name,
                    'Student Roll No': student_roll,
                    'Submitted Date': formatted_date
                }
                
                # Add question answers
                question_answers = answer.get('question_answers', {})
                for i, question in enumerate(test_questions, 1):
                    answer_text = question_answers.get(str(question.get('_id', '')), '').strip()
                    row[f'Q{i:03d} Answer'] = answer_text
                
                csv_data.append(row)
            
            if not csv_data:
                return False, "No valid answers found to export"
            
            # Create CSV with proper formatting
            output = io.StringIO()
            
            # Get all possible fieldnames
            all_fieldnames = set()
            for row in csv_data:
                all_fieldnames.update(row.keys())
            
            fieldnames = ['Test Name', 'Student Name', 'Student Roll No', 'Submitted Date']
            
            # Add question fields in order
            max_questions = max(len(row) - len(fieldnames) for row in csv_data) if csv_data else 0
            for i in range(1, max_questions + 1):
                fieldnames.append(f'Q{i:03d} Answer')
            
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(csv_data)
            
            return True, output.getvalue()
            
        except Exception as e:
            return False, f"Error exporting test answers: {str(e)}"

    def export_test_grades_to_csv(self, test_id=None):
        """Export test grades to CSV format with proper formatting"""
        try:
            test_grades = get_test_grades(self.user_id, test_id)
            if not test_grades:
                return False, "No test grades found to export"
            
            # Get test details if test_id provided
            test_name = "All Tests"
            if test_id:
                test = get_test_by_id(test_id, self.user_id)
                if test:
                    test_name = test.get('test_name', 'Unknown Test')
            
            csv_data = []
            for grade in test_grades:
                # Clean and format the data
                student_name = grade.get('student_name', '').strip()
                student_roll = grade.get('student_roll_no', '').strip()
                
                # Format scores properly
                overall_score = grade.get('overall_score', 0)
                overall_percentage = grade.get('overall_percentage', '0%')
                overall_grade = grade.get('overall_grade', 'F')
                
                # Format creation date
                created_at = grade.get('created_at')
                if created_at:
                    try:
                        formatted_date = created_at.strftime('%Y-%m-%d %H:%M:%S')
                    except:
                        formatted_date = str(created_at)
                else:
                    formatted_date = ''
                
                row = {
                    'Test Name': test_name,
                    'Student Name': student_name,
                    'Student Roll No': student_roll,
                    'Overall Score': f"{overall_score:.2f}",
                    'Overall Percentage': overall_percentage,
                    'Overall Grade': overall_grade,
                    'Total Questions': grade.get('total_questions', 0),
                    'Answered Questions': grade.get('answered_questions', 0),
                    'Graded Date': formatted_date
                }
                
                # Add question-wise scores
                question_details = grade.get('question_details', [])
                for i, q_detail in enumerate(question_details, 1):
                    score = q_detail.get('score', 0) * 100
                    grade_letter = q_detail.get('grade', 'F')
                    
                    row[f'Q{i:03d} Score'] = f"{score:.1f}%"
                    row[f'Q{i:03d} Grade'] = grade_letter
                
                csv_data.append(row)
            
            if not csv_data:
                return False, "No valid grades found to export"
            
            # Create CSV with proper formatting
            output = io.StringIO()
            
            # Get all possible fieldnames
            all_fieldnames = set()
            for row in csv_data:
                all_fieldnames.update(row.keys())
            
            fieldnames = ['Test Name', 'Student Name', 'Student Roll No', 'Overall Score', 
                         'Overall Percentage', 'Overall Grade', 'Total Questions', 
                         'Answered Questions', 'Graded Date']
            
            # Add question fields in order
            max_questions = max(len(row) - len(fieldnames) for row in csv_data) if csv_data else 0
            for i in range(1, max_questions + 1):
                fieldnames.extend([f'Q{i:03d} Score', f'Q{i:03d} Grade'])
            
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(csv_data)
            
            return True, output.getvalue()
            
        except Exception as e:
            return False, f"Error exporting test grades: {str(e)}"

    def import_test_answers_from_csv(self, csv_content, test_id):
        """Import test answers from CSV format with improved error handling"""
        try:
            # Validate test exists
            test = get_test_by_id(test_id, self.user_id)
            if not test:
                return False, "Test not found or doesn't belong to you", []
            
            # Get test questions for validation
            test_questions = []
            for qid in test.get('question_ids', []):
                question = self.db.questions.find_one({'_id': ObjectId(qid), 'user_id': self.user_id})
                if question:
                    test_questions.append(question)
            
            if not test_questions:
                return False, "No questions found for this test", []
            
            # Parse CSV content
            csv_reader = csv.DictReader(csv_content.splitlines())
            
            # Validate CSV structure
            required_fields = ['Student Name', 'Student Roll No']
            
            if not csv_reader.fieldnames:
                return False, "Invalid CSV file: No headers found", []
            
            missing_fields = [field for field in required_fields if field not in csv_reader.fieldnames]
            if missing_fields:
                return False, f"Invalid CSV format: Missing required columns: {', '.join(missing_fields)}", []
            
            imported_count = 0
            errors = []
            
            for row_num, row in enumerate(csv_reader, 1):
                try:
                    # Validate required fields
                    student_name = row.get('Student Name', '').strip()
                    student_roll_no = row.get('Student Roll No', '').strip()
                    
                    if not student_name:
                        errors.append(f"Row {row_num}: Missing student name")
                        continue
                    
                    if not student_roll_no:
                        errors.append(f"Row {row_num}: Missing student roll number")
                        continue
                    
                    # Extract question answers from the row
                    question_answers = {}
                    answer_found = False
                    
                    for i, question in enumerate(test_questions, 1):
                        # Look for answer columns
                        answer_key = f'Q{i:03d} Answer'
                        if answer_key in row:
                            answer_text = row[answer_key].strip()
                            if answer_text and answer_text.lower() not in ['enter your answer for question', '']:
                                question_answers[str(question.get('_id', ''))] = answer_text
                                answer_found = True
                    
                    if not answer_found:
                        errors.append(f"Row {row_num}: No valid answers found for any questions")
                        continue
                    
                    # Save test answer
                    from core.db import save_test_answer
                    success, message = save_test_answer(
                        student_name,
                        student_roll_no,
                        test_id,
                        question_answers,
                        self.user_id
                    )
                    
                    if success:
                        imported_count += 1
                    else:
                        errors.append(f"Row {row_num}: {message}")
                        
                except Exception as e:
                    errors.append(f"Row {row_num}: {str(e)}")
            
            if imported_count == 0:
                return False, "No answers were imported. Please check your CSV format.", errors
            
            return True, f"Successfully imported {imported_count} test answers", errors
            
        except Exception as e:
            return False, f"Error importing test answers: {str(e)}", []

    def generate_test_answer_template_csv(self, test_id):
        """Generate a clean CSV template for test answers"""
        try:
            test = get_test_by_id(test_id, self.user_id)
            if not test:
                return False, "Test not found"
            
            # Get questions for this test
            questions = []
            for qid in test.get('question_ids', []):
                question = self.db.questions.find_one({'_id': ObjectId(qid), 'user_id': self.user_id})
                if question:
                    questions.append(question)
            
            if not questions:
                return False, "No questions found for this test"
            
            # Create clean template CSV
            csv_data = []
            
            # Column headers only
            headers = ['Student Name', 'Student Roll No']
            for i in range(1, len(questions) + 1):
                headers.append(f'Q{i:03d} Answer')
            
            csv_data.append(headers)
            
            # Example row with sample data
            example_row = ['John Doe', '2023001']
            for i in range(1, len(questions) + 1):
                example_row.append(f'Enter your answer for question {i} here')
            
            csv_data.append(example_row)
            
            # Create CSV with proper formatting
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerows(csv_data)
            
            return True, output.getvalue()
            
        except Exception as e:
            return False, f"Error generating test answer template: {str(e)}" 