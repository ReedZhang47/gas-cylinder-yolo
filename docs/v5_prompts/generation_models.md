# C/D 生成模型与工作流入口

本文件保留论文方法所需的模型记录，避免正文依赖本地历史归档。

## C：Qwen-Image-Edit-2509

作者提供的工作流组件如下：

| 组件 | 文件 |
|---|---|
| Image-Edit 模型 | `qwen_image_edit_2509_fp8_e4m3fn.safetensors` |
| 文本编码器 | `qwen_2.5_vl_7b_fp8_scaled.safetensors` |
| VAE | `qwen_image_vae.safetensors` |
| 可选四步加速 LoRA | `Qwen-Image-Edit-2509-Lightning-4steps-V1.0-bf16.safetensors` |

图示含标准采样与 Lightning 路径，不能据此宣称全部 C 图均采用四步生成。实际逐图执行图保存在 PNG 元数据中；1085 张 C 图的 seed/正向提示词已进入 `cd1085_seed_prompts.csv`，提取方法见 `d1085_review_and_metadata_20261008.md`。

## D：Qwen-Image-2.1 与 real93 LoRA

正式生成使用 `qwen_image_2.1_int8_convrot.safetensors`、`qwen3vl_8b_int8_convrot.safetensors`、`qwen_image_2.1_vae_bf16.safetensors` 及 `step-1860.safetensors`，LoRA 强度 0.8。训练方法、权重哈希、固定 N114 对照见 `qwen21_lora_training_validation.md`。

2026-10-10 作者确认：LoRA 参数比较 PNG 中的 `qwen_image_2.1.safetensors` 是上述底模的手动改名，权重未变；此处为作者确认的别名关系，不另称已做双文件哈希比对。现有 153 张参数对照（三提示词、三 seed、16 个 LoRA 配置及无 LoRA 基线）的三维评价执行计划见 [LORA_COMPARE_EVALUATION_PLAN.md](../LORA_COMPARE_EVALUATION_PLAN.md)。本轮 CLIP 自动评价、双人评分及全部分歧人工裁决已于 2026-10-11 完成；最终报告见 [report.md](../../experiments/lora_compare/report.md)，主图聚焦 CLIP、训练可用性与真实性，完整提示词指标保留于补充结果。

工作流保存在 `pilot_workflow_api.json`、`pilot_workflow_ui.json` 和 `new24_workflows/`；前两者虽保留 pilot 文件名，也是完整批次的工作流依据。原两组生成方法见 `full_generation_20261004.md`。实际 D 图名/来源/seed/提示词以 2026-10-08 归档为准，不重复读取 Comfy Desktop 日志。
