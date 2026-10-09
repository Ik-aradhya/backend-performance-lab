from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

app = FastAPI()


# ---------- Response Schemas ----------

class CourseProgress(BaseModel):
    course_id: int
    title: str
    completed_lessons: int
    total_lessons: int
    progress: int


class CourseProgressResponse(BaseModel):
    user_id: int
    courses: List[CourseProgress]


# ---------- Fake Database ----------

users = {
    42: {"id": 42, "name": "Aradhya"}
}

courses = [
    {"id": 1, "user_id": 42, "title": "Python"},
    {"id": 2, "user_id": 42, "title": "FastAPI"},
]

lessons = [
    {"id": 1, "course_id": 1},
    {"id": 2, "course_id": 1},
    {"id": 3, "course_id": 1},
    {"id": 4, "course_id": 1},
    {"id": 5, "course_id": 2},
    {"id": 6, "course_id": 2},
]

progress = {
    (42, 1): {1, 2, 3},
    (42, 2): {5},
}


# ---------- Endpoint ----------

@app.get(
    "/course-progress/{user_id}",
    response_model=CourseProgressResponse
)
def get_course_progress(user_id: int):

    # Find user
    user = users.get(user_id)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    result = []

    # Find user's courses
    user_courses = [
        course
        for course in courses
        if course["user_id"] == user_id
    ]

    # Find lessons and progress
    for course in user_courses:

        course_lessons = [
            lesson
            for lesson in lessons
            if lesson["course_id"] == course["id"]
        ]

        total_lessons = len(course_lessons)

        completed_lessons = len(
            progress.get((user_id, course["id"]), set())
        )

        progress_percentage = (
            int((completed_lessons / total_lessons) * 100)
            if total_lessons > 0
            else 0
        )

        result.append(
            CourseProgress(
                course_id=course["id"],
                title=course["title"],
                completed_lessons=completed_lessons,
                total_lessons=total_lessons,
                progress=progress_percentage,
            )
        )

    return CourseProgressResponse(
        user_id=user_id,
        courses=result
    )