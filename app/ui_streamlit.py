import sys
import os
from datetime import datetime

# ------------------ FIX IMPORT PATH ------------------
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import streamlit as st
import pandas as pd

from app.engine import classify_learner
from app.recommender import recommend
from utils.logger import log_progress
from app.feedback_generator import generate_feedback
from utils.report_generator import generate_pdf
from app.ai_tutor import ask_tutor



# ------------------ CONFIG ------------------
st.set_page_config(page_title="AI Personalized Learning", layout="wide")

# ------------------ SIDEBAR ------------------
st.sidebar.title("🎛 Navigation")
page = st.sidebar.radio(
    "Go to",
    ["Student View", "Teacher Dashboard", "🤖 AI Tutor Chat"]
)



# ======================================================
# ====================== STUDENT VIEW ==================
# ======================================================
if page == "Student View":

    st.title("🎓 AI Personalized Learning Platform")
    st.caption("Smart adaptive learning for every student")

    # ---- Current Date & Time ----
    now = datetime.now().strftime("%A, %d %B %Y — %I:%M %p")
    st.markdown(f"🕒 **{now}**")

    st.markdown("---")

    # ---------------- INPUT AREA ----------------
    col1, col2 = st.columns([2, 1])

    with col1:
        student_id = st.text_input("👤 Student Name / ID")
        topic = st.selectbox("📘 Topic", ["fractions"])

    with col2:
        st.info(
            "ℹ️ Tips:\n"
            "- Higher accuracy = better mastery\n"
            "- More hint usage = more dependency\n"
            "- Engagement reflects motivation"
        )

    st.markdown("### 📊 Learning Behavior")

    c1, c2, c3 = st.columns(3)
    with c1:
        accuracy = st.slider("Accuracy", 0.0, 1.0, 0.6)
        hesitation = st.slider("Hesitation", 0.0, 1.0, 0.2)
    with c2:
        time = st.slider("Response Time (sec)", 2.0, 20.0, 8.0)
        engagement = st.slider("Engagement", 0.0, 1.0, 0.7)
    with c3:
        hint = st.slider("Hint Usage", 0.0, 1.0, 0.3)

    analyze = st.button("🚀 Analyze & Generate Learning Plan", use_container_width=True)

    # ---------------- PROCESS ----------------
    if analyze:

        if not student_id.strip():
            st.error("Please enter Student Name / ID")
            st.stop()

        learner_type = classify_learner(accuracy, time, hesitation, engagement, hint)
        plan = recommend(topic, learner_type)
        feedback = generate_feedback(learner_type, accuracy, hint)

        st.session_state.plan = plan
        st.session_state.feedback = feedback

        log_progress(student_id, accuracy, time, hesitation, engagement, hint, learner_type)

        # 🎉 Celebration effect
        # st.balloons()

        st.success(f"Profile Generated Successfully — Level: {plan['level']}")

        # ---------------- RESULTS TABS ----------------
        tab1, tab2, tab3 = st.tabs(["👩‍🎓 Student View", "👨‍🏫 Teacher View", "🤖 AI Feedback"])

        with tab1:
            st.subheader("📘 Your Learning Plan")
            st.write(f"**Level:** {plan['level']}")
            st.write(f"**Next Step:** {plan['next_step']}")
            st.write(f"**Focus Area:** {plan['focus_area']}")

        with tab2:
            st.subheader("👨‍🏫 Teacher Insights")
            st.write(f"**Insight:** {plan['teacher_insight']}")
            st.write(f"**Strategy:** {plan['instruction_strategy']}")
            st.write(f"**Assessment:** {plan['assessment']}")
            st.write(f"**Risk:** {plan['risk_flag']}")

        with tab3:
            st.subheader("🤖 AI Feedback")
            st.success(feedback)

    # ---------------- PDF REPORT ----------------
    st.markdown("---")

    if "pdf_bytes" not in st.session_state:
        st.session_state.pdf_bytes = None

    if st.button("📄 Generate PDF Report"):

        if "plan" not in st.session_state or "feedback" not in st.session_state:
            st.error("Please run analysis first.")
        else:
            try:
                path = generate_pdf(student_id, st.session_state.plan, st.session_state.feedback)

                with open(path, "rb") as f:
                    st.session_state.pdf_bytes = f.read()

                st.success("PDF generated successfully. Ready for download.")

            except Exception as e:
                st.error(f"PDF Error: {e}")

    if st.session_state.pdf_bytes:
        st.download_button(
            "⬇ Download Report",
            data=st.session_state.pdf_bytes,
            file_name=f"{student_id}_report.pdf",
            mime="application/pdf"
        )


