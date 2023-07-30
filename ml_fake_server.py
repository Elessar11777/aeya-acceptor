import flask

@app.route('/ml_process', method=['POST'])
def ml_process():
    data = flask.request.get_json()
    if not data:
        return "No JSON data provided", 400
    else:
        data