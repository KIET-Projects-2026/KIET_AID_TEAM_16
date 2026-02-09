import jwt
from flask import request, jsonify, g
from functools import wraps
from config import SECRET_KEY
from db.mongo import users
from bson.objectid import ObjectId


def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get('Authorization', None)
        if not auth:
            return jsonify({'error': 'Authorization header missing'}), 401
        parts = auth.split()
        if parts[0].lower() != 'bearer' or len(parts) != 2:
            return jsonify({'error': 'Invalid authorization header'}), 401
        token = parts[1]
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expired'}), 401
        except Exception:
            return jsonify({'error': 'Invalid token'}), 401

        user = users.find_one({'_id': ObjectId(payload['user_id'])})
        if not user:
            return jsonify({'error': 'User not found'}), 401

        g.user = user
        g.user_id = str(user['_id'])
        g.role = user.get('role', 'patient')
        return f(*args, **kwargs)
    return decorated


def require_role(role):
    def inner(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not hasattr(g, 'role'):
                return jsonify({'error': 'Unauthorized'}), 401
            if g.role != role:
                return jsonify({'error': 'Forbidden — insufficient role'}), 403
            return f(*args, **kwargs)
        return wrapper
    return inner
