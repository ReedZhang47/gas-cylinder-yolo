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

## D493 规模实验（2026-10-10 06:20 流水线已完成）

已从 D1085 用 seed 42 随机无放回冻结 493 张；六模型、300 轮和 dev61 三层评测与 C493 一致，大点复用 D1085。默认只检查和显示计划：

```powershell
& D:\yolo\.venv\Scripts\python.exe D:\yolo\scripts\run_v5_d_scale.py
```

已完成流水线命令（保留供复现）：六模型训练 → 三层评测 → D1085−D493 配对统计。当前结果已落盘，独立验收待完成：

```powershell
& D:\yolo\.venv\Scripts\python.exe -u D:\yolo\scripts\run_v5_d_scale.py --execute
```

分段、恢复、结果路径和耗时见 `docs/D_SCALE_RUNBOOK.md`；冻结与执行状态在 `experiments/v5_d_scale/`，当前日志在 `logs/v5_d_scale/`。

## LoRA 参数评价（2026-10-11 已完成）

最终报告为 [experiments/lora_compare/report.md](experiments/lora_compare/report.md)，主图为 [lora_final_evaluation.pdf](paper/figures/lora_compare/lora_final_evaluation.pdf)，主表为 [lora_task_evaluation.tex](paper/tables/lora_task_evaluation.tex)。完整产物索引见 [README.md](README.md)。

只读验收：检查 153 张冻结输入、真实评分与裁决来源、17 配置统计、配对差值及正式产物哈希；使用已有分数，不调用 CLIP 推理、不改写产物。

```powershell
& D:\yolo\.venv\Scripts\python.exe D:\yolo\scripts\audit_lora_compare.py
```

需要从已完成的人评重新生成数据和图件时，依次执行以下三步；第三步生成当前三指标主图、提示词补充图和主展示表。

```powershell
& D:\yolo\.venv\Scripts\python.exe D:\yolo\scripts\analyze_lora_reviews.py --adjudication D:\yolo\experiments\lora_compare\review\anonymous_adjudication_v3.json
& D:\yolo\.venv\Scripts\python.exe D:\yolo\scripts\finalize_lora_evaluation.py
& D:\yolo\.venv\Scripts\python.exe D:\yolo\scripts\present_lora_task_evaluation.py
```

上述再生步骤会改写输出；`acceptance.json` 保存的是当前已验收版本的哈希与视觉检查结果，再生后须重新核验并记录。冻结自动评价源码为 `scripts/eval_lora_compare.py`，本地 CLIP 运行依赖与模型位于 `.tmp/lora-eval/`，原图位于 `D:\gas_cylinders\lora-compare`。清理明细在 [cleanup_manifest.json](experiments/lora_compare/cleanup_manifest.json)。

## 已完成工作入口

- C/D 2170 行 seed 与提示词：`docs/v5_prompts/cd1085_seed_prompts.csv`；来源与核验见同目录 `d1085_review_and_metadata_20261008.md`。无需重导出，额外逐图参数从 PNG 读取。
- LoRA 训练与验证：`docs/v5_prompts/qwen21_lora_training_validation.md`。Pod 与远端卷已删除，不再巡检。
- 生图工作流和完整生成记录：`docs/v5_prompts/README.md`、`full_generation_20261004.md`；不重复读取 Desktop 日志。
- 四臂正式结果：`experiments/v4_protocol/` 与 `experiments/v5_d/`；当前图稿再生入口：`paper/figures/ppt_editable/README.md`。
