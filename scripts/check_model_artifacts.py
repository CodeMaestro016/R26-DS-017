#!/usr/bin/env python3
"""
Diagnostic script to check model artifacts for PP1 demo.
Checks scaler and label encoder files for corruption and loading issues.
"""

import os
import sys
import pickle
import joblib
import numpy as np

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def check_file_diagnostics(file_path: str, file_type: str):
    """Check diagnostics for a single file."""
    print("=" * 60)
    print(f"CHECKING {file_type.upper()}")
    print("=" * 60)
    
    # Absolute path
    abs_path = os.path.abspath(file_path)
    print(f"Absolute path: {abs_path}")
    
    # File existence
    exists = os.path.exists(file_path)
    print(f"File exists: {exists}")
    
    if not exists:
        print(f"❌ File not found: {file_path}")
        return False
    
    # File size
    try:
        size = os.path.getsize(file_path)
        print(f"File size: {size} bytes ({size/1024:.2f} KB)")
    except Exception as e:
        print(f"❌ Could not get file size: {e}")
        return False
    
    # First 16 bytes
    try:
        with open(file_path, 'rb') as f:
            first_bytes = f.read(16)
        print(f"First 16 bytes (hex): {first_bytes.hex()}")
        print(f"First 16 bytes (repr): {repr(first_bytes)}")
    except Exception as e:
        print(f"❌ Could not read first bytes: {e}")
        return False
    
    # Try joblib.load()
    print("\nTrying joblib.load()...")
    try:
        obj = joblib.load(file_path)
        print(f"✅ joblib.load() successful")
        print(f"Object type: {type(obj)}")
        
        if file_type == "scaler":
            if hasattr(obj, 'mean_'):
                print(f"Scaler mean_ shape: {obj.mean_.shape}")
                print(f"Scaler mean_ type: {type(obj.mean_)}")
            if hasattr(obj, 'scale_'):
                print(f"Scaler scale_ shape: {obj.scale_.shape}")
                print(f"Scaler scale_ type: {type(obj.scale_)}")
            if hasattr(obj, 'n_features_in_'):
                print(f"Scaler n_features_in_: {obj.n_features_in_}")
                
        elif file_type == "label_encoder":
            if hasattr(obj, 'classes_'):
                print(f"Label encoder classes_: {obj.classes_}")
                print(f"Classes type: {type(obj.classes_)}")
                print(f"Number of classes: {len(obj.classes_)}")
        
        return True
        
    except Exception as e:
        print(f"❌ joblib.load() failed: {e}")
    
    # Try pickle.load()
    print("\nTrying pickle.load()...")
    try:
        with open(file_path, 'rb') as f:
            obj = pickle.load(f)
        print(f"✅ pickle.load() successful")
        print(f"Object type: {type(obj)}")
        
        if file_type == "scaler":
            if hasattr(obj, 'mean_'):
                print(f"Scaler mean_ shape: {obj.mean_.shape}")
                print(f"Scaler mean_ type: {type(obj.mean_)}")
            if hasattr(obj, 'scale_'):
                print(f"Scaler scale_ shape: {obj.scale_.shape}")
                print(f"Scaler scale_ type: {type(obj.scale_)}")
            if hasattr(obj, 'n_features_in_'):
                print(f"Scaler n_features_in_: {obj.n_features_in_}")
                
        elif file_type == "label_encoder":
            if hasattr(obj, 'classes_'):
                print(f"Label encoder classes_: {obj.classes_}")
                print(f"Classes type: {type(obj.classes_)}")
                print(f"Number of classes: {len(obj.classes_)}")
        
        return True
        
    except Exception as e:
        print(f"❌ pickle.load() failed: {e}")
    
    print(f"\n❌ Both joblib.load() and pickle.load() failed")
    print(f"❌ {file_type} file is corrupted or not a valid pickle/joblib file")
    return False


def main():
    """Main diagnostic function."""
    print("=" * 80)
    print("PP1 MODEL ARTIFACTS DIAGNOSTIC")
    print("=" * 80)
    
    # Determine paths
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    models_dir = os.path.join(project_root, "models", "observed_behavior")
    
    scaler_path = os.path.join(models_dir, "feature_scaler_observed_behavior.pkl")
    encoder_path = os.path.join(models_dir, "label_encoder_observed_behavior.pkl")
    
    print(f"Models directory: {models_dir}")
    print(f"Models directory exists: {os.path.exists(models_dir)}")
    
    # Check scaler
    scaler_ok = check_file_diagnostics(scaler_path, "scaler")
    
    # Check label encoder
    encoder_ok = check_file_diagnostics(encoder_path, "label_encoder")
    
    # Summary
    print("\n" + "=" * 80)
    print("DIAGNOSTIC SUMMARY")
    print("=" * 80)
    print(f"Scaler file: {'✅ OK' if scaler_ok else '❌ CORRUPTED/MISSING'}")
    print(f"Label encoder file: {'✅ OK' if encoder_ok else '❌ CORRUPTED/MISSING'}")
    
    if scaler_ok and encoder_ok:
        print("\n✅ All model artifacts are OK")
        print("You can run the demo without fallback flags:")
        print("python scripts\\run_pp1_professional_v2v_demo.py --scenario 2 --keep-open-seconds 30")
    else:
        print("\n❌ Some model artifacts are corrupted or missing")
        print("You need to re-download the files from Colab or use fallback flags:")
        print("python scripts\\run_pp1_professional_v2v_demo.py --scenario 2 --allow-identity-scaler --allow-default-labels --keep-open-seconds 30")
    
    print("=" * 80)


if __name__ == "__main__":
    main()
