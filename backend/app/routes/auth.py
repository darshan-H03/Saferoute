"""
Authentication routes – Firebase Auth sync and user profile.
"""
from flask import Blueprint, jsonify, request, g
from app.firebase_auth import firebase_auth_required, get_firebase_uid
from app.firebase_admin_init import db as firestore_db

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/sync")
@firebase_auth_required
def sync_user():
    """
    Sync or create user document in Firestore upon Firebase registration / Google sign-in.
    Body JSON: { name?, email?, phone? }
    """
    uid = get_firebase_uid()
    data = request.get_json(silent=True) or {}

    user_info = getattr(g, "firebase_user", {})
    email = data.get("email") or user_info.get("email", "")
    name = data.get("name") or user_info.get("name") or email.split("@")[0] if email else "User"
    phone = data.get("phone") or user_info.get("phone_number")

    user_data = {
        "id": uid,
        "name": name,
        "email": email,
        "phone": phone,
        "provider": user_info.get("firebase", {}).get("sign_in_provider", "password")
    }

    if firestore_db:
        user_ref = firestore_db.collection("users").document(uid)
        doc = user_ref.get()
        if not doc.exists:
            user_ref.set(user_data)
        else:
            # Update existing with non-empty fields if necessary
            update_fields = {k: v for k, v in user_data.items() if v is not None}
            user_ref.update(update_fields)

    return jsonify({
        "message": "User profile synchronized successfully.",
        "user": user_data
    }), 200


@auth_bp.get("/me")
@firebase_auth_required
def me():
    """Return the currently authenticated user's profile from Firebase/Firestore."""
    uid = get_firebase_uid()
    user_info = getattr(g, "firebase_user", {})
    
    if firestore_db:
        doc = firestore_db.collection("users").document(uid).get()
        if doc.exists:
            return jsonify({"user": doc.to_dict()}), 200

    # Fallback to token claims
    email = user_info.get("email", "")
    return jsonify({
        "user": {
            "id": uid,
            "name": user_info.get("name") or (email.split("@")[0] if email else "User"),
            "email": email,
            "phone": user_info.get("phone_number")
        }
    }), 200


@auth_bp.put("/me")
@firebase_auth_required
def update_me():
    """
    Update basic profile fields in Firestore.
    Body JSON: { name?, phone? }
    """
    uid = get_firebase_uid()
    data = request.get_json(silent=True) or {}

    updates = {}
    if "name" in data:
        name = (data.get("name") or "").strip()
        if not name:
            return jsonify({"error": "Name cannot be empty."}), 400
        updates["name"] = name

    if "phone" in data:
        updates["phone"] = (data.get("phone") or "").strip() or None

    if firestore_db and updates:
        user_ref = firestore_db.collection("users").document(uid)
        user_ref.set(updates, merge=True)

    return jsonify({"message": "Profile updated."}), 200
