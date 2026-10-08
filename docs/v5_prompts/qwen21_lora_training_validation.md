# real93 → Qwen-Image-2.1 LoRA：训练与本机验证记录

状态：2026-09-27 完成训练、权重归档和本机兼容性验证。本文是 v5 D 臂训练方法与图件的证据索引；2026-10-08 D 人工筛选和补充批次完成，最终 1085 张在 `D:\gas_cylinders\D1085\images`，待框标注，检测实验尚未完成。C/D seed、提示词和 new24 入表已完成，核验见 `d1085_review_and_metadata_20261008.md`；原两组候选生成记录见 `full_generation_20261004.md`。其它逐图参数仍使用 PNG 元数据、工作流使用工作区 JSON，不重复读取 Comfy Desktop 日志。云端资源已删除；运维过程与文件交接见 `../archive/runpod_qwen21_handoff.md`。

## 训练输入和环境

- 目标：以 real93 的真实工地照片拟合 Qwen-Image-2.1 文生图 DiT 的 LoRA，供 D 臂候选图生成。
- 数据：A臂93 张真实巡检照片及 93 条逐图人工复核 caption，`metadata.csv` 的两列为 `image,prompt`，无空 caption、无重复图片名；93 条均以触发词 `cylsite93` 开头。精确的可提交文本副本为 `real93_lora_metadata.csv`，SHA256 `597ed5fa8d6fd0ff333a6b30e1f161a5a6025e38117f890ddee8e793d86ebec8`。YOLO 框标签保留在来源数据中溯源，不参与 LoRA 损失；本次训练没有单独的验证集。
- 正式数据包 `real93_REVIEWED.tar` 的 SHA256 为 `43d2f6d17ee54cd145df309a480172a6acc20b0c5686db87dd18d0a078abefdb`。DiffSynth-Studio 固定源码包 SHA256 为 `06447dc97e986e56d041dae52316a319baff679148922789ae1cae5f5895cff2`，本地训练脚本在 `runpod_qwen21/`，上传的脚本包 SHA256 为 `20f5aa596268201d9ea99b845fd8535e2c25626f5a67c2d2881696783b4a6e7b`。上传前后校验一致。前两个 tar 已从临时传输目录复制到 `D:\yolo\weights\qwen21_real93_r16\`，副本哈希再次核对一致，供后续复现；这些大型包不入 Git。
- 平台：Runpod Secure RTX A6000 48 GB（EU-SE-1），镜像 `runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404`；单 GPU 进程。先用两张图完成技术烟测，再执行完整训练。源模型通过 DiffSynth-Studio 从 `Qwen/Qwen-Image-2.1` 读取 transformer、text encoder 和 VAE；训练脚本对这些模型路径传入 `--fp8_models`。

## 实际训练配置

后续生成审核补充（2026-10-04）：real93 部分照片含底部检查表/水印，实际训练输入未去除。例如 real_photo_8 的原始文件与训练副本 SHA256 均为 `97bb0ff0e7b9fffd318f289aaeb25ad062b8996f8ca84e709cacb5d851095652`，图中蓝白表格条完整保留。此类版式会随训练进入 LoRA，后续生成已观察到类似页脚；提示词修正与来源核对见 `full_generation_20261004.md`。这一观察不改变既有训练记录或权重，也不构成过拟合程度的定量评估。

配置以本地归档的 `weights/qwen21_real93_r16/training_args.json` 和 `runpod_qwen21/run_train.sh` 为准。

| 项目 | 实际值 |
|---|---|
| 任务与可训练部分 | DiffSynth-Studio `sft`；`lora_base_model=dit`；自动选择 LoRA 目标模块；不训练文本编码器 LoRA |
| 训练量 | 93 图 × `dataset_repeat=5` × `num_epochs=4` = **1860 optimizer steps**；每轮 465 步 |
| LoRA rank | 16 |
| learning rate / weight decay | `1e-4` / `1e-4` |
| optimizer / learning-rate scheduler | `torch.optim.AdamW` / `torch.optim.lr_scheduler.ConstantLR`，均为所归档 DiffSynth-Studio 源码在未指定自定义优化器时的实现 |
| loss | `FlowMatchSFTLoss`（Qwen-Image-2.1 `sft` 路径） |
| 单步数据 | DataLoader 默认 batch size 1、`shuffle=True`、`dataset_num_workers=0` |
| gradient accumulation | 1 |
| 图像上限 | `max_pixels=1048576`、动态尺寸按 32 对齐；不是统一输出图尺寸 |
| 内存与运行 | `use_gradient_checkpointing=true`，`find_unused_parameters=true`；`accelerate launch --num_processes 1` |
| 记录与保存 | `enable_csv_log=true`；每 250 步保存，并保留第 1860 步最终权重 |

训练日志说明框架自动选中 32 个 transformer block，每块 4 个 attention 投影与 3 个 image-MLP 投影，共 224 组 LoRA 矩阵。`--lora_target_modules ''` 表示交给框架自动搜索，不表示未训练任何层。正式运行从 2026-09-26 11:19:50 UTC 启动，约在 2026-09-27 00:25 UTC 完成（约 13 小时；结束时刻据最终检查点和巡检记录，非独立精确计时）。

`weights/qwen21_real93_r16/outputs/qwen21_real93_r16/loss.csv` 包含表头和 1860 条连续的 1–1860 步记录，loss 全为有限数；第 1860 步为 `0.4796445369720459`。四个 465 步区段的平均训练 loss 分别为 `0.321368`、`0.323002`、`0.321451`、`0.329631`。它们不是验证损失，也不显示单调下降；不能仅据此判定生成质量或过拟合。训练日志与完整 loss.csv 均在本地完整归档中。

## 检查点与完整性

检查点为 `step-250/500/750/1000/1250/1500/1750/1860.safetensors`。最终权重 `weights/qwen21_real93_r16/step-1860.safetensors` 为 83,943,552 bytes、448 个可读取张量，SHA256 `f3e1a947f0e062f1d3e39a239e10fd2a467e2481efa4c7f0a00edd4c3eb5d4da`；ComfyUI 使用的 `E:\Comfy-Desktop\ComfyUI-Shared\models\loras\step-1860.safetensors` 哈希相同。完整归档 `weights/qwen21_real93_r16/qwen21_real93_r16_complete_20260927.tar` 为 671,754,240 bytes，SHA256 `2d078a07e4fd5e1eba5aaee81304d41c6ef733e5134f4173a8b3bab5e13f0092`；两者均与云端传输前哈希一致。

## 底模兼容性核对

本机实际推理底模为 `D:\Comfy-Desktop\ComfyUI-Shared\models\diffusion_models\qwen_image_2.1_int8_convrot.safetensors`。直接读取 safetensors 形状：新 LoRA 的典型 attention `lora_A=[16,4096]`、`lora_B=[4096,16]`，对应底模线性层 `[4096,4096]`。全部 224 组中，160 组直接匹配底模权重；其余 64 组来自 32 块各自的 `img_mlp.gate_layer` 和 `img_mlp.proj`，分别匹配底模合并的 `gate_up=[24576,4096]` 的一个 `[12288,4096]` 半区。**形状不匹配为 0**。合并后每块有 6 个实际补丁位置，因此 ComfyUI 的 `32 × 6 = 192 patches attached` 与权重结构一致。

这一核对证明形状兼容；是否进入采样还要核对 PNG 工作流连线和运行日志，见下节。

## 固定输入的本机推理验证：N114

作者在 Comfy Desktop 中用 `new150_prompts.jsonl` 的 `N114` 做五次生成，固定提示词和 seed `99999`，仅改变是否接入 LoRA 与其强度。提示词原文以对应 JSONL 为准，要求宽幅工地场景中两个彼此分开的完整气瓶。五张 PNG 的原输出位于 `D:\Comfy-Desktop\ComfyUI-Shared\output\`，已逐字节复制到 `D:\yolo\weights\qwen21_real93_r16\validation_n114\` 留存；逐文件 SHA256 与关键参数见 `qwen21_lora_n114_validation.csv`。副本哈希与原图、CSV 一致；PNG 自身包含 `prompt` 与 `workflow` 元数据。

本次固定正面提示词如下（UTF-8 SHA256 `44163d9f7af8c0fc1004c4a239afeab4f8d452bfb373af6ba0202c71ebe4bbee`），与五张 PNG 元数据及当前 JSONL 的 `N114` 逐字一致；它不含训练 caption 使用的 `cylsite93` 触发词。

> A realistic, unstaged construction-site inspection photograph with natural camera perspective and believable materials. In a broad panoramic site view, two gas cylinders stand separately at different depths, each fully discernible. Exactly two complete industrial gas cylinders are visible, clearly separated from each other, with no overlap or object crossing either body. No other gas cylinders. No collage, illustration, watermark, captions, or legible brand text.

共同推理设置：INT8 convrot Qwen-Image-2.1 底模、`qwen3vl_8b_int8_convrot.safetensors` 文本编码器、`qwen_image_2.1_vae_bf16.safetensors` VAE；输出均为 1184×896，25 步，Euler/simple，CFG 1.0，denoise 1.0，空负面提示词。五个 PNG 中的完整正面提示词、seed、模型及采样参数一致。

| PNG | 有效 LoRA 强度 | KSampler 模型输入 | 日志的 DiT 补丁数 |
|---|---:|---|---:|
| `Lora-Test_00001_.png` | 0（底模） | 节点 1，直接来自 UNETLoader | 0 |
| `Lora-Test_00002_.png` | 0.2 | 节点 2，来自 LoRA Loader | 192 |
| `Lora-Test_00003_.png` | 0.5 | 节点 2，来自 LoRA Loader | 192 |
| `Lora-Test_00004_.png` | 0.8 | 节点 2，来自 LoRA Loader | 192 |
| `Lora-Test_00005_.png` | 1.0 | 节点 2，来自 LoRA Loader | 192 |

特别注意：第一张 PNG 的未连接 LoRA 节点仍显示 `strength_model=0.2`，但 KSampler 的 `model=['1',0]` 绕过该节点；其**有效强度为 0**。其余四张的 KSampler 均连接节点 2。`E:\Comfy-Desktop\ComfyUI-Installs\ComfyUI\logs\comfyui.log` 的对应五次运行依次记录 `0/192/192/192/192 patches attached`，随后各有 `Prompt executed`，没有 LoRA 加载或形状报错。对应日志行的摘录已保存在 `D:\yolo\weights\qwen21_real93_r16\validation_n114\comfyui_n114_runtime_excerpt.txt`。日志另有 ComfyUI-Manager 更新频道错误，与这五次推理无关。

结论限于：最终权重文件正确、与本机 2.1 底模形状兼容，且在四次非零强度的推理中实际施加。作者肉眼观察到强度变化及高强度下疑似过拟合，但尚无盲评、画质指标或适合 D 臂的标注质量审核。此五张不自动计入目标 1085 张 D 臂训练图，也不能证明 D 臂检测收益。

## 论文和绘图使用边界

- Methods 可写实 93 个图文对、触发词、训练框架与硬件、rank/重复/轮数/步数、学习率、图像像素上限、保存间隔及最终权重；数据包和权重哈希提供复核依据。
- Fig. 2 的 LoRA 拟合阶段现为**已完成**；输出的 D 臂 1085 张数据集仍为计划阶段。N114 五张可作“底模与 LoRA 强度技术对照”候选图，但进入论文图前还需人工选图、图注说明共同 seed/提示词及是否存在瑕疵。
- Results 不应把训练 loss、补丁数量或 N114 单提示词对照写成数据多样性、标注可用性、过拟合程度或下游检测性能的定量结果。正式 D 臂图像、质检、标注和六检测器评估按 `NEXT_STEPS.md` 执行。
