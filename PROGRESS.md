# 已核验进展 · v5

最近核验：2026-09-27（中国标准时间）；训练、归档和本机固定输入验证已完成。

## 当前状态

- v4：A/B/C 三臂、C 臂 493→1085 规模点、六 detector 的三层评估及配对聚类 bootstrap 已完成；原始结果在 experiments/v4_protocol/。
- v5 D：Qwen-Image-2.1 LoRA 已在 Runpod A6000 上以 93 张审阅图文对完成 1860 步训练（repeat 5、4 epochs、rank 16）。最终权重和八个检查点已归档并校验 SHA256；Pod/远端卷已删除。训练方法、完整参数、loss 及文件哈希见 docs/v5_prompts/qwen21_lora_training_validation.md。
- 新 LoRA 的 224 组矩阵均与本机 4096 维 2.1 底模对应；固定 N114 提示词、seed 99999 的五张对照中，底模直连为 0 个补丁，强度 0.2/0.5/0.8/1.0 的四张各为 192 个补丁。加载与连接已验证；画质、过拟合程度及 D 数据集可用性尚未量化。93 条 real93 优化提示词与 150 条新场景提示词仍待人工批准。
- 尚无正式 D 生成集、标签、YOLO run 或检测结果。
- 论文 Fig. 1–5、7、10 已绘制或重绘，结果图中的 D 位置留空；当前 TeX 正文仍引用部分 v4 结果图。图件接线状态见 paper/FIGURES.md。

## v4 主结果

主指标为 mAP50-95；下表是 arm 级 detector+checkpoint 联合选择后的 pooled OOF AP，来自 dev61 的 held-out 逐图预测，不能称为最终测试成绩。

| 训练臂 | 图数 | mAP50-95 | mAP50 |
|---|---:|---:|---:|
| A · real93 | 93 | 0.4320 | 0.6738 |
| B · aug1085 | 1085 | 0.3349 | 0.6588 |
| C · gen1085 | 1085 | 0.6429 | 0.8370 |
| C · gen493（规模点） | 493 | 0.5019 | 0.7367 |

配对图片聚类 bootstrap：C−A = +0.2109，95% CI [+0.112,+0.320]；C−B = +0.3080，[+0.205,+0.407]；B−A = −0.0972，[−0.197,+0.017]。因此 C 的优势在此开发集上有区间支持，B 与 A 无法区分，不能写成“B 比 A 差”。C 的 493→1085 差值为 +0.1410，[+0.060,+0.249]。详情与逐 detector 数字以 bootstrap_paired.json、bootstrap_paired_L3.json 及各臂 v4_protocol_*.json 为准。

## 口径

dev61 共 61 图、72 个标注框；与训练来源独立，但已经用于研究决策。固定终点 last.pt 是透明基线；交叉拟合 OOF 是选权流程的主要泛化估计；全 dev61 选权只用于部署，其同集分数是 development score。D 在 v4 结果已知后提出，D−A/B/C 属 v5 新增比较。具体折定义、统计规则与时间顺序见 EXPERIMENTS.md。

既有模型配置、图形文件与未完成项分别见 paper/figures/fig02/README.md、paper/FIGURES.md、NEXT_STEPS.md。更长的阶段叙述可在 Git 历史中查阅。
