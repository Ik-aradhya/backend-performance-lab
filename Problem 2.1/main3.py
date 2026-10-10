import json
import time

large_response = {
    "user_id": 42,
    "courses": [
        {
            "course_id": i,
            "title": f"Course {i}",
            "completed_lessons": 15,
            "total_lessons": 20,
            "progress": 75,
            
        }
        for i in range(1000)
    ],
}

start = time.perf_counter()
serialized = json.dumps(large_response)
elapsed_ms = (time.perf_counter() - start) * 1000

print(f"Serialization: {elapsed_ms:.3f} ms")
print(f"Payload size: {len(serialized.encode('utf-8')) / 1024:.2f} KB")