# v5 D 臂：提示词与批量生图

## 当前入口

兼容 Qwen-Image-2.1 的 LoRA 正在 Runpod 训练；最近核验状态、远端路径和完成后下载步骤见 runpod_qwen21_handoff.md。旧 Liblib 权重与当前底模不兼容；2026-09-26 的七张试图及 trial_workflow_api.json 仅作故障审计，不能直接作为正式生成依据。

| 文件 | 角色 |
|---|---|
| ../Prompts_Based_on_real93.md | 原始 93 条描述素材，保留供对照 |
| real93_cores.tsv、new150_cores.tsv | 逐条可审阅的场景核心 |
| build_prompt_sets.py | 检查 ID、数量、重复并生成完整提示词 |
| real93_prompts.jsonl、new150_prompts.jsonl | 批量脚本输入；当前均为 draft |
| real93_lora_metadata.csv | 已用于云端 LoRA 训练的 93 条人工复核 caption 精确副本（无照片） |
| trial_workflow_api.json | 旧的、LoRA 不兼容的试图工作流快照 |
| scripts/comfy_batch_t2i.py | 默认 dry-run；经批准后顺序排队、稳定 seed、恢复和 manifest |

LoRA 训练使用的 93 条人工复核 caption 已保存在 real93_lora_metadata.csv；本机 .tmp/runpod_qwen21/real93 和已上传的 real93_REVIEWED.tar 使用同一内容。它们与后续批量生图提示词是两个不同产物。有关旧数据包、传输和训练启动的历史记录在 docs/archive/runpod_qwen21_2026-09-26.md。

## 正式生成前的门槛

1. 下载并核对云端训练权重及日志；在本机确认 4096 维底模兼容、无 LoRA 加载错误，并完成同 prompt/seed 的 strength 0/1 对照。
2. 人工逐条审阅 93+150 条提示词，批准后将 JSONL 中 review_status 改为 approved；保存最终工作流、模型版本、尺寸、步数、采样器、LoRA 强度和 seed 策略。
3. 先在 ComfyUI 做一条真实 API 试运行，核对 PNG 元数据、输出路径、manifest 与断点恢复；再小批检查数量、形态、可标注性和近重复。
4. 初步预算为 93×6=558 与 150×5=750 张候选，质检后目标保留 465+620=1085 张。实际保留率不足时补生成；每张候选都记录提示词、seed、参数、取舍与理由。图像保留后再预标注并逐张人工复核。

批量脚本不应在旧 trial_workflow_api.json 上解除兼容性阻断。RunComfy 的未执行方案已移至 docs/archive/runcomfy_qwen21_setup_draft.md。
