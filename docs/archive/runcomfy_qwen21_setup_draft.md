# RunComfy Qwen-Image-2.1 文生图 LoRA 首轮配置草案

日期：2026-09-26。依据作者提供的 RunComfy 设置截图。目标是用 real93 照片训练
与当前 Qwen-Image-2.1 推理底模兼容的 LoRA，随后用于 D 臂文生图。

## 开始训练前的门槛

先在 RunComfy 的 `real93` 数据集页面确认：93 张目标图片都有逐图 caption，
而且 caption 描述**照片实际内容**，特别是气瓶的实际数量、颜色、放置方式和
周边施工场景。YOLO 的 `.txt` 框坐标不是训练 caption。若只有图片而没有逐图
caption，不应拿一条泛化的 Default Caption 直接启动完整训练。项目里的
`real93_prompts.jsonl` 是待审的**生成**提示词，不应未经逐图核对直接替代
照片 caption；其中“恰好一个/两个气瓶”可能与照片实际内容不同。可先审阅
`captions_from_original_draft/` 中已提取的 93 条原始逐图描述，流程见
`captioning_real93.md`；通过后另建带 caption 的 RunComfy 数据集。

如使用触发词 `cylsite93`，每张训练 caption 应包含 `[trigger]` 占位符或
实际触发词，且预览/正式生成时也应使用同一个词。先检查 RunComfy 的 caption
预览，确认 `[trigger]` 已正确替换，避免重复写入两次。

## 截图对应的建议值

| 分区 | 首轮设置 | 理由 |
|---|---|---|
| JOB | Training Name `real93_qwen21_t2i_r16_v1`；Trigger Word `cylsite93` | 区分旧的不兼容 LoRA；触发词需与 caption 和生成提示词一致 |
| MODEL | Qwen-Image-2.1；`Comfy-Org/Qwen-Image-2.1`；Transparency OFF；Low VRAM ON；Layer Offloading OFF | 与目标底模一致；云 GPU 首轮不必卸载 |
| QUANTIZATION | Transformer / Text Encoder 均为 `8bit convrot`；Compile Model OFF | 使用模型包匹配格式；先取得可复现基线 |
| TARGET / SAVE | LoRA；Linear Rank `16`；BF16；Save Every `250`；Keep `8` | 与前次 rank 相同便于比较；保留首轮 2000 步的全部中间检查点 |
| TRAINING | Batch 1；Gradient Accumulation 1；Steps `2000`；AdamW8Bit；LR `0.0001`；Weight Decay `0.0001`；Timestep Shift / Balanced；MSE | 首轮用较温和学习率，避免直接照搬旧训练的 `0.0004`；3000 步不必预先跑满 |
| TRAINING toggles | EMA OFF；Cache Text Embeddings OFF；各项 Regularization OFF | 首轮保持简单；Caption Dropout 0.05 时不缓存文本嵌入 |
| DATASET | Target `real93_qwen21_captioned_v1`（93 条审阅后上传的新数据集）；Control 1/2/3 空；Num Repeats 1；LoRA Weight 1；Default Caption 空；Caption Dropout 0.05；Cache Latents ON；Is Regularization OFF；Flip X/Y OFF；768 和 1024 ON，512/1280/1536/256 OFF | 文生图只需目标图与 caption；保留气瓶细节，避免低分辨率削弱小目标 |
| VALIDATION | 暂 OFF，另用固定的 SAMPLE 提示词检查 | 目前无独立验证数据集 |
| SAMPLE | Every 250；FlowMatch；1024×1024；Seed 42；Walk Seed OFF；Guidance 3；Steps 30；Skip First Sample OFF；Disable Sampling OFF | 各保存点保持提示词和种子不变，比较学习与退化 |

`Cache Latents` 应在数据集整理完成后开启；若中途改图片/裁剪/分辨率，确认缓存
重新生成。云端如发生 OOM，再考虑 Layer Offloading；不要预先改动量化格式。

## 将 10 条示例 Sample Prompts 删除，换成 4 条固定检查提示词

每条 LoRA Scale 保持 1.0，不添加 Control Images：

1. `[trigger], a realistic construction-site inspection photograph, one blue industrial gas cylinder standing alone beside concrete formwork, full body visible, no other gas cylinders.`
2. `[trigger], a realistic construction-site inspection photograph, two industrial gas cylinders standing separately at least one meter apart on a wet concrete deck, both full bodies visible, no other gas cylinders.`
3. `[trigger], a realistic construction-site inspection photograph, one industrial gas cylinder secured upright to a two-wheeled trolley beside a scaffold, full body visible, no other gas cylinders.`
4. `A realistic construction-site inspection photograph of an empty concrete deck with scaffolding and timber formwork, no gas cylinders visible.`

第 4 条不含触发词，检查 LoRA 是否让普通工地场景也无故出现气瓶。
各检查提示词可设不同**固定**种子，例如 42、43、44、45；不要让种子随
checkpoint 变化。RunComfy 预览的 Guidance 3 / 30 步是训练过程的固定比较条件；
导出后还应在实际 ComfyUI 工作流的 1184×896、25 步、CFG 1 下对照测试。
两个推理栈即使填写同样参数，也不保证像素级相同。

## 检查点选择与正式使用

在 500、1000、1500、2000 步比较同一组预览；优先选气瓶形态、数量、场景
多样性与可标注性均较好的 checkpoint，不按最低 loss 或最大步数自动选择。
导出后先核对 LoRA 的关键层形状与 Qwen-Image-2.1 底模匹配，并确认 ComfyUI
日志无 `lora key not loaded` 或 `shape invalid`；再做同 prompt、同 seed、
strength 0/1 的对照。若数量和放置方式仍有问题，优先检查训练集实际分布与
caption 准确性，而不是继续加步数。

参考：[RunComfy 2.1 训练指南](https://www.runcomfy.com/zh-CN/trainer/ai-toolkit/qwen-image-2-1-lora-training)、
[AI Toolkit 官方仓库](https://github.com/ostris/ai-toolkit)。
