import streamlit as st
from core.db import save_question, save_student_answer, get_questions, save_grades, clear_grades, detect_rule_type, get_grade_thresholds, save_grade_thresholds, get_db, get_student_answers, get_grades, save_test, get_tests, get_test_by_id, delete_test, save_test_answer, get_test_answers, save_test_grades, get_test_grades, clear_test_grades
from services.grading_service import grade_all
from services.test_grading_service import grade_test, get_test_statistics
from services.auth_service import create_user, authenticate_user, create_session_token, verify_session_token, get_user_by_id, refresh_session_token, get_session_info
from services.import_export_service import ImportExportService
from bson.objectid import ObjectId
import json
import pickle
import base64
import time
import os
import tempfile
import csv
import io
import zipfile
from datetime import datetime

st.set_page_config(page_title="Scorix", layout="wide")

# Session file path
SESSION_FILE = os.path.join(tempfile.gettempdir(), "semantic_grader_session.pkl")

def save_session_to_file(session_data):
    """Save session data to a temporary file"""
    try:
        with open(SESSION_FILE, 'wb') as f:
            pickle.dump(session_data, f)
        return True
    except Exception:
        return False

def load_session_from_file():
    """Load session data from temporary file"""
    try:
        if os.path.exists(SESSION_FILE):
            with open(SESSION_FILE, 'rb') as f:
                session_data = pickle.load(f)
            return session_data
    except Exception:
        pass
    return None

def clear_session_file():
    """Clear session file"""
    try:
        if os.path.exists(SESSION_FILE):
            os.remove(SESSION_FILE)
    except Exception:
        pass

def encode_session_data(data):
    """Encode session data for storage"""
    try:
        serialized = pickle.dumps(data)
        encoded = base64.b64encode(serialized).decode('utf-8')
        return encoded
    except Exception:
        return None

def decode_session_data(encoded_data):
    """Decode session data from storage"""
    try:
        if not encoded_data:
            return None
        decoded = base64.b64decode(encoded_data.encode('utf-8'))
        data = pickle.loads(decoded)
        return data
    except Exception:
        return None

def get_persistent_session():
    """Get session data from persistent storage with multiple fallback methods"""
    
    # Method 1: Direct session state access
    try:
        if hasattr(st, 'session_state'):
            session_data = st.session_state.get('persistent_session', None)
            if session_data:
                return session_data
    except Exception:
        pass
    
    # Method 2: Internal session state access
    try:
        if hasattr(st, '_session_state') and hasattr(st._session_state, '_session_state'):
            session_data = st._session_state._session_state.get('persistent_session', None)
            if session_data:
                return session_data
    except Exception:
        pass
    
    # Method 3: File-based storage (most reliable)
    try:
        file_session = load_session_from_file()
        if file_session:
            return file_session
    except Exception:
        pass
    
    # Method 4: Query params (for backward compatibility)
    try:
        if hasattr(st, 'query_params'):
            encoded_data = st.query_params.get('session', None)
            if encoded_data:
                decoded_data = decode_session_data(encoded_data)
                if decoded_data:
                    return decoded_data
    except Exception:
        pass
    
    return {}

def set_persistent_session(session_data):
    """Set session data in persistent storage with multiple methods"""
    
    # Method 1: File-based storage (most reliable)
    try:
        save_session_to_file(session_data)
    except Exception:
        pass
    
    # Method 2: Direct session state access
    try:
        if hasattr(st, 'session_state'):
            st.session_state['persistent_session'] = session_data
    except Exception:
        pass
    
    # Method 3: Internal session state access
    try:
        if hasattr(st, '_session_state') and hasattr(st._session_state, '_session_state'):
            st._session_state._session_state['persistent_session'] = session_data
    except Exception:
        pass
    
    # Method 4: Query params as fallback
    try:
        if hasattr(st, 'query_params'):
            encoded_data = encode_session_data(session_data)
            if encoded_data:
                st.query_params['session'] = encoded_data
    except Exception:
        pass

def clear_query_params():
    """Clear session-related query parameters to keep URL clean"""
    try:
        if hasattr(st, 'query_params') and 'session' in st.query_params:
            current_params = st.query_params.to_dict()
            if 'session' in current_params:
                del current_params['session']
                st.query_params.from_dict(current_params)
    except Exception:
        pass

def migrate_query_params_to_session():
    """Migrate any existing session data from query params to session state"""
    try:
        if hasattr(st, 'query_params') and 'session' in st.query_params:
            encoded_data = st.query_params.get('session')
            if encoded_data:
                decoded_data = decode_session_data(encoded_data)
                if decoded_data:
                    set_persistent_session(decoded_data)
                    clear_query_params()
                    return True
    except Exception:
        pass
    return False

def initialize_session():
    """Initialize session from persistent storage on app startup"""
    
    # Check if we already have a session in current state
    if st.session_state.token and st.session_state.user:
        return
    
    # Try to restore from persistent storage
    persistent_session = get_persistent_session()
    if persistent_session.get('token'):
        payload = verify_session_token(persistent_session['token'])
        if payload:
            st.session_state.token = persistent_session['token']
            if persistent_session.get('user'):
                st.session_state.user = persistent_session['user']
            else:
                # Fetch user data from database
                user = get_user_by_id(ObjectId(payload['user_id']))
                if user:
                    st.session_state.user = user
        else:
            # Clear invalid persistent session
            set_persistent_session({})
            clear_session_file()

def check_auth():
    """Check if user is authenticated with persistent session"""
    
    # First check current session state
    if st.session_state.token:
        payload = verify_session_token(st.session_state.token)
        if payload:
            # If user data is missing, fetch it from database
            if not st.session_state.user and payload.get('user_id'):
                user = get_user_by_id(ObjectId(payload['user_id']))
                if user:
                    st.session_state.user = user
            return True
        else:
            # Try to refresh the token
            refreshed_token = refresh_session_token(st.session_state.token)
            if refreshed_token:
                st.session_state.token = refreshed_token
                save_session()
                return True
    
    # Check persistent session
    persistent_session = get_persistent_session()
    if persistent_session.get('token'):
        payload = verify_session_token(persistent_session['token'])
        if payload:
            # Restore session from persistent storage
            st.session_state.token = persistent_session['token']
            if persistent_session.get('user'):
                st.session_state.user = persistent_session['user']
            else:
                # Fetch user data from database
                user = get_user_by_id(ObjectId(payload['user_id']))
                if user:
                    st.session_state.user = user
                    # Update persistent session
                    persistent_session['user'] = user
                    set_persistent_session(persistent_session)
            return True
        else:
            # Try to refresh the persistent token
            refreshed_token = refresh_session_token(persistent_session['token'])
            if refreshed_token:
                st.session_state.token = refreshed_token
                if persistent_session.get('user'):
                    st.session_state.user = persistent_session['user']
                else:
                    # Fetch user data from database
                    session_info = get_session_info(refreshed_token)
                    if session_info and session_info.get('user_id'):
                        user = get_user_by_id(ObjectId(session_info['user_id']))
                        if user:
                            st.session_state.user = user
                            persistent_session['user'] = user
                
                # Update persistent session with new token
                persistent_session['token'] = refreshed_token
                set_persistent_session(persistent_session)
                save_session()
                return True
    
    return False

