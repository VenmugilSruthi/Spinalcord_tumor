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
    app = Flask(__name__)
    
    # ✅ FIXED CORS Configuration
    CORS(
        app,
        origins=[
            "https://spinalcord-tumor-1.onrender.com",  # Your frontend domain
            "http://localhost:3000",                    # Local React dev
            "http://localhost:5173",                    # Local Vite dev
            "*"                                         # Allow all for testing
        ],
        supports_credentials=True,
        allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
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

    # ✅ Add explicit OPTIONS handling for preflight requests
    @app.before_request
    def handle_preflight():
        from flask import request
        if request.method == "OPTIONS":
            response = jsonify({"status": "OK"})
            response.headers.add("Access-Control-Allow-Origin", "*")
            response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
            response.headers.add("Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS")
            return response

    # Register the blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(predict_bp, url_prefix='/api/predict')
    app.register_blueprint(chatbot_bp, url_prefix='/api/chatbot')
    app.register_blueprint(profile_bp, url_prefix='/api/profile')
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
