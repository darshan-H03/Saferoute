from functools import wraps
from flask import request, jsonify, g
import firebase_admin.auth

def firebase_auth_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Authorization token missing or invalid format."}), 401
        
        token = auth_header.split("Bearer ")[1].strip()
        try:
            decoded_token = firebase_admin.auth.verify_id_token(token)
            g.firebase_user = decoded_token
            g.user_id = decoded_token.get("uid")
        except Exception as e:
            return jsonify({"error": f"Invalid or expired Firebase token: {str(e)}"}), 401
            
        return f(*args, **kwargs)
    return decorated_function

def get_firebase_uid():
    return getattr(g, "user_id", None)
