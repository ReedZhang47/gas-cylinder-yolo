# 论文计划 · v5

## 主线与证据

研究问题：在只有 93 张真实工地照片时，编辑合成与传统增广如何影响气瓶违规放置检测；新增 D 臂进一步检验 real93 LoRA 文生图能否带来可用的场景变化。A/B/C 与 C 臂 493→1085 已按 v4 协议完成。D 是 v4 结果已知后的扩展；兼容 LoRA 已完成训练和本机加载验证，但尚不能写成已验证的场景覆盖或检测优势。训练与验证的可引用事实见 `docs/v5_prompts/qwen21_lora_training_validation.md`。

主要性能指标为 mAP50-95；mAP50 是附加列。dev61 已用于研究决策，只能称开发集；交叉拟合 pooled OOF 是当前主要估计，全 dev61 部署选择分数不是最终测试成绩。D−A/B/C 已使用相同折定义取得逐图 OOF，并完成配对图片聚类区间。最好另收集并预先冻结一批外部测试图，再作最终确认。精确规则见仓库根 EXPERIMENTS.md。

## 正文状态

paper/working_paper.tex 是英文工作稿。方法与 v4 三臂、规模实验可依据已落盘 JSON 写实；D 的 LoRA 拟合、候选生成和人工筛选已可写实：2026-10-04 原两组生成 1308 张候选，随后筛选并补充 new24；2026-10-08 核验最终 new150 551＋real93 421＋new24 113＝1085 张，位于 `D:\gas_cylinders\D1085\images`。2026-10-09 D 标注、六 detector 训练、三层评估与统计已完成验收（1085 图、1357 框）。联合 OOF mAP50-95 0.6479，D−A/B 的区间为正，D−C 区间跨零；结论不可写为 D 优于 C。完整数字与诊断见 `experiments/v5_d/acceptance.md`。C/D 2170 张的 seed/提示词和 24 段新增提示词已归档，方法与来源映射见 `docs/v5_prompts/d1085_review_and_metadata_20261008.md`；原候选生成参数和冻结哈希见 `docs/v5_prompts/full_generation_20261004.md`。逐图参数以 PNG 元数据为准，工作流使用工作区 JSON，不再重复读取 Comfy Desktop 日志。本次仅更新计划和数据证据入口，正文及图件内容待后续统一同步。

2026-10-06 图件改为可人工调整的 PowerPoint COM 工作稿，入口为 `paper/figures/ppt_editable/`。原 Fig. 2 拆为新 Fig. 2 Image-Edit 与新 Fig. 3 LoRA T2I，后续编号顺延；已重绘新 Fig. 1–8、11，包括原 v4 规模图，原 Fig. 4 的结果改为新 Fig. 5 柱形图。原约 12 图规划暂为 13 图，清单与映射见 `paper/FIGURES.md`。本轮只制作 PPT 草稿，不导出 PDF、不改正文图号与 LaTeX 引用；当前 TeX 仍使用旧图。

| 部分 | 当前工作 |
|---|---|
| Introduction / Related Work | 围绕稀缺危险样本、真实来源、合成路径和人工复核整理文献；避免先行宣称 D 扩展场景 |
| Methods | 记录 C/D 模型与工作流、来源、质检和三层评估；C 精确模型文件见 ../docs/v5_prompts/generation_models.md |
| Results | 保留 v4 A/B/C 和 493→1085 实测值；D 结果已齐，待填入四臂结果、配对区间及统一错误分析 |
| Discussion | 讨论 dev61 规模与适应性决策、生成缺陷、来源依赖、许可与人工标注成本 |
| Conclusion | 等 D 与独立外部测试证据确定后写 |

同日完成前三张重排和合并稿首页目录；其余图件保持不变。目录整理将旧图移入 `figures/archive/v5_vector/`，仅同步 TeX 的旧 PDF 查找路径，正文图号和图注保持原样。

图表进入正文前逐项核对源数据、指标、统计角色和图注。现有九张表为 v4 版本，应在投稿排版时合并或移入补充材料，不以增加图表数量代替论证。

## 投稿准备

目标期刊、模板、APC、分区与预印本政策在实际投稿前以期刊当时官网核验；本文件不维护易过期的排名或周期。投稿前还需核查 Qwen 系模型、生成素材、数据和权重的发布许可，并明确 AI 工具使用披露。可公开的工作流、LoRA、YOLO 权重和带标签数据需逐项完成授权审查后再发布。

已完成结果见 PROGRESS.md、experiments/v4_protocol/ 和 experiments/v5_d/；当前执行顺序见 NEXT_STEPS.md。
