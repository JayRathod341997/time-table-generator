import streamlit as st
import pandas as pd
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    st.error("⚠️ GROQ_API_KEY not found. Please set it in your .env file.")
    st.stop()

st.set_page_config(page_title="College Timetable Generator", layout="wide")
st.title("📅 College Timetable Generator (Multi-Department)")

# ---------------------- Step 1: Department Input ----------------------
num_departments = st.number_input("Enter number of departments:", min_value=1, step=1)
departments = []

for i in range(num_departments):
    dept_name = st.text_input(f"Enter name for Department {i+1}", key=f"dept_{i}")
    if dept_name:
        departments.append(dept_name)

# ---------------------- Step 2: Department Configurations ----------------------
department_data = {}

if departments:
    st.subheader("Department Configurations")

    for dept in departments:
        with st.expander(f"⚙️ Configure {dept}"):
            start_time = st.time_input(f"Start Time - {dept}", key=f"start_{dept}")
            end_time = st.time_input(f"End Time - {dept}", key=f"end_{dept}")

            # Break and lecture duration
            add_break = st.checkbox(f"Add break for {dept}?", key=f"break_{dept}")
            break_time = None
            break_duration = None
            if add_break:
                break_time = st.time_input(f"Break Start Time - {dept}", key=f"break_time_{dept}")
                break_duration = st.number_input(
                    f"Break Duration (minutes) - {dept}",
                    min_value=5,
                    step=5,
                    key=f"break_dur_{dept}"
                )

            lecture_duration = st.number_input(
                f"Lecture Duration (minutes) - {dept}",
                min_value=10,
                step=5,
                key=f"lec_dur_{dept}"
            )

            # Faculty-Subject Mapping
            st.markdown("### Faculty → Subject Mapping")
            num_faculty = st.number_input(
                f"Enter number of faculty in {dept}",
                min_value=1,
                step=1,
                key=f"num_fac_{dept}"
            )
            faculty_subject_map = {}

            for j in range(num_faculty):
                faculty = st.text_input(f"Faculty {j+1} Name - {dept}", key=f"fac_{dept}_{j}")
                subject = st.text_input(
                    f"Subject taught by {faculty if faculty else 'Faculty'} - {dept}",
                    key=f"sub_{dept}_{j}"
                )
                if faculty and subject:
                    faculty_subject_map[faculty] = subject

            department_data[dept] = {
                "start": start_time,
                "end": end_time,
                "break_time": break_time,
                "break_duration": break_duration,
                "lecture_duration": lecture_duration,
                "faculty_subject_map": faculty_subject_map
            }

# ---------------------- Step 3: Generate Timetables ----------------------
# ---------------------- Step 3: Generate Timetables ----------------------
import pandas as pd
import re
from io import StringIO   # ✅ correct import
def extract_csv_block(text):
    """
    Extracts CSV content starting from 'Start,End,Subject,Faculty'
    until the last valid row.
    """
    match = re.search(r"(Start,End,Subject,Faculty[\s\S]+?)(?:\n\n|\Z)", text)
    if match:
        return match.group(1).strip()
    return None
import io
if st.button("Generate Timetables"):
    for dept, config in department_data.items():
        st.subheader(f"📊 Timetable for {dept}")

        with st.spinner("🤖 Generating optimized timetable..."):
            llm = ChatGroq(
                temperature=0,
                model="deepseek-r1-distill-llama-70b"
            )

            prompt = f"""
            Generate an optimized college timetable for {dept} with the following constraints:
            - Working hours: {config['start']} to {config['end']}
            - Lecture duration: {config['lecture_duration']} minutes
            - Break: {config['break_time']} for {config['break_duration']} minutes 
            - Faculty and subjects: {config['faculty_subject_map']}
            
            Return timetable ONLY in CSV format with these exact headers:
            Start,End,Subject,Faculty
            """

            response = llm.invoke(prompt)
            content = response.content.strip()
            csv_text = extract_csv_block(content)
            print(csv_text)
            if csv_text:
                df = pd.read_csv(io.StringIO(csv_text))
                st.table(df) 
            else:
                st.error("❌ No valid CSV found in AI response")
                st.text_area("Raw AI response", content, height=200)