def save_session():
    """Save current session to persistent storage"""
    if st.session_state.token and st.session_state.user:
        session_data = {
            'token': st.session_state.token,
            'user': st.session_state.user
        }
        set_persistent_session(session_data)
        clear_query_params()

def clear_session():
    """Clear both current and persistent session"""
    st.session_state.user = None
    st.session_state.token = None
    set_persistent_session({})
    clear_query_params()
    clear_session_file()

def auto_refresh_session():
    """Automatically refresh session if needed"""
    if st.session_state.token:
        session_info = get_session_info(st.session_state.token)
        if session_info and not session_info['is_expired']:
            # If session expires in less than 10 minutes, refresh it
            time_remaining = int(session_info['expires_at'] - time.time())
            if time_remaining < 600:  # 10 minutes
                refreshed_token = refresh_session_token(st.session_state.token)
                if refreshed_token:
                    st.session_state.token = refreshed_token
                    save_session()
                    return True
    return False

def login_page():
    """Login page"""
    st.title("🔐 Login to Scorix")
    
    # Check if there's a recoverable session
    persistent_session = get_persistent_session()
    if persistent_session.get('token'):
        session_info = get_session_info(persistent_session['token'])
        if session_info and not session_info['is_expired']:
            st.info("🔍 Found an active session. You can continue with your previous session.")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Continue Previous Session"):
                    st.session_state.token = persistent_session['token']
                    if persistent_session.get('user'):
                        st.session_state.user = persistent_session['user']
                    else:
                        user = get_user_by_id(ObjectId(session_info['user_id']))
                        if user:
                            st.session_state.user = user
                    save_session()
                    clear_query_params()
                    st.success("Session restored!")
                    st.rerun()
            with col2:
                if st.button("🗑️ Clear Previous Session"):
                    set_persistent_session({})
                    clear_query_params()
                    clear_session_file()
                    st.success("Previous session cleared!")
                    st.rerun()
            st.divider()
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        
        if submitted:
            if username and password:
                user, message = authenticate_user(username, password)
                if user:
                    st.session_state.user = user
                    st.session_state.token = create_session_token(user["_id"], user["username"])
                    # Save session persistently
                    save_session()
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error(message)
            else:
                st.error("Please enter both username and password")
    
    st.divider()
    st.write("Don't have an account?")
    if st.button("Sign Up"):
        st.session_state.show_signup = True
        st.rerun()

def signup_page():
    """Signup page"""
    st.title("📝 Create Account")
    
    with st.form("signup_form"):
        username = st.text_input("Username (min 3 characters)")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        submitted = st.form_submit_button("Create Account")
        
        if submitted:
            if not username or len(username) < 3:
                st.error("Username must be at least 3 characters long")
            elif not email or "@" not in email:
                st.error("Please enter a valid email address")
            elif not password or len(password) < 6:
                st.error("Password must be at least 6 characters long")
            elif password != confirm_password:
                st.error("Passwords do not match")
            else:
                success, message = create_user(username, email, password)
                if success:
                    st.success("Account created successfully! Please login.")
                    st.session_state.show_signup = False
                    st.rerun()
                else:
                    st.error(message)
    
    st.divider()
    st.write("Already have an account?")
    if st.button("Login"):
        st.session_state.show_signup = False
        st.rerun()

def logout():
    """Logout function"""
    clear_session()
    st.rerun()

