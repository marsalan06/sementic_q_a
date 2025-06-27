import streamlit as st
from core.db import save_question, save_student_answer, get_questions, save_grades, clear_grades, detect_rule_type, get_grade_thresholds, save_grade_thresholds
from services.grading_service import grade_all
from services.auth_service import create_user, authenticate_user, create_session_token, verify_session_token
from bson.objectid import ObjectId

st.set_page_config(page_title="Semantic Grader", layout="wide")

# Initialize session state
if 'user' not in st.session_state:
    st.session_state.user = None
if 'token' not in st.session_state:
    st.session_state.token = None

def check_auth():
    """Check if user is authenticated"""
    if st.session_state.token:
        payload = verify_session_token(st.session_state.token)
        if payload:
            return True
    return False

def login_page():
    """Login page"""
    st.title("🔐 Login to Semantic Grader")
    
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
    st.session_state.user = None
    st.session_state.token = None
    st.rerun()

def main_app():
    """Main application after authentication"""
    # Header with user info and logout
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        st.title("🎓 Semantic Grader")
    with col2:
        st.write(f"**Welcome, {st.session_state.user['username']}!**")
    with col3:
        if st.button("🚪 Logout"):
            logout()
    
    # Navigation
    page = st.sidebar.selectbox("Navigation", ["Create Question", "Upload Answers", "Grade Settings", "Run Grading"])
    
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
            save_question(question, sample_answer, rules, st.session_state.user["_id"])
            # Clear cached grading results when new question is added
            if 'grading_results' in st.session_state:
                del st.session_state.grading_results
            st.success("✅ Question saved successfully.")

    elif page == "Upload Answers":
        st.header("📤 Upload Student Answers")
        questions = get_questions(st.session_state.user["_id"])
        
        if not questions:
            st.warning("No questions found. Please create a question first.")
            return
            
        question_titles = [q["question"] for q in questions]
        selected_index = st.selectbox("Select a question:", range(len(question_titles)), format_func=lambda i: question_titles[i])

        selected_question_id = str(questions[selected_index]["_id"])

        with st.form(key="answer_form"):
            name = st.text_input("Student Name")
            roll_no = st.text_input("Student Roll No")
            answer = st.text_area("Student Answer")
            submitted = st.form_submit_button("Submit Answer")

        if submitted:
            save_student_answer(name, roll_no, answer, selected_question_id, st.session_state.user["_id"])
            # Clear cached grading results when new answer is added
            if 'grading_results' in st.session_state:
                del st.session_state.grading_results
            st.success("✅ Student answer saved successfully.")

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
                save_grade_thresholds(new_thresholds, st.session_state.user["_id"])
                st.success("✅ Grade thresholds updated successfully!")
                
                # Clear cached grading results when thresholds change
                if 'grading_results' in st.session_state:
                    del st.session_state.grading_results
                
                st.rerun()
        
        # Quick preset buttons
        st.divider()
        st.subheader("🚀 Quick Presets")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📚 Standard (85/70/55/40)"):
                standard_thresholds = {"A": 85, "B": 70, "C": 55, "D": 40, "F": 0}
                save_grade_thresholds(standard_thresholds, st.session_state.user["_id"])
                st.success("✅ Applied standard thresholds!")
                st.rerun()
        
        with col2:
            if st.button("🎯 Strict (90/80/70/60)"):
                strict_thresholds = {"A": 90, "B": 80, "C": 70, "D": 60, "F": 0}
                save_grade_thresholds(strict_thresholds, st.session_state.user["_id"])
                st.success("✅ Applied strict thresholds!")
                st.rerun()
        
        with col3:
            if st.button("📖 Lenient (80/65/50/35)"):
                lenient_thresholds = {"A": 80, "B": 65, "C": 50, "D": 35, "F": 0}
                save_grade_thresholds(lenient_thresholds, st.session_state.user["_id"])
                st.success("✅ Applied lenient thresholds!")
                st.rerun()

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
                clear_grades(st.session_state.user["_id"])
                results = grade_all(debug=debug_mode, user_id=st.session_state.user["_id"])
                save_grades(results, st.session_state.user["_id"])
                st.session_state.grading_results = results
            st.success("✅ Grading completed.")

        st.subheader("📊 Grading Results")
        
        # Use stored results if available, otherwise run grading once
        if st.session_state.grading_results is not None:
            graded = st.session_state.grading_results
        else:
            with st.spinner("Loading grading results..."):
                graded = grade_all(debug=debug_mode, user_id=st.session_state.user["_id"])
        
        if graded:
            for i, r in enumerate(graded):
                with st.expander(f"{r['student_name']} ({r['student_roll_no']}) - Grade: {r['grade']}"):
                    st.markdown(f"**Student Answer:**")
                    st.text_area("Answer", value=r.get('student_answer', 'No answer available'), height=100, disabled=True, key=f"answer_{i}_{r['student_roll_no']}")
                    st.markdown(f"**Correct %:** {r['correct_%']}")
                    st.markdown("✅ **Matched Rules:**")
                    st.write(r["matched_rules"])
                    st.markdown("❌ **Missed Rules:**")
                    st.write(r["missed_rules"])
        else:
            st.info("No graded results available. Run grading first.")

# Main app logic
if check_auth():
    main_app()
else:
    if st.session_state.get('show_signup', False):
        signup_page()
    else:
        login_page()
