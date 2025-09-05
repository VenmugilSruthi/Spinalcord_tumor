# routes/predict.py
import os
import uuid
import datetime
import io
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from PIL import Image

# --- CORRECTION ---
# Use a relative import to access the parent directory
from ..validator_loader import is_mri_scan
from ..model_loader import make_prediction
# --- END OF CORRECTION ---

predict_bp = Blueprint("predict", __name__)

@predict_bp.route("/upload", methods=["POST"])
@jwt_required()
def upload_file():
    if "mriScan" not in request.files:
        return jsonify({"msg": "No file part"}), 400
    
    file = request.files["mriScan"]
    if file.filename == "":
        return jsonify({"msg": "No selected file"}), 400

    image_bytes = file.read()

    try:
        is_valid_mri, confidence = is_mri_scan(image_bytes)
        
        if not is_valid_mri:
            return jsonify({
                "msg": f"Validation Error: The uploaded image is not a valid spinal cord MRI scan. Confidence: {confidence:.2f}%"
            }), 400
        
        prediction_label, prediction_confidence = make_prediction(image_bytes)

        result = "Tumor Detected" if prediction_label == 1 else "No Tumor"
        confidence_percent = f"{prediction_confidence * 100:.2f}%"
        
        prediction_result = {
            "result": result,
            "confidence": confidence_percent
        }
        
        filename = secure_filename(file.filename)
        save_dir = "uploads"
        os.makedirs(save_dir, exist_ok=True)
        file_path = os.path.join(save_dir, filename)
        
        with open(file_path, "wb") as f:
            f.write(image_bytes)

        record = {
            "id": str(uuid.uuid4()),
            "user": get_jwt_identity(),
            "filename": filename,
            "result": prediction_result["result"],
            "confidence": prediction_result["confidence"],
            "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        return jsonify({"prediction": prediction_result, "record": record}), 200

    except Exception as e:
        print(f"Error during prediction or validation: {e}")
        return jsonify({"msg": f"An error occurred on the server: {e}"}), 500

@predict_bp.route("/stats", methods=["GET"])
@jwt_required()
def stats():
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
