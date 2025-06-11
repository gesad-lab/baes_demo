import streamlit as st
import requests

st.title("Student Management System")

def add_student(name, registration_number, course):
    response = requests.post("http://localhost:8000/students", json={
        "name": name,
        "registration_number": registration_number,
        "course": course
    })
    return response.status_code, response.json()

def main():
    st.header("Add New Student")
    
    name = st.text_input("Student Name", max_chars=50)
    registration_number = st.text_input("Registration Number", max_chars=20)
    course = st.selectbox("Course", ["Computer Science", "Mathematics", "Physics", "Chemistry", "Biology"])
    
    if st.button("Submit"):
        if name and registration_number:
            status_code, response = add_student(name, registration_number, course)
            if status_code == 201:
                st.success("Student added successfully!")
            else:
                st.error("Failed to add student: " + response.get("detail", "Unknown error"))
        else:
            st.error("Please fill in all required fields.")

if __name__ == "__main__":
    main()