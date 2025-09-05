import os
from flask import Flask, jsonify
from flask_cors import CORS
from extensions import mongo
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import your route blueprints
from routes.auth import auth_bp
from routes.predict import predict_bp
from routes.chatbot import chatbot_bp
from routes.profile import profile_bp

def create_app():
    # I've renamed the variable inside the function to avoid confusion
    flask_app = Flask(__name__)

    # Allow Authorization header in CORS
    CORS(
        flask_app,
        resources={
            r"/": {"origins": "*"},
            r"/api/*": {"origins": "*"}
        },
        supports_credentials=True,
        allow_headers=["Content-Type", "Authorization"]
    )

    # --- CONFIGURATION FROM .ENV FILE ---
    flask_app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
    flask_app.config["MONGO_URI"] = os.getenv("MONGO_URI")
    
    # --- INITIALIZE EXTENSIONS ---
    mongo.init_app(flask_app)
    jwt = JWTManager(flask_app)

    # Health check route
    @flask_app.route('/')
    def health_check():
        try:
            mongo.db.command('ping')
            return jsonify({"status": "Backend is running and CONNECTED to the database!"})
        except Exception as e:
            return jsonify({"status": "Backend is running but FAILED to connect to the database.", "error": str(e)}), 500

    # Register the blueprints
    flask_app.register_blueprint(auth_bp, url_prefix='/api/auth')
    flask_app.register_blueprint(predict_bp, url_prefix='/api/predict')
    flask_app.register_blueprint(chatbot_bp, url_prefix='/api/chatbot')
    flask_app.register_blueprint(profile_bp, url_prefix='/api/profile')

    return flask_app

# --- THIS IS THE CRITICAL CHANGE ---
# Create the app instance in the global scope so Gunicorn can find it.
app = create_app()

# This block is now only used for running the app locally on your computer.
# Render's Gunicorn server will NOT run this part.
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
