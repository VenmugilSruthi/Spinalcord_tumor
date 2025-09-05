# routes/predict.py
import os
import uuid
import datetime
import io
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from PIL import Image

# --- CORRECTION: Use relative imports for modules in the parent directory ---
from ..model_loader import make_prediction
from ..validator_loader import is_mri_scan
from ..extensions import mongo

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
        # Validate the image content with the real model
        is_valid_mri, confidence = is_mri_scan(image_bytes)
        
        if not is_valid_mri:
            return jsonify({
                "msg": f"Validation Error: The uploaded image is not a valid spinal cord MRI scan. Confidence: {confidence:.2f}%"
            }), 400
        
        # If validation passes, run the real tumor prediction
        prediction_label, prediction_confidence = make_prediction(image_bytes)

        # Convert the prediction from 0/1 to a human-readable string
        result = "Tumor Detected" if prediction_label == 1 else "No Tumor"
        confidence_percent = f"{prediction_confidence * 100:.2f}%"
        
        # Create the prediction object to be sent back to the frontend
        prediction_result = {
            "result": result,
            "confidence": confidence_percent
        }
        
        # Save the file (optional, for record keeping)
        filename = secure_filename(file.filename)
        save_dir = "uploads"
        os.makedirs(save_dir, exist_ok=True)
        file_path = os.path.join(save_dir, filename)
        
        with open(file_path, "wb") as f:
            f.write(image_bytes)

        # SAVE PREDICTION TO MONGODB
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
        print(f"Error during prediction or validation: {e}")
        return jsonify({"msg": f"An error occurred on the server: {e}"}), 500

# Stats endpoint (recent predictions)
@predict_bp.route("/stats", methods=["GET"])
@jwt_required()
def stats():
    try:
        user_id = get_jwt_identity()

        # FETCH REAL DATA FROM MONGODB
        recent_predictions = list(mongo.db.predictions.find(
            {"user_id": user_id},
            {"_id": 0}
        ).sort("date", -1).limit(20))

        # Get total counts of predictions for the current user
        total_counts = mongo.db.predictions.aggregate([
            {"$match": {"user_id": user_id}},
            {"$group": {
                "_id": "$result",
                "count": {"$sum": 1}
            }}
        ])

        tumor_count = 0
        no_tumor_count = 0
        for item in total_counts:
            if item['_id'] == 'Tumor Detected':
                tumor_count = item['count']
            else:
                no_tumor_count = item['count']
        
        # Format dates for the frontend
        for pred in recent_predictions:
            pred['date'] = pred['date'].strftime("%Y-%m-%d %H:%M:%S")

        response_data = {
            "total_counts": {
                "tumor": tumor_count,
                "no_tumor": no_tumor_count
            },
            "recent_predictions": recent_predictions
        }
        
        return jsonify(response_data), 200

    except Exception as e:
        print(f"Error fetching stats: {e}")
        return jsonify({"msg": "An error occurred fetching statistics"}), 500
