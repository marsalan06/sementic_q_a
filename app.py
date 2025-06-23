import streamlit as st
from core.db import save_question, save_student_answer, get_questions, save_grades, clear_grades
from services.grading_service import grade_all

st.set_page_config(page_title="Semantic Grader", layout="wide")

page = st.sidebar.selectbox("Navigation", ["Create Question", "Upload Answers", "Run Grading"])

if page == "Create Question":
    st.header("📝 Create a New Question")
    question = st.text_area("Enter the question text:")
    sample_answer = st.text_area("Enter the sample answer:")

    rules = []
    rule_count = st.number_input("How many marking rules?", min_value=1, step=1)
    for i in range(rule_count):
        rule = st.text_input(f"Rule {i + 1}")
        rules.append(rule)

    if st.button("Save Question"):
        save_question(question, sample_answer, rules)
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
        st.success("✅ Student answer saved successfully.")

elif page == "Run Grading":
    st.header("🎯 Run Semantic Grading")
    
    debug_mode = st.checkbox("Enable Debug Mode", help="Show detailed analysis of grading process")
    
    if st.button("Run Grading & Save to DB"):
        clear_grades()
        results = grade_all(debug=debug_mode)
        save_grades(results)
        st.success("✅ Grading completed.")

    st.subheader("📊 Grading Results")
    graded = grade_all(debug=debug_mode)
    for r in graded:
        with st.expander(f"{r['student_name']} ({r['student_roll_no']}) - Grade: {r['grade']}"):
            st.markdown(f"**Correct %:** {r['correct_%']}")
            st.markdown("✅ **Matched Rules:**")
            st.write(r["matched_rules"])
            st.markdown("❌ **Missed Rules:**")
            st.write(r["missed_rules"])
