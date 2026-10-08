# 已核验进展 · v5

最近核验：2026-10-08（中国标准时间）；D 人工图像筛选及补充批次完成，最终 1085 张统一命名；C/D 共 2170 张的 seed、提示词导出及 new24 入表完成。当前待 D 框标注与复核。

## 当前状态

- 2026-10-08 工作区整理：试点/上传准备/旧实验和临时产物已归档，归档目录停止 Git 追踪；正式方法、C/D 元数据、v4 结果和当前 PPT 保留。正文六张 PDF 已移到受跟踪的 `paper/figures/manuscript/` 并核对内容一致，目录职责见 `docs/WORKSPACE_LAYOUT.md`。

- v4：A/B/C 三臂、C 臂 493→1085 规模点、六 detector 的三层评估及配对聚类 bootstrap 已完成；原始结果在 experiments/v4_protocol/。
- v5 D：Qwen-Image-2.1 LoRA 已在 Runpod A6000 上以 93 张审阅图文对完成 1860 步训练（repeat 5、4 epochs、rank 16）。最终权重和八个检查点已归档并校验 SHA256；Pod/远端卷已删除。训练方法、完整参数、loss 及文件哈希见 docs/v5_prompts/qwen21_lora_training_validation.md。
- 新 LoRA 的 224 组矩阵均与本机 4096 维 2.1 底模对应；固定 N114 提示词、seed 99999 的五张对照中，底模直连为 0 个补丁，强度 0.2/0.5/0.8/1.0 的四张各为 192 个补丁。加载与连接已验证；画质、过拟合程度及 D 数据集可用性尚未量化。作者批准扩大生成，运行使用获批的冻结提示词副本；源 JSONL 的 draft 编辑状态不代表本批尚未获准执行。
- D 人工审核保留图在 `D:\gas_cylinders\D`：new150 551、real93 421、new24 113，共 1085 张。最终图片在 `D:\gas_cylinders\D1085\images`，D_0001–0551 / D_0552–0972 / D_0973–1085 分别对应上述三组；全部 1085 张与审核来源一对一匹配 SHA256，哈希唯一。目前无 TXT 标签，正式带框训练集、YOLO run 和检测结果尚未形成。
- new24 的 PNG 实际正向文本去重得到 24 段，归档 ID N151–N174；`new24_prompts.csv` / JSONL 已保存，并加入 `d_prompt_catalog.csv`（267 条，保留数合计 1085）。原 465＋620 是初始预算，实际保留组成为 421＋551＋113。
- C 两目录分别 493、592 张；D 最终目录 1085 张。`docs/v5_prompts/cd1085_seed_prompts.csv` 为图名、seed、提示词 3 列/2170 数据行，无缺失，全部逐行与当前 PNG 复核。核验记录见 `docs/v5_prompts/d1085_review_and_metadata_20261008.md`。
- 2026-10-04 历史批次：15:26–22:11 完成 93×6＋150×5 共 1308 张候选，约 6 小时 45 分钟。仅修改 R001/N092 后扩大生成；检查表来源已在 real_photo_8 与训练副本中核对。LoRA 0.8、随机 seed；记录见 docs/v5_prompts/full_generation_20261004.md。其后作者筛选原两组并补充 new24，当前数量和路径以上述 2026-10-08 核验为准。
- 2026-10-04：LoRA 0.8、随机 seed 的 API 单图及已完成条目跳过检查通过；随后完成 4 条 real93＋new150 每类 1 条共 14 张小批，全部 PNG 参数/哈希与 API history 核验通过。作者要求修正 R001/N092 后接受其余问题并扩大生成。小批历史记录见 本地 docs/archive/comfy_pilots_20261004/small_pilot_20261004.md；后续 C/D 正式图的 seed 与提示词已于 2026-10-08 统一导出。
- 后续证据入口：PNG 元数据、已导出 CSV 与工作区工作流 JSON；不重复读取 Comfy Desktop 日志或验证已确认的 LoRA 加载。下一阶段为打标、标签复核及训练输入冻结。
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

既有模型配置、图形文件与未完成项分别见 docs/v5_prompts/generation_models.md、paper/FIGURES.md、NEXT_STEPS.md。更长的阶段叙述可在 Git 历史中查阅。
