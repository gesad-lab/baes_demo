import streamlit as st
import requests

API_URL = "http://localhost:8000/students"

def create_student(student_data):
    response = requests.post(API_URL, json=student_data)
    return response.status_code, response.json()

def main():
    st.title("Student Management System")

    with st.form(key='student_form'):
        name = st.text_input("Student Name", max_chars=100)
        code = st.text_input("Student Code", max_chars=10)
        credits = st.number_input("Credits", min_value=1, max_value=30)
        instructor = st.text_input("Instructor Name", max_chars=100)

        submit_button = st.form_submit_button("Add Student")

        if submit_button:
            if not name or not code or not instructor:
                st.error("Please fill in all fields.")
            else:
                student_data = {
                    "name": name,
                    "code": code,
                    "credits": credits,
                    "instructor": instructor
                }
                status_code, response = create_student(student_data)
                if status_code == 201:
                    st.success("Student added successfully!")
                else:
                    st.error("Error adding student: " + response.get("detail", "Unknown error"))

if __name__ == "__main__":
    main()