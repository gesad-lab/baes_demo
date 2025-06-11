from fastapi import FastAPI, HTTPException, Path
from pydantic import BaseModel, Field, constr
from typing import List

app = FastAPI()

class Student(BaseModel):
    name: constr(min_length=1, max_length=100) = Field(..., description="The full name of the student")
    registration_number: constr(min_length=1, max_length=20) = Field(..., description="Unique registration number for the student")
    course: constr(min_length=1, max_length=100) = Field(..., description="The course the student is enrolled in")

students_db = []

@app.post("/students/", response_model=Student, status_code=201)
async def create_student(student: Student):
    if any(s.registration_number == student.registration_number for s in students_db):
        raise HTTPException(status_code=400, detail="Registration number already exists")
    students_db.append(student)
    return student

@app.get("/students/", response_model=List[Student])
async def get_students():
    return students_db

@app.get("/students/{registration_number}", response_model=Student)
async def get_student(registration_number: str = Path(..., description="The registration number of the student")):
    for student in students_db:
        if student.registration_number == registration_number:
            return student
    raise HTTPException(status_code=404, detail="Student not found")

@app.put("/students/{registration_number}", response_model=Student)
async def update_student(registration_number: str, updated_student: Student):
    for index, student in enumerate(students_db):
        if student.registration_number == registration_number:
            students_db[index] = updated_student
            return updated_student
    raise HTTPException(status_code=404, detail="Student not found")

@app.delete("/students/{registration_number}", status_code=204)
async def delete_student(registration_number: str):
    for index, student in enumerate(students_db):
        if student.registration_number == registration_number:
            del students_db[index]
            return
    raise HTTPException(status_code=404, detail="Student not found")