from flask import Flask, jsonify, make_response, request
from flask_expects_json import expects_json

app = Flask(__name__)

# Constants

INTEREST_RATE = 2.5

# JSON schemas for endpoints

interest_schema = {
    "type": "object",
    "properties": {"interest_rate": {"type": "number"}},
    "required": ["interest_rate"],
}

# Flask setup


@app.errorhandler(400)
def bad_request(error):
    """Return the error as JSON in an 'error' field"""
    return make_response(jsonify({"error": error.description}), 400)


# Endpoints


@app.route("/interest-rate", methods=["PATCH"])
@expects_json(interest_schema)
def interest_rate():
    """
    Change the interest rate used by the application

    JSON Params:
        New interest rate
    Return:
        200: JSON with the old and new interest rates
        400: Incoming data had an error. Details in 'error' field
    """
    global INTEREST_RATE
    j = request.get_json()
    new_interest_rate = j["interest_rate"]
    old_interest_rate = INTEREST_RATE
    INTEREST_RATE = new_interest_rate
    return jsonify(
        {"old_interest_rate": old_interest_rate, "new_interest_rate": new_interest_rate}
    )
