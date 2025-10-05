# main_server.py
from wsgiref.simple_server import make_server
from spyne import Application, rpc, ServiceBase, Unicode, Integer, Boolean, Float, ComplexModel, Array
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication
import mysql.connector

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
    """Create a new database connection using db.properties."""
    return mysql.connector.connect(
        host=DB_CONFIG["DB_HOST"],
        user=DB_CONFIG["DB_USER"],
        password=DB_CONFIG["DB_PASS"],
        database=DB_CONFIG["DB_NAME"],
    )

# ---------------------------------------------------
# Entities (match DDL.sql shape)
#   student(ID, name, dept_name, tot_cred)
#   course(course_id, title, dept_name, credits)
# ---------------------------------------------------
class Student(ComplexModel):
    ID = Unicode
    name = Unicode
    dept_name = Unicode
    tot_cred = Integer

class Course(ComplexModel):
    course_id = Unicode
    title = Unicode
    dept_name = Unicode
    credits = Integer

# ---------------------------------------------------
# UtilityService: pure functions (no DB)
# ---------------------------------------------------
class UtilityService(ServiceBase):
    @rpc(Unicode, _returns=Unicode)
    def normalize_name(ctx, s):
        s = (s or "").strip()
        return " ".join(w.capitalize() for w in s.split())

    @rpc(Unicode, _returns=Boolean)
    def validate_student_id(ctx, s):
        """Very simple rule: 1 letter + 4 digits, e.g., S9009"""
        s = (s or "").strip()
        if len(s) == 5 and s[0].isalpha() and s[1:].isdigit():
            return True
        return False

# ---------------------------------------------------
# EntityService: minimal DB CRUD (kept small for teaching)
# ---------------------------------------------------
class EntityService(ServiceBase):
    # ---- STUDENTS ----
    @rpc(Unicode, Unicode, Unicode, Integer, _returns=Boolean)
    def create_student(ctx, ID, name, dept_name, tot_cred):
        try:
            conn = get_conn(); cur = conn.cursor()
            cur.execute(
                "INSERT INTO student (ID, name, dept_name, tot_cred) VALUES (%s, %s, %s, %s)",
                (ID, name, dept_name if dept_name else None, int(tot_cred or 0)),
            )
            conn.commit()
            return True
        except Exception as e:
            print("Entity.create_student error:", e)
            return False
        finally:
            try: cur.close(); conn.close()
            except: pass

    @rpc(Unicode, _returns=Student)
    def get_student(ctx, ID):
        try:
            conn = get_conn(); cur = conn.cursor(dictionary=True)
            cur.execute("SELECT ID, name, dept_name, tot_cred FROM student WHERE ID=%s", (ID,))
            row = cur.fetchone()
            if not row:
                return Student(ID="NOT_FOUND", name="", dept_name="", tot_cred=0)
            row["tot_cred"] = int(row["tot_cred"] or 0)
            return Student(**row)
        except Exception as e:
            print("Entity.get_student error:", e)
            return Student(ID="ERROR", name=str(e), dept_name="", tot_cred=0)
        finally:
            try: cur.close(); conn.close()
            except: pass

    @rpc(_returns=Array(Student))
    def list_students(ctx):
        out = []
        try:
            conn = get_conn(); cur = conn.cursor(dictionary=True)
            cur.execute("SELECT ID, name, dept_name, tot_cred FROM student ORDER BY ID")
            for r in cur.fetchall():
                out.append(Student(ID=r["ID"], name=r["name"], dept_name=r["dept_name"], tot_cred=int(r["tot_cred"] or 0)))
        except Exception as e:
            print("Entity.list_students error:", e)
        finally:
            try: cur.close(); conn.close()
            except: pass
        return out

    # ---- COURSES ----
    @rpc(Unicode, Unicode, Unicode, Integer, _returns=Boolean)
    def create_course(ctx, course_id, title, dept_name, credits):
        try:
            conn = get_conn(); cur = conn.cursor()
            cur.execute(
                "INSERT INTO course (course_id, title, dept_name, credits) VALUES (%s, %s, %s, %s)",
                (course_id, title, dept_name if dept_name else None, int(credits or 0)),
            )
            conn.commit()
            return True
        except Exception as e:
            print("Entity.create_course error:", e)
            return False
        finally:
            try: cur.close(); conn.close()
            except: pass

    @rpc(Unicode, _returns=Course)
    def get_course(ctx, course_id):
        try:
            conn = get_conn(); cur = conn.cursor(dictionary=True)
            cur.execute("SELECT course_id, title, dept_name, credits FROM course WHERE course_id=%s", (course_id,))
            row = cur.fetchone()
            if not row:
                return Course(course_id="NOT_FOUND", title="", dept_name="", credits=0)
            row["credits"] = int(row["credits"] or 0)
            return Course(**row)
        except Exception as e:
            print("Entity.get_course error:", e)
            return Course(course_id="ERROR", title=str(e), dept_name="", credits=0)
        finally:
            try: cur.close(); conn.close()
            except: pass

