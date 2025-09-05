# predict.py
import os
import uuid
import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename

predict_bp = Blueprint("predict", __name__)

# Fake model prediction (replace with real ML model later)
def fake_model_predict(file_path):
    # Here you can load your ML/DL model and do prediction
    import random
    result = random.choice(["Tumor Detected", "No Tumor"])
    confidence = round(random.uniform(70, 99), 2)
    return {"result": result, "confidence": f"{confidence}%"}

# Upload MRI for prediction
@predict_bp.route("/upload", methods=["POST"])
@jwt_required()
def upload_file():
    if "mriScan" not in request.files:
        return jsonify({"msg": "No file part"}), 400
    
    file = request.files["mriScan"]
    if file.filename == "":
        return jsonify({"msg": "No selected file"}), 400

    filename = secure_filename(file.filename)
    save_dir = "uploads"
    os.makedirs(save_dir, exist_ok=True)
    file_path = os.path.join(save_dir, filename)
    file.save(file_path)

    # Run prediction
    prediction = fake_model_predict(file_path)

    # Save record in memory (later replace with DB)
    record = {
        "id": str(uuid.uuid4()),
        "user": get_jwt_identity(),
        "filename": filename,
        "result": prediction["result"],
        "confidence": prediction["confidence"],
        "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    # For now, return directly
    return jsonify({"prediction": prediction, "record": record}), 200

# Stats endpoint (recent predictions)
@predict_bp.route("/stats", methods=["GET"])
@jwt_required()
def stats():
    # Replace with DB query in future
    dummy_data = {
        "total_counts": {"tumor": 5, "no_tumor": 7},
        "recent_predictions": [
            {
                "date": "2025-09-05 10:00:00",
                "filename": "scan1.png",
                "result": "Tumor Detected",
                "confidence": "95%"
            },
            {
                "date": "2025-09-05 09:30:00",
                "filename": "scan2.png",
                "result": "No Tumor",
                "confidence": "88%"
            }
        ]
    }
    return jsonify(dummy_data), 200
