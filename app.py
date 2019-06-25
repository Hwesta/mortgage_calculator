from flask import Flask, jsonify, make_response

app = Flask(__name__)

# Flask setup


@app.errorhandler(400)
def bad_request(error):
    """Return the error as JSON in an 'error' field"""
    return make_response(jsonify({"error": error.description}), 400)