# ---------------------------------------------------
# TaskService (business process) that USES Utility + Entity
# NOTE: This service orchestrates; it is not an entity CRUD itself.
# ---------------------------------------------------
class OnboardResult(ComplexModel):
    success = Boolean
    normalized_name = Unicode
    tuition_estimate = Float
    message = Unicode

class TaskService(ServiceBase):
    @rpc(Unicode, Unicode, Unicode, Integer, Unicode, _returns=OnboardResult)
    def onboard_student_into_course(ctx, student_id, name, dept_name, init_credits, course_id):
        """
        Business process:
        1) Validate and normalize input (UtilityService)
        2) Create student (EntityService)
        3) Fetch course credits (EntityService)
        4) Ask microservice for tuition calculation (TuitionPolicyService)
        5) Return a single summarized result (OnboardResult)
        """
        # 1) validate + normalize
        if not UtilityService.validate_student_id(ctx, student_id):
            return OnboardResult(success=False, normalized_name="", tuition_estimate=0.0,
                                 message="Invalid student ID format")
        norm_name = UtilityService.normalize_name(ctx, name)

        # 2) create student
        ok = EntityService.create_student(ctx, student_id, norm_name, dept_name, init_credits)
        if not ok:
            return OnboardResult(success=False, normalized_name=norm_name, tuition_estimate=0.0,
                                 message="Failed to create student")

        # 3) get course info
        course = EntityService.get_course(ctx, course_id)
        if course.course_id in ("NOT_FOUND", "ERROR", None, ""):
            return OnboardResult(success=False, normalized_name=norm_name, tuition_estimate=0.0,
                                 message="Course not found")

        # 4) call microservice (TuitionPolicyService) via SOAP client
        #    We avoid hardcoding urls elsewhere; teaching purpose simplicity here.
        try:
            from zeep import Client
            micro = Client(wsdl="http://localhost:8001/?wsdl")
            # tuition is based solely on credits (non-breakable rule)
            tuition = float(micro.service.calc_tuition(course.credits))
        except Exception as e:
            print("TaskService tuition call error:", e)
            tuition = 0.0

        # 5) return consolidated result
        msg = f"Student {student_id} onboarded to {course.course_id}."
        return OnboardResult(success=True, normalized_name=norm_name, tuition_estimate=tuition, message=msg)

# ---------------------------------------------------
# Publish all services (TaskService consumes Utility/Entity internally)
# ---------------------------------------------------
app = Application(
    [UtilityService, EntityService, TaskService],
    tns="urn:examples.main",
    in_protocol=Soap11(validator="lxml"),
    out_protocol=Soap11(),
)
wsgi_app = WsgiApplication(app)

if __name__ == "__main__":
    print("Loaded DB config:", DB_CONFIG)
    server = make_server("0.0.0.0", 8000, wsgi_app)
    print("Main (Task) SOAP server on http://localhost:8000  (WSDL at ?wsdl)")
    server.serve_forever()
