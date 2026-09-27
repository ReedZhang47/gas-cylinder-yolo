# 论文 12 图清单 · v5

状态截至 2026-09-27。当前定稿的是版式与 A/B/C 已有证据；D 位置均待真实数据填充。SVG 和再生脚本与各现有 PDF 同目录。paper/figures/archive/v4/ 存放旧稿；paper/figures/archive/drafts/ 存放旧 PPT/SVG 和 Fig. 2 照片提取脚本。

| 图 | 目的 | 当前文件 / 状态 |
|---:|---|---|
| 1 | 四臂研究总流程 | figures/fig01/fig1_pipeline.pdf；D 为计划态；已接入 TeX |
| 2 | C 编辑与 D LoRA 文生图工作流 | figures/fig02/fig2_generation_workflows.pdf；D LoRA 拟合与加载已验证，正式数据集仍待生成；已接入 TeX |
| 3 | 四臂训练图像样例 | figures/fig03/fig3_training_examples.pdf；A/B/C 实图，D 留空 |
| 4 | 四臂联合 OOF 主结果与配对区间 | figures/fig04/fig4_arm_level_comparison.pdf；A/B/C 已填，D 留空 |
| 5 | 六 detector 在各臂的固定终点表现 | figures/fig05/fig5_detector_consistency.pdf；A/B/C 已填，D 留空 |
| 6 | C 臂 493→1085 规模效应 | 待升级；v4 图在 figures/archive/v4/fig6_scale_curve.pdf |
| 7 | 漏检与每图误报的阈值权衡 | figures/fig07/fig7_operating_tradeoff.pdf；A/B/C OOF，D 留空 |
| 8 | 新收集并冻结的独立外部测试 | 待采集与评估；不可把 dev61 改名为 final test |
| 9 | 困难条件分层结果 | 待 Fig. 8 数据；预先定义小目标、遮挡或场景分层并标样本数 |
| 10 | 检出与失败案例 | figures/fig10/fig10_detection_cases.pdf；dev61 精选案例，D 留空 |
| 11 | 漏检、背景误报、定位与重复框构成 | 待四臂逐图结果和统一错误分类 |
| 12 | LoRA 开/关或标注复核消融 | 已有 N114 固定提示词/seed 的技术对照；正式消融与检测收益仍待受控实验 |

Fig. 4、7 使用 dev61 交叉拟合 held-out 结果；Fig. 5 是固定终点开发集分数；Fig. 10 是部署权重的示例展示，不估计案例发生率。D 的结果不得从 A/B/C 外推。

当前 paper/working_paper.tex 的结果段还引用 figures/archive/v4/ 中的图；新图进入正文时须一起核对编号、图注、交叉引用和表格。
