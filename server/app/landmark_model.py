from __future__ import annotations

import torch
from torch import nn


class TemporalBlock(nn.Module):
    def __init__(self, channels: int, dilation: int, dropout: float) -> None:
        super().__init__()
        self.block = nn.Sequential(
            nn.Conv1d(
                channels,
                channels,
                kernel_size=3,
                padding=dilation,
                dilation=dilation,
            ),
            nn.BatchNorm1d(channels),
            nn.ReLU(inplace=False),
            nn.Dropout(dropout),
            nn.Conv1d(
                channels,
                channels,
                kernel_size=3,
                padding=dilation,
                dilation=dilation,
            ),
            nn.BatchNorm1d(channels),
            nn.ReLU(inplace=False),
        )

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        return inputs + self.block(inputs)


class LandmarkTCN(nn.Module):
    def __init__(
        self,
        input_size: int,
        hidden_size: int,
        num_classes: int,
        dropout: float,
    ) -> None:
        super().__init__()
        self.input_projection = nn.Sequential(
            nn.LayerNorm(input_size),
            nn.Linear(input_size, hidden_size),
            nn.ReLU(inplace=False),
        )
        self.temporal = nn.Sequential(
            TemporalBlock(hidden_size, dilation=1, dropout=dropout),
            TemporalBlock(hidden_size, dilation=2, dropout=dropout),
            TemporalBlock(hidden_size, dilation=4, dropout=dropout),
        )
        self.classifier = nn.Sequential(
            nn.Dropout(dropout),
            nn.Linear(hidden_size * 2, num_classes),
        )

    def forward(self, sequence: torch.Tensor) -> torch.Tensor:
        features = self.input_projection(sequence)
        features = self.temporal(features.transpose(1, 2).contiguous())
        pooled = torch.cat(
            (features.mean(dim=2), features.amax(dim=2)),
            dim=1,
        )
        return self.classifier(pooled)
