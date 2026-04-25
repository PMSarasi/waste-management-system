import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms
from PIL import Image
import os
import timm
from sklearn.metrics import accuracy_score
import matplotlib.pyplot as plt

# ============================================
# STEP 1: DATASET CLASS
# ============================================
class WasteDataset(Dataset):
    def __init__(self, root_dir, transform=None):
        self.root_dir = root_dir
        self.transform = transform
        self.classes = ['cardboard', 'glass', 'metal', 'paper', 'plastic', 'trash']
        self.class_to_idx = {cls: idx for idx, cls in enumerate(self.classes)}
        
        self.images = []
        self.labels = []
        
        for class_name in self.classes:
            class_dir = os.path.join(root_dir, class_name)
            for img_name in os.listdir(class_dir):
                self.images.append(os.path.join(class_dir, img_name))
                self.labels.append(self.class_to_idx[class_name])
    
    def __len__(self):
        return len(self.images)
    
    def __getitem__(self, idx):
        image = Image.open(self.images[idx]).convert('RGB')
        label = self.labels[idx]
        if self.transform:
            image = self.transform(image)
        return image, label

# ============================================
# STEP 2: DATA TRANSFORMS
# ============================================
train_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.RandomHorizontalFlip(),
    transforms.RandomRotation(15),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

val_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

# ============================================
# STEP 3: LOAD DATASETS
# ============================================
train_dataset = WasteDataset("data/train", transform=train_transform)
val_dataset = WasteDataset("data/val", transform=val_transform)

train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
val_loader = DataLoader(val_dataset, batch_size=32, shuffle=False)

print(f"✅ Train: {len(train_dataset)} images")
print(f"✅ Val: {len(val_dataset)} images")

# ============================================
# STEP 4: LOAD EFFICIENTNET (TRANSFER LEARNING)
# ============================================
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")

model = timm.create_model('efficientnet_b0', pretrained=True)
num_classes = 6
model.classifier = nn.Linear(model.classifier.in_features, num_classes)
model = model.to(device)

# Freeze base layers
for param in model.parameters():
    param.requires_grad = False
for param in model.classifier.parameters():
    param.requires_grad = True

# ============================================
# STEP 5: TRAINING SETUP
# ============================================
criterion = nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.classifier.parameters(), lr=0.001)

# ============================================
# STEP 6: TRAINING LOOP
# ============================================
print("\n🚀 Starting Training...")
print("=" * 50)

train_losses = []
val_accuracies = []

for epoch in range(10):
    # Training
    model.train()
    train_loss = 0
    for images, labels in train_loader:
        images, labels = images.to(device), labels.to(device)
        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        train_loss += loss.item()
    
    # Validation
    model.eval()
    all_preds = []
    all_labels = []
    with torch.no_grad():
        for images, labels in val_loader:
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            _, preds = torch.max(outputs, 1)
            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())
    
    val_acc = accuracy_score(all_labels, all_preds)
    avg_loss = train_loss / len(train_loader)
    
    train_losses.append(avg_loss)
    val_accuracies.append(val_acc)
    
    print(f"Epoch {epoch+1}/10 | Loss: {avg_loss:.4f} | Val Acc: {val_acc:.4f}")

# ============================================
# STEP 7: FINE-TUNING (UNFREEZE LAST LAYERS)
# ============================================
print("\n🔧 Fine-tuning last layers...")

for param in model.parameters():
    param.requires_grad = True

optimizer = torch.optim.Adam(model.parameters(), lr=0.0001)

for epoch in range(5):
    model.train()
    train_loss = 0
    for images, labels in train_loader:
        images, labels = images.to(device), labels.to(device)
        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        train_loss += loss.item()
    
    # Validation
    model.eval()
    all_preds = []
    all_labels = []
    with torch.no_grad():
        for images, labels in val_loader:
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            _, preds = torch.max(outputs, 1)
            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())
    
    val_acc = accuracy_score(all_labels, all_preds)
    print(f"Fine-tune Epoch {epoch+1}/5 | Val Acc: {val_acc:.4f}")

# ============================================
# STEP 8: SAVE MODEL
# ============================================
torch.save(model.state_dict(), "models/waste_classifier.pth")
print("\n✅ Model saved to models/waste_classifier.pth")

# Plot training curves
plt.figure(figsize=(12, 4))
plt.subplot(1, 2, 1)
plt.plot(train_losses)
plt.title('Training Loss')
plt.xlabel('Epoch')
plt.ylabel('Loss')

plt.subplot(1, 2, 2)
plt.plot(val_accuracies)
plt.title('Validation Accuracy')
plt.xlabel('Epoch')
plt.ylabel('Accuracy')
plt.ylim(0, 1)

plt.savefig("outputs/training_curves.png")
print("✅ Training curves saved to outputs/training_curves.png")
plt.show()

print("\n🎉 TRAINING COMPLETE!")