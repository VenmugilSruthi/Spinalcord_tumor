import os
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

class Config:
    """
    Flask configuration settings.
    """
    # Secret key for signing session cookies and JWTs
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a-super-secret-key-you-should-change'
    
    # MongoDB connection URI
    MONGO_URI = os.environ.get('MONGO_URI') or 'your_mongodb_connection_string_here'
    
    # JWT Secret Key
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'another-super-secret-jwt-key'


