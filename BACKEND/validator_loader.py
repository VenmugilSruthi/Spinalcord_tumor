# validator_loader.py
import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
import io

# --- 1. Define the Model Architecture for the Validator ---
# This must match the architecture you used in train_validator.py
def get_validator_architecture():
    # Assuming you used a ResNet18
    model = models.resnet18(weights=None)
    num_ftrs = model.fc.in_features
    model.fc = nn.Linear(num_ftrs, 1) # Output is a single value for binary classification
    return model

# --- 2. Define the Image Transformation Pipeline for the Validator ---
# This must match the transformations in train_validator.py
DATASET_MEAN = 0.3247  # Replace with your calculated mean
DATASET_STD = 0.2072   # Replace with your calculated std

TRANSFORM = transforms.Compose([
    transforms.Grayscale(num_output_channels=1),
    transforms.ToTensor(),
    transforms.Normalize([DATASET_MEAN], [DATASET_STD]),
    transforms.Resize((224, 224), antialias=True),
    transforms.Lambda(lambda x: x.repeat(3, 1, 1)) # Duplicate channels
])

# --- 3. Load the Validator Model and Weights ---
print("🧠 Loading MRI Validator model...")
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
validator_model = get_validator_architecture()
try:
    validator_model.load_state_dict(torch.load('mri_validator.pth', map_location=device))
    validator_model.to(device)
    validator_model.eval()
    print("✅ MRI Validator model loaded successfully.")
except FileNotFoundError:
    print("❌ Error: mri_validator.pth not found. The validator will not work.")
    validator_model = None
except Exception as e:
    print(f"❌ Error loading validator model: {e}")
    validator_model = None

# --- 4. Validation Function ---
def is_mri_scan(image_bytes):
    """
    Checks if an image is a valid MRI scan using the loaded model.
    Returns (True/False, Confidence)
    """
    if validator_model is None:
        # If model failed to load, skip validation and return True by default
        return True, 0.0

    try:
        # Open the image from bytes
        image = Image.open(io.BytesIO(image_bytes))

        # Apply transformations and add batch dimension
        image_tensor = TRANSFORM(image).unsqueeze(0).to(device)

        with torch.no_grad():
            output = validator_model(image_tensor)
            probability = torch.sigmoid(output).item()
            
            # Set a threshold for validation (e.g., 0.8 is a good start)
            is_valid = probability > 0.8
            
        return is_valid, probability * 100 # Return as percentage
        
    except Exception as e:
        print(f"Error during MRI validation: {e}")
        return False, 0.0
