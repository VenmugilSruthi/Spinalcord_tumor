# routes/predict.py
import os
import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename

# ✅ Absolute imports (BACKEND is the top-level package)
from BACKEND.model_loader import make_prediction
from BACKEND.validator_loader import is_mri_scan
from BACKEND.extensions import mongo

predict_bp = Blueprint("predict", __name__)

@predict_bp.route("/upload", methods=["POST"])
@jwt_required()
def upload_file():
    if "mriScan" not in request.files:
        return jsonify({"msg": "No file part"}), 400
    
    file = request.files["mriScan"]
    if file.filename == "":
        return jsonify({"msg": "No selected file"}), 400

    # Read the file's bytes
    image_bytes = file.read()

    try:
        # Validate MRI scan
        is_valid_mri, confidence = is_mri_scan(image_bytes)
        if not is_valid_mri:
            return jsonify({
                "msg": f"Validation Error: Not a valid spinal cord MRI scan. Confidence: {confidence:.2f}%"
            }), 400
        
        # Make prediction
        prediction_label, prediction_confidence = make_prediction(image_bytes)
        result = "Tumor Detected" if prediction_label == 1 else "No Tumor"
        confidence_percent = f"{prediction_confidence * 100:.2f}%"
        
        prediction_result = {
            "result": result,
            "confidence": confidence_percent
        }
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        save_dir = "uploads"
        os.makedirs(save_dir, exist_ok=True)
        file_path = os.path.join(save_dir, filename)
        with open(file_path, "wb") as f:
            f.write(image_bytes)

        # Save prediction to MongoDB
        user_id = get_jwt_identity()
        prediction_data = {
            "user_id": user_id,
            "filename": filename,
            "result": prediction_result["result"],
            "confidence": prediction_result["confidence"],
            "date": datetime.datetime.now()
        }
        mongo.db.predictions.insert_one(prediction_data)

        return jsonify({"prediction": prediction_result, "record": prediction_data}), 200

    except Exception as e:
        print(f"Error during prediction: {e}")
        return jsonify({"msg": f"An error occurred on the server: {e}"}), 500

# --- Stats endpoint ---
@predict_bp.route("/stats", methods=["GET"])
@jwt_required()
def stats():
    try:
        user_id = get_jwt_identity()

        # Recent predictions
        recent_predictions = list(mongo.db.predictions.find(
            {"user_id": user_id},
            {"_id": 0}
        ).sort("date", -1).limit(20))

        # Totals
        total_counts = mongo.db.predictions.aggregate([
            {"$match": {"user_id": user_id}},
            {"$group": {"_id": "$result", "count": {"$sum": 1}}}
        ])

        tumor_count, no_tumor_count = 0, 0
        for item in total_counts:
            if item["_id"] == "Tumor Detected":
                tumor_count = item["count"]
            else:
                no_tumor_count = item["count"]

        for pred in recent_predictions:
            pred["date"] = pred["date"].strftime("%Y-%m-%d %H:%M:%S")

        return jsonify({
            "total_counts": {"tumor": tumor_count, "no_tumor": no_tumor_count},
            "recent_predictions": recent_predictions
        }), 200

    except Exception as e:
        print(f"Error fetching stats: {e}")
        return jsonify({"msg": "An error occurred fetching statistics"}), 500
