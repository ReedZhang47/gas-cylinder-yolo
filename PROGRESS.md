# 已核验进展 · v5

最近核验：2026-10-11（中国标准时间）。D1085 六 detector 训练、dev61 三层评估及 D−A/B/C 配对统计已完成验收。D493 完整流水线于 2026-10-10 01:44:16 启动、06:20:50 完成，训练、评测及规模配对统计已落盘；执行记录为 completed，独立验收待完成。LoRA 参数评价已完成最终验收。

## LoRA 参数评价最终验收（2026-10-11）

153 张输入矩阵及 PNG 有效采样连线已核验，协议在评分前冻结。官方 OpenAI CLIP ViT-L/14（224）以 CUDA float32 完成全部 153 个 CLIP-T 分数；三条评价短文本为 45/38/44 token，无截断。17 行汇总表、匹配差值、排名敏感性、主图 PDF/SVG/300 dpi PNG 和九页完整网格已生成；两套匿名包每人 153 张，PNG 元数据已去除，像素与原图一致。原图前后哈希不变。

双人各 153 张评分及 110 张分歧人工裁决均已完成；43 张使用双方一致答案，共 153 张最终标签，无剩余人工评分。原始 JSON 位于 `experiments/lora_compare/review/`，不可变导入副本在 `restricted/raw/`，最终标签在 `restricted/final_labels.json`。冻结原图、CLIP 分数和协议保持不变。

现用 1860 / 0.8：CLIP 30.41±1.51（16 个 LoRA 配置中第 2），训练可用 6/9，很真实 6/9（观察最高）。相较 1500 / 0.8，CLIP 低 0.35、可用和很真实均多 2；相较 1860 / 0.2，CLIP 高 0.83、可用少 1、很真实多 3。三指标呈现支持其作为目标检测数据的优先候选；完整提示词满足结果仍保留。主图调整是阅览结果后的呈现选择，未修改原始指标或标签。

正式报告：[report.md](experiments/lora_compare/report.md)；论文文本：[methods_results.md](experiments/lora_compare/methods_results.md)；主图：[lora_final_evaluation.pdf](paper/figures/lora_compare/lora_final_evaluation.pdf)；主表：[lora_task_evaluation.tex](paper/tables/lora_task_evaluation.tex)；符合性补充图：[lora_prompt_compliance_supplement.pdf](paper/figures/lora_compare/lora_prompt_compliance_supplement.pdf)。完整数据为 [summary.csv](experiments/lora_compare/summary.csv) 和 [final_results.json](experiments/lora_compare/human_analysis/final_results.json)，验收哈希在 [acceptance.json](experiments/lora_compare/acceptance.json)。

一次性脚本、渲染预览及废弃 v1/v2 评审 ZIP 已清理；版本源码、协议、旧评审页面、真实评分及当前匿名包保留。删除明细和哈希见 [cleanup_manifest.json](experiments/lora_compare/cleanup_manifest.json)，只读复核见 [audit_lora_compare.py](scripts/audit_lora_compare.py)。此项是补充参数评价，不改变 D 检测实验。

## D 规模实验准备（既有记录）

从 D1085 按文件名排序的总体中，用 Python `random.Random(42).sample` 等概率、无放回抽取 493 张，一次冻结、不分层、不重抽。实际 321 张有框、172 张空标、621 框；来源 new150 248＋real93 190＋new24 55。C493 与 D1085 六模型训练参数已逐项核对一致，D493 使用相同 300 轮和 dev61 三层协议；规模统计为 D1085−D493，复用大点结果。冻结与执行状态在 `experiments/v5_d_scale/`，命令和恢复见 `docs/D_SCALE_RUNBOOK.md`；日志位于 `logs/v5_d_scale/`；六模型流水线已完成，结果在 `v5_protocol_D493v5.json` 和 `bootstrap_D1085_minus_D493.json`，独立验收待完成。C493 是早期批次，D493 是随机子集，写作需说明构造差别。

