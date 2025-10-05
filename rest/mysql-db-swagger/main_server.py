# main_server.py (REST + Swagger)
from flask import Flask, request, jsonify
import mysql.connector
import requests
from flasgger import Swagger

# ---------------------------------------------------
# Load DB config from external properties file
# ---------------------------------------------------
def load_db_config(filename="db.properties"):
    cfg = {}
    with open(filename) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            key, value = line.split("=", 1)
            cfg[key.strip()] = value.strip()
    return cfg

DB_CONFIG = load_db_config()

def get_conn():
    return mysql.connector.connect(
        host=DB_CONFIG["DB_HOST"],
        user=DB_CONFIG["DB_USER"],
        password=DB_CONFIG["DB_PASS"],
        database=DB_CONFIG["DB_NAME"],
    )

# ---------------------------------------------------
# Internal utilities (not necessarily exposed)
# ---------------------------------------------------
def normalize_name(s: str) -> str:
    s = (s or "").strip()
    return " ".join(w.capitalize() for w in s.split())

def validate_student_id(s: str) -> bool:
    s = (s or "").strip()
    return len(s) == 5 and s[0].isalpha() and s[1:].isdigit()

# ---------------------------------------------------
# Flask + Swagger
# ---------------------------------------------------
app = Flask(__name__)
swagger = Swagger(app, template={
    "swagger": "2.0",
    "info": {"title": "University Task Service", "version": "1.0.0"},
    "basePath": "/",
    "schemes": ["http"],
})

# ---------------------------------------------------
# ENTITY ENDPOINTS (DB CRUD)
#   student(ID, name, dept_name, tot_cred)
#   course(course_id, title, dept_name, credits)
# ---------------------------------------------------
@app.post("/entity/students")
def create_student():
    """
    Create a student
    ---
    tags: [Entity:Student]
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [ID, name]
          properties:
            ID: {type: string, example: "S1001"}
            name: {type: string, example: "Alice Smith"}
            dept_name: {type: string, example: "Comp. Sci."}
            tot_cred: {type: integer, example: 0}
    responses:
      201:
        description: Created
        schema: {type: object, properties: {ok: {type: boolean}}}
      400:
        description: Error
    """
    data = request.get_json(force=True)
    ID = data.get("ID")
    name = data.get("name")
    dept_name = data.get("dept_name")
    tot_cred = int(data.get("tot_cred") or 0)
    try:
        conn = get_conn(); cur = conn.cursor()
        cur.execute(
            "INSERT INTO student (ID, name, dept_name, tot_cred) VALUES (%s, %s, %s, %s)",
            (ID, name, dept_name if dept_name else None, tot_cred),
        )
        conn.commit()
        return jsonify(ok=True), 201
    except Exception as e:
        print("create_student error:", e)
        return jsonify(ok=False, error=str(e)), 400
    finally:
        try: cur.close(); conn.close()
        except: pass

@app.get("/entity/students/<ID>")
def get_student(ID):
    """
    Get a student
    ---
    tags: [Entity:Student]
    parameters:
      - in: path
        name: ID
        type: string
        required: true
    responses:
      200:
        description: The student
        schema:
          type: object
          properties:
            ID: {type: string}
            name: {type: string}
            dept_name: {type: string}
            tot_cred: {type: integer}
      404:
        description: Not found
    """
    try:
        conn = get_conn(); cur = conn.cursor(dictionary=True)
        cur.execute("SELECT ID, name, dept_name, tot_cred FROM student WHERE ID=%s", (ID,))
        row = cur.fetchone()
        if not row:
            return jsonify(error="NOT_FOUND"), 404
        row["tot_cred"] = int(row["tot_cred"] or 0)
        return jsonify(row)
    except Exception as e:
        print("get_student error:", e)
        return jsonify(error=str(e)), 400
    finally:
        try: cur.close(); conn.close()
        except: pass

@app.get("/entity/students")
def list_students():
    """
    List students
    ---
    tags: [Entity:Student]
    responses:
      200:
        description: List of students
        schema:
          type: array
          items:
            type: object
            properties:
              ID: {type: string}
              name: {type: string}
              dept_name: {type: string}
              tot_cred: {type: integer}
    """
    out = []
    try:
        conn = get_conn(); cur = conn.cursor(dictionary=True)
        cur.execute("SELECT ID, name, dept_name, tot_cred FROM student ORDER BY ID")
        for r in cur.fetchall():
            out.append({"ID": r["ID"], "name": r["name"], "dept_name": r["dept_name"], "tot_cred": int(r["tot_cred"] or 0)})
        return jsonify(out)
    except Exception as e:
        print("list_students error:", e)
        return jsonify(error=str(e)), 400
    finally:
        try: cur.close(); conn.close()
        except: pass

@app.post("/entity/courses")
def create_course():
    """
    Create a course
    ---
    tags: [Entity:Course]
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [course_id, title]
          properties:
            course_id: {type: string, example: "CS-909"}
            title: {type: string, example: "Intro to DB"}
            dept_name: {type: string, example: "Inf. Sys."}
            credits: {type: integer, example: 3}
    responses:
      201:
        description: Created
        schema: {type: object, properties: {ok: {type: boolean}}}
      400:
        description: Error
    """
    data = request.get_json(force=True)
    course_id = data.get("course_id")
    title = data.get("title")
    dept_name = data.get("dept_name")
    credits = int(data.get("credits") or 0)
    try:
        conn = get_conn(); cur = conn.cursor()
        cur.execute(
            "INSERT INTO course (course_id, title, dept_name, credits) VALUES (%s, %s, %s, %s)",
            (course_id, title, dept_name if dept_name else None, credits),
        )
        conn.commit()
        return jsonify(ok=True), 201
    except Exception as e:
        print("create_course error:", e)
        return jsonify(ok=False, error=str(e)), 400
    finally:
        try: cur.close(); conn.close()
        except: pass

