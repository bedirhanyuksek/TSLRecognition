# Runtime Models

The inference backend expects these files in this directory:

| File | Purpose | Repository status |
| --- | --- | --- |
| `landmark_tcn_full.pt` | Project-trained 226-class production checkpoint | Tracked |
| `sign_gate.pt` | Project-trained sign/no-sign checkpoint | Tracked |
| `holistic_landmarker.task` | MediaPipe Holistic Landmarker runtime asset | Downloaded locally, not tracked |

Download and verify the MediaPipe runtime asset from the repository root:

```bash
python3 server/scripts/download_holistic_model.py
```

Expected SHA-256:

```text
e2dab61191e2dcd0a15f943d8e3ed1dce13c82dfa597b9dd39f562975a50c3f8
```

The download script uses the model bundle linked by the official Google
MediaPipe Holistic Landmarker documentation. The file remains ignored so that
the third-party binary is not redistributed by this repository.
