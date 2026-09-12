# Machine Learning

This directory contains the training, preprocessing, and evaluation artifacts
used during development of the sign-recognition models. It does not contain the
AUTSL videos, extracted landmark caches, or personal no-sign recordings.

## Pipelines

### Final 226-class Landmark TCN

The production word classifier uses 24-frame sequences with 300 normalized
MediaPipe landmark features per frame. The final configuration is in
`configs/landmark_tcn_full.yaml`.

Recorded evaluation results:

- Validation: 4,418 samples, 88.23% top-1 and 97.76% top-5 accuracy.
- Test: 3,742 samples, 86.56% top-1 and 98.24% top-5 accuracy.

Artifacts are under `evaluation/final/validation/` and
`evaluation/final/test/`. The training log is `evaluation/final/train.log`.

### Balanced 226-class experiment

This experiment used 10 training and 5 validation samples per class to test a
class-balanced pipeline before full-data training. Its best recorded validation
result was 61.77% top-1 and 86.46% top-5 accuracy. Configuration and artifacts
are in `configs/landmark_tcn_balanced.yaml` and `evaluation/balanced/`.

### Sign/no-sign gate

The binary gate is applied before word classification. The included sign-only
test report records 99.97% sign recall on 3,742 sign samples at a threshold of
0.8. It does not contain a held-out no-sign false-positive measurement. The
configuration and report are in `configs/sign_gate.yaml` and
`evaluation/sign_gate/`.

### Early Transformer experiments

`experiments/transformer20/` contains the earlier 20-class landmark Transformer
pipeline. Preserved validation results are 53.13% for the 25-samples-per-class
subset, 72.15% for 100 samples per class, and 80.17% for the full 20-class train
split. The latter two runs have summaries and evaluation JSON files but no
preserved checkpoints.

## Data and reproducibility

The repository intentionally excludes raw videos, generated landmark arrays,
and private no-sign recordings. The source, configurations, logs, and metrics
are retained, but training is only partially reproducible until the documented
dataset and split manifests are supplied. Dataset use must follow the original
dataset license.

## Working directories

Run the final pipeline from this directory:

```bash
cd ml
PYTHONPATH=src python -m chatsl_ml.train_landmarks --config configs/landmark_tcn_full.yaml
PYTHONPATH=src python -m unittest discover -s tests
```

Landmark extraction and evaluation require explicit manifest, data, checkpoint,
and output paths. Inspect their command-line options with:

```bash
PYTHONPATH=src python -m chatsl_ml.extract_landmarks --help
PYTHONPATH=src python -m chatsl_ml.evaluate_landmarks --help
```

Run historical Transformer commands from its experiment directory:

```bash
cd ml/experiments/transformer20
PYTHONPATH=src python src/train.py --help
PYTHONPATH=src python src/evaluate.py --help
```

The Transformer experiment keeps a separate requirements file because its
historical dependency constraints differ from the final pipeline.
