# Runpod Qwen-Image-2.1 LoRA scripts

These are the scripts already uploaded to the active Pod. `setup.sh` unpacks
the reviewed real93 dataset and pinned DiffSynth-Studio source; `run_train.sh`
runs a two-image smoke test or the 93-image full fit; `launch_detached.sh`
starts the selected mode in the background. The active full run must not be
started a second time.

Current Pod ID, process/log/output paths, last verified progress, and the
download/stop checklist are in `docs/v5_prompts/runpod_qwen21_handoff.md`.
The local tarballs and key material are in ignored `.tmp/runpod_qwen21/`.
The unsuccessful SSH proxy experiment is archived at
`scripts/legacy/runpod/ssh_proxy_connect.py`.
