from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_bcrypt import Bcrypt
from flask_pymongo import PyMongo
from dotenv import load_dotenv
import os

# -----------------------
# Load .env variables (optional, for local testing)
# -----------------------
load_dotenv()

# -----------------------
# Create Flask app
# -----------------------
app = Flask(__name__)
CORS(app)
bcrypt = Bcrypt(app)

# -----------------------
# MongoDB setup
# -----------------------
MONGO_URI = os.environ.get("MONGO_URI")
if not MONGO_URI:
    raise ValueError("MONGO_URI environment variable not set")

app.config["MONGO_URI"] = MONGO_URI
mongo = PyMongo(app)

# -----------------------
# JWT setup
# -----------------------
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "super-secret-key")
app.config["JWT_SECRET_KEY"] = JWT_SECRET_KEY
jwt = JWTManager(app)

# -----------------------
# Auth: Login endpoint
# -----------------------
@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data or "email" not in data or "password" not in data:
        return jsonify({"msg": "Email and password required"}), 400

    email = data["email"]
    password = data["password"]

    user = mongo.db.users.find_one({"email": email})
    if user and bcrypt.check_password_hash(user["password"], password):
        access_token = create_access_token(identity=str(user["_id"]))
        return jsonify({"token": access_token}), 200

    return jsonify({"msg": "Invalid credentials"}), 401

# -----------------------
# Upload MRI scan endpoint
# -----------------------
@app.route("/api/predict/upload", methods=["POST"])
@jwt_required()
def upload_mri():
    if "mriScan" not in request.files:
        return jsonify({"msg": "No file uploaded"}), 400

    file = request.files["mriScan"]
    filename = file.filename
    filepath = os.path.join("uploads", filename)
    os.makedirs("uploads", exist_ok=True)
    file.save(filepath)

    # -----------------------
    # TODO: Replace with your actual ML model logic
    # -----------------------
    prediction_result = {"result": "tumor", "confidence": 0.95}

    return jsonify({"prediction": prediction_result}), 200

# -----------------------
# Root endpoint
# -----------------------
@app.route("/", methods=["GET"])
def root():
    return jsonify({"msg": "Spinal Cord Tumor Detection API is running"}), 200

# -----------------------
# Run app locally
# -----------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
