from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, constr, conint
from typing import List

app = FastAPI()

class Student(BaseModel):
    name: constr(min_length=1, max_length=100) = Field(..., description="The full name of the student")
    code: constr(min_length=1, max_length=10) = Field(..., description="Unique code identifying the student")
    credits: conint(ge=0) = Field(..., description="Total credits earned by the student")
    instructor: constr(min_length=1, max_length=100) = Field(..., description="Name of the instructor assigned to the student")

students_db = []

@app.post("/students/", response_model=Student, status_code=201)
async def create_student(student: Student):
    if any(s.code == student.code for s in students_db):
        raise HTTPException(status_code=400, detail="Student code already exists")
    students_db.append(student)
    return student

@app.get("/students/", response_model=List[Student])
async def read_students(skip: int = Query(0, ge=0), limit: int = Query(10, gt=0)):
    return students_db[skip: skip + limit]

@app.get("/students/{student_code}", response_model=Student)
async def read_student(student_code: str):
    for student in students_db:
        if student.code == student_code:
            return student
    raise HTTPException(status_code=404, detail="Student not found")

@app.put("/students/{student_code}", response_model=Student)
async def update_student(student_code: str, updated_student: Student):
    for index, student in enumerate(students_db):
        if student.code == student_code:
            students_db[index] = updated_student
            return updated_student
    raise HTTPException(status_code=404, detail="Student not found")

@app.delete("/students/{student_code}", status_code=204)
async def delete_student(student_code: str):
    for index, student in enumerate(students_db):
        if student.code == student_code:
            del students_db[index]
            return
    raise HTTPException(status_code=404, detail="Student not found")