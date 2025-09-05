import torch
from torchvision import datasets, transforms
from torch.utils.data import DataLoader
import os

print("--- Calculating Dataset Statistics ---")

DATA_DIR = 'validator_data/train' # We only calculate on the training set

# A simple transform to get the images into tensor format
# We convert to grayscale first to get the correct stats
stats_transforms = transforms.Compose([
    transforms.Grayscale(num_output_channels=1),
    transforms.Resize((224, 224)),
    transforms.ToTensor()
])

dataset = datasets.ImageFolder(os.path.join(DATA_DIR), transform=stats_transforms)
dataloader = DataLoader(dataset, batch_size=64, shuffle=False, num_workers=0)

# Calculate mean and std
mean = 0.
std = 0.
nb_samples = 0.
for images, _ in dataloader:
    batch_samples = images.size(0)
    images = images.view(batch_samples, images.size(1), -1)
    mean += images.mean(2).sum(0)
    std += images.std(2).sum(0)
    nb_samples += batch_samples

mean /= nb_samples
std /= nb_samples

print(f"\nCalculated Mean: {mean.item():.4f}")
print(f"Calculated Std:  {std.item():.4f}")
print("\nCOPY these values and paste them into the next two files.")