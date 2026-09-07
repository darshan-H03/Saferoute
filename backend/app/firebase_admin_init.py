import os
import firebase_admin
from firebase_admin import credentials, firestore

# Export the firestore client so it can be used across the app
db = None

def init_firebase(app):
    global db
    
    # Path to your service account JSON file
    cred_path = app.config.get("FIREBASE_SERVICE_ACCOUNT_PATH", "firebase-service-account.json")
    
    if not os.path.exists(cred_path):
        app.logger.warning(f"Firebase credentials not found at {cred_path}. Firebase will not work.")
        return

    # Check if already initialized to prevent errors in testing or hot-reloading
    if not firebase_admin._apps:
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        app.logger.info("Firebase Admin SDK initialized successfully.")
    
    db = firestore.client()
