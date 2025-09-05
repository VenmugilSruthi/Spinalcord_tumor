# app.py

# --- Imports ---
from flask import Flask, request, jsonify
from flask_cors import CORS
import os

# Import the prediction function from your model_loader.py file.
# The `model_loader.py` file already handles loading the model onto the CPU.
from model_loader import make_prediction

# --- Initialize Flask App ---
app = Flask(__name__)

# Enables CORS for all routes, which is necessary for a separate frontend.
CORS(app) 

# --- Routes ---

# @app.route('/api/auth/login', methods=['POST'])
# def login():
#    # Your login logic here
#    ...

# @app.route('/api/chatbot/ask', methods=['POST'])
# def chatbot_ask():
#    # Your chatbot logic here
#    ...

# @app.route('/api/predict/stats', methods=['GET'])
# def predict_stats():
#    # Your stats logic here
#    ...

# --- Corrected Prediction Route ---
@app.route('/api/predict/upload', methods=['POST'])
def predict_tumor():
    """
    Handles image upload, passes it to the model for prediction, and returns the result.
    The actual prediction logic is in model_loader.py to avoid timeouts.
    """
    # 1. Check if a file was uploaded in the request
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    try:
        # 2. Call the make_prediction function from model_loader.py.
        # This function handles all the image processing (resizing, converting to tensor)
        # and runs the model on the CPU.
        prediction, probability = make_prediction(file.stream.read())
        
        if prediction is None:
            # If the prediction function returned None, it means an error occurred.
            return jsonify({'error': 'An internal error occurred during prediction'}), 500
        
        # 3. Format the result for the frontend
        if prediction == 1:
            result = "Spinal cord tumor is present."
        else:
            result = "No spinal cord tumor found."

        # 4. Return the JSON response
        return jsonify({
            'prediction': result,
            'probability': probability
        }), 200

    except Exception as e:
        # Catch any unexpected errors and return a server error message.
        print(f"An error occurred in predict_tumor: {e}")
        return jsonify({'error': 'An internal server error occurred'}), 500

# --- Main entry point for the app ---
if __name__ == '__main__':
    # When deploying on Render, you don't need app.run() because Gunicorn runs it.
    # This is useful for local development.
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
