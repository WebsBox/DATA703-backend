from flask import jsonify

def ok(data=None, message="success", status=200):
    body = {"code": status, "message": message}
    if data is not None:
        body["data"] = data
    return jsonify(body), status

def fail(message="error", status=400, data=None):
    body = {"code": status, "message": message}
    if data is not None:
        body["data"] = data
    return jsonify(body), status