## D 验收

- 数据：1085 图/1085 标签，713 张有框、372 张空标、1357 框；来源为 new150 551＋real93 421＋new24 113。冻结输入、来源哈希和既有 dev61 五折保持一致。
- 训练：yolov8s/m、yolo11s/m、yolo26s/m 全部完成 300 轮，batch 均为 16，选权候选 30 个/模型齐全；无协议定义的 non-convergent run。
- 评估：180 个 checkpoint 缓存齐全；从逐图预测重算六模型完整曲线、固定终点、OOF 与联合选权，全部复现正式 JSON。A/B/C 原始结果和缓存未改动。
- 统计：3 组配对 × 13 个对象，共 39 项比较，各 10000 次图片重抽、seed 0；点估计、差值、折定义和溯源通过核验。
- 诊断：YOLO11m 第 3–4 轮训练集自评 loss 为 NaN，后续恢复、末轮有限，训练 loss/指标正常；一次 NMS 超时定位为单张假输入预热。保留原 run 和记录，自评不参与选权。

正式证据：`experiments/v5_d/acceptance.md` / `acceptance.json`；六模型数字在 `detector_metrics.csv`，正式选择在 `v5_protocol_D1085v5.json`，逐图和 bootstrap 同目录。操作与恢复见 `docs/D_DETECTOR_RUNBOOK.md`。

## 四臂主结果

主指标为 mAP50-95。下表是 detector+checkpoint 联合选择的 pooled OOF AP，来自 dev61 held-out 逐图预测；它们是开发 benchmark 分析，不能称为最终测试成绩。

| 训练臂 | 图数 | mAP50-95 | mAP50 |
|---|---:|---:|---:|
| A · real93 | 93 | 0.4320 | 0.6738 |
| B · aug1085 | 1085 | 0.3349 | 0.6588 |
| C · gen1085 | 1085 | 0.6429 | 0.8370 |
| D · LoRA1085 | 1085 | 0.6479 | 0.8209 |
| C · gen493（规模点） | 493 | 0.5019 | 0.7367 |

配对图片聚类 bootstrap 主指标差值：

| 比较 | 差值 | 95% CI |
|---|---:|---|
| D−A | +0.2159 | [+0.0642, +0.3543] |
| D−B | +0.3130 | [+0.1859, +0.4245] |
| D−C | +0.0050 | [−0.1357, +0.1338] |

D 相对 A/B 的主指标差值有区间支持；D 与 C 的联合选权表现当前无法区分，不能宣称 D 优于 C 或两者等效。全 dev61 部署选择为 **yolo26s / epoch270.pt**，development mAP50-95 0.6891、mAP50 0.8610；该同集分数仅用于部署选择。

既有 v4：C−A = +0.2109，95% CI [+0.112,+0.320]；C−B = +0.3080，[+0.205,+0.407]；B−A = −0.0972，[−0.197,+0.017]；C 的 493→1085 = +0.1410，[+0.060,+0.249]。原始 JSON 位于 `experiments/v4_protocol/`。

## 其它已完成工作与边界

D 的 Qwen-Image-2.1 LoRA 已完成 real93 图文对 1860 步拟合、兼容加载验证、完整候选生成与人工筛选。C/D 共 2170 行 seed/提示词与来源映射已归档，new24 的 24 段词已并入 267 条总表；方法证据见 `docs/v5_prompts/`，无需重复云端巡检、打标、日志读取或生图。

dev61 共 61 图/72 框，已用于研究决策。D 是在 v4 结果已知后加入的扩展，D−A/B/C 属 v5 新增比较；单训练 seed 和重复使用开发集的限制仍在，最终确认需新收集并冻结的外部 test。协议详见 EXPERIMENTS.md。

当前可编辑 PPT 与 TeX 尚未填入本次 D 数值；下一步为四臂图表、正文和统一错误分析。图件编号与状态见 `paper/FIGURES.md`，队列见 NEXT_STEPS.md。
