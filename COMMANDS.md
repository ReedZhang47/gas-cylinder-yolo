# 常用命令 · v5

2026-10-09：**D 六 detector 训练、推理与统计已完成并验收，无需重跑。** 结果见 `experiments/v5_d/acceptance.md`。执行细节、耗时参考与恢复说明见 `docs/D_DETECTOR_RUNBOOK.md`。

## 只读验收

以下命令核验已有权重/输入哈希，从逐图缓存重算选权和点估计；不训练、不调用 GPU 推理、不重新抽样 CI：

```powershell
& D:\yolo\.venv\Scripts\python.exe D:\yolo\scripts\audit_v5_d.py
```

## D 六 detector

项目解释器为 `D:\yolo\.venv\Scripts\python.exe`。以下默认仅核验输入并显示计划：

```powershell
& D:\yolo\.venv\Scripts\python.exe D:\yolo\scripts\run_v5_d.py
```

完整流水线命令（保留供复现：六模型训练 → 三层评估 → D−A/B/C bootstrap）：

```powershell
& D:\yolo\.venv\Scripts\python.exe D:\yolo\scripts\run_v5_d.py --execute
```

需要分段时加 `--stage train`、`--stage eval` 或 `--stage bootstrap`；中断恢复按交接文档操作。D 使用独立配置和 run，不传给旧 `run_v4_arms.ps1`。A/B/C 结果直接复用。

## 已完成工作入口

- C/D 2170 行 seed 与提示词：`docs/v5_prompts/cd1085_seed_prompts.csv`；来源与核验见同目录 `d1085_review_and_metadata_20261008.md`。无需重导出，额外逐图参数从 PNG 读取。
- LoRA 训练与验证：`docs/v5_prompts/qwen21_lora_training_validation.md`。Pod 与远端卷已删除，不再巡检。
- 生图工作流和完整生成记录：`docs/v5_prompts/README.md`、`full_generation_20261004.md`；不重复读取 Desktop 日志。
- 四臂正式结果：`experiments/v4_protocol/` 与 `experiments/v5_d/`；当前图稿再生入口：`paper/figures/ppt_editable/README.md`。
