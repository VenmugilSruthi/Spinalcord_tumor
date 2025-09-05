import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
import io

# --- 1. Define the Model Architecture ---
# This must be the EXACT same architecture you used for training.
def get_model_architecture():
    """Defines and returns the DenseNet121 model structure."""
    # Load the model structure WITHOUT pre-trained weights, as we will load our own.
    model = models.densenet121(weights=None) 
    
    # Adjust the classifier to match your trained model
    model.classifier = nn.Sequential(
        nn.Linear(model.classifier.in_features, 1),
        nn.Sigmoid()
    )
    return model

# --- 2. Define the Image Transformation Pipeline ---
# This must be the EXACT same transformation you used for training.
def get_image_transform():
    """Defines and returns the image transformation pipeline."""
    return transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.Grayscale(num_output_channels=3),  # Convert grayscale to 3 channels for DenseNet
        transforms.ToTensor(),
        transforms.Normalize([0.5]*3, [0.5]*3)
    ])

# --- 3. Load the Model and YOUR Custom Weights ---
print("🧠 Loading custom-trained PyTorch model...")
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = get_model_architecture()

# UPDATED: Load the saved weights from YOUR .pth file
model.load_state_dict(torch.load('densenet_spinal_tumor.pth', map_location=device))

model.to(device)
model.eval()  # Set the model to evaluation mode
print("✅ Custom model loaded successfully!")

# --- 4. Prediction Function ---
def make_prediction(image_bytes):
    """
    Takes image bytes, preprocesses the image, and returns a prediction.
    """
    try:
        transform = get_image_transform()
        # Open the image from the bytes received in the request
        image = Image.open(io.BytesIO(image_bytes)).convert('L') # Convert to grayscale
        
        # Apply transformations and add a batch dimension
        image_tensor = transform(image).unsqueeze(0).to(device)

        # Make a prediction
        with torch.no_grad():
            output = model(image_tensor)
            # The output is a probability between 0 and 1
            probability = output.item()
            
            # Set a threshold to decide the class
            prediction = 1 if probability > 0.5 else 0
            
        return prediction, probability

    except Exception as e:
        print(f"Error during prediction: {e}")
        return None, None
