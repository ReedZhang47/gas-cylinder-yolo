#!/usr/bin/env bash
set -euo pipefail

# Run after uploading the two local tar files into /workspace/staging.
WORK=/workspace
STAGING="$WORK/staging"
DATA_TAR="${DATA_TAR:-$STAGING/real93_REVIEWED.tar}"
CODE_TAR="${CODE_TAR:-$STAGING/DiffSynth-Studio_7686e54d41d2.tar}"

test -f "$DATA_TAR"
test -f "$CODE_TAR"
mkdir -p "$WORK/DiffSynth-Studio" "$WORK/cache/pip" "$WORK/model_cache"
tar -xf "$CODE_TAR" -C "$WORK/DiffSynth-Studio"
tar -xf "$DATA_TAR" -C "$WORK"

python3 - <<'PY'
import torch
print('torch=', torch.__version__, 'cuda=', torch.version.cuda)
print('gpu=', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'NONE')
if not torch.cuda.is_available():
    raise SystemExit('No CUDA GPU; stop before model download or training')
if torch.cuda.get_device_properties(0).total_memory < 44 * 1024**3:
    raise SystemExit('This setup expects a 48 GB GPU')
PY

export PIP_CACHE_DIR="$WORK/cache/pip"
python3 -m pip install --break-system-packages -e "$WORK/DiffSynth-Studio"
python3 -m pip check
python3 - <<'PY'
from diffsynth.pipelines.qwen_image_21 import QwenImage21Pipeline
print('DiffSynth Qwen-Image-2.1 import: OK')
PY

echo 'Setup complete. Run ./run_train.sh smoke for a two-image technical test.'
