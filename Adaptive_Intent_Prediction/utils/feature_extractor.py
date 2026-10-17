"""
Appearance Feature Extractor

Extracts 512-dimensional features from pedestrian crops
using ImageNet pretrained ResNet18.
"""

import cv2
import numpy as np
import torch

from torchvision import models
from torchvision import transforms


class AppearanceFeatureExtractor:

    def __init__(self):

        # Device
        self.device = (
            "cuda"
            if torch.cuda.is_available()
            else "cpu"
        )

        # Pretrained ResNet18
        weights = models.ResNet18_Weights.DEFAULT

        model = models.resnet18(
            weights=weights
        )

        # Remove classifier
        self.model = torch.nn.Sequential(
            *list(model.children())[:-1]
        )

        self.model.eval()
        self.model.to(self.device)

        # Image preprocessing
        self.transform = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((224,224)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485,0.456,0.406],
                std=[0.229,0.224,0.225]
            )
        ])

    def extract(
        self,
        image: np.ndarray
    ) -> np.ndarray:

        # OpenCV BGR -> RGB
        image = cv2.cvtColor(
            image,
            cv2.COLOR_BGR2RGB
        )

        tensor = self.transform(
            image
        ).unsqueeze(0)

        tensor = tensor.to(self.device)

        with torch.no_grad():

            feature = self.model(
                tensor
            )

        feature = feature.squeeze()

        return feature.cpu().numpy()