@app.get("/entity/courses/<course_id>")
def get_course(course_id):
    """
    Get a course
    ---
    tags: [Entity:Course]
    parameters:
      - in: path
        name: course_id
        type: string
        required: true
    responses:
      200:
        description: The course
        schema:
          type: object
          properties:
            course_id: {type: string}
            title: {type: string}
            dept_name: {type: string}
            credits: {type: integer}
      404:
        description: Not found
    """
    try:
        conn = get_conn(); cur = conn.cursor(dictionary=True)
        cur.execute("SELECT course_id, title, dept_name, credits FROM course WHERE course_id=%s", (course_id,))
        row = cur.fetchone()
        if not row:
            return jsonify(error="NOT_FOUND"), 404
        row["credits"] = int(row["credits"] or 0)
        return jsonify(row)
    except Exception as e:
        print("get_course error:", e)
        return jsonify(error=str(e)), 400
    finally:
        try: cur.close(); conn.close()
        except: pass

# ---------------------------------------------------
# TASK ENDPOINT (business process) – calls microservice (REST)
# ---------------------------------------------------
@app.post("/task/onboard_student_into_course")
def onboard_student_into_course():
    """
    Onboard a student into a course
    ---
    tags: [Task]
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [student_id, name, course_id]
          properties:
            student_id: {type: string, example: "S9009"}
            name: {type: string, example: "alice smith"}
            dept_name: {type: string, example: "Inf. Sys."}
            init_credits: {type: integer, example: 0}
            course_id: {type: string, example: "CS-909"}
    responses:
      200:
        description: Onboarding result
        schema:
          type: object
          properties:
            success: {type: boolean}
            normalized_name: {type: string}
            tuition_estimate: {type: number, format: float}
            message: {type: string}
      400:
        description: Validation or processing error
    """
    data = request.get_json(force=True)
    student_id = data.get("student_id", "")
    name = data.get("name", "")
    dept_name = data.get("dept_name")
    init_credits = int(data.get("init_credits") or 0)
    course_id = data.get("course_id", "")

    if not validate_student_id(student_id):
        return jsonify(success=False, normalized_name="", tuition_estimate=0.0,
                       message="Invalid student ID format"), 400
    norm_name = normalize_name(name)

    try:
        conn = get_conn(); cur = conn.cursor()
        cur.execute(
            "INSERT INTO student (ID, name, dept_name, tot_cred) VALUES (%s, %s, %s, %s)",
            (student_id, norm_name, dept_name if dept_name else None, init_credits),
        )
        conn.commit()
    except Exception as e:
        print("task.create_student error:", e)
        return jsonify(success=False, normalized_name=norm_name, tuition_estimate=0.0,
                       message="Failed to create student"), 400
    finally:
        try: cur.close(); conn.close()
        except: pass

    try:
        conn = get_conn(); cur = conn.cursor(dictionary=True)
        cur.execute("SELECT credits FROM course WHERE course_id=%s", (course_id,))
        row = cur.fetchone()
        if not row:
            return jsonify(success=False, normalized_name=norm_name, tuition_estimate=0.0,
                           message="Course not found"), 404
        credits = int(row["credits"] or 0)
    except Exception as e:
        print("task.get_course error:", e)
        return jsonify(success=False, normalized_name=norm_name, tuition_estimate=0.0,
                       message=str(e)), 400
    finally:
        try: cur.close(); conn.close()
        except: pass

    try:
        resp = requests.get("http://localhost:8001/policy/calc_tuition", params={"credits": credits}, timeout=5)
        tuition = float(resp.json().get("tuition", 0.0)) if resp.ok else 0.0
    except Exception as e:
        print("task.micro_call error:", e)
        tuition = 0.0

    msg = f"Student {student_id} onboarded to {course_id}."
    return jsonify(success=True, normalized_name=norm_name, tuition_estimate=tuition, message=msg)

# ---------------------------------------------------
# Optional utility endpoints (documented)
# ---------------------------------------------------
@app.get("/utility/normalize")
def util_norm():
    """
    Normalize a name
    ---
    tags: [Utility]
    parameters:
      - in: query
        name: s
        type: string
        required: true
    responses:
      200:
        schema: {type: object, properties: {result: {type: string}}}
    """
    s = request.args.get("s", "")
    return jsonify(result=normalize_name(s))

@app.get("/utility/validate_student_id")
def util_validate():
    """
    Validate a student ID
    ---
    tags: [Utility]
    parameters:
      - in: query
        name: s
        type: string
        required: true
    responses:
      200:
        schema: {type: object, properties: {valid: {type: boolean}}}
    """
    s = request.args.get("s", "")
    return jsonify(valid=validate_student_id(s))

# ---------------------------------------------------
# Run
# ---------------------------------------------------
if __name__ == "__main__":
    print("Swagger UI: http://localhost:8000/apidocs")
    print("Loaded DB config:", DB_CONFIG)
    app.run(host="0.0.0.0", port=8000, debug=False)
