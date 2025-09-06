from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_bcrypt import Bcrypt
from pymongo import MongoClient
from bson.objectid import ObjectId
from dotenv import load_dotenv
import os
from werkzeug.utils import secure_filename
import logging

# -----------------------
# Basic Logging Setup
# -----------------------
logging.basicConfig(level=logging.INFO)

# -----------------------
# Load .env variables
# -----------------------
load_dotenv()

# -----------------------
# Create Flask app
# -----------------------
app = Flask(__name__)
# Allow all origins for simplicity in this example. For production, you'd restrict this.
CORS(app, supports_credentials=True) 
bcrypt = Bcrypt(app)

# -----------------------
# MongoDB setup
# -----------------------
MONGO_URI = os.environ.get("MONGO_URI")
if not MONGO_URI:
    raise ValueError("MONGO_URI environment variable not set")
    
# Use MongoClient directly for better control
client = MongoClient(MONGO_URI)
db = client.get_database() # The database name is part of your MONGO_URI
users_collection = db.users
predictions_collection = db.predictions
chatbot_collection = db.chatbot_history

# -----------------------
# JWT setup
# -----------------------
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "a-super-secret-key-that-is-long")
app.config["JWT_SECRET_KEY"] = JWT_SECRET_KEY
jwt = JWTManager(app)

# ==========================================================
# NEW AND REQUIRED - Auth: Register endpoint
# ==========================================================
@app.route("/api/auth/register", methods=["POST"])
def register():
    try:
        data = request.get_json()
        if not data or not data.get('name') or not data.get('email') or not data.get('password'):
            return jsonify({"msg": "Missing name, email, or password"}), 400

        name = data['name']
        email = data['email'].lower() # Store email in lowercase to prevent duplicates
        password = data['password']

        # Check if user already exists
        if users_collection.find_one({"email": email}):
            return jsonify({"msg": "User with this email already exists"}), 409

        # --- THIS IS THE CRITICAL FIX ---
        # Hash the password before storing it
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        # Insert the new user with the hashed password
        users_collection.insert_one({
            "name": name,
            "email": email,
            "password": hashed_password  # <-- Store the hashed version
        })

        return jsonify({"msg": "User registered successfully"}), 201

    except Exception as e:
        logging.error(f"Error in registration: {e}")
        return jsonify({"msg": "An internal error occurred"}), 500


# -----------------------
# Auth: Login endpoint (No changes needed here)
# -----------------------
@app.route("/api/auth/login", methods=["POST"])
def login():
    try:
        data = request.get_json()
        if not data or "email" not in data or "password" not in data:
            return jsonify({"msg": "Email and password required"}), 400

        email = data["email"].lower()
        password = data["password"]

        user = users_collection.find_one({"email": email})

        # This line will now work because the password in the DB is hashed
        if user and bcrypt.check_password_hash(user["password"], password):
            # Include user details in the response
            user_info = {
                "id": str(user["_id"]),
                "name": user["name"],
                "email": user["email"]
            }
            access_token = create_access_token(identity=str(user["_id"]))
            return jsonify(token=access_token, user=user_info), 200

        return jsonify({"msg": "Invalid credentials"}), 401
    except Exception as e:
        logging.error(f"Error in login: {e}")
        return jsonify({"msg": "An internal error occurred"}), 500

# -----------------------
# Upload MRI scan endpoint
# -----------------------
@app.route("/api/predict/upload", methods=["POST"])
@jwt_required()
def upload_mri():
    if "mriScan" not in request.files:
        return jsonify({"msg": "No file part in the request"}), 400

    file = request.files["mriScan"]
    if file.filename == '':
        return jsonify({"msg": "No file selected for uploading"}), 400

    # For security, always use secure_filename
    filename = secure_filename(file.filename)
    
    # In a real app, you would process this file with a model
    # Here we just simulate a prediction
    # You could save the file if needed, but for prediction it's often done in memory
    
    # --- TODO: Replace with your actual ML model logic ---
    prediction_result = {"result": "Tumor Detected", "confidence": "95.0%"}

    return jsonify({"prediction": prediction_result}), 200

# -----------------------
# Root endpoint
# -----------------------
@app.route("/", methods=["GET"])
def root():
    return jsonify({"msg": "Spinal Cord Tumor Detection API is running"}), 200

# -----------------------
# Run app
# -----------------------
if __name__ == "__main__":
    # Use PORT from environment variables, default to 5000 for local dev
    port = int(os.environ.get("PORT", 5000))
    # debug=False is important for production on Render
    app.run(host="0.0.0.0", port=port, debug=False)
