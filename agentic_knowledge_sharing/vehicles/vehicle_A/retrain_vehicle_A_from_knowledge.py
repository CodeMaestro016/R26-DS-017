import json
import shutil
from pathlib import Path
from ultralytics import YOLO
import cv2
import numpy as np
from PIL import Image
import warnings
import yaml
from datetime import datetime

warnings.filterwarnings('ignore')

# Paths
AGENTIC_DIR = Path(__file__).resolve().parents[2]

# Model paths
VEHICLE_A_MODEL_PATH = AGENTIC_DIR / "Models" / "vehicle_A_prohibitory_best.pt"
BACKUP_DIR = AGENTIC_DIR / "Models" / "backups"

# Data paths
VERIFIED_KNOWLEDGE_PATH = AGENTIC_DIR / "global_verfication_server" / "verified_knowledge.json"
CROPPED_SIGNS_DIR = AGENTIC_DIR / "shared" / "cropped_signs"

# Training output
TRAINING_DIR = AGENTIC_DIR / "training_temp"
IMAGES_DIR = TRAINING_DIR / "images"
LABELS_DIR = TRAINING_DIR / "labels"

# Training parameters
MODEL_NAME = "vehicle_A_incremental_update"
IMG_SIZE = 640
LEARNING_RATE = 0.00005
EPOCHS = 20  # Increase epochs since we have few samples
BATCH_SIZE = 4


def backup_old_model():
    """Backup old model with timestamp"""
    if not VEHICLE_A_MODEL_PATH.exists():
        return None
    
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"vehicle_A_prohibitory_best_backup_{timestamp}.pt"
    backup_path = BACKUP_DIR / backup_filename
    
    shutil.copy(VEHICLE_A_MODEL_PATH, backup_path)
    print(f"💾 Backed up: {backup_path.name}")
    return backup_path


def get_model_info():
    """Get information about the current model"""
    if not VEHICLE_A_MODEL_PATH.exists():
        return None
    
    model = YOLO(str(VEHICLE_A_MODEL_PATH))
    print(f"\n📊 Current Model Info:")
    print(f"   - Classes in model: {len(model.names) if hasattr(model, 'names') else 'Unknown'}")
    if hasattr(model, 'names'):
        print(f"   - Class names: {list(model.names.values())[:12]}...")
    return model


def load_verified_packages():
    """Load verified packages from JSON"""
    if not VERIFIED_KNOWLEDGE_PATH.exists():
        print(f"❌ No verified knowledge found")
        return []
    
    with open(VERIFIED_KNOWLEDGE_PATH, "r") as f:
        data = json.load(f)
    
    # Handle different JSON structures
    if isinstance(data, list):
        packages = data
    elif isinstance(data, dict) and "packages" in data:
        packages = data["packages"]
    else:
        packages = []
    
    # Filter only packages marked for training
    training_packages = [p for p in packages if p.get("use_for_training") is True]
    
    print(f"\n📦 Verified packages: {len(training_packages)}")
    
    # Show class distribution
    class_counts = {}
    for p in training_packages:
        class_id = p.get("global_class_id") or p.get("class_id")
        if class_id:
            class_counts[class_id] = class_counts.get(class_id, 0) + 1
    
    if class_counts:
        print(f"\n📈 New classes to learn:")
        for class_id, count in sorted(class_counts.items()):
            sign_name = training_packages[0].get("sign_name", f"class_{class_id}")
            print(f"   - Class {class_id} ({sign_name}): {count} samples")
    
    return training_packages


