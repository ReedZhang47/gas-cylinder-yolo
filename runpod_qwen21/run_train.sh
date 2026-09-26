#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-}"
if [[ "$MODE" != smoke && "$MODE" != full ]]; then
  echo 'Usage: run_train.sh smoke|full' >&2
  exit 2
fi

WORK=/workspace
CODE="$WORK/DiffSynth-Studio"
DATA="$WORK/real93"
test -f "$CODE/examples/qwen_image_21/model_training/train.py"
test -d "$DATA/images"

if [[ "$MODE" == smoke ]]; then
  test -f "$DATA/metadata.csv"
  head -n 3 "$DATA/metadata.csv" > "$DATA/metadata.SMOKE.csv"
  METADATA="$DATA/metadata.SMOKE.csv"
  REPEAT=1
  EPOCHS=1
  SAVE=2
  OUTPUT="$WORK/outputs/qwen21_smoke"
else
  if [[ ! -f "$DATA/metadata.csv" ]]; then
    echo 'Reviewed metadata.csv is absent. Refusing a paid full training run.' >&2
    exit 3
  fi
  METADATA="$DATA/metadata.csv"
  REPEAT="${DATASET_REPEAT:-5}"
  EPOCHS="${NUM_EPOCHS:-4}"
  SAVE="${SAVE_STEPS:-250}"
  OUTPUT="$WORK/outputs/qwen21_real93_r16"
fi

export HF_HOME="$WORK/cache/huggingface"
export DIFFSYNTH_MODEL_BASE_PATH="$WORK/model_cache"
export DIFFSYNTH_DOWNLOAD_SOURCE=HuggingFace
export TOKENIZERS_PARALLELISM=false
mkdir -p "$HF_HOME" "$OUTPUT"

MODEL_REF='Qwen/Qwen-Image-2.1:transformer/diffusion_pytorch_model*.safetensors,Qwen/Qwen-Image-2.1:text_encoder/model*.safetensors,Qwen/Qwen-Image-2.1:vae/diffusion_pytorch_model*.safetensors'
cd "$CODE"
accelerate launch --num_processes 1 examples/qwen_image_21/model_training/train.py \
  --dataset_base_path "$DATA" \
  --dataset_metadata_path "$METADATA" \
  --data_file_keys image \
  --max_pixels "${MAX_PIXELS:-1048576}" \
  --dataset_repeat "$REPEAT" \
  --num_epochs "$EPOCHS" \
  --model_id_with_origin_paths "$MODEL_REF" \
  --fp8_models "$MODEL_REF" \
  --learning_rate 1e-4 \
  --weight_decay 0.0001 \
  --remove_prefix_in_ckpt 'pipe.dit.' \
  --output_path "$OUTPUT" \
  --lora_base_model dit \
  --lora_target_modules '' \
  --lora_rank 16 \
  --use_gradient_checkpointing \
  --find_unused_parameters \
  --enable_csv_log \
  --save_steps "$SAVE"
