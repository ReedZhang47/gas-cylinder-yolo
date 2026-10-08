# Runpod Qwen-Image-2.1 LoRA scripts

These are the scripts used for the completed real93 LoRA training. `setup.sh` unpacks
the reviewed real93 dataset and pinned DiffSynth-Studio source; `run_train.sh`
runs a two-image smoke test or the 93-image full fit; `launch_detached.sh`
starts the selected mode in the background. Training finished at step 1,860;
the Pod and remote volume were deleted. These small scripts remain tracked
as the executable record of the published training method.

Current method, parameters, weight hashes and validation evidence are in
`docs/v5_prompts/qwen21_lora_training_validation.md`. Large verified training
artifacts remain in ignored `weights/qwen21_real93_r16/`.
Local historical operations are in ignored `docs/archive/`; upload/caption
preparation helpers are in ignored `scripts/legacy/runpod_preparation/`.
The protected local transfer directory `.tmp/runpod_qwen21/` remains ignored.
