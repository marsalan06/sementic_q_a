import streamlit as st
from core.db import save_question, save_student_answer, get_questions, save_grades, clear_grades, detect_rule_type
from services.grading_service import grade_all

st.set_page_config(page_title="Semantic Grader", layout="wide")

page = st.sidebar.selectbox("Navigation", ["Create Question", "Upload Answers", "Run Grading"])

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
        save_question(question, sample_answer, rules)
        # Clear cached grading results when new question is added
        if 'grading_results' in st.session_state:
            del st.session_state.grading_results
        st.success("✅ Question saved successfully.")

elif page == "Upload Answers":
    st.header("📤 Upload Student Answers")
    questions = get_questions()
    question_titles = [q["question"] for q in questions]
    selected_index = st.selectbox("Select a question:", range(len(question_titles)), format_func=lambda i: question_titles[i])

    selected_question_id = str(questions[selected_index]["_id"])

    with st.form(key="answer_form"):
        name = st.text_input("Student Name")
        roll_no = st.text_input("Student Roll No")
        answer = st.text_area("Student Answer")
        submitted = st.form_submit_button("Submit Answer")

    if submitted:
        save_student_answer(name, roll_no, answer, selected_question_id)
        # Clear cached grading results when new answer is added
        if 'grading_results' in st.session_state:
            del st.session_state.grading_results
        st.success("✅ Student answer saved successfully.")

elif page == "Run Grading":
    st.header("🎯 Run Semantic Grading")
    
    st.info("""
    🔧 **Dynamic Hybrid Matching System:**
    - 🔍 **Exact Phrase**: Automatically extracts and matches specific content
    - 🔑 **Keyword Matching**: Uses lemmatization to match important terms dynamically
    - 🧠 **Semantic**: Uses embeddings for conceptual understanding
    """)
    
    debug_mode = st.checkbox("Enable Debug Mode", help="Show detailed analysis of grading process")
    
    # Use session state to store grading results
    if 'grading_results' not in st.session_state:
        st.session_state.grading_results = None
    
    if st.button("Run Grading & Save to DB"):
        with st.spinner("Running grading analysis..."):
            clear_grades()
            results = grade_all(debug=debug_mode)
            save_grades(results)
            st.session_state.grading_results = results
        st.success("✅ Grading completed.")

    st.subheader("📊 Grading Results")
    
    # Use stored results if available, otherwise run grading once
    if st.session_state.grading_results is not None:
        graded = st.session_state.grading_results
    else:
        with st.spinner("Loading grading results..."):
            graded = grade_all(debug=debug_mode)
    
    if graded:
        for r in graded:
            with st.expander(f"{r['student_name']} ({r['student_roll_no']}) - Grade: {r['grade']}"):
                st.markdown(f"**Correct %:** {r['correct_%']}")
                st.markdown("✅ **Matched Rules:**")
                st.write(r["matched_rules"])
                st.markdown("❌ **Missed Rules:**")
                st.write(r["missed_rules"])
    else:
        st.info("No graded results available. Run grading first.")
