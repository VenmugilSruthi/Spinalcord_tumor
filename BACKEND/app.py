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
from routes.profile import profile_bp # <-- ADD THIS LINE

def create_app():
    app = Flask(__name__)

    # ✅ FIX: Allow Authorization header in CORS
    CORS(
        app,
        resources={
            r"/": {"origins": "*"},        # allow health check
            r"/api/*": {"origins": "*"}    # allow all API routes
        },
        supports_credentials=True,
        allow_headers=["Content-Type", "Authorization"]
)

    # --- CONFIGURATION FROM .ENV FILE ---
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
    app.config["MONGO_URI"] = os.getenv("MONGO_URI")
    
    # --- INITIALIZE EXTENSIONS ---
    mongo.init_app(app)
    jwt = JWTManager(app)

    # ✅ Health check route
    @app.route('/')
    def health_check():
        try:
            mongo.db.command('ping')
            return jsonify({"status": "Backend is running and CONNECTED to the database!"})
        except Exception as e:
            return jsonify({"status": "Backend is running but FAILED to connect to the database.", "error": str(e)}), 500

    # Register the blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(predict_bp, url_prefix='/api/predict')
    app.register_blueprint(chatbot_bp, url_prefix='/api/chatbot')
    app.register_blueprint(profile_bp, url_prefix='/api/profile') # <-- ADD THIS LINE

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
