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
from datetime import datetime, timezone

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
CORS(app, supports_credentials=True) 
bcrypt = Bcrypt(app)

# -----------------------
# MongoDB setup
# -----------------------
MONGO_URI = os.environ.get("MONGO_URI")
if not MONGO_URI:
    raise ValueError("MONGO_URI environment variable not set")
    
client = MongoClient(MONGO_URI)
db = client.get_database() 
users_collection = db.users
predictions_collection = db.predictions
chatbot_collection = db.chatbot_history

# -----------------------
# JWT setup
# -----------------------
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "a-super-secret-key-that-is-long")
app.config["JWT_SECRET_KEY"] = JWT_SECRET_KEY
jwt = JWTManager(app)

# -----------------------
# Auth: Register endpoint
# -----------------------
@app.route("/api/auth/register", methods=["POST"])
def register():
    try:
        data = request.get_json()
        if not data or not data.get('name') or not data.get('email') or not data.get('password'):
            return jsonify({"msg": "Missing name, email, or password"}), 400

        name = data['name']
        email = data['email'].lower()
        password = data['password']

        if users_collection.find_one({"email": email}):
            return jsonify({"msg": "User with this email already exists"}), 409

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        users_collection.insert_one({
            "name": name, "email": email, "password": hashed_password
        })
        return jsonify({"msg": "User registered successfully"}), 201
    except Exception as e:
        logging.error(f"Error in registration: {e}")
        return jsonify({"msg": "An internal error occurred"}), 500

# -----------------------
# Auth: Login endpoint
# -----------------------
@app.route("/api/auth/login", methods=["POST"])
def login():
    try:
        data = request.get_json()
        email = data["email"].lower()
        password = data["password"]
        user = users_collection.find_one({"email": email})

        if user and bcrypt.check_password_hash(user["password"], password):
            user_info = {"id": str(user["_id"]), "name": user["name"], "email": user["email"]}
            access_token = create_access_token(identity=str(user["_id"]))
            return jsonify(token=access_token, user=user_info), 200
        return jsonify({"msg": "Invalid credentials"}), 401
    except Exception as e:
        logging.error(f"Error in login: {e}")
        return jsonify({"msg": "An internal error occurred"}), 500

# -----------------------
# Profile: Get User Data endpoint
# -----------------------
@app.route("/api/profile/<string:email>", methods=["GET"])
@jwt_required()
def get_profile_by_email(email):
    try:
        current_user_id = get_jwt_identity()
        user = users_collection.find_one({"email": email.lower()})

        if not user or str(user["_id"]) != current_user_id:
             return jsonify({"msg": "User not found or unauthorized"}), 404

        user_info = {
            "id": str(user["_id"]),
            "name": user.get("name"),
            "email": user.get("email"),
            "profilePhoto": user.get("profilePhoto")
        }
        return jsonify(user_info), 200
    except Exception as e:
        logging.error(f"Error fetching profile by email: {e}")
        return jsonify({"msg": "An internal error occurred"}), 500

# -----------------------
# Prediction: Upload MRI scan and save result
# -----------------------
@app.route("/api/predict/upload", methods=["POST"])
@jwt_required()
def upload_mri():
    if "mriScan" not in request.files:
        return jsonify({"msg": "No file part in the request"}), 400
    file = request.files["mriScan"]
    if file.filename == '':
        return jsonify({"msg": "No file selected for uploading"}), 400

    current_user_id = get_jwt_identity()
    filename = secure_filename(file.filename)
    
    # --- TODO: Replace with your actual ML model logic ---
    prediction_result = {"result": "Tumor Detected", "confidence": "95.0%"}

    try:
        predictions_collection.insert_one({
            "userId": ObjectId(current_user_id),
            "filename": filename,
            "result": prediction_result["result"],
            "confidence": prediction_result["confidence"],
            "timestamp": datetime.now(timezone.utc)
        })
    except Exception as e:
        logging.error(f"Error saving prediction to DB: {e}")
    
    return jsonify({"prediction": prediction_result}), 200

# -----------------------
# Dashboard: Get prediction statistics
# -----------------------
@app.route("/api/predict/stats", methods=["GET"])
@jwt_required()
def get_prediction_stats():
    try:
        current_user_id = get_jwt_identity()
        
        cursor = predictions_collection.find(
            {"userId": ObjectId(current_user_id)}
        ).sort("timestamp", -1).limit(10)

        recent_predictions = [{
            "date": pred.get("timestamp").strftime("%Y-%m-%d %H:%M"),
            "filename": pred.get("filename", "N/A"),
            "result": pred.get("result"),
            "confidence": pred.get("confidence")
        } for pred in cursor]

        tumor_count = predictions_collection.count_documents({
            "userId": ObjectId(current_user_id), "result": "Tumor Detected"
        })
        no_tumor_count = predictions_collection.count_documents({
            "userId": ObjectId(current_user_id), "result": {"$ne": "Tumor Detected"}
        })

        return jsonify({
            "recent_predictions": recent_predictions,
            "total_counts": {"tumor": tumor_count, "no_tumor": no_tumor_count}
        }), 200
    except Exception as e:
        logging.error(f"Error fetching prediction stats: {e}")
        return jsonify({"msg": "An internal error occurred"}), 500

# ==========================================================
# CHATBOT 'ASK' ENDPOINT
# ==========================================================
@app.route("/api/chatbot/ask", methods=["POST"])
@jwt_required()
def ask_chatbot():
    try:
        data = request.get_json()
        question = data.get("question")
        if not question:
            return jsonify({"msg": "No question provided"}), 400
        
        current_user_id = get_jwt_identity()
        
        # --- TODO: Replace with actual AI/NLP logic ---
        # For now, we provide a simple, static answer.
        answer = f"Thank you for asking about '{question}'. This is a placeholder response. For medical advice, please consult a professional."

        # Save the conversation to history
        chatbot_collection.insert_one({
            "userId": ObjectId(current_user_id),
            "question": question,
            "answer": answer,
            "timestamp": datetime.now(timezone.utc)
        })
        
        return jsonify({"answer": answer}), 200
    except Exception as e:
        logging.error(f"Error in chatbot ask endpoint: {e}")
        return jsonify({"msg": "An internal error occurred"}), 500

# ==========================================================
# CHATBOT HISTORY ENDPOINT
# ==========================================================
@app.route("/api/chatbot/history", methods=["GET"])
@jwt_required()
def get_chat_history():
    try:
        current_user_id = get_jwt_identity()
        
        cursor = chatbot_collection.find(
            {"userId": ObjectId(current_user_id)}
        ).sort("timestamp", -1)

        history = [{
            "question": chat.get("question"),
            "answer": chat.get("answer"),
            "timestamp": chat.get("timestamp").strftime("%Y-%m-%d %H:%M")
        } for chat in cursor]
        
        return jsonify(history), 200
    except Exception as e:
        logging.error(f"Error fetching chat history: {e}")
        return jsonify({"msg": "An internal error occurred"}), 500

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
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)

