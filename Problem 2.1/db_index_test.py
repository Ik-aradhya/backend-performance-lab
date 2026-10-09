import math
import sqlite3
import statistics
import tempfile
import time
from contextlib import closing
from pathlib import Path


DB_PATH = Path(__file__).resolve().with_name("courses.db")
INDEX_NAME = "idx_courses_user_id"
USER_ID = 5000
RUNS = 500


def _measure_queries(database_path, user_id=USER_ID, runs=RUNS):
    durations = []
    with closing(sqlite3.connect(database_path)) as conn:
        cursor = conn.cursor()
        for _ in range(runs):
            start = time.perf_counter()
            cursor.execute(
                "SELECT * FROM courses WHERE user_id = ?",
                (user_id,)
            )
            cursor.fetchall()
            durations.append((time.perf_counter() - start) * 1000)
    return durations


def without_index(database_path, user_id=USER_ID, runs=RUNS):
    with closing(sqlite3.connect(database_path)) as conn:
        conn.execute(f"DROP INDEX IF EXISTS {INDEX_NAME}")
        conn.commit()
    return _measure_queries(database_path, user_id, runs)


def with_index(database_path, user_id=USER_ID, runs=RUNS):
    with closing(sqlite3.connect(database_path)) as conn:
        conn.execute(
            f"CREATE INDEX IF NOT EXISTS {INDEX_NAME} ON courses(user_id)"
        )
        conn.commit()
    return _measure_queries(database_path, user_id, runs)


def percentile(durations, percentile_value):
    ordered = sorted(durations)
    position = (len(ordered) - 1) * percentile_value / 100
    lower_index = math.floor(position)
    upper_index = math.ceil(position)
    if lower_index == upper_index:
        return ordered[lower_index]
    fraction = position - lower_index
    return ordered[lower_index] + (
        ordered[upper_index] - ordered[lower_index]
    ) * fraction


def report(label, durations):
    print(f"{label} ({len(durations)} queries)")
    print(f"  average: {statistics.fmean(durations):.4f} ms")
    print(f"  p50:     {statistics.median(durations):.4f} ms")
    print(f"  p95:     {percentile(durations, 95):.4f} ms")
    print(f"  p99:     {percentile(durations, 99):.4f} ms")


with tempfile.TemporaryDirectory(prefix="course-index-benchmark-") as temp_dir:
    benchmark_path = Path(temp_dir) / "courses.db"
    with closing(sqlite3.connect(DB_PATH)) as source, closing(
        sqlite3.connect(benchmark_path)
    ) as copy:
        source.backup(copy)

    durations_without_index = without_index(benchmark_path)
    durations_with_index = with_index(benchmark_path)

report("Without index", durations_without_index)
report("With index", durations_with_index)