# 可编辑论文图稿（PowerPoint COM）

2026-10-06 根据作者意见重绘：直接用 PowerPoint COM 创建原生形状、线条、图片和文本框。当前交付是供作者继续删改的 PPT 草稿，本轮不导出 PDF。旧 PDF/SVG 和旧绘图脚本已迁入 `../archive/v5_vector/`，LaTeX 仅同步旧 PDF 的查找路径。

| 新编号 | 原编号 | 文件 | 内容 |
|---:|---:|---|---|
| 1 | 1 | `fig01_study_pipeline.pptx` | 四臂来源、六模型训练、三层开发评估 |
| 2 | 2 的 C 部分 | `fig02_image_edit_workflow.pptx` | Image-Edit 条件输入、编码、模型路径、采样与复核 |
| 3 | 2 的 D 部分 | `fig03_lora_t2i_workflow.pptx` | 实际 LoRA 训练、适配器、提示词预算、生成与质检 |
| 4 | 3 | `fig04_training_examples.pptx` | A/B/C 训练图和细线框，D 留空 |
| 5 | 4 | `fig05_oof_bar_comparison.pptx` | OOF 柱形主结果及相对 real93 的配对差值与区间 |
| 6 | 5 | `fig06_detector_comparison.pptx` | 六检测器固定终点分数，D 留空 |
| 7 | 6 | `fig07_image_edit_scale.pptx` | C 臂 493→1085 规模效应，real93 只作背景参照 |
| 8 | 7 | `fig08_operating_tradeoff.pptx` | held-out 预测的漏检与误报权衡，D 留空 |
| 11 | 10 | `fig11_detection_cases.pptx` | GT 和部署预测，D 留空 |

`all_figures_editable.pptx` 是包含首页图目录和九张图的合并浏览稿（共 10 页）。单图和合并稿是独立文件；后续人工改稿以选定文件为准。

## 编辑方式

- 全部可见文字是独立文本框，只用 **Times New Roman** 和 **Arial**。前三张的说明与参数值主要用深色 Times New Roman，短标签采用 Arial；其余图沿用原有字体安排。
- 图片嵌入 PPT，不依赖私人数据目录即可打开；没有烘焙标注框或置信度数字。
- 标签与检测框为 0.7 pt 独立矩形。图片外框为 0.35 pt，D 占位线为 0.5 pt，可单独删除、移动或修改。
- 柱形、区间、曲线、矩阵由独立形状和文本框组成。它们不是关联 Excel 数据的自动图表，改动数值时需同步移动图形。
- 工作流节点的轮廓与文字也是独立对象。对象按 `text_…`、`rect_…`、`line_…`、`picture_…` 命名，可用选择窗格定位。
- 模型文件、证据路径与解释边界写在各图备注页。

## 内容边界

2026-10-08 数据更新：D 已完成人工图像筛选并统一命名，最终 1085 张由 new150 551、real93 421、new24 113 构成，待框标注。new24 24 段提示词和 C/D 2170 行 seed/提示词已归档，见 `../../../docs/v5_prompts/d1085_review_and_metadata_20261008.md`。以下图件说明描述既有 PPT 内容；本次未再生 PPT，Fig. 1/3 中旧候选预算和目标状态应在下次改稿时同步实际数据组成。

Fig. 2 的标准/Lightning 模式来自作者手绘工作流。四步路径表示可选能力，不表示全部 C 图均以四步生成；参考照片与保留图不是前后配对。精确模型见 `../../../docs/v5_prompts/generation_models.md`，逐图 C 工作流与参数待归档。

Fig. 3 使用已完成的 **Qwen-Image-2.1** 兼容训练：93 个复核图文对、repeat 5、4 epochs、1,860 steps、rank 16、LR 1e-4。旧 Liblib 的 2,000 步/LR 0.0004 权重不兼容，不作为正式 D 方法。生成使用最终 LoRA 0.8、随机 seed、1184×896、25 步 Euler/simple、CFG 1、denoise 1、batch 1。1,308 候选已生成，1,085 是筛选目标。两张照片只是未筛选候选。

Fig. 4 的 A/B 同行共用真实来源，C 是其他来源的独立编辑样例。Fig. 5/8 用 dev61 held-out OOF；Fig. 6 用 epoch 300 固定终点；Fig. 11 用部署权重精选案例。D 结果无，保持留空。Fig. 6 保留数字颜色规则：打印数值 ≥0.500 用白色，否则黑色。

## 再生

`prepare_figures.py` 提取无标注照片与项目 JSON 的证据，写入 `scene.json`；`build_figures.ps1` 用 COM 插入对象，导出 PNG 预览。需要本机 PowerPoint 和带 Pillow 的 Python。

```powershell
& 'C:\Users\Reed\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B 'D:\yolo\paper\figures\ppt_editable\prepare_figures.py'
& 'C:\Users\Reed\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe' -NoProfile -File 'D:\yolo\paper\figures\ppt_editable\build_figures.ps1'
```

可加 `-Figures '1,2,3'` 只再生指定单图，再加 `-RefreshReview` 更新合并稿中的对应页面和首页目录。未选中的图页保持原有对象和布局。脚本会覆盖相应自动生成 PPT；人工调整后直接保存 PPT 即可，无需运行脚本。

`media/` 是重建用的原图依赖副本。`previews/` 是 PowerPoint 导出的预览。检查记录位于 `../archive/production_checks/`。


## 前三张重排与页面尺寸

Fig. 1 为 **1330 × 408 pt**，(a)(b)(c) 横向排列，以开放式四臂条目、检测器矩阵和评估分支组织内容。Fig. 2 为 **920 × 754 pt**，采用编码分支、模型准备和迭代去噪的技术示意图；Fig. 3 为 **1080 × 896 pt**，采用 LoRA 矩阵示意与训练/生成参数表。后二者保持 (a)(b) 两个竖向流程并列，参数均处于相应流程环节。

三张画布按实际内容确定比例，移除重复总标题，只保留面板标题。正文采用接近黑色的文字，少量颜色用于四臂、Image-Edit 数据流和 LoRA 适配器；不再以同一种带分隔线的矩形节点排满三张图。所有表格的标签、数值与细线仍可独立编辑。

一个 PPT 的页面共用尺寸，因此合并稿保留 960 × 640 pt 画布，前三张等比放入。各单图 PPT 保留原始尺寸。首页目录提供九个内部跳转链接；放映时点击标题可跳转。

`revise_first_three.py` 更新前三张的场景定义；`prepare_figures.py` 负责完整数据与场景再生；`build_figures.ps1` 执行原生 COM 绘制。当前 `scene.json` 和 `media/` 足以直接运行 COM 脚本，不需先重读私人数据集。
