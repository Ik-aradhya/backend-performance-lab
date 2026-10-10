import sqlite3
import time
import random
import statistics


DB_NAME = "courses.db"
NUM_ROWS = 100_000
NUM_RUNS = 100
USER_ID = 5000


def create_database():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS courses")

    cursor.execute("""
        CREATE TABLE courses (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL
        )
    """)

    data = [
        (i, random.randint(1, 10_000), f"Course {i}")
        for i in range(1, NUM_ROWS + 1)
    ]

    cursor.executemany(
        "INSERT INTO courses (id, user_id, title) VALUES (?, ?, ?)",
        data,
    )

    conn.commit()
    conn.close()


def benchmark_query(conn, user_id, runs=NUM_RUNS):
    cursor = conn.cursor()
    timings = []

    for _ in range(runs):
        start = time.perf_counter()

        cursor.execute(
            "SELECT * FROM courses WHERE user_id = ?",
            (user_id,),
        )
        cursor.fetchall()

        end = time.perf_counter()
        timings.append((end - start) * 1000)

    return timings


def print_stats(label, timings):
    print(f"\n{label}")
    print(f"Average: {statistics.mean(timings):.4f} ms")
    print(f"P50:     {statistics.median(timings):.4f} ms")
    print(f"P95:     {statistics.quantiles(timings, n=100)[94]:.4f} ms")
    print(f"P99:     {statistics.quantiles(timings, n=100)[98]:.4f} ms")


if __name__ == "__main__":
    create_database()

    conn = sqlite3.connect(DB_NAME)

    # Stage 1: Without index
    conn.execute("DROP INDEX IF EXISTS idx_courses_user_id")
    conn.commit()

    timings_without_index = benchmark_query(conn, USER_ID)
    print_stats("WITHOUT INDEX", timings_without_index)

    # Stage 2: With index
    conn.execute("""
        CREATE INDEX idx_courses_user_id
        ON courses(user_id)
    """)
    conn.commit()

    timings_with_index = benchmark_query(conn, USER_ID)
    print_stats("WITH INDEX", timings_with_index)

    conn.close()