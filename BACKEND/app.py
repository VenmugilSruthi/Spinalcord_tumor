from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_bcrypt import Bcrypt
from flask_pymongo import PyMongo
import os

app = Flask(__name__)
CORS(app)
bcrypt = Bcrypt(app)

# -----------------------
# MongoDB setup
# -----------------------
app.config["MONGO_URI"] = os.environ.get(
    "MONGO_URI",
    "mongodb://localhost:27017/spinalcord"
)
mongo = PyMongo(app)

# -----------------------
# JWT setup
# -----------------------
app.config["JWT_SECRET_KEY"] = os.environ.get(
    "JWT_SECRET_KEY",
    "super-secret-key"
)
jwt = JWTManager(app)

# -----------------------
# Auth: Login endpoint
# -----------------------
@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

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

    # TODO: Replace with your ML model logic
    prediction_result = {"result": "tumor", "confidence": 0.95}

    return jsonify({"prediction": prediction_result}), 200

# -----------------------
# Run app
# -----------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
