import os
import google.generativeai as genai
from flask import Blueprint, request, jsonify
from datetime import datetime
from extensions import mongo
from flask_jwt_extended import jwt_required, get_jwt_identity

chatbot_bp = Blueprint('chatbot_bp', __name__)

# --- CONFIGURE THE GEMINI AI MODEL ---
chat = None
try:
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
    if not GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY not found in .env file.")
    genai.configure(api_key=GOOGLE_API_KEY)
    
    model = genai.GenerativeModel(
        model_name='gemini-1.5-flash',
        system_instruction=(
            "You are a friendly and helpful AI assistant for a web application "
            "that detects spinal tumors from MRI scans. The application was created by "
            "Venmugil Sruthi and Vidhi Pant. Answer user questions about the application, "
            "spinal health, and medical imaging. Keep answers concise and helpful. "
            "If a user asks something unrelated, politely guide them back."
        )
    )
    chat = model.start_chat(history=[])
    print("✅ Gemini AI Model initialized successfully.")
except Exception as e:
    print(f"❌ ERROR initializing Gemini AI Model: {e}")

# --- Ask Chatbot (Now requires login) ---
@chatbot_bp.route('/ask', methods=['POST'])
@jwt_required() # Protect this route
def ask_chatbot():
    if not chat:
        return jsonify({"answer": "AI model is offline. Please check server config."}), 500

    data = request.get_json()
    user_identity = get_jwt_identity() # Get user email from token
    question = data.get("question", "").strip()

    if not question:
        return jsonify({"error": "No question provided."}), 400

    try:
        response = chat.send_message(question)
        answer = response.text
    except Exception as e:
        print(f"❌ ERROR: Gemini API call failed: {e}")
        answer = "Sorry, I'm having trouble thinking right now. Please try again."

    mongo.db.chats.insert_one({
        "userId": user_identity, # Use email (from token) for consistency
        "question": question,
        "answer": answer,
        "timestamp": datetime.now()
    })
    return jsonify({"answer": answer}), 200

# --- Retrieve Chat History (Now requires login) ---
@chatbot_bp.route('/history', methods=['GET']) # Removed <userId> from URL
@jwt_required() # Protect this route
def get_chat_history():
    user_identity = get_jwt_identity() # Get user email from token
    history = list(mongo.db.chats.find({"userId": user_identity}).sort("timestamp", -1))
    
    response = [
        {
            "question": item["question"],
            "answer": item["answer"],
            "timestamp": item["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
        }
        for item in history
    ]
    return jsonify(response), 200