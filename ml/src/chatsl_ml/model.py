from __future__ import annotations

import torch
from torch import nn
from torchvision.models import MobileNet_V3_Small_Weights, mobilenet_v3_small


class TemporalCNN(nn.Module):
    def __init__(
        self,
        num_classes: int,
        hidden_size: int = 256,
        dropout: float = 0.3,
        pretrained: bool = False,
    ) -> None:
        super().__init__()
        if pretrained:
            raise ValueError("Pretrained weights are not supported by the local CNN baseline")
        self.features = nn.Sequential(
            nn.Conv2d(3, 32, kernel_size=3, stride=2, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=False),
            nn.Conv2d(32, 64, kernel_size=3, stride=2, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=False),
            nn.MaxPool2d(2),
            nn.Conv2d(64, 128, kernel_size=3, stride=2, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=False),
        )
        self.pool = nn.AdaptiveAvgPool2d(1)
        self.temporal = nn.Sequential(
            nn.Linear(128, hidden_size),
            nn.ReLU(inplace=False),
            nn.Dropout(dropout),
        )
        self.classifier = nn.Linear(hidden_size, num_classes)

    def forward(self, video: torch.Tensor) -> torch.Tensor:
        batch, frames, channels, height, width = video.shape
        images = video.contiguous().reshape(
            batch * frames, channels, height, width
        )
        features = self.pool(self.features(images)).flatten(1)
        features = features.reshape(batch, frames, -1)
        features = self.temporal(features)
        return self.classifier(features.mean(dim=1))


class PretrainedTemporalMobileNet(nn.Module):
    def __init__(
        self,
        num_classes: int,
        hidden_size: int = 512,
        dropout: float = 0.4,
        pretrained: bool = True,
        freeze_backbone: bool = True,
        trainable_backbone_blocks: int = 0,
    ) -> None:
        super().__init__()
        weights = MobileNet_V3_Small_Weights.DEFAULT if pretrained else None
        backbone = mobilenet_v3_small(weights=weights)
        self.features = backbone.features
        self.pool = nn.AdaptiveAvgPool2d(1)
        feature_size = backbone.classifier[0].in_features

        self.frozen_blocks: list[nn.Module] = []
        if freeze_backbone:
            for parameter in self.features.parameters():
                parameter.requires_grad = False
        elif trainable_backbone_blocks > 0:
            for parameter in self.features.parameters():
                parameter.requires_grad = False
            trainable_blocks = list(self.features.children())[-trainable_backbone_blocks:]
            for block in trainable_blocks:
                for parameter in block.parameters():
                    parameter.requires_grad = True
            self.frozen_blocks = list(self.features.children())[:-trainable_backbone_blocks]

        # Mean/max/std describe pose; frame differences retain motion direction.
        temporal_size = feature_size * 4
        self.classifier = nn.Sequential(
            nn.LayerNorm(temporal_size),
            nn.Linear(temporal_size, hidden_size),
            nn.ReLU(inplace=False),
            nn.Dropout(dropout),
            nn.Linear(hidden_size, num_classes),
        )

    def train(self, mode: bool = True) -> "PretrainedTemporalMobileNet":
        super().train(mode)
        if not any(parameter.requires_grad for parameter in self.features.parameters()):
            self.features.eval()
        for block in self.frozen_blocks:
            block.eval()
        return self

    def forward(self, video: torch.Tensor) -> torch.Tensor:
        batch, frames, channels, height, width = video.shape
        images = video.contiguous().reshape(
            batch * frames, channels, height, width
        )
        features = self.pool(self.features(images)).flatten(1)
        features = features.reshape(batch, frames, -1)
        differences = features[:, 1:] - features[:, :-1]
        summary = torch.cat(
            (
                features.mean(dim=1),
                features.amax(dim=1),
                features.std(dim=1, unbiased=False),
                differences.mean(dim=1),
            ),
            dim=1,
        )
        return self.classifier(summary.contiguous())


def build_model(config: dict, num_classes: int) -> nn.Module:
    name = config.get("name", "temporal_cnn")
    common = {
        "num_classes": num_classes,
        "hidden_size": config["hidden_size"],
        "dropout": config["dropout"],
        "pretrained": config.get("pretrained", False),
    }
    if name == "temporal_cnn":
        return TemporalCNN(**common)
    if name == "pretrained_temporal_mobilenet":
        return PretrainedTemporalMobileNet(
            **common,
            freeze_backbone=config.get("freeze_backbone", True),
            trainable_backbone_blocks=config.get("trainable_backbone_blocks", 0),
        )
    raise ValueError(f"Unknown model: {name}")