# ======================================================
# ================= TEACHER DASHBOARD ==================
# ======================================================
elif page == "Teacher Dashboard":

    st.title("📊 Teacher Analytics Dashboard")

    if not os.path.exists("data/progress_log.csv"):
        st.warning("No student data available.")
        st.stop()

    df = pd.read_csv("data/progress_log.csv")

    if df.empty:
        st.warning("No records found.")
        st.stop()

    # Handle timestamp safely
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"])
    else:
        df["timestamp"] = range(len(df))

    # Convert numeric columns safely
    for col in ["accuracy", "engagement", "hint"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # ------------------------------------------------
    # 📌 CLASS OVERVIEW
    # ------------------------------------------------
    st.subheader("🏫 Class Overview")

    class_avg_accuracy = df["accuracy"].mean()
    class_avg_engagement = df["engagement"].mean()
    class_avg_hint = df["hint"].mean()

    c1, c2, c3 = st.columns(3)
    c1.metric("Class Avg Accuracy", round(class_avg_accuracy, 2))
    c2.metric("Class Avg Engagement", round(class_avg_engagement, 2))
    c3.metric("Class Avg Hint Usage", round(class_avg_hint, 2))

    st.markdown("---")

    # ------------------------------------------------
    # 📌 STUDENT COMPARISON TABLE
    # ------------------------------------------------
    st.subheader("👥 Student Performance Comparison")

    # Aggregate per student
    student_summary = (
        df.groupby("student_id")
        .agg(
            Attempts=("accuracy", "count"),
            Avg_Accuracy=("accuracy", "mean"),
            Avg_Engagement=("engagement", "mean"),
            Avg_Hint_Usage=("hint", "mean"),
        )
        .reset_index()
    )

    # Round values
    student_summary["Avg_Accuracy"] = student_summary["Avg_Accuracy"].round(2)
    student_summary["Avg_Engagement"] = student_summary["Avg_Engagement"].round(2)
    student_summary["Avg_Hint_Usage"] = student_summary["Avg_Hint_Usage"].round(2)

    # Sort best students first
    student_summary = student_summary.sort_values(
        by="Avg_Accuracy", ascending=False
    )

    st.dataframe(student_summary, use_container_width=True)

    st.markdown("---")

    # ------------------------------------------------
    # 📌 TOP & AT-RISK STUDENTS
    # ------------------------------------------------
    st.subheader("🏆 Top & ⚠ At-Risk Students")

    top_students = student_summary.head(3)
    weak_students = student_summary.tail(3)

    col1, col2 = st.columns(2)

    with col1:
        st.success("🏆 Top Performers")
        st.dataframe(top_students, use_container_width=True)

    with col2:
        st.error("⚠ Needs Attention")
        st.dataframe(weak_students, use_container_width=True)

    st.markdown("---")

    # ------------------------------------------------
    # 📌 INDIVIDUAL STUDENT VIEW
    # ------------------------------------------------
    st.subheader("📈 Individual Student Progress")

    selected_student = st.selectbox(
        "Select student to view timeline",
        df["student_id"].unique()
    )

    student_df = df[df["student_id"] == selected_student].sort_values("timestamp")

    st.line_chart(
        student_df.set_index("timestamp")[["accuracy", "engagement", "hint"]]
    )

    st.dataframe(student_df.tail(10), use_container_width=True)




# ======================================================
# ===================== AI CHAT TUTOR ==================
# ======================================================
elif page == "🤖 AI Tutor Chat":

    st.title("🤖 AI Tutor")
    st.caption("Ask anything about your topic. I will explain like a teacher.")

    # Session chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Show previous messages
    for role, msg in st.session_state.chat_history:
        if role == "user":
            st.markdown(f"**👤 You:** {msg}")
        else:
            st.markdown(f"**🤖 Tutor:** {msg}")

    st.markdown("---")

    user_input = st.text_input("Ask your doubt (e.g., 'Explain fractions simply')")

    if st.button("Ask Tutor"):

        if not user_input.strip():
            st.warning("Please enter a question.")
        else:
            with st.spinner("Thinking..."):
                reply = ask_tutor(user_input)

            # Save conversation
            st.session_state.chat_history.append(("user", user_input))
            st.session_state.chat_history.append(("tutor", reply))

            # Rerun to update UI
            st.rerun()
