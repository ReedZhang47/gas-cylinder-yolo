# v5 D 臂：提示词与批量生图

## 当前入口

兼容 Qwen-Image-2.1 的 real93 LoRA 已完成训练及本机固定输入验证。训练方法、参数、loss、哈希、权重维度和 N114 五张对照记录见 qwen21_lora_training_validation.md；Runpod 资源收尾与完整归档见 runpod_qwen21_handoff.md。旧 Liblib 权重与当前底模不兼容；trial_workflow_api.json 是旧工作流快照，不能直接作为正式生成依据。

| 文件 | 角色 |
|---|---|
| ../Prompts_Based_on_real93.md | 原始 93 条描述素材，保留供对照 |
| real93_cores.tsv、new150_cores.tsv | 逐条可审阅的场景核心 |
| build_prompt_sets.py | 检查 ID、数量、重复并生成完整提示词 |
| real93_prompts.jsonl、new150_prompts.jsonl | 批量脚本输入；当前均为 draft |
| real93_lora_metadata.csv | 已用于云端 LoRA 训练的 93 条人工复核 caption 精确副本（无照片） |
| qwen21_lora_training_validation.md | 实际训练环境与参数、loss/检查点、维度核对和固定 N114 推理验证 |
| qwen21_lora_n114_validation.csv | 五张固定 seed 对照图的有效强度、连线、参数和 PNG SHA256 |
| trial_workflow_api.json | 旧的、LoRA 不兼容的试图工作流快照 |
| scripts/comfy_batch_t2i.py | 默认 dry-run；经批准后顺序排队、稳定 seed、恢复和 manifest |

LoRA 训练使用的 93 条人工复核 caption 已保存在 real93_lora_metadata.csv；本机 .tmp/runpod_qwen21/real93 和已上传的 real93_REVIEWED.tar 使用同一内容。它们与后续批量生图提示词是两个不同产物。有关旧数据包、传输和训练启动的历史记录在 docs/archive/runpod_qwen21_2026-09-26.md。

## 正式生成前的门槛

1. 人工逐条审阅 93+150 条提示词，批准后将 JSONL 中 review_status 改为 approved；保存正式工作流、模型版本、尺寸、步数、采样器、LoRA 强度和 seed 策略。N114 固定输入验证不等于该提示词已获批。
2. 在 ComfyUI 做一条真实 API 试运行，核对 PNG 元数据、输出路径、manifest 与断点恢复；再小批检查数量、形态、可标注性和近重复。
3. 初步预算为 93×6=558 与 150×5=750 张候选，质检后目标保留 465+620=1085 张。实际保留率不足时补生成；每张候选都记录提示词、seed、参数、取舍与理由。图像保留后再预标注并逐张人工复核。

批量脚本不应在旧 trial_workflow_api.json 上解除兼容性阻断。RunComfy 的未执行方案已移至 docs/archive/runcomfy_qwen21_setup_draft.md。
