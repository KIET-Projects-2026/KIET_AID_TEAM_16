from flask import Blueprint, request, jsonify
from db.mongo import users
import bcrypt
import jwt
from config import SECRET_KEY
from bson.objectid import ObjectId

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/signup", methods=["POST"])
def signup():
    data = request.json
    email = (data.get("email") or "").strip().lower()
    name = (data.get("name") or "").strip()
    password = data.get("password")

    # Basic validation
    if not name or not email or not password:
        return jsonify({"error": "Name, email and password are required"}), 400

    # Enforce gmail domain
    if not email.endswith("@gmail.com"):
        return jsonify({"error": "Email must be a @gmail.com address"}), 400

    if users.find_one({"email": email}):
        return jsonify({"error": "User already exists"}), 400

    role = data.get("role", "patient")  # 'doctor' or 'patient'
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    res = users.insert_one({
        "name": name,
        "email": email,
        "password": hashed,
        "role": role
    })
    user_id = str(res.inserted_id)
    token = jwt.encode({"user_id": user_id, "email": email, "role": role}, SECRET_KEY, algorithm="HS256")
    return jsonify({"message": "Signup successful", "token": token, "user_id": user_id})

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.json
    email = (data.get("email") or "").strip().lower()
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    if not email.endswith("@gmail.com"):
        return jsonify({"error": "Email must be a @gmail.com address"}), 400

    user = users.find_one({"email": email})
    if not user or not bcrypt.checkpw(password.encode(), user["password"]):
        return jsonify({"error": "Invalid credentials"}), 401

    user_id = str(user["_id"])
    token = jwt.encode({"user_id": user_id, "email": user["email"], "role": user.get("role", "patient")}, SECRET_KEY, algorithm="HS256")

    return jsonify({
        "message": "Login successful",
        "token": token,
        "user_id": user_id,
        "name": user["name"],
        "role": user.get("role", "patient")
    })

@auth_bp.route('/me', methods=['GET'])
def me():
    auth = request.headers.get('Authorization')
    if not auth:
        return jsonify({'error': 'Authorization header required'}), 401
    parts = auth.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        return jsonify({'error': 'Invalid authorization header'}), 401
    token = parts[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    except Exception:
        return jsonify({'error': 'Invalid token'}), 401

    user = users.find_one({'_id': ObjectId(payload['user_id'])}, {'password': 0})
    if not user:
        return jsonify({'error': 'User not found'}), 404
    user['_id'] = str(user['_id'])
    return jsonify({'user': user})

@auth_bp.route('/users', methods=['GET'])
def list_users():
    # list all patients (doctors should call this via auth on frontend)
    role = request.args.get('role')
    query = {}
    if role:
        query['role'] = role
    docs = list(users.find(query, {'password': 0}))
    for d in docs:
        d['_id'] = str(d['_id'])
    return jsonify({'users': docs})
