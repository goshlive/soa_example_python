# client.py
from zeep import Client

# Connect to both services
task = Client(wsdl="http://localhost:8000/?wsdl")    # TaskService + Utility/Entity behind it
policy = Client(wsdl="http://localhost:8001/?wsdl")  # TuitionPolicyService (non-breakable)

# --- Prepare a course via EntityService (exposed on main_server but not the focus) ---
print("== SETUP: Create course CS-909 ==")
print(task.service.create_course("CS-909", "Intro to Database", "Inf. Sys.", 3))

# --- Business process: Onboard a student into a course (TaskService) ---
print("\n== TASK: Onboard student into course ==")
res = task.service.onboard_student_into_course("S9009", "  alice smith ", "Inf. Sys.", 0, "CS-909")
print("success:", res.success)
print("normalized_name:", res.normalized_name)
print("tuition_estimate:", res.tuition_estimate)
print("message:", res.message)

# --- Demonstrate microservice's fixed rules independently (optional) ---
print("\n== POLICY: Fixed rules ==")
print("Max credits allowed:", policy.service.max_credits())
print("Tuition for 3 credits:", policy.service.calc_tuition(3))

# --- Show that entity data was actually created (optional inspection) ---
print("\n== ENTITY: List students after onboarding ==")
for s in task.service.list_students():
    print(s.ID, s.name, s.dept_name, s.tot_cred)

print("\n== ENTITY: Get course CS-909 ==")
c = task.service.get_course("CS-909")
print(c.course_id, c.title, c.dept_name, c.credits)
