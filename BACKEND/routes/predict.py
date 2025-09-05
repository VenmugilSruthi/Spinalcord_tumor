from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from extensions import mongo
from model_loader import make_prediction
import torch
import torchvision.models as models
from torchvision import transforms
from PIL import Image
import io


# --- PASTE THE SAME CALCULATED VALUES HERE ---
# Make sure these numbers are identical to the ones in train_validator.py
DATASET_MEAN = 0.3247
DATASET_STD = 0.2072
# -----------------------------------------

# --- Load the MRI Validator Model ---
validator_model = models.resnet18()
validator_model.fc = torch.nn.Linear(validator_model.fc.in_features, 1)
try:
    validator_model.load_state_dict(torch.load('mri_validator.pth', map_location=torch.device('cpu')))
    validator_model.eval()
    print("✅ MRI Validator model loaded successfully.")
except FileNotFoundError:
    print("🔴 WARNING: 'mri_validator.pth' not found. Image validation will be skipped.")
    validator_model = None

# --- Robust Image Transformations (MUST BE IDENTICAL TO TRAINING) ---
validator_transforms = transforms.Compose([
    transforms.Grayscale(num_output_channels=1),
    transforms.ToTensor(),
    transforms.Normalize([DATASET_MEAN], [DATASET_STD]),
    transforms.Resize((224, 224), antialias=True),
    transforms.Lambda(lambda x: x.repeat(3, 1, 1))
])

def is_image_mri(image_bytes):
    if not validator_model: return True
    try:
        image = Image.open(io.BytesIO(image_bytes))
        image_tensor = validator_transforms(image).unsqueeze(0)
        with torch.no_grad():
            output = validator_model(image_tensor)
            probability = torch.sigmoid(output).item()
        print(f"🔬 MRI Validation Check - Probability: {probability:.4f}")
        
        # <<< THE FINAL FIX IS HERE >>>
        # The model learned that 'mri' is class 0 (low probability).
        # So, we check if the probability is LESS THAN 0.5.
        return probability < 0.5
        
    except Exception as e:
        print(f"Error during MRI validation: {e}"); return False

predict_bp = Blueprint('predict', __name__)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@predict_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_file():
    if 'mriScan' not in request.files: return jsonify({'msg': 'No file part in the request'}), 400
    file = request.files['mriScan']
    if file.filename == '': return jsonify({'msg': 'No file selected'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        image_bytes = file.read()

        if not is_image_mri(image_bytes):
            return jsonify({'msg': "Validation Error: The uploaded image does not appear to be a medical MRI scan. Please upload a relevant image."}), 400

        prediction_label, probability = make_prediction(image_bytes)
        if prediction_label is None: return jsonify({'msg': 'Error processing the image'}), 500

        result_text = "Tumor Detected" if prediction_label == 1 else "No Tumor"
        confidence_str = f"{probability:.2%}"
        
        mongo.db.predictions.insert_one({
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "filename": filename, "result": result_text, "confidence": confidence_str,
            "user": get_jwt_identity()
        })

        return jsonify({'fileName': filename, 'prediction': {'result': result_text, 'confidence': confidence_str}}), 200
    else:
        return jsonify({'msg': 'File type not allowed'}), 400

@predict_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_stats():
    user = get_jwt_identity()
    preds = list(mongo.db.predictions.find({"user": user}).sort("date", -1).limit(20))
    tumor_count = mongo.db.predictions.count_documents({"user": user, "result": "Tumor Detected"})
    no_tumor_count = mongo.db.predictions.count_documents({"user": user, "result": "No Tumor"})
    formatted_preds = [{"date": p["date"], "filename": p["filename"], "result": p["result"], "confidence": p["confidence"]} for p in preds]
    return jsonify({"total_counts": {"tumor": tumor_count, "no_tumor": no_tumor_count}, "recent_predictions": formatted_preds}), 200