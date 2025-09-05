# In routes/profile.py

import os
from flask import Blueprint, request, jsonify, url_for, current_app
from werkzeug.utils import secure_filename
from extensions import mongo
from flask_jwt_extended import jwt_required

profile_bp = Blueprint('profile', __name__)

UPLOAD_FOLDER = 'static/profile_pics'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@profile_bp.route('/<email>', methods=['GET'])
@jwt_required()
def get_user_profile(email):
    try:
        user_data = mongo.db.users.find_one({'email': email})
        if user_data:
            profile_info = {
                'name': user_data.get('name'),
                'email': user_data.get('email'),
                'profilePhoto': url_for('static', filename=f'profile_pics/{user_data.get("profilePhoto")}', _external=True) if user_data.get("profilePhoto") else None
            }
            return jsonify(profile_info), 200
        else:
            return jsonify({'msg': 'User not found'}), 404
    except Exception as e:
        return jsonify({'msg': 'An error occurred', 'error': str(e)}), 500


@profile_bp.route('/upload-photo', methods=['POST'])
@jwt_required()
def upload_profile_photo():
    user_email = request.form.get('userEmail')
    if not user_email:
        return jsonify({'error': 'User email is required'}), 400

    if 'profilePicture' not in request.files:
        return jsonify({'error': 'No file part'}), 400
        
    file = request.files['profilePicture']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        unique_filename = f"{user_email.split('@')[0]}_{filename}"
        
        upload_path = os.path.join(current_app.root_path, UPLOAD_FOLDER)
        os.makedirs(upload_path, exist_ok=True)
        
        file.save(os.path.join(upload_path, unique_filename))
        
        mongo.db.users.update_one(
            {'email': user_email},
            {'$set': {'profilePhoto': unique_filename}}
        )

        photo_url = url_for('static', filename=f'profile_pics/{unique_filename}', _external=True)

        return jsonify({'success': True, 'photoUrl': photo_url}), 200
    else:
        return jsonify({'error': 'File type not allowed'}), 400


@profile_bp.route('/update', methods=['PUT'])
@jwt_required()
def update_profile():
    data = request.get_json()
    current_email = data.get('currentUserEmail')
    new_name = data.get('name')

    if not current_email or not new_name:
        return jsonify({'error': 'Missing data for update'}), 400

    result = mongo.db.users.update_one(
        {'email': current_email},
        {'$set': {'name': new_name}}
    )

    if result.matched_count:
        return jsonify({'success': True, 'msg': 'Profile updated successfully'}), 200
    else:
        return jsonify({'error': 'User not found or no changes made'}), 404