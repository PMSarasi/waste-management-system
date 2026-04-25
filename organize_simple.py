import os
import shutil
import random

print("=" * 60)
print("📂 SIMPLE DATASET ORGANIZER")
print("=" * 60)

# Set random seed
random.seed(42)

# Define paths
BASE_DIR = r"D:\copies from Robert gordon university C drive things\Blue Chip Technologies Asia\Task 25\smart_waste_advisor"

SOURCE_DIR = os.path.join(BASE_DIR, "data", "raw", "dataset-resized")
TRAIN_DIR = os.path.join(BASE_DIR, "data", "train")
VAL_DIR = os.path.join(BASE_DIR, "data", "val")
TEST_DIR = os.path.join(BASE_DIR, "data", "test")

print(f"\n📁 Source: {SOURCE_DIR}")

# Check if source exists
if not os.path.exists(SOURCE_DIR):
    print(f"\n❌ ERROR: Source folder NOT FOUND!")
    print(f"Please check: {SOURCE_DIR}")
    exit(1)

print("✅ Source folder found!")

# Get all classes
CLASSES = []
for item in os.listdir(SOURCE_DIR):
    item_path = os.path.join(SOURCE_DIR, item)
    if os.path.isdir(item_path) and not item.startswith('.'):
        CLASSES.append(item)

print(f"\n📊 Found classes: {CLASSES}")

# Clear existing folders
for folder in [TRAIN_DIR, VAL_DIR, TEST_DIR]:
    if os.path.exists(folder):
        shutil.rmtree(folder)
    os.makedirs(folder)

print("\n📊 Creating train/val/test splits (70/15/15)...")
print("-" * 50)

total_train = 0
total_val = 0
total_test = 0

for class_name in CLASSES:
    class_path = os.path.join(SOURCE_DIR, class_name)
    
    # Get all image files
    images = [f for f in os.listdir(class_path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    
    if len(images) == 0:
        print(f"⚠️ No images in {class_name}")
        continue
    
    # Shuffle images
    random.shuffle(images)
    
    # Calculate splits
    n_total = len(images)
    n_train = int(0.7 * n_total)
    n_val = int(0.15 * n_total)
    n_test = n_total - n_train - n_val
    
    train_imgs = images[:n_train]
    val_imgs = images[n_train:n_train + n_val]
    test_imgs = images[n_train + n_val:]
    
    # Create class folders
    os.makedirs(os.path.join(TRAIN_DIR, class_name), exist_ok=True)
    os.makedirs(os.path.join(VAL_DIR, class_name), exist_ok=True)
    os.makedirs(os.path.join(TEST_DIR, class_name), exist_ok=True)
    
    # Copy files
    for img in train_imgs:
        src = os.path.join(class_path, img)
        dst = os.path.join(TRAIN_DIR, class_name, img)
        shutil.copy2(src, dst)
    
    for img in val_imgs:
        src = os.path.join(class_path, img)
        dst = os.path.join(VAL_DIR, class_name, img)
        shutil.copy2(src, dst)
    
    for img in test_imgs:
        src = os.path.join(class_path, img)
        dst = os.path.join(TEST_DIR, class_name, img)
        shutil.copy2(src, dst)
    
    total_train += len(train_imgs)
    total_val += len(val_imgs)
    total_test += len(test_imgs)
    
    print(f"✅ {class_name:12} | Train: {len(train_imgs):3} | Val: {len(val_imgs):3} | Test: {len(test_imgs):3}")

print("-" * 50)
print(f"{'TOTAL':12} | Train: {total_train:3} | Val: {total_val:3} | Test: {total_test:3}")

print("\n" + "=" * 60)
print("🎉 DATASET ORGANIZED SUCCESSFULLY!")
print("=" * 60)

print("\n🚀 NEXT STEP: Run python train_model.py")
