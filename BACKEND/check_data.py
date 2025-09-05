import os
import random
from PIL import Image
import matplotlib.pyplot as plt

# --- CONFIGURATION ---
DATA_DIR = 'validator_data'
NUM_SAMPLES = 4 # We will show 4 random images from each folder

def check_folders():
    print("--- Running Data Sanity Check ---")
    
    mri_path = os.path.join(DATA_DIR, 'train', 'mri')
    not_mri_path = os.path.join(DATA_DIR, 'train', 'not_mri')

    # Check if paths exist
    if not os.path.exists(mri_path) or not os.path.exists(not_mri_path):
        print(f"\n[ERROR] Could not find '{mri_path}' or '{not_mri_path}'.")
        print("Please make sure your data folders are set up correctly inside the BACKEND directory.")
        return

    try:
        mri_images = [os.path.join(mri_path, f) for f in os.listdir(mri_path)]
        not_mri_images = [os.path.join(not_mri_path, f) for f in os.listdir(not_mri_path)]
    except Exception as e:
        print(f"Error reading image files: {e}")
        return

    if len(mri_images) < NUM_SAMPLES or len(not_mri_images) < NUM_SAMPLES:
        print("\n[ERROR] Not enough images in training folders to pull samples.")
        print(f"Found {len(mri_images)} in 'mri' and {len(not_mri_images)} in 'not_mri'.")
        print(f"Please ensure you have at least {NUM_SAMPLES} in each.")
        return

    # Get random samples
    random_mris = random.sample(mri_images, NUM_SAMPLES)
    random_not_mris = random.sample(not_mri_images, NUM_SAMPLES)

    # Plot the images
    fig, axes = plt.subplots(2, NUM_SAMPLES, figsize=(12, 6))
    fig.suptitle("Random Samples from Your Training Data", fontsize=16)

    # Plot MRI samples
    for i, img_path in enumerate(random_mris):
        img = Image.open(img_path)
        axes[0, i].imshow(img, cmap='gray')
        axes[0, i].set_title(f"From 'mri' folder")
        axes[0, i].axis('off')

    # Plot Not-MRI samples
    for i, img_path in enumerate(random_not_mris):
        img = Image.open(img_path)
        axes[1, i].imshow(img)
        axes[1, i].set_title(f"From 'not_mri' folder")
        axes[1, i].axis('off')

    plt.tight_layout()
    plt.show()

if __name__ == '__main__':
    check_folders()