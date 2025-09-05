# routes/auth.py
import os
from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
from google.oauth2 import id_token
from google.auth.transport import requests

# ✅ Correct import (since extensions.py is in BACKEND folder, not in routes/)
from ..extensions import mongo

auth_bp = Blueprint('auth_bp', __name__)

# --- Google Sign-In Route ---
@auth_bp.route('/google-login', methods=['POST'])
def google_login():
    data = request.get_json()
    token = data.get('token')
    if not token:
        return jsonify({"msg": "Missing token"}), 400

    try:
        CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
        if not CLIENT_ID:
            raise ValueError("GOOGLE_CLIENT_ID not found in environment variables.")
            
        idinfo = id_token.verify_oauth2_token(token, requests.Request(), CLIENT_ID)
        email = idinfo['email']
        name = idinfo['name']
        
        users = mongo.db.users
        user = users.find_one({'email': email})

        if not user:
            # Create a new user with a secure placeholder password for Google accounts
            hashed_password = generate_password_hash(os.urandom(24).hex())
            users.insert_one({'name': name, 'email': email, 'password': hashed_password})
            user = users.find_one({'email': email})

        access_token = create_access_token(identity=email)
        return jsonify(token=access_token, user={'name': user['name'], 'email': user['email']}), 200

    except ValueError as e:
        print(f"Google Token Verification Error: {e}")
        return jsonify({"msg": "Invalid Google token or configuration error."}), 401
    except Exception as e:
        print(f"An error occurred during Google login: {e}")
        return jsonify({"msg": "An internal server error occurred"}), 500

# --- Email/Password Registration Route ---
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')

    if not all([name, email, password]):
        return jsonify({"msg": "Missing required fields"}), 400

    users = mongo.db.users
    if users.find_one({'email': email}):
        return jsonify({"msg": "User with this email already exists"}), 409

    # Always use the modern, secure hashing method for new users
    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
    users.insert_one({'name': name, 'email': email, 'password': hashed_password})

    return jsonify({"msg": "User registered successfully"}), 201

# --- Email/Password Login Route ---
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"msg": "Missing email or password"}), 400

    users = mongo.db.users
    user = users.find_one({'email': email})

    # Use the standard, secure check. This will work for all newly created users.
    if user and check_password_hash(user['password'], password):
        access_token = create_access_token(identity=email)
        return jsonify(token=access_token, user={'name': user['name'], 'email': user['email']})

    return jsonify({"msg": "Bad email or password"}), 401
