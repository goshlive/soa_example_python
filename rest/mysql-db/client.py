# client.py (REST client)
import requests
import json

MAIN = "http://localhost:8000"
MICRO = "http://localhost:8001"

def pp(title, obj):
    print(f"\n== {title} ==")
    print(json.dumps(obj, indent=2))

# --- SETUP: create a course (Entity) ---
r = requests.post(f"{MAIN}/entity/courses", json={
    "course_id": "CS-909",
    "title": "Intro to Database",
    "dept_name": "Inf. Sys.",
    "credits": 3
})
pp("SETUP create course CS-909", {"status": r.status_code, "body": r.json() if r.content else None})

# --- TASK: onboard a student into a course (business process) ---
r = requests.post(f"{MAIN}/task/onboard_student_into_course", json={
    "student_id": "S9009",
    "name": "  alice smith ",
    "dept_name": "Inf. Sys.",
    "init_credits": 0,
    "course_id": "CS-909"
})
res = r.json()
pp("TASK onboard_student_into_course", res)

# --- POLICY: fixed rules (microservice) ---
r1 = requests.get(f"{MICRO}/policy/max_credits")
r2 = requests.get(f"{MICRO}/policy/calc_tuition", params={"credits": 3})
pp("POLICY max_credits", r1.json())
pp("POLICY tuition for 3 credits", r2.json())

# --- ENTITY: verify data created ---
r = requests.get(f"{MAIN}/entity/students")
pp("ENTITY list_students", r.json())

r = requests.get(f"{MAIN}/entity/courses/CS-909")
pp("ENTITY get_course CS-909", r.json())
