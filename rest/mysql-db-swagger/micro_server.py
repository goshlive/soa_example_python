# micro_server.py (REST + Swagger)
from flask import Flask, request, jsonify
from flasgger import Swagger

app = Flask(__name__)
swagger = Swagger(app, template={
    "swagger": "2.0",
    "info": {"title": "Tuition Policy Service", "version": "1.0.0"},
    "basePath": "/",
    "schemes": ["http"],
})

# Very specific, non-breakable rules (no DB)
BASE_FEE = 100.0
PER_CREDIT = 50.0
MAX_CREDITS = 24

@app.get("/policy/calc_tuition")
def calc_tuition():
    """
    Calculate tuition
    ---
    tags: [Policy]
    parameters:
      - in: query
        name: credits
        type: integer
        required: true
        description: Number of credits (>= 0)
        default: 3
    responses:
      200:
        description: Tuition value
        schema:
          type: object
          properties:
            tuition: {type: number, format: float}
    """
    try:
        credits = int(request.args.get("credits", "0"))
    except ValueError:
        credits = 0
    tuition = BASE_FEE + PER_CREDIT * max(0, credits)
    return jsonify(tuition=float(tuition))

@app.get("/policy/max_credits")
def max_credits():
    """
    Maximum allowed credits
    ---
    tags: [Policy]
    responses:
      200:
        schema:
          type: object
          properties:
            max_credits: {type: integer}
    """
    return jsonify(max_credits=MAX_CREDITS)

if __name__ == "__main__":
    print("Swagger UI: http://localhost:8001/apidocs")
    app.run(host="0.0.0.0", port=8001, debug=False)