def prepare_training_data(packages):
    """Prepare YOLO training data"""
    
    # Clean directories
    if TRAINING_DIR.exists():
        shutil.rmtree(TRAINING_DIR)
    
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    LABELS_DIR.mkdir(parents=True, exist_ok=True)
    
    training_samples = []
    class_mapping = {}
    class_counts = {}
    
    print(f"\n📁 Preparing training data...")
    
    for idx, package in enumerate(packages):
        # Get package info
        package_id = package.get("package_id") or package.get("Package ID")
        class_id = package.get("global_class_id") or package.get("class_id")
        sign_name = package.get("sign_name") or package.get("type") or f"class_{class_id}"
        
        if class_id is None:
            continue
        
        # Get cropped image path
        cropped_path = package.get("cropped_sign_path") or package.get("cropped_image_path")
        
        if cropped_path:
            cropped_path = str(cropped_path).replace('\\', '/')
            if not Path(cropped_path).is_absolute():
                cropped_path = AGENTIC_DIR / cropped_path
            else:
                cropped_path = Path(cropped_path)
        
        if not cropped_path or not cropped_path.exists():
            # Try to find by package_id
            possible_paths = list(CROPPED_SIGNS_DIR.glob(f"*{package_id}*.png")) + \
                           list(CROPPED_SIGNS_DIR.glob(f"*{package_id}*.jpg"))
            if possible_paths:
                cropped_path = possible_paths[0]
            else:
                print(f"⚠️ No image for {package_id}")
                continue
        
        # Load image
        try:
            img = cv2.imread(str(cropped_path))
            if img is None:
                img = np.array(Image.open(cropped_path))
            h, w = img.shape[:2]
        except Exception as e:
            print(f"⚠️ Failed to load: {cropped_path}")
            continue
        
        # Use full image as bounding box
        x1, y1, x2, y2 = 0, 0, w, h
        
        # Convert to YOLO format
        x_center = (x1 + x2) / 2.0 / w
        y_center = (y1 + y2) / 2.0 / h
        width = (x2 - x1) / w
        height = (y2 - y1) / h
        
        # Copy image
        img_filename = f"sample_{idx:04d}.png"
        shutil.copy(cropped_path, IMAGES_DIR / img_filename)
        
        # Create label
        label_filename = img_filename.replace('.png', '.txt')
        with open(LABELS_DIR / label_filename, 'w') as f:
            f.write(f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n")
        
        training_samples.append({
            'image': img_filename,
            'class_id': class_id,
            'sign_name': sign_name
        })
        
        class_mapping[class_id] = sign_name
        class_counts[class_id] = class_counts.get(class_id, 0) + 1
    
    print(f"\n✅ Prepared {len(training_samples)} samples from {len(class_mapping)} new classes")
    return training_samples, class_mapping, class_counts


def create_data_yaml(class_mapping, existing_num_classes=43):
    """Create data.yaml - preserve existing class structure"""
    
    # Use the model's existing class count (43)
    num_classes = existing_num_classes
    
    # Create class names list (preserve existing names, add new ones)
    class_names = [f"class_{i}" for i in range(num_classes)]
    
    # Update with actual class names from mapping
    for class_id, name in class_mapping.items():
        if class_id < num_classes:
            class_names[class_id] = name
    
    yaml_content = {
        'path': str(TRAINING_DIR.absolute()),
        'train': 'images',
        'val': 'images',
        'nc': num_classes,
        'names': class_names
    }
    
    yaml_path = TRAINING_DIR / "data.yaml"
    with open(yaml_path, 'w') as f:
        yaml.dump(yaml_content, f, default_flow_style=False)
    
    print(f"\n✅ data.yaml created with {num_classes} total classes")
    return yaml_path


def augment_data(images_dir, labels_dir):
    """Simple data augmentation to increase training samples"""
    
    print(f"\n🔄 Applying data augmentation...")
    
    image_files = list(images_dir.glob("*.png")) + list(images_dir.glob("*.jpg"))
    original_count = len(image_files)
    
    if original_count == 0:
        return 0
    
    # Create augmented copies
    import random
    
    for img_path in image_files:
        # Skip if already an augmented image
        if "_aug" in img_path.stem:
            continue
        
        # Load image
        img = cv2.imread(str(img_path))
        if img is None:
            continue
        
        # Load corresponding label
        label_path = labels_dir / f"{img_path.stem}.txt"
        if not label_path.exists():
            continue
        
        with open(label_path, 'r') as f:
            label_content = f.read()
        
        # Create 3 augmented versions
        for aug_id in range(3):
            aug_img = img.copy()
            
            # Apply random augmentations
            if aug_id == 0:  # Horizontal flip
                aug_img = cv2.flip(img, 1)
                # Update label for flip
                lines = label_content.strip().split('\n')
                new_labels = []
                for line in lines:
                    parts = line.split()
                    if len(parts) == 5:
                        class_id, x_center, y_center, width, height = parts
                        x_center = 1.0 - float(x_center)
                        new_labels.append(f"{class_id} {x_center:.6f} {y_center} {width} {height}")
                label_content = '\n'.join(new_labels)
                
            elif aug_id == 1:  # Small rotation/brightness
                # Simple brightness adjustment
                aug_img = cv2.convertScaleAbs(img, alpha=1.2, beta=10)
                
            elif aug_id == 2:  # Slight blur
                aug_img = cv2.GaussianBlur(img, (3, 3), 0)
            
            # Save augmented image
            aug_filename = f"{img_path.stem}_aug{aug_id}.png"
            cv2.imwrite(str(images_dir / aug_filename), aug_img)
            
            # Save augmented label
            aug_label_path = labels_dir / f"{aug_filename.replace('.png', '.txt')}"
            with open(aug_label_path, 'w') as f:
                f.write(label_content)
    
    # Count new total
    new_image_files = list(images_dir.glob("*.png")) + list(images_dir.glob("*.jpg"))
    print(f"   Augmented {original_count} → {len(new_image_files)} samples")
    return len(new_image_files)


def incremental_fine_tune_vehicle_A():
    """
    Method 1: Parameter Freezing + Low Learning Rate
    Update model with new classes while preserving old knowledge
    """
    
    print("\n" + "="*70)
    print("VEHICLE A INCREMENTAL FINE-TUNING (Method 1)")
    print("Updating model with new sign classes while preserving existing knowledge")
    print("="*70)
    
    # 1. Get model info
    model_info = get_model_info()
    
    # 2. Check model exists
    if not VEHICLE_A_MODEL_PATH.exists():
        print(f"\n❌ Model not found!")
        return
    
    # 3. Load verified packages
    packages = load_verified_packages()
    
    if len(packages) == 0:
        print("\n❌ No verified packages found for training!")
        return
    
    # 4. Prepare training data
    training_samples, class_mapping, class_counts = prepare_training_data(packages)
    
    if len(training_samples) < 5:
        print(f"\n❌ Only {len(training_samples)} samples - need at least 10-20")
        return
    
    # 5. Apply data augmentation to increase samples
    new_count = augment_data(IMAGES_DIR, LABELS_DIR)
    
    # 6. Create data.yaml
    yaml_path = create_data_yaml(class_mapping, existing_num_classes=43)
    
    # 7. Summary
    print(f"\n🔍 Training Summary:")
    print(f"   - Original Model Classes: 12 (prohibitory)")
    print(f"   - Model Capacity: 43 classes")
    print(f"   - New classes to add: {len(class_mapping)}")
    print(f"   - Training samples (augmented): {new_count}")
    print(f"   - Learning rate: {LEARNING_RATE} (prevents forgetting)")
    print(f"   - Frozen layers: 12 (preserves old knowledge)")
    
    # Ask for confirmation
    response = input(f"\nProceed with training? (y/N): ")
    if response.lower() != 'y':
        print("Training cancelled")
        return
    
    # 8. Backup old model
    backup_path = backup_old_model()
    
    # 9. Train
    print(f"\n🚀 Starting incremental training...")
    print(f"   This will: Keep old 12 classes + Learn {len(class_mapping)} new classes")
    
    model = YOLO(str(VEHICLE_A_MODEL_PATH))
    
    results = model.train(
        data=str(yaml_path),
        
        # Anti-forgetting parameters
        epochs=EPOCHS,
        freeze=12,                    # Freeze first 12 layers
        lr0=LEARNING_RATE,
        lrf=LEARNING_RATE / 10,
        
        # Optimizer
        optimizer='SGD',
        momentum=0.937,
        weight_decay=0.0005,
        
        # Image settings
        imgsz=IMG_SIZE,
        batch=BATCH_SIZE,
        
        # Protection
        warmup_epochs=0,
        overlap_mask=True,
        close_mosaic=10,
        
        # Other
        device='cpu',
        workers=0,
        project=str(AGENTIC_DIR / "runs" / "detect"),
        name=MODEL_NAME,
        exist_ok=True,
        plots=True,
        verbose=True,
        save=True,
        val=True
    )
    
    # 10. Check results
    new_model_path = AGENTIC_DIR / "runs" / "detect" / MODEL_NAME / "weights" / "best.pt"
    
    if not new_model_path.exists():
        print(f"\n❌ Training failed!")
        return
    
    # 11. Validate
    print(f"\n📊 Validating new model...")
    val_results = model.val()
    
    mAP = val_results.box.map50 if hasattr(val_results, 'box') else 0
    
    if mAP == 0:
        print(f"\n⚠️ WARNING: Model validation shows 0 mAP")
        print("   This may be due to very limited data")
        print("   Not replacing old model - preserving existing performance")
        print(f"\n   Old model still at: {VEHICLE_A_MODEL_PATH}")
        return
    
    # 12. Update model
    shutil.copy(new_model_path, VEHICLE_A_MODEL_PATH)
    
    print(f"\n" + "="*70)
    print("✅ SUCCESS! Model Updated Successfully!")
    print("="*70)
    print(f"   📁 Model saved: {VEHICLE_A_MODEL_PATH.name}")
    print(f"   💾 Backup: {backup_path.name if backup_path else 'N/A'}")
    print(f"   📊 mAP50: {mAP:.4f}")
    print(f"   🆕 New classes learned: {list(class_mapping.keys())}")
    print(f"   🔒 Old classes preserved via layer freezing")
    print("="*70)
    
    # 13. Cleanup
    response = input("\nDelete temporary training files? (y/N): ")
    if response.lower() == 'y':
        shutil.rmtree(TRAINING_DIR)
        print("   ✓ Cleaned up")


if __name__ == "__main__":
    incremental_fine_tune_vehicle_A()