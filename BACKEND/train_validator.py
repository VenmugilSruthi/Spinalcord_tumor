import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import datasets, transforms, models
import os
import torchvision

# --- PASTE YOUR CALCULATED VALUES HERE ---
# Replace 0.5 and 0.5 with the numbers from the calculate_stats.py script
DATASET_MEAN = 0.3247 
DATASET_STD = 0.2072
# -----------------------------------------

print(f"Using Mean: {DATASET_MEAN} and Std: {DATASET_STD} for normalization.")

# --- Configuration ---
DATA_DIR = 'validator_data'
MODEL_SAVE_PATH = 'mri_validator.pth'
NUM_EPOCHS = 10
BATCH_SIZE = 32
LEARNING_RATE = 0.001

# --- Robust Image Transformations ---
data_transforms = transforms.Compose([
    transforms.Grayscale(num_output_channels=1), # Force to 1-channel grayscale first
    transforms.ToTensor(),
    transforms.Normalize([DATASET_MEAN], [DATASET_STD]), # Use our calculated stats
    transforms.Resize((224, 224), antialias=True), # Resize after tensor conversion
    transforms.Lambda(lambda x: x.repeat(3, 1, 1)) # Duplicate channels for ResNet
])

# ... (The rest of the file is mostly the same, but copy it all to be safe) ...

image_datasets = {x: datasets.ImageFolder(os.path.join(DATA_DIR, x), data_transforms)
                  for x in ['train', 'val']}
dataloaders = {x: DataLoader(image_datasets[x], batch_size=BATCH_SIZE, shuffle=True, num_workers=0)
               for x in ['train', 'val']}
dataset_sizes = {x: len(image_datasets[x]) for x in ['train', 'val']}
class_names = image_datasets['train'].classes

print(f"Classes found: {class_names}")
print(f"Training data size: {dataset_sizes['train']}")
print(f"Validation data size: {dataset_sizes['val']}")

model = models.resnet18(weights=models.ResNet18_Weights.DEFAULT) # Use new 'weights' API
num_ftrs = model.fc.in_features
model.fc = nn.Linear(num_ftrs, 1)

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
model = model.to(device)
print(f"Using device: {device}")

criterion = nn.BCEWithLogitsLoss()
optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)

def train_model(model, criterion, optimizer, num_epochs=10):
    for epoch in range(num_epochs):
        print(f'Epoch {epoch+1}/{num_epochs}'); print('-' * 10)
        for phase in ['train', 'val']:
            model.train() if phase == 'train' else model.eval()
            running_loss, running_corrects = 0.0, 0
            for inputs, labels in dataloaders[phase]:
                inputs, labels = inputs.to(device), labels.to(device).float().view(-1, 1)
                optimizer.zero_grad()
                with torch.set_grad_enabled(phase == 'train'):
                    outputs = model(inputs)
                    preds = torch.sigmoid(outputs) > 0.5
                    loss = criterion(outputs, labels)
                    if phase == 'train':
                        loss.backward(); optimizer.step()
                running_loss += loss.item() * inputs.size(0)
                running_corrects += torch.sum(preds == labels.data)
            epoch_loss = running_loss / dataset_sizes[phase]
            epoch_acc = running_corrects.double() / dataset_sizes[phase]
            print(f'{phase} Loss: {epoch_loss:.4f} Acc: {epoch_acc:.4f}')
    return model

print("\nStarting training...")
trained_model = train_model(model, criterion, optimizer, num_epochs=NUM_EPOCHS)

print(f"\nTraining complete. Saving model to {MODEL_SAVE_PATH}")
torch.save(trained_model.state_dict(), MODEL_SAVE_PATH)
print("Model saved successfully!")