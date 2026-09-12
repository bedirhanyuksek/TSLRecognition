from pathlib import Path

import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset


class LandmarkDataset(Dataset):
    def __init__(self, manifest: str | Path, landmark_dir: str | Path, split: str, label_to_id=None):
        self.manifest = pd.read_csv(manifest)
        self.manifest = self.manifest[self.manifest["split"].astype(str).str.lower() == split].reset_index(drop=True)
        self.landmark_dir = Path(landmark_dir)
        if label_to_id is None:
            labels = sorted(self.manifest["label"].astype(str).unique())
            label_to_id = {label: idx for idx, label in enumerate(labels)}
        self.label_to_id = label_to_id
        self.id_to_label = {idx: label for label, idx in self.label_to_id.items()}

    def __len__(self):
        return len(self.manifest)

    def __getitem__(self, idx):
        row = self.manifest.iloc[idx]
        path = self.landmark_dir / f"{row.sample_id}.npz"
        data = np.load(path)
        x = torch.from_numpy(data["landmarks"].astype(np.float32))
        y = torch.tensor(self.label_to_id[str(row.label)], dtype=torch.long)
        return x, y
