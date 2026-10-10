import time

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import time
import json

app = FastAPI()


# =========================
# Response Models
# =========================

class CourseProgress(BaseModel):
    course_id: int
    title: str
    completed_lessons: int
    total_lessons: int
    progress: int


class CourseProgressResponse(BaseModel):
    user_id: int
    courses: list[CourseProgress]


# =========================
# Fake Database
# =========================

users = {
    42: {"id": 42, "name": "Aradhya"}
}

courses = [
    {"id": 1, "user_id": 42, "title": "Python"},
    {"id": 2, "user_id": 42, "title": "FastAPI"},
    {"id": 3, "user_id": 42, "title": "PostgreSQL"},
]

lessons = [
    {"id": 1, "course_id": 1},
    {"id": 2, "course_id": 1},
    {"id": 3, "course_id": 1},

    {"id": 4, "course_id": 2},
    {"id": 5, "course_id": 2},

    {"id": 6, "course_id": 3},
    {"id": 7, "course_id": 3},
    {"id": 8, "course_id": 3},
]

progress = {
    (42, 1): {1, 2},
    (42, 2): {4},
    (42, 3): {6, 7},
}


# =========================
# Fake DB Layer
# =========================

class FakeDB:

    def __init__(self):
        self.query_count = 0

    def _query(self):
        self.query_count += 1
        time.sleep(0.005)

    def get_user(self, user_id: int):
        self._query()

        return users.get(user_id)

    def get_courses(self, user_id: int):
        self._query()

        return [
            course
            for course in courses
            if course["user_id"] == user_id
        ]

    def get_lessons(self, course_id: int):
        self._query()

        return [
            lesson
            for lesson in lessons
            if lesson["course_id"] == course_id
        ]

    def get_progress(self, user_id: int, course_id: int):
        self._query()

        return progress.get((user_id, course_id), set())

    def get_all_lessons(self, course_ids):
        self._query()
        return [
            lesson for lesson in lessons
            if lesson["course_id"] in course_ids
            ]

    def get_all_progress(self, user_id, course_ids):
        self._query()
        return {
            course_id: progress.get((user_id, course_id), set())
            for course_id in course_ids}

    def __init__(self):
        self.query_count = 0
        self.db_time_ms = 0.0

    def _query(self):
        start = time.perf_counter()
        time.sleep(0.005)
        self.query_count += 1
        self.db_time_ms += (
            time.perf_counter() - start
        ) * 1000


# =========================
# Endpoint
# =========================

@app.get(
    "/course-progress/{user_id}",
    response_model=CourseProgressResponse
)
def get_course_progress(user_id: int):


    db = FakeDB()
    db.db_time_ms = 0.0
    db.query_count = 0

    # Query 1
    user = db.get_user(user_id)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    result = []
    user_courses = db.get_courses(user_id)

    course_ids = [course["id"] for course in user_courses]

    all_lessons = db.get_all_lessons(course_ids)
    all_progress = db.get_all_progress(user_id, course_ids)

    for course in user_courses:
        course_lessons = [
            lesson for lesson in all_lessons
            if lesson["course_id"] == course["id"]
            ]
        total_lessons = len(course_lessons)

        completed_lessons = len(
            all_progress.get(course["id"], set())
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

    print(f"Total DB queries: {db.query_count}")
    print(
        f"queries={db.query_count}, "
        f"db_time_ms={db.db_time_ms:.2f}"
        )

    # 1. Pydantic model creation
    model_start = time.perf_counter()

    response = CourseProgressResponse(
        user_id=user_id,
        courses=result
    )

    model_end = time.perf_counter()

    # 2. JSON serialization
    json_start = time.perf_counter()

    json_payload = response.model_dump_json()

    json_end = time.perf_counter()

    # 3. Payload size
    payload_size = len(json_payload.encode("utf-8"))

    # 4. Print measurements
    print(f"Courses returned: {len(result)}")
    print(f"Model creation: {(model_end - model_start) * 1000:.4f} ms")
    print(f"JSON serialization: {(json_end - json_start) * 1000:.4f} ms")
    print(f"Payload size: {payload_size:,} bytes ({payload_size / 1024:.2f} KB)")

    return response


if __name__ == "__main__":
    large_response = {
        "user_id": 42,
        "courses": [
            {
                "course_id": i,
                "title": f"Course {i}",
                "completed_lessons": 15,
                "total_lessons": 20,
                "progress": 75,
                "description": "A sample course description " * 20,
            }
            for i in range(1000)
        ],
    }

    start = time.perf_counter()
    serialized = json.dumps(large_response)
    elapsed_ms = (time.perf_counter() - start) * 1000

    print(f"Serialization: {elapsed_ms:.3f} ms")
    print(f"Payload size: {len(serialized.encode('utf-8')) / 1024:.2f} KB")