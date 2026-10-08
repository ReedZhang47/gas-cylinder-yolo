# 常用命令 · v5

请先看 NEXT_STEPS.md 的当前阶段。Python 入口以本机实际解释器为准；项目虚拟环境为 D:\yolo\.venv\Scripts\python.exe。

截至 2026-10-08，LoRA 训练、D 人工筛选后的 1085 张、new24 提示词入表及 C/D 共 2170 行 seed/提示词导出均已完成。当前对 `D:\gas_cylinders\D1085\images` 打标、复核；逐图参数使用 PNG 元数据，工作流使用工作区 JSON，不重复读取 Comfy Desktop 日志。下列云端巡检与生图预检仅为历史方法，不是当前执行队列。

## C/D PNG 元数据归档

当前汇总在 `docs/v5_prompts/cd1085_seed_prompts.csv`；来源映射与校验见 `docs/v5_prompts/d1085_review_and_metadata_20261008.md`。导出已完成，无需重跑。若以后图片发生变化，需要重新核验时，以下脚本只读取图片、准备 JSON，并保存 new24 工作流快照，不读取 Desktop 日志，也不提交生图；它不直接改写最终 CSV：

~~~powershell
& 'C:\Users\Reed\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' D:\yolo\scripts\export_cd_png_metadata.py --output D:\yolo\.tmp\cd_metadata_refresh.json
~~~

## 已完成的 LoRA 训练

Pod 和远端卷已删除，不再巡检。方法与参数见 `docs/v5_prompts/qwen21_lora_training_validation.md`；`runpod_qwen21/` 中已使用的训练脚本保留供复现。旧运维、上传包准备和 caption 草稿脚本均已归档，目录边界见 `docs/WORKSPACE_LAYOUT.md`。

## 本地 D 生图预检（历史）

先核对兼容权重、最终工作流和提示词审阅状态。以下默认仅预检，不提交队列：

~~~powershell
& D:\yolo\.venv\Scripts\python.exe D:\yolo\scripts\comfy_batch_t2i.py --prompts D:\yolo\docs\v5_prompts\real93_prompts.jsonl --variants 6 --limit 1
~~~

加载对照、单条输出审查、小批和完整批次均已完成，不再重复这些步骤。已完成批次参数见 docs/v5_prompts/full_generation_20261004.md；脚本保留供后续另行授权的补生成使用。

## v4 复核入口

~~~powershell
& D:\yolo\.venv\Scripts\python.exe D:\yolo\scripts\eval_v4_protocol.py --protocol-only
& D:\yolo\.venv\Scripts\python.exe D:\yolo\scripts\bootstrap_paired.py --self-test
~~~

完整 v4 结果在 experiments/v4_protocol/。旧作图器 paper/make_figures.py 用于 v4 图和表；当前可编辑图稿的再生方式见 paper/figures/ppt_editable/README.md。正文当前六张 PDF 在 paper/figures/manuscript/。不要把 D 传给尚未扩展的 v4 训练脚本。
