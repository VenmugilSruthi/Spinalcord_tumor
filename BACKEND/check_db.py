import os
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ConfigurationError

# --- This script tests the MongoDB connection string from your .env file ---

def check_database_connection():
    """
    Attempts to connect to the MongoDB database and prints the status.
    """
    print("Attempting to connect to the database...")
    
    # Load environment variables from the .env file
    load_dotenv()
    
    # Get the MongoDB connection string
    mongo_uri = os.environ.get('MONGO_URI')
    
    if not mongo_uri:
        print("\n--- ERROR ---")
        print("MONGO_URI not found in your .env file.")
        print("Please make sure the .env file exists and contains the correct variable.")
        return

    print(f"Found MONGO_URI: {mongo_uri[:25]}... (rest is hidden for security)")

    try:
        # Create a new client and connect to the server
        # serverSelectionTimeoutMS is set to 5 seconds for a quick test
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        
        # The ismaster command is cheap and does not require auth.
        client.admin.command('ismaster')
        
        print("\n--- SUCCESS ---")
        print("Database connection successful!")
        print("Your backend application is ready to connect.")
        
    except ConfigurationError as e:
        print("\n--- CONFIGURATION ERROR ---")
        print("There seems to be a typo or an issue with your connection string.")
        print("Please double-check the MONGO_URI in your .env file.")
        print(f"Details: {e}")

    except ConnectionFailure as e:
        print("\n--- CONNECTION FAILURE ---")
        print("Could not connect to the MongoDB server.")
        print("Please check the following:")
        print("1. Your internet connection is working.")
        print("2. Your IP address is whitelisted in MongoDB Atlas (try setting it to 0.0.0.0/0).")
        print("3. The username and password in your MONGO_URI are correct.")
        print(f"Details: {e}")
        
    except Exception as e:
        print(f"\n--- AN UNEXPECTED ERROR OCCURRED ---")
        print(f"Details: {e}")

# Run the connection test
if __name__ == "__main__":
    check_database_connection()
