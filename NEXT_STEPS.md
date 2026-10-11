# 下一步 · v5

LoRA 参数评价已全部完成（2026-10-11）：原 CLIP、双人各 153 张评分及 110 张分歧人工裁决已验收。最终报告见 `experiments/lora_compare/report.md`。现用 1860 / 0.8 的 CLIP 为 30.41±1.51、排名第 2；裁决后训练可用 6/9（并列 2–6）、提示词全部满足 4/9（并列 12–14）、很真实 6/9。训练可用观察最高为 1860 / 0.2（7/9）。保留现用配置作为 D 臂给定条件，但不宣称综合最优或已证明近优。

下一步可将最终 LoRA 表格、三面板主图及提示词符合性补充图和方法/结果文本并入论文，入口为 [主表](paper/tables/lora_task_evaluation.tex)、[主图](paper/figures/lora_compare/lora_final_evaluation.pdf)、[提示词补充图](paper/figures/lora_compare/lora_prompt_compliance_supplement.pdf) 和 [方法/结果文本](experiments/lora_compare/methods_results.md)，完整指标表仍保留在 `paper/tables/lora_parameter_sensitivity.tex`。主图以 CLIP、训练可用和真实性解释 1860 / 0.8 的优先候选地位；此次调整为阅览结果后的呈现选择，完整指标未删。本次参数评价已无剩余人工评分；如需进一步选参，另用新提示词和匹配 seed 独立确认，不自动重训 D。

产物已整理，位置索引见 [README.md](README.md)，清理记录见 [cleanup_manifest.json](experiments/lora_compare/cleanup_manifest.json)，只读复核命令见 [COMMANDS.md](COMMANDS.md)。

2026-10-10：D1085 六 detector 各 300 轮训练、dev61 三层评估和 D−A/B/C 配对 bootstrap 已完成并验收。结果及两条诊断记录见 `experiments/v5_d/acceptance.md`。作者回复“继续”后，D493 完整流水线于北京时间 01:44 启动、06:20 完成，训练、评测与配对统计结果已落盘，待独立验收。

1. **完成 D493 独立验收**：流水线执行记录为 completed；检查六模型、180 个 checkpoint 的评测及 D1085−D493 配对统计。随机子集 seed 42 已冻结为 493 图/621 框，不重抽；D1085 大点复用。结果在 `experiments/v5_d_scale/`，执行与恢复见 `docs/D_SCALE_RUNBOOK.md`。
2. **整合四臂论文与图表**：依据 `paper/FIGURES.md` 填 D 实际组成、带框样例、联合 OOF、六 detector 数字和配对区间，补 C/D 两条规模曲线，统一正文、图注、表格及编号。D493 数值待独立验收后引用。
3. **统一错误分析**：依据四臂逐图预测制定相同的错误分类和展示规则，补阈值权衡、失败案例与错误构成，报告样本数和统计角色。
4. **冻结真正的外部测试**：另收集未参与任何决策的新图，先冻结检测/阈值/分层协议，再评估。dev61 保持开发集身份。

当前联合 OOF 主指标：D=0.6479、C=0.6429；D−A/B 的主指标区间为正，D−C=+0.0050，95% CI [−0.1357,+0.1338]。写作不得宣称 D 优于 C 或两者等效；D 比较是 v5 后续扩展。

D 为 1085 图/1085 标签、1357 框；C/D seed 与提示词已归档。执行和只读验收入口见 `docs/D_DETECTOR_RUNBOOK.md`。
