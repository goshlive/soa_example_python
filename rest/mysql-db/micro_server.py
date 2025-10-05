# micro_server.py (REST version)
from flask import Flask, request, jsonify

app = Flask(__name__)

# Very specific, non-breakable rules (no DB)
BASE_FEE = 100.0
PER_CREDIT = 50.0
MAX_CREDITS = 24

@app.get("/policy/calc_tuition")
def calc_tuition():
    # /policy/calc_tuition?credits=3
    try:
        credits = int(request.args.get("credits", "0"))
    except ValueError:
        credits = 0
    tuition = BASE_FEE + PER_CREDIT * max(0, credits)
    return jsonify(tuition=float(tuition))

@app.get("/policy/max_credits")
def max_credits():
    return jsonify(max_credits=MAX_CREDITS)

if __name__ == "__main__":
    print("Micro (Tuition Policy) REST server on http://localhost:8001")
    app.run(host="0.0.0.0", port=8001, debug=False)
