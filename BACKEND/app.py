# app.py

# --- Imports ---
from flask import Flask, request, jsonify
from flask_cors import CORS # It's a good practice to include this for CORS issues
from PIL import Image
import torch
import torchvision.transforms as transforms
import os

# --- Load your custom model and class ---
# Make sure 'your_model_module' is the name of your Python file
# that contains the definition of 'YourModelClass'.
# 'path/to/your/model.pth' must be the correct path to your model file.
from your_model_module import YourModelClass  
model_path = 'path/to/your/model.pth'

# --- Initialize Flask App ---
app = Flask(__name__)
CORS(app) # Enables CORS for all routes

# --- Load the PyTorch Model onto the CPU ---
try:
    # We load the model once when the app starts.
    # The map_location=torch.device('cpu') argument is crucial for Render's free tier.
    model = YourModelClass()
    model.load_state_dict(torch.load(model_path, map_location=torch.device('cpu')))
    model.eval() # Set the model to evaluation mode
    print("✅ Custom model loaded successfully!")
except Exception as e:
    print(f"Error loading model: {e}")
    # You might want to return a 500 error if the model fails to load

# --- Define the Image Transformation Pipeline ---
# This includes the image resizing step to reduce processing time.
transform = transforms.Compose([
    transforms.Resize((256, 256)), # Add this line to shrink the image
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

# --- Prediction Route ---
@app.route('/api/predict/upload', methods=['POST'])
def predict_tumor():
    # 1. Check if a file was uploaded
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    try:
        # 2. Open the image, resize it, and convert to a tensor
        # This is the key optimization for speed.
        img = Image.open(file.stream).convert('RGB')
        img_tensor = transform(img).unsqueeze(0)

        # 3. Make the prediction
        with torch.no_grad():
            output = model(img_tensor)
            
            # The rest of your prediction logic goes here.
            # Example:
            prediction_label = output.argmax(dim=1).item()
            if prediction_label == 1:
                result = "Spinal cord tumor is present."
            else:
                result = "No spinal cord tumor found."

        # 4. Return the result
        return jsonify({'prediction': result}), 200

    except Exception as e:
        print(f"An error occurred during prediction: {e}")
        return jsonify({'error': 'An internal error occurred'}), 500

# --- Add other routes here (e.g., login, chatbot) ---
# ... Your other routes and functions ...

# --- Main entry point for the app ---
if __name__ == '__main__':
    # When deploying on Render, you don't need app.run() because Gunicorn runs it.
    # This is useful for local development.
    app.run(host='0.0.0.0', port=os.environ.get('PORT', 5000))