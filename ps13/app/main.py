import os
from contextlib import asynccontextmanager

import asyncpg
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel


class CourseProgress(BaseModel):
    course_id: int
    title: str
    completed_lessons: int
    total_lessons: int
    progress: int


class CourseProgressResponse(BaseModel):
    user_id: int
    courses: list[CourseProgress]


SCHEMA = (
    """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS courses (
        id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(id),
        title TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS lessons (
        id INTEGER PRIMARY KEY,
        course_id INTEGER NOT NULL REFERENCES courses(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS lesson_progress (
        user_id INTEGER NOT NULL REFERENCES users(id),
        lesson_id INTEGER NOT NULL REFERENCES lessons(id),
        PRIMARY KEY (user_id, lesson_id)
    )
    """,
)


async def initialize_database(pool: asyncpg.Pool) -> None:
    async with pool.acquire() as connection:
        for statement in SCHEMA:
            await connection.execute(statement)

        await connection.execute(
            "INSERT INTO users (id, name) VALUES (42, 'Aradhya') "
            "ON CONFLICT (id) DO NOTHING"
        )
        await connection.executemany(
            "INSERT INTO courses (id, user_id, title) VALUES ($1, 42, $2) "
            "ON CONFLICT (id) DO NOTHING",
            [(1, "Python"), (2, "FastAPI"), (3, "PostgreSQL")],
        )
        await connection.executemany(
            "INSERT INTO lessons (id, course_id) VALUES ($1, $2) "
            "ON CONFLICT (id) DO NOTHING",
            [(1, 1), (2, 1), (3, 1), (4, 2), (5, 2), (6, 3), (7, 3), (8, 3)],
        )
        await connection.executemany(
            "INSERT INTO lesson_progress (user_id, lesson_id) VALUES (42, $1) "
            "ON CONFLICT (user_id, lesson_id) DO NOTHING",
            [(1,), (2,), (4,), (6,), (7,)],
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    pool = await asyncpg.create_pool(
        os.getenv(
            "DATABASE_URL",
            "postgresql://postgres:postgres@localhost:5432/course_progress",
        )
    )
    await initialize_database(pool)
    app.state.pool = pool
    try:
        yield
    finally:
        await pool.close()


app = FastAPI(lifespan=lifespan)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get(
    "/course-progress/{user_id}",
    response_model=CourseProgressResponse,
)
async def get_course_progress(
    user_id: int,
    request: Request,
) -> CourseProgressResponse:
    pool: asyncpg.Pool = request.app.state.pool
    async with pool.acquire() as connection:
        user_exists = await connection.fetchval(
            "SELECT EXISTS(SELECT 1 FROM users WHERE id = $1)",
            user_id,
        )
        if not user_exists:
            raise HTTPException(status_code=404, detail="User not found")

        rows = await connection.fetch(
            """
            SELECT
                c.id AS course_id,
                c.title,
                COUNT(DISTINCT l.id) AS total_lessons,
                COUNT(DISTINCT lp.lesson_id) AS completed_lessons
            FROM courses AS c
            LEFT JOIN lessons AS l ON l.course_id = c.id
            LEFT JOIN lesson_progress AS lp
                ON lp.lesson_id = l.id AND lp.user_id = $1
            WHERE c.user_id = $1
            GROUP BY c.id, c.title
            ORDER BY c.id
            """,
            user_id,
        )

    courses = []
    for row in rows:
        total = row["total_lessons"]
        completed = row["completed_lessons"]
        courses.append(
            CourseProgress(
                course_id=row["course_id"],
                title=row["title"],
                completed_lessons=completed,
                total_lessons=total,
                progress=int(completed / total * 100) if total else 0,
            )
        )

    return CourseProgressResponse(user_id=user_id, courses=courses)