def main_app():
    """Main application after authentication"""
    # Header with user info and logout
    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
    with col1:
        st.title("🎓 Scorix")
    with col2:
        st.write(f"**Welcome, {st.session_state.user['username']}!**")
        
        # Show session status
        session_info = get_session_info(st.session_state.token)
        if session_info:
            if session_info['is_expired']:
                st.error("⚠️ Session expired")
            else:
                # Calculate time remaining
                time_remaining = int(session_info['expires_at'] - time.time())
                if time_remaining > 3600:  # More than 1 hour
                    st.success(f"🟢 Session active ({time_remaining//3600}h {(time_remaining%3600)//60}m)")
                elif time_remaining > 300:  # More than 5 minutes
                    st.warning(f"🟡 Session expires in {time_remaining//60}m")
                else:
                    st.error(f"🔴 Session expires in {time_remaining}s")
    
    with col3:
        if st.button("🔄 Refresh Session"):
            refreshed_token = refresh_session_token(st.session_state.token)
            if refreshed_token:
                st.session_state.token = refreshed_token
                save_session()
                st.success("Session refreshed!")
                st.rerun()
            else:
                st.error("Failed to refresh session")
    
    with col4:
        if st.button("🚪 Logout"):
            logout()
    
    # Navigation
    page = st.sidebar.selectbox("Navigation", ["Create Question", "Test Management", "Upload Answers", "Grade Settings", "Run Grading", "Data Management"])
    
    if page == "Create Question":
        st.header("📝 Create a New Question")
        question = st.text_area("Enter the question text:")
        sample_answer = st.text_area("Enter the sample answer:")

        st.subheader("📋 Marking Rules")
        st.info("""
        💡 **Rule Types (Auto-detected):**
        - 🔍 **exact_phrase**: For formulas and specific mentions (e.g., "mentions F = ma")
        - 🔑 **contains_keywords**: For specific terms that must be present (e.g., "contains protons, electrons")
        - 🧠 **semantic**: For conceptual understanding (e.g., "explains the relationship")
        """)
        
        rules = []
        rule_count = st.number_input("How many marking rules?", min_value=1, step=1)
        for i in range(rule_count):
            rule = st.text_input(f"Rule {i + 1}")
            if rule:
                # Show rule type using dynamic detection
                rule_type = detect_rule_type(rule)
                icons = {
                    "exact_phrase": "🔍",
                    "contains_keywords": "🔑", 
                    "semantic": "🧠"
                }
                st.caption(f"Type: {rule_type} {icons.get(rule_type, '🧠')}")
            rules.append(rule)

        if st.button("Save Question"):
            success, message = save_question(question, sample_answer, rules, st.session_state.user["_id"])
            if success:
                st.success(f"✅ {message}")
                # Clear cached grading results when new question is added
                if 'grading_results' in st.session_state:
                    del st.session_state.grading_results
            else:
                st.error(f"❌ {message}")

    elif page == "Test Management":
        st.header("📋 Test Management")
        
        # Create tabs for different test operations
        tab1, tab2, tab3, tab4 = st.tabs(["📝 Create Test", "📊 Test Overview", "📤 Upload Test Answers", "🎯 Grade Tests"])
        
        with tab1:
            st.subheader("📝 Create a New Test")
            
            # Get available questions
            questions = get_questions(st.session_state.user["_id"])
            if not questions:
                st.warning("⚠️ No questions found. Please create questions first before creating a test.")
            else:
                with st.form("create_test_form"):
                    test_name = st.text_input("Test Name", placeholder="e.g., Physics Midterm Exam")
                    test_description = st.text_area("Test Description (Optional)", placeholder="Brief description of the test...")
                    
                    st.subheader("📋 Select Questions for this Test")
                    st.info("💡 Select the questions you want to include in this test. Students will need to answer all selected questions.")
                    
                    # Display questions with checkboxes
                    selected_questions = []
                    for i, question in enumerate(questions):
                        question_text = question["question"]
                        question_id = str(question["_id"])
                        
                        # Create a unique key for each checkbox
                        checkbox_key = f"question_{question_id}"
                        if st.checkbox(f"**Q{i+1}:** {question_text[:100]}{'...' if len(question_text) > 100 else ''}", key=checkbox_key):
                            selected_questions.append(question_id)
                    
                    st.write(f"**Selected Questions:** {len(selected_questions)}")
                    
                    submitted = st.form_submit_button("💾 Create Test")
                    
                    if submitted:
                        if not test_name:
                            st.error("❌ Test name is required")
                        elif not selected_questions:
                            st.error("❌ Please select at least one question")
                        else:
                            success, message = save_test(test_name, test_description, selected_questions, st.session_state.user["_id"])
                            if success:
                                st.success(f"✅ {message}")
                                st.rerun()
                            else:
                                st.error(f"❌ {message}")
        
        with tab2:
            st.subheader("📊 Test Overview")
            
            tests = get_tests(st.session_state.user["_id"])
            if not tests:
                st.info("ℹ️ No tests created yet. Create your first test in the 'Create Test' tab.")
            else:
                # Display tests in a table format
                for test in tests:
                    test_id = str(test["_id"])
                    test_name = test["test_name"]
                    test_description = test.get("test_description", "")
                    question_count = len(test.get("question_ids", []))
                    created_at = test.get("created_at", "")
                    
                    # Get test statistics
                    test_answers = get_test_answers(st.session_state.user["_id"], test_id)
                    test_grades = get_test_grades(st.session_state.user["_id"], test_id)
                    
                    with st.expander(f"📋 {test_name} ({question_count} questions)", expanded=False):
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            st.write(f"**Description:** {test_description or 'No description'}")
                            st.write(f"**Created:** {created_at.strftime('%Y-%m-%d %H:%M:%S') if created_at else 'Unknown'}")
                            st.write(f"**Status:** {'🟢 Active' if test.get('is_active', True) else '🔴 Inactive'}")
                        
                        with col2:
                            st.metric("📝 Submissions", len(test_answers))
                            st.metric("📊 Graded", len(test_grades))
                        
                        # Show questions in this test
                        st.subheader("📋 Questions in this Test")
                        question_ids = test.get("question_ids", [])
                        for i, qid in enumerate(question_ids, 1):
                            question = next((q for q in questions if str(q["_id"]) == qid), None)
                            if question:
                                st.write(f"**Q{i}:** {question['question'][:100]}{'...' if len(question['question']) > 100 else ''}")
                        
                        # Action buttons
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            # Handle delete with confirmation using session state
                            delete_key = f"delete_{test_id}"
                            confirm_key = f"confirm_delete_{test_id}"
                            
                            if delete_key not in st.session_state:
                                st.session_state[delete_key] = False
                            if confirm_key not in st.session_state:
                                st.session_state[confirm_key] = False
                            
                            if not st.session_state[delete_key]:
                                if st.button("🗑️ Delete Test", key=f"btn_{delete_key}"):
                                    st.session_state[delete_key] = True
                                    st.rerun()
                            else:
                                st.warning("⚠️ Are you sure you want to delete this test?")
                                col_confirm1, col_confirm2 = st.columns(2)
                                with col_confirm1:
                                    if st.button("✅ Yes, Delete", key=f"btn_{confirm_key}"):
                                        st.info(f"Deleting test {test_id}...")
                                        success, message = delete_test(test_id, st.session_state.user["_id"])
                                        if success:
                                            st.success(f"✅ {message}")
                                            # Clear session state
                                            st.session_state[delete_key] = False
                                            st.session_state[confirm_key] = False
                                            st.rerun()
                                        else:
                                            st.error(f"❌ {message}")
                                            st.session_state[delete_key] = False
                                            st.session_state[confirm_key] = False
                                with col_confirm2:
                                    if st.button("❌ Cancel", key=f"btn_cancel_{test_id}"):
                                        st.session_state[delete_key] = False
                                        st.session_state[confirm_key] = False
                                        st.rerun()
                        
                        with col2:
                            if len(test_answers) > 0:
                                if st.button("📊 View Results", key=f"results_{test_id}"):
                                    st.session_state.selected_test_id = test_id
                                    st.session_state.show_test_results = True
                                    st.rerun()
                        
                        with col3:
                            if len(test_answers) > 0 and len(test_grades) == 0:
                                if st.button("🎯 Grade Test", key=f"grade_{test_id}"):
                                    st.session_state.selected_test_id = test_id
                                    st.session_state.grade_test = True
                                    st.rerun()
        
        with tab3:
            st.subheader("📤 Upload Test Answers")
            
            tests = get_tests(st.session_state.user["_id"])
            if not tests:
                st.warning("⚠️ No tests found. Please create a test first.")
            else:
                # Select test
                test_options = {test["test_name"]: str(test["_id"]) for test in tests}
                selected_test_name = st.selectbox(
                    "Select a test:",
                    options=list(test_options.keys()),
                    help="Choose which test to upload answers for"
                )
                selected_test_id = test_options[selected_test_name]
                
                # Get test details
                test = get_test_by_id(selected_test_id, st.session_state.user["_id"])
                if test:
                    st.info(f"📋 **Test:** {test['test_name']}")
                    st.write(f"**Questions:** {len(test.get('question_ids', []))}")
                    
                    # Manual entry form
                    st.subheader("📝 Manual Entry")
                    with st.form("manual_test_answer_form"):
                        student_name = st.text_input("Student Name")
                        student_roll_no = st.text_input("Student Roll No")
                        
                        st.subheader("📝 Answer Each Question")
                        question_answers = {}
                        question_ids = test.get("question_ids", [])
                        
                        for i, qid in enumerate(question_ids, 1):
                            question = next((q for q in questions if str(q["_id"]) == qid), None)
                            if question:
                                question_text = question["question"]
                                answer = st.text_area(
                                    f"Q{i}: {question_text[:100]}{'...' if len(question_text) > 100 else ''}",
                                    max_chars=4000,
                                    key=f"test_answer_{qid}"
                                )
                                question_answers[qid] = answer
                        
                        submitted = st.form_submit_button("💾 Submit Test Answer")
                        
                        if submitted:
                            if not student_name or not student_roll_no:
                                st.error("❌ Student name and roll number are required")
                            else:
                                success, message = save_test_answer(
                                    student_name, student_roll_no, selected_test_id, 
                                    question_answers, st.session_state.user["_id"]
                                )
                                if success:
                                    st.success(f"✅ {message}")
                                    st.rerun()
                                else:
                                    st.error(f"❌ {message}")
                    
                    # CSV upload
                    st.subheader("📤 CSV Upload")
                    st.info("💡 Upload a CSV file with student answers for this test.")
                    
                    uploaded_file = st.file_uploader(
                        "Upload Test Answers CSV",
                        type=["csv"],
                        help="Upload a CSV file containing test answers"
                    )
                    
                    if uploaded_file and st.button("📥 Import Test Answers"):
                        with st.spinner("Importing test answers..."):
                            try:
                                file_content = uploaded_file.read().decode('utf-8')
                                import_export_service = ImportExportService(st.session_state.user["_id"])
                                success, message, errors = import_export_service.import_test_answers_from_csv(file_content, selected_test_id)
                                if success:
                                    st.success(f"✅ {message}")
                                    if errors:
                                        st.warning(f"⚠️ {len(errors)} errors occurred:")
                                        for error in errors[:5]:
                                            st.write(f"• {error}")
                                        if len(errors) > 5:
                                            st.write(f"• ... and {len(errors) - 5} more errors")
                                    st.rerun()
                                else:
                                    st.error(f"❌ {message}")
                            except Exception as e:
                                st.error(f"❌ Import failed: {str(e)}")
        
        with tab4:
            st.subheader("🎯 Grade Tests")
            
            tests = get_tests(st.session_state.user["_id"])
            if not tests:
                st.warning("⚠️ No tests found. Please create a test first.")
            else:
                # Select test to grade
                test_options = {test["test_name"]: str(test["_id"]) for test in tests}
                selected_test_name = st.selectbox(
                    "Select a test to grade:",
                    options=list(test_options.keys()),
                    help="Choose which test to grade"
                )
                selected_test_id = test_options[selected_test_name]
                
                # Get test details and answers
                test = get_test_by_id(selected_test_id, st.session_state.user["_id"])
                test_answers = get_test_answers(st.session_state.user["_id"], selected_test_id)
                test_grades = get_test_grades(st.session_state.user["_id"], selected_test_id)
                
                if test:
                    st.info(f"📋 **Test:** {test['test_name']}")
                    st.write(f"**Questions:** {len(test.get('question_ids', []))}")
                    st.write(f"**Submissions:** {len(test_answers)}")
                    st.write(f"**Already Graded:** {len(test_grades)}")
                    
                    if len(test_answers) == 0:
                        st.warning("⚠️ No test answers found. Please upload answers first.")
                    else:
                        debug_mode = st.checkbox("Enable Debug Mode", help="Show detailed analysis of grading process")
                        
                        if st.button("🎯 Grade Test & Save Results"):
                            with st.spinner("Running test grading analysis..."):
                                # Clear existing grades for this test
                                clear_success, clear_message = clear_test_grades(st.session_state.user["_id"], selected_test_id)
                                if not clear_success:
                                    st.warning(f"Warning: {clear_message}")
                                
                                # Run grading
                                results = grade_test(selected_test_id, st.session_state.user["_id"], debug=debug_mode)
                                
                                if results:
                                    # Save grades
                                    save_success, save_message = save_test_grades(results, st.session_state.user["_id"])
                                    if save_success:
                                        st.success(f"✅ {save_message}")
                                        st.rerun()
                                    else:
                                        st.error(f"❌ {save_message}")
                                else:
                                    st.warning("⚠️ No results to save. Please ensure you have test answers.")
                        
                        # Show test statistics if available
                        if len(test_grades) > 0:
                            st.subheader("📊 Test Statistics")
                            stats = get_test_statistics(selected_test_id, st.session_state.user["_id"])
                            if stats:
                                col1, col2, col3, col4 = st.columns(4)
                                with col1:
                                    st.metric("Total Students", stats["total_students"])
                                with col2:
                                    st.metric("Average Score", f"{stats['average_percentage']:.1f}%")
                                with col3:
                                    st.metric("Highest Score", f"{stats['max_score']*100:.1f}%")
                                with col4:
                                    st.metric("Lowest Score", f"{stats['min_score']*100:.1f}%")
                                
                                # Grade distribution
                                st.subheader("📈 Grade Distribution")
                                grade_dist = stats["grade_distribution"]
                                for grade in ["A", "B", "C", "D", "F"]:
                                    count = grade_dist.get(grade, 0)
                                    percentage = (count / stats["total_students"]) * 100 if stats["total_students"] > 0 else 0
                                    st.write(f"**Grade {grade}:** {count} students ({percentage:.1f}%)")
        
        # Handle test results view
        if st.session_state.get('show_test_results', False) and st.session_state.get('selected_test_id'):
            test_id = st.session_state.selected_test_id
            test = get_test_by_id(test_id, st.session_state.user["_id"])
            test_grades = get_test_grades(st.session_state.user["_id"], test_id)
            
            if test and test_grades:
                st.subheader(f"📊 Test Results: {test['test_name']}")
                
                # Display results in a table
                for grade in test_grades:
                    student_name = grade.get("student_name", "Unknown")
                    student_roll = grade.get("student_roll_no", "Unknown")
                    overall_score = grade.get("overall_percentage", "0%")
                    overall_grade = grade.get("overall_grade", "F")
                    
                    with st.expander(f"{student_name} ({student_roll}) - {overall_score} - Grade {overall_grade}", expanded=False):
                        st.write(f"**Overall Score:** {overall_score}")
                        st.write(f"**Overall Grade:** {overall_grade}")
                        st.write(f"**Questions Answered:** {grade.get('answered_questions', 0)}/{grade.get('total_questions', 0)}")
                        
                        # Show question-wise breakdown
                        st.subheader("📝 Question-wise Breakdown")
                        question_details = grade.get("question_details", [])
                        for i, q_detail in enumerate(question_details, 1):
                            score = q_detail.get("score", 0) * 100
                            q_grade = q_detail.get("grade", "F")
                            st.write(f"**Q{i}:** {score:.1f}% (Grade {q_grade})")
                
                if st.button("🔙 Back to Test Management"):
                    st.session_state.show_test_results = False
                    st.session_state.selected_test_id = None
                    st.rerun()

    elif page == "Upload Answers":
        st.header("📤 Upload Student Answers")
        questions = get_questions(st.session_state.user["_id"])
        
        if not questions:
            st.warning("No questions found. Please create a question first.")
            return
            
        question_titles = [q["question"] for q in questions]
        selected_index = st.selectbox("Select a question:", range(len(question_titles)), format_func=lambda i: question_titles[i])

        selected_question_id = str(questions[selected_index]["_id"])

        # Standards/info box for answer submission
        st.info("""
        **Answer Submission Standards:**
        - **Maximum answer length:** 4,000 characters (about 600–800 words)
        - **Matching criteria:**
            - 🔍 *Exact phrases*: Include any required formulas or specific wording.
            - 🔑 *Keywords*: Make sure to mention all required terms.
            - 🧠 *Semantic understanding*: Clearly explain concepts and relationships.
        - **Assessment uncertainty:** Automated grading is not perfect. Borderline or ambiguous answers may require manual review.
        - **General standards:**
            - Be clear, concise, and relevant.
            - Address all parts of the question.
            - Avoid unnecessary information.
        """)

        with st.form(key="answer_form"):
            name = st.text_input("Student Name")
            roll_no = st.text_input("Student Roll No")
            answer = st.text_area("Student Answer", max_chars=4000)
            submitted = st.form_submit_button("Submit Answer")

        if submitted:
            success, message = save_student_answer(name, roll_no, answer, selected_question_id, st.session_state.user["_id"])
            if success:
                st.success(f"✅ {message}")
                # Clear cached grading results when new answer is added
                if 'grading_results' in st.session_state:
                    del st.session_state.grading_results
            else:
                st.error(f"❌ {message}")

    elif page == "Grade Settings":
        st.header("📋 Grade Settings")
        
        st.info("""
        🎯 **Customize Grade Thresholds:**
        Set the minimum percentage required for each grade level.
        Changes will apply to all future grading operations.
        """)
        
        # Get current grade thresholds
        current_thresholds = get_grade_thresholds(st.session_state.user["_id"])
        
        # Display current settings
        st.subheader("📊 Current Grade Thresholds")
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("A Grade", f"≥ {current_thresholds['A']}%")
        with col2:
            st.metric("B Grade", f"≥ {current_thresholds['B']}%")
        with col3:
            st.metric("C Grade", f"≥ {current_thresholds['C']}%")
        with col4:
            st.metric("D Grade", f"≥ {current_thresholds['D']}%")
        with col5:
            st.metric("F Grade", f"< {current_thresholds['D']}%")
        
        st.divider()
        
        # Grade threshold input form
        st.subheader("⚙️ Update Grade Thresholds")
        
        with st.form("grade_thresholds_form"):
            st.write("**Set minimum percentage for each grade:**")
            
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                a_threshold = st.number_input(
                    "A Grade (%)", 
                    min_value=0, 
                    max_value=100, 
                    value=current_thresholds['A'],
                    help="Minimum percentage for A grade"
                )
            
            with col2:
                b_threshold = st.number_input(
                    "B Grade (%)", 
                    min_value=0, 
                    max_value=100, 
                    value=current_thresholds['B'],
                    help="Minimum percentage for B grade"
                )
            
            with col3:
                c_threshold = st.number_input(
                    "C Grade (%)", 
                    min_value=0, 
                    max_value=100, 
                    value=current_thresholds['C'],
                    help="Minimum percentage for C grade"
                )
            
            with col4:
                d_threshold = st.number_input(
                    "D Grade (%)", 
                    min_value=0, 
                    max_value=100, 
                    value=current_thresholds['D'],
                    help="Minimum percentage for D grade"
                )
            
            with col5:
                st.write("**F Grade**")
                st.write(f"< {d_threshold}%")
            
            # Validation
            thresholds_valid = True
            if a_threshold <= b_threshold:
                st.error("❌ A grade threshold must be higher than B grade threshold")
                thresholds_valid = False
            if b_threshold <= c_threshold:
                st.error("❌ B grade threshold must be higher than C grade threshold")
                thresholds_valid = False
            if c_threshold <= d_threshold:
                st.error("❌ C grade threshold must be higher than D grade threshold")
                thresholds_valid = False
            
            # Preview new thresholds
            if thresholds_valid:
                new_thresholds = {
                    "A": a_threshold,
                    "B": b_threshold,
                    "C": c_threshold,
                    "D": d_threshold,
                    "F": 0
                }
                
                st.subheader("👀 Preview New Thresholds")
                preview_col1, preview_col2, preview_col3, preview_col4, preview_col5 = st.columns(5)
                
                with preview_col1:
                    st.metric("A Grade", f"≥ {new_thresholds['A']}%", delta=f"{new_thresholds['A'] - current_thresholds['A']:+d}%")
                with preview_col2:
                    st.metric("B Grade", f"≥ {new_thresholds['B']}%", delta=f"{new_thresholds['B'] - current_thresholds['B']:+d}%")
                with preview_col3:
                    st.metric("C Grade", f"≥ {new_thresholds['C']}%", delta=f"{new_thresholds['C'] - current_thresholds['C']:+d}%")
                with preview_col4:
                    st.metric("D Grade", f"≥ {new_thresholds['D']}%", delta=f"{new_thresholds['D'] - current_thresholds['D']:+d}%")
                with preview_col5:
                    st.metric("F Grade", f"< {new_thresholds['D']}%")
            
            submitted = st.form_submit_button("💾 Save Grade Thresholds", disabled=not thresholds_valid)
            
            if submitted and thresholds_valid:
                success, message = save_grade_thresholds(new_thresholds, st.session_state.user["_id"])
                if success:
                    st.success(f"✅ {message}")
                    # Clear cached grading results when thresholds change
                    if 'grading_results' in st.session_state:
                        del st.session_state.grading_results
                    st.rerun()
                else:
                    st.error(f"❌ {message}")
        
        # Quick preset buttons
        st.divider()
        st.subheader("🚀 Quick Presets")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📚 Standard (85/70/55/40)"):
                standard_thresholds = {"A": 85, "B": 70, "C": 55, "D": 40, "F": 0}
                success, message = save_grade_thresholds(standard_thresholds, st.session_state.user["_id"])
                if success:
                    st.success(f"✅ {message}")
                    st.rerun()
                else:
                    st.error(f"❌ {message}")
        
        with col2:
            if st.button("🎯 Strict (90/80/70/60)"):
                strict_thresholds = {"A": 90, "B": 80, "C": 70, "D": 60, "F": 0}
                success, message = save_grade_thresholds(strict_thresholds, st.session_state.user["_id"])
                if success:
                    st.success(f"✅ {message}")
                    st.rerun()
                else:
                    st.error(f"❌ {message}")
        
        with col3:
            if st.button("📖 Lenient (80/65/50/35)"):
                lenient_thresholds = {"A": 80, "B": 65, "C": 50, "D": 35, "F": 0}
                success, message = save_grade_thresholds(lenient_thresholds, st.session_state.user["_id"])
                if success:
                    st.success(f"✅ {message}")
                    st.rerun()
                else:
                    st.error(f"❌ {message}")

    elif page == "Run Grading":
        st.header("🎯 Run Semantic Grading")
        
        st.info("""
        🔧 **Dynamic Hybrid Matching System:**
        - 🔍 **Exact Phrase**: Automatically extracts and matches specific content
        - 🔑 **Keyword Matching**: Uses lemmatization to match important terms dynamically
        - 🧠 **Semantic**: Uses embeddings for conceptual understanding
        """)
        
        # Display current grade thresholds
        current_thresholds = get_grade_thresholds(st.session_state.user["_id"])
        st.subheader("📊 Current Grade Thresholds")
        threshold_col1, threshold_col2, threshold_col3, threshold_col4, threshold_col5 = st.columns(5)
        
        with threshold_col1:
            st.metric("A Grade", f"≥ {current_thresholds['A']}%")
        with threshold_col2:
            st.metric("B Grade", f"≥ {current_thresholds['B']}%")
        with threshold_col3:
            st.metric("C Grade", f"≥ {current_thresholds['C']}%")
        with threshold_col4:
            st.metric("D Grade", f"≥ {current_thresholds['D']}%")
        with threshold_col5:
            st.metric("F Grade", f"< {current_thresholds['D']}%")
        
        st.info("💡 **Tip:** You can customize these thresholds in the 'Grade Settings' page.")
        
        debug_mode = st.checkbox("Enable Debug Mode", help="Show detailed analysis of grading process")
        
        # Use session state to store grading results
        if 'grading_results' not in st.session_state:
            st.session_state.grading_results = None
        
        if st.button("Run Grading & Save to DB"):
            with st.spinner("Running grading analysis..."):
                # Clear existing grades
                clear_success, clear_message = clear_grades(st.session_state.user["_id"])
                if not clear_success:
                    st.warning(f"Warning: {clear_message}")
                
                # Run grading
                results = grade_all(debug=debug_mode, user_id=st.session_state.user["_id"])
                
                if results:
                    # Save grades
                    save_success, save_message = save_grades(results, st.session_state.user["_id"])
                    if save_success:
                        st.success(f"✅ {save_message}")
                        st.session_state.grading_results = results
                    else:
                        st.error(f"❌ {save_message}")
                else:
                    st.warning("⚠️ No results to save. Please ensure you have questions and student answers.")
                    st.session_state.grading_results = []
        
        st.divider()
        st.subheader("📚 Questions and Student Answers Overview")
        
        # Get questions and their associated data
        questions = get_questions(st.session_state.user["_id"])
        answers = get_student_answers(st.session_state.user["_id"])
        grades = get_grades(st.session_state.user["_id"])
        
        if not questions:
            st.info("ℹ️ No questions found. Create a question first to see student answers and grades.")
        else:
            # Add dropdown to select question
            question_options = {q["question"][:80] + ("..." if len(q["question"]) > 80 else ""): str(q["_id"]) for q in questions}
            selected_question_text = st.selectbox(
                "Select a question to view:",
                options=list(question_options.keys()),
                help="Choose which question's answers and grades to display"
            )
            selected_question_id = question_options[selected_question_text]
            
            # Only show the selected question
            for question in questions:
                question_id = str(question["_id"])
                if question_id != selected_question_id:
                    continue
                question_text = question["question"]
                
                # Filter answers for this question
                question_answers = [a for a in answers if str(a.get("question_id")) == question_id]
                
                # Filter grades for this question
                question_grades = [g for g in grades if str(g.get("question_id")) == question_id]
                
                # Create a mapping of student answers to grades
                grades_dict = {g.get("student_roll_no"): g for g in question_grades}
                
                # Display question header
                st.markdown(f"### 📝 **Question:** {question_text[:100]}{'...' if len(question_text) > 100 else ''}")
                
                # Show question details in an expander
                with st.expander(f"📋 Question Details & Sample Answer", expanded=False):
                    st.markdown(f"**Full Question:**")
                    st.write(question_text)
                    
                    if question.get("sample_answer"):
                        st.markdown(f"**Sample Answer:**")
                        st.write(question["sample_answer"])
                    
                    if question.get("marking_scheme"):
                        st.markdown(f"**Marking Rules:**")
                        for i, rule in enumerate(question["marking_scheme"], 1):
                            rule_text = rule.get("text", "")
                            rule_type = rule.get("type", "semantic")
                            icons = {
                                "exact_phrase": "🔍",
                                "contains_keywords": "🔑", 
                                "semantic": "🧠"
                            }
                            st.write(f"{i}. {rule_text} {icons.get(rule_type, '🧠')}")
                
                # Show student answers count
                st.markdown(f"**📊 Student Answers:** {len(question_answers)}")
                
                if question_answers:
                    # Group answers by grade if grades exist
                    if question_grades:
                        # Create grade categories
                        grade_categories = {
                            "A": [], "B": [], "C": [], "D": [], "F": []
                        }
                        
                        for answer in question_answers:
                            roll_no = answer.get("student_roll_no")
                            grade_info = grades_dict.get(roll_no)
                            
                            if grade_info:
                                grade = grade_info.get("grade", "F")
                                grade_categories[grade].append({
                                    "answer": answer,
                                    "grade_info": grade_info
                                })
                            else:
                                grade_categories["F"].append({
                                    "answer": answer,
                                    "grade_info": None
                                })
                        
                        # Display answers grouped by grade
                        for grade in ["A", "B", "C", "D", "F"]:
                            grade_answers = grade_categories[grade]
                            if grade_answers:
                                grade_color = {
                                    "A": "🟢", "B": "🟡", "C": "🟠", 
                                    "D": "🔴", "F": "⚫"
                                }
                                
                                st.markdown(f"**{grade_color.get(grade, '⚫')} Grade {grade} ({len(grade_answers)} students):**")
                                
                                for item in grade_answers:
                                    answer = item["answer"]
                                    grade_info = item["grade_info"]
                                    
                                    student_name = answer.get("student_name", "Unknown")
                                    student_roll = answer.get("student_roll_no", "Unknown")
                                    student_answer = answer.get("student_ans", answer.get("student_answer", "No answer"))
                                    
                                    # Create expander for each student
                                    expander_title = f"{student_name} ({student_roll})"
                                    if grade_info:
                                        expander_title += f" - {grade_info.get('correct_%', 'N/A')} - Grade {grade}"
                                    
                                    with st.expander(expander_title, expanded=False):
                                        st.markdown("**Student Answer:**")
                                        st.text_area(
                                            "Answer", 
                                            value=student_answer, 
                                            height=100, 
                                            disabled=True, 
                                            key=f"answer_{question_id}_{student_roll}"
                                        )
                                        
                                        if grade_info:
                                            st.markdown(f"**Score:** {grade_info.get('correct_%', 'N/A')}")
                                            st.markdown(f"**Grade:** {grade}")
                                            
                                            if grade_info.get("matched_rules"):
                                                st.markdown("✅ **Matched Rules:**")
                                                st.write(grade_info["matched_rules"])
                                            
                                            if grade_info.get("missed_rules"):
                                                st.markdown("❌ **Missed Rules:**")
                                                st.write(grade_info["missed_rules"])
                                        else:
                                            st.info("⚠️ No grading data available for this student")
                    else:
                        # No grades available, show all answers
                        st.markdown("**📝 Student Answers (No grades available):**")
                        
                        for answer in question_answers:
                            student_name = answer.get("student_name", "Unknown")
                            student_roll = answer.get("student_roll_no", "Unknown")
                            student_answer = answer.get("student_ans", answer.get("student_answer", "No answer"))
                            
                            with st.expander(f"{student_name} ({student_roll})", expanded=False):
                                st.markdown("**Student Answer:**")
                                st.text_area(
                                    "Answer", 
                                    value=student_answer, 
                                    height=100, 
                                    disabled=True, 
                                    key=f"answer_{question_id}_{student_roll}"
                                )
                                st.info("⚠️ No grading data available. Run grading to see scores and grades.")
                else:
                    st.info("ℹ️ No student answers for this question yet.")
                
                st.divider()

    elif page == "Data Management":
        st.header("📋 Data Management")
        import_export_service = ImportExportService(st.session_state.user["_id"])
        tab1, tab2, tab3, tab4 = st.tabs(["📤 Export All Data", "📥 Import Answers", "📋 Template", "🗑️ Bulk Operations"])

        with tab1:
            st.subheader("📤 Export All Data (CSV ZIP)")
            if st.button("📤 Export All Data as ZIP"):
                with st.spinner("Exporting all data as CSV ZIP..."):
                    # Export each as CSV
                    success_q, questions_csv = import_export_service.export_questions_to_csv()
                    success_a, answers_csv = import_export_service.export_student_answers_to_csv()
                    success_g, grades_csv = import_export_service.export_grades_to_csv()
                    success_t, tests_csv = import_export_service.export_tests_to_csv()
                    success_ta, test_answers_csv = import_export_service.export_test_answers_to_csv()
                    success_tg, test_grades_csv = import_export_service.export_test_grades_to_csv()
                    
                    if success_q and success_a and success_g:
                        zip_buffer = io.BytesIO()
                        with zipfile.ZipFile(zip_buffer, "w") as zf:
                            zf.writestr("questions.csv", questions_csv)
                            zf.writestr("answers.csv", answers_csv)
                            zf.writestr("grades.csv", grades_csv)
                            if success_t:
                                zf.writestr("tests.csv", tests_csv)
                            if success_ta:
                                zf.writestr("test_answers.csv", test_answers_csv)
                            if success_tg:
                                zf.writestr("test_grades.csv", test_grades_csv)
                        zip_buffer.seek(0)
                        st.success("✅ All data exported successfully!")
                        st.download_button(
                            label="📥 Download All Data (CSV ZIP)",
                            data=zip_buffer,
                            file_name="semantic_grader_data.zip",
                            mime="application/zip"
                        )
                    else:
                        st.error("❌ Failed to export all data. Please ensure you have questions, answers, and grades.")

        with tab2:
            st.subheader("📥 Import Student Answers (CSV)")
            questions = get_questions(st.session_state.user["_id"])
            if questions:
                # Standards/info box for answer import
                st.info("""
                **Answer Submission Standards:**
                - **Maximum answer length:** 4,000 characters (about 600–800 words)
                - **Matching criteria:**
                    - 🔍 *Exact phrases*: Include any required formulas or specific wording.
                    - 🔑 *Keywords*: Make sure to mention all required terms.
                    - 🧠 *Semantic understanding*: Clearly explain concepts and relationships.
                - **Assessment uncertainty:** Automated grading is not perfect. Borderline or ambiguous answers may require manual review.
                - **General standards:**
                    - Be clear, concise, and relevant.
                    - Address all parts of the question.
                    - Avoid unnecessary information.
                """)
                question_options = {q["question"][:50] + "...": str(q["_id"]) for q in questions}
                selected_question = st.selectbox(
                    "Select question for these answers:",
                    options=list(question_options.keys()),
                    help="Choose which question these student answers belong to"
                )
                selected_question_id = question_options[selected_question]
                uploaded_file = st.file_uploader(
                    "Upload Student Answers CSV",
                    type=["csv"],
                    help="Upload a CSV file containing student answers"
                )
                if uploaded_file and st.button("📥 Import Answers"):
                    with st.spinner("Importing student answers..."):
                        try:
                            file_content = uploaded_file.read().decode('utf-8')
                            success, message, errors = import_export_service.import_student_answers_from_csv(file_content, selected_question_id)
                            if success:
                                st.success(f"✅ {message}")
                                if errors:
                                    st.warning(f"⚠️ {len(errors)} errors occurred:")
                                    for error in errors[:5]:
                                        st.write(f"• {error}")
                                    if len(errors) > 5:
                                        st.write(f"• ... and {len(errors) - 5} more errors")
                            else:
                                st.error(f"❌ {message}")
                        except Exception as e:
                            st.error(f"❌ Import failed: {str(e)}")
            else:
                st.warning("⚠️ No questions found. Please create a question first.")

        with tab3:
            st.subheader("📋 Templates (CSV)")
            templates = import_export_service.get_export_templates()
            
            # Student Answers Template
            st.write("**📝 Student Answers Template:**")
            answers_template = templates['student_answers']
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(answers_template['headers'])
            writer.writerow(answers_template['example'])
            st.download_button(
                label="📥 Download Answers Template",
                data=output.getvalue(),
                file_name="student_answers_template.csv",
                mime="text/csv"
            )
            st.code(output.getvalue())
            
            st.divider()
            
            # Test Answers Template
            st.write("**📋 Test Answers Template:**")
            test_answers_template = templates['test_answers']
            test_output = io.StringIO()
            test_writer = csv.writer(test_output)
            test_writer.writerow(test_answers_template['headers'])
            test_writer.writerow(test_answers_template['example'])
            st.download_button(
                label="📥 Download Test Answers Template",
                data=test_output.getvalue(),
                file_name="test_answers_template.csv",
                mime="text/csv"
            )
            st.code(test_output.getvalue())
            
            st.info("""
            **Instructions:**
            1. Download the appropriate template
            2. Fill in your data following the format
            3. Save as CSV
            4. Upload using the Import tab
            """)

        with tab4:
            st.subheader("🗑️ Bulk Operations")
            st.warning("⚠️ **Danger Zone** - These operations cannot be undone!")
            
            # Show current counts
            try:
                db = get_db()
                answers_count = db.answers.count_documents({"user_id": st.session_state.user["_id"]})
                grades_count = db.grades.count_documents({"user_id": st.session_state.user["_id"]})
                tests_count = db.tests.count_documents({"user_id": st.session_state.user["_id"]})
                test_answers_count = db.test_answers.count_documents({"user_id": st.session_state.user["_id"]})
                test_grades_count = db.test_grades.count_documents({"user_id": st.session_state.user["_id"]})
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("📝 Student Answers", answers_count)
                    st.metric("📋 Tests", tests_count)
                with col2:
                    st.metric("📊 Grades", grades_count)
                    st.metric("📝 Test Answers", test_answers_count)
                with col3:
                    st.metric("📊 Test Grades", test_grades_count)
                
                if answers_count == 0 and grades_count == 0 and tests_count == 0 and test_answers_count == 0 and test_grades_count == 0:
                    st.info("ℹ️ No data to delete. You can safely skip bulk operations.")
                else:
                    st.info("💡 **Tip**: Consider exporting your data before performing bulk deletions.")
            except Exception as e:
                st.error(f"❌ Error checking data counts: {str(e)}")
            
            st.divider()
            
            # Clear Student Answers
            st.write("**🗑️ Clear All Student Answers**")
            confirm_answers = st.checkbox("I understand this will delete ALL student answers", key="confirm_answers_bulk")
            with st.form("clear_answers_form_bulk"):
                clear_answers_submitted = st.form_submit_button("🗑️ Clear All Student Answers", disabled=not confirm_answers)
                if clear_answers_submitted:
                    if confirm_answers:
                        with st.spinner("Clearing all student answers..."):
                            try:
                                db = get_db()
                                count = db.answers.count_documents({"user_id": st.session_state.user["_id"]})
                                if count == 0:
                                    st.info("ℹ️ No student answers found to delete")
                                else:
                                    result = db.answers.delete_many({"user_id": st.session_state.user["_id"]})
                                    st.success(f"✅ Deleted {result.deleted_count} student answers")
                                    if 'grading_results' in st.session_state:
                                        del st.session_state.grading_results
                            except Exception as e:
                                st.error(f"❌ Error: {str(e)}")
                                st.error("Please check your database connection and try again.")
                    else:
                        st.error("Please check the box to enable deletion.")
            
            st.divider()
            
            # Clear Grades
            st.write("**🗑️ Clear All Grades**")
            confirm_grades = st.checkbox("I understand this will delete ALL grading results", key="confirm_grades_bulk")
            with st.form("clear_grades_form_bulk"):
                clear_grades_submitted = st.form_submit_button("🗑️ Clear All Grades", disabled=not confirm_grades)
                if clear_grades_submitted:
                    if confirm_grades:
                        with st.spinner("Clearing all grades..."):
                            try:
                                db = get_db()
                                count = db.grades.count_documents({"user_id": st.session_state.user["_id"]})
                                if count == 0:
                                    st.info("ℹ️ No grades found to delete")
                                else:
                                    result = db.grades.delete_many({"user_id": st.session_state.user["_id"]})
                                    st.success(f"✅ Deleted {result.deleted_count} grades")
                                    if 'grading_results' in st.session_state:
                                        del st.session_state.grading_results
                            except Exception as e:
                                st.error(f"❌ Error: {str(e)}")
                                st.error("Please check your database connection and try again.")
                    else:
                        st.error("Please check the box to enable deletion.")
            
            st.divider()
            
            # Clear Test Grades
            st.write("**🗑️ Clear All Test Grades**")
            confirm_test_grades = st.checkbox("I understand this will delete ALL test grading results", key="confirm_test_grades_bulk")
            with st.form("clear_test_grades_form_bulk"):
                clear_test_grades_submitted = st.form_submit_button("🗑️ Clear All Test Grades", disabled=not confirm_test_grades)
                if clear_test_grades_submitted:
                    if confirm_test_grades:
                        with st.spinner("Clearing all test grades..."):
                            try:
                                success, message = clear_test_grades(st.session_state.user["_id"])
                                if success:
                                    st.success(f"✅ {message}")
                                    if 'grading_results' in st.session_state:
                                        del st.session_state.grading_results
                                else:
                                    st.error(f"❌ {message}")
                            except Exception as e:
                                st.error(f"❌ Error: {str(e)}")
                                st.error("Please check your database connection and try again.")
                    else:
                        st.error("Please check the box to enable deletion.")
            
            st.divider()
            
            # Clear Test Answers
            st.write("**🗑️ Clear All Test Answers**")
            confirm_test_answers = st.checkbox("I understand this will delete ALL test submissions", key="confirm_test_answers_bulk")
            with st.form("clear_test_answers_form_bulk"):
                clear_test_answers_submitted = st.form_submit_button("🗑️ Clear All Test Answers", disabled=not confirm_test_answers)
                if clear_test_answers_submitted:
                    if confirm_test_answers:
                        with st.spinner("Clearing all test answers..."):
                            try:
                                db = get_db()
                                count = db.test_answers.count_documents({"user_id": st.session_state.user["_id"]})
                                if count == 0:
                                    st.info("ℹ️ No test answers found to delete")
                                else:
                                    result = db.test_answers.delete_many({"user_id": st.session_state.user["_id"]})
                                    st.success(f"✅ Deleted {result.deleted_count} test answers")
                                    if 'grading_results' in st.session_state:
                                        del st.session_state.grading_results
                            except Exception as e:
                                st.error(f"❌ Error: {str(e)}")
                                st.error("Please check your database connection and try again.")
                    else:
                        st.error("Please check the box to enable deletion.")
            
            st.info("""
            **🗑️ Bulk Operations:**
            - **Clear Student Answers**: Remove all individual question submissions
            - **Clear Grades**: Remove all individual question grading results
            - **Clear Test Grades**: Remove all test grading results
            - **Clear Test Answers**: Remove all test submissions
            
            **⚠️ Warning**: These operations are permanent and cannot be undone!
            Consider exporting your data before performing bulk deletions.
            """)

# Initialize session state with persistence
if 'user' not in st.session_state:
    st.session_state.user = None
if 'token' not in st.session_state:
    st.session_state.token = None
if 'show_signup' not in st.session_state:
    st.session_state.show_signup = False
if 'selected_test_id' not in st.session_state:
    st.session_state.selected_test_id = None
if 'show_test_results' not in st.session_state:
    st.session_state.show_test_results = False
if 'grade_test' not in st.session_state:
    st.session_state.grade_test = False

# Migrate any existing query param sessions to session state
migrate_query_params_to_session()

# Initialize session from persistent storage
initialize_session()

# Main app logic
if check_auth():
    # Auto-refresh session if needed
    auto_refresh_session()
    main_app()
else:
    if st.session_state.get('show_signup', False):
        signup_page()
    else:
        login_page()
