import torch
import cv2
import numpy as np
from PIL import Image
from torchvision import transforms
import matplotlib.pyplot as plt

class GradCAM:
    def __init__(self, model, target_layer):
        self.model = model
        self.model.eval()
        self.target_layer = target_layer
        self.gradients = None
        self.activations = None
        
        # Register hooks
        target_layer.register_forward_hook(self.save_activation)
        target_layer.register_backward_hook(self.save_gradient)
    
    def save_activation(self, module, input, output):
        self.activations = output
    
    def save_gradient(self, module, grad_input, grad_output):
        self.gradients = grad_output[0]
    
    def generate_heatmap(self, image_tensor, class_idx=None):
        # Forward pass
        output = self.model(image_tensor)
        
        if class_idx is None:
            class_idx = torch.argmax(output, dim=1).item()
        
        # Zero gradients
        self.model.zero_grad()
        
        # Backward pass
        one_hot = torch.zeros_like(output)
        one_hot[0][class_idx] = 1
        output.backward(gradient=one_hot)
        
        # Compute weights
        weights = torch.mean(self.gradients, dim=[2, 3], keepdim=True)
        cam = torch.sum(weights * self.activations, dim=1, keepdim=True)
        cam = torch.relu(cam)
        cam = cam.squeeze().detach().numpy()
        
        # Normalize
        cam = (cam - np.min(cam)) / (np.max(cam) - np.min(cam) + 1e-8)
        
        return cam

def overlay_heatmap(image_path, heatmap, alpha=0.5):
    # Load image
    image = cv2.imread(image_path)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    image = cv2.resize(image, (224, 224))
    
    # Resize heatmap
    heatmap = cv2.resize(heatmap, (224, 224))
    
    # Convert to colormap
    heatmap_colored = cv2.applyColorMap(np.uint8(255 * heatmap), cv2.COLORMAP_JET)
    heatmap_colored = cv2.cvtColor(heatmap_colored, cv2.COLOR_BGR2RGB)
    
    # Overlay
    overlayed = cv2.addWeighted(image, 1 - alpha, heatmap_colored, alpha, 0)
    
    return overlayed

def explain_prediction(model, image_path, device, class_names):
    # Load and preprocess image
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    image = Image.open(image_path).convert('RGB')
    input_tensor = transform(image).unsqueeze(0).to(device)
    
    # Get prediction
    with torch.no_grad():
        output = model(input_tensor)
        probs = torch.softmax(output, dim=1)
        pred_class = torch.argmax(probs, dim=1).item()
        confidence = probs[0][pred_class].item()
    
    # Generate Grad-CAM
    target_layer = model.blocks[6]  # Last block of EfficientNet
    grad_cam = GradCAM(model, target_layer)
    heatmap = grad_cam.generate_heatmap(input_tensor, pred_class)
    
    # Overlay
    overlayed = overlay_heatmap(image_path, heatmap)
    
    # Display
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    axes[0].imshow(image)
    axes[0].set_title(f'Original Image\nPrediction: {class_names[pred_class]}')
    axes[0].axis('off')
    
    axes[1].imshow(heatmap, cmap='jet')
    axes[1].set_title('Grad-CAM Heatmap\n(Red = High Importance)')
    axes[1].axis('off')
    
    axes[2].imshow(overlayed)
    axes[2].set_title(f'Overlay | Confidence: {confidence:.2%}')
    axes[2].axis('off')
    
    plt.tight_layout()
    plt.savefig("outputs/heatmaps/gradcam_output.png")
    plt.show()
    
    return pred_class, confidence, overlayed

# Test function (run after model is trained)
def test_explanation(model_path, test_image_path):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    # Load model
    import timm
    import torch.nn as nn
    model = timm.create_model('efficientnet_b0', pretrained=False)
    model.classifier = nn.Linear(model.classifier.in_features, 6)
    model.load_state_dict(torch.load(model_path, map_location=device))
    model = model.to(device)
    model.eval()
    
    class_names = ['cardboard', 'glass', 'metal', 'paper', 'plastic', 'trash']
    
    # Generate explanation
    pred_class, confidence, _ = explain_prediction(model, test_image_path, device, class_names)
    
    print(f"\n🔍 EXPLANATION RESULTS:")
    print(f"Predicted: {class_names[pred_class]}")
    print(f"Confidence: {confidence:.2%}")
    print(f"Heatmap saved to: outputs/heatmaps/gradcam_output.png")

if __name__ == "__main__":
    test_explanation("models/waste_classifier.pth", "test_image.jpg")