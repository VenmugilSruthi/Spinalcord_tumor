from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from datetime import timedelta

# Blueprints
from routes.auth import auth_bp
from routes.chatbot import chatbot_bp
from routes.predict import predict_bp
from routes.profile import profile_bp

def create_app():
    app = Flask(__name__)
    
    # JWT configuration
    app.config["JWT_SECRET_KEY"] = "your-secret-key"  # ⚠️ change this in production
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)

    jwt = JWTManager(app)

    # ✅ CORS
    CORS(
        app,
        origins=[
            "https://spinalcord-tumor-1.onrender.com",
            "http://localhost:3000",
            "http://localhost:5173"
        ],
        supports_credentials=True,
        allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    )

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(chatbot_bp, url_prefix="/api/chatbot")
    app.register_blueprint(predict_bp, url_prefix="/api/predict")
    app.register_blueprint(profile_bp, url_prefix="/api/profile")

    # Root route
    @app.route("/")
    def home():
        return jsonify({"status": "Backend is running and CONNECTED to the database!"})

    return app

# For local debugging
if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
