# 可编辑论文图稿（PowerPoint COM）

2026-10-09 已按作者提供的论文参考风格更新前三张（只参考视觉风格，不采用参考图内容）。直接用 PowerPoint COM 创建原生形状、线条、图片和文本框。当前交付是供作者继续删改的 PPT 草稿，本轮不导出 PDF。旧 PDF/SVG 和旧绘图脚本已迁入 `../archive/v5_vector/`，LaTeX 仅同步旧 PDF 的查找路径。

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

2026-10-09：D 的图像、标注、六模型训练和评估均已验收。Fig. 1 已同步完成状态；Fig. 3 采用实际的“计划生成 → 筛选 → 补生成 → 筛选 → 最终 1085 张合格图片”流程，不列中间批次数量或旧保留预算。

Fig. 2 展示 real_photo_12 与 real_photo_36 共同生成 Placement_Issues_0301；该对应关系已由结果 PNG 的节点 23、25 和 7 核对。图中英文指令为概述。标准/Lightning 路径表示采样选项，不表示全部 C 图使用统一参数。精确模型见 `../../../docs/v5_prompts/generation_models.md`。

Fig. 3 使用已完成的 **Qwen-Image-2.1** 兼容训练：93 个复核图文对、repeat 5、4 epochs、1,860 steps、rank 16、LR 1e-4。旧 Liblib 的 2,000 步/LR 0.0004 权重不兼容，不作为正式 D 方法。生成使用最终 LoRA 0.8、随机 seed、1184×896、25 步 Euler/simple、CFG 1、denoise 1、batch 1。最终 1,085 张已审核接收；展示 D_0003、D_0159、D_0985、D_1006 四张正式数据集图片，不展示 real93 照片。

Fig. 4 的 A/B 同行共用真实来源，C 是其他来源的独立编辑样例。Fig. 5/8 用 dev61 held-out OOF；Fig. 6 用 epoch 300 固定终点；Fig. 11 用部署权重精选案例。D 结果已齐，但图 4/5/6/8/11 的 D 区域尚未在本次改图中填入。Fig. 6 保留数字颜色规则：打印数值 ≥0.500 用白色，否则黑色。

## 再生

`prepare_figures.py` 提取无标注照片与项目 JSON 的证据，写入 `scene.json`；`build_figures.ps1` 用 COM 插入对象，导出 PNG 预览。需要本机 PowerPoint 和带 Pillow 的 Python。

```powershell
& 'C:\Users\Reed\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B 'D:\yolo\paper\figures\ppt_editable\prepare_figures.py'
& 'C:\Users\Reed\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe' -NoProfile -File 'D:\yolo\paper\figures\ppt_editable\build_figures.ps1'
```

可加 `-Figures '1,2,3'` 只再生指定单图，再加 `-RefreshReview` 更新合并稿中的对应页面和首页目录。未选中的图页保持原有对象和布局。脚本会覆盖相应自动生成 PPT；人工调整后直接保存 PPT 即可，无需运行脚本。

`media/` 是重建用的原图依赖副本。`previews/` 是 PowerPoint 导出的预览。检查记录位于 `../archive/production_checks/`。


## 前三张重排与页面尺寸

- Fig. 1：**1330 × 408 pt**，保留原横向三段布局，图形和文字改为黑白灰。real93 展示照片按前后层级 30–14–7 堆叠，使用白边、轻微旋转和阴影；六检测器直接列出型号。
- Fig. 2：**1380 × 650 pt**，浅蓝背景、虚线分区、浅色编码模块和清晰的数据流。两张参考照片保持原始比例，与 C 图 301 建立明确对应。
- Fig. 3：**1340 × 850 pt**，训练与生成并列；蓝色表示冻结权重，浅橙表示低秩更新。最终四张 D 图以无重叠横排展示，取消旧候选配额。

说明文字以 Times New Roman 为主，短标签采用 Arial。所有照片、文字和连接线均为可编辑的独立对象。新图经过本机 PowerPoint 导出预览检查，前三张没有文本溢出。单图 PPT 嵌入字体并设淡入切换。

`all_figures_editable.pptx` 保留 960 × 640 pt 画布，前三张按比例放入；其它六张图的对象和布局保留。TeX 与正文 PDF 不在本次修改范围。

`revise_first_three.py` 更新前三张场景；`build_figures.ps1` 绘制原生对象；`package_first_three.py` 打包自包含 PPTD/PPTX 伴随项目到 `first_three_project/`。每张项目均含 manifest、pages、media 和 PPTX。`scene.json` 与 `media/` 可直接用于重建；原始版本备份位于 `_archive/20261009/first_three_before/`（仓库根目录，本地归档）。
