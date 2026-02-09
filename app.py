from flask import Flask, jsonify, request
from flask_cors import CORS
from routes.auth import auth_bp
from routes.chatbot import chat_bp
import logging

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)
CORS(app)

app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(chat_bp, url_prefix="/api/chat")


@app.route('/')
def index():
    return jsonify({'status': 'ok', 'message': 'Healthcare Chatbot backend running', 'routes': [r.rule for r in app.url_map.iter_rules()]})


@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found', 'path': request.path}), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Server error'}), 500


if __name__ == "__main__":
    logging.info("Registered routes:")
    for r in app.url_map.iter_rules():
        logging.info(f"{r.rule} -> {r.endpoint}")
    app.run(host='0.0.0.0', debug=True)

