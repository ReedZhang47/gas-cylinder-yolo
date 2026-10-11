# 前三张论文图 · 2026-10-09

每个子目录含 `figure.pptd`、`pages/figure.page`、`media/` 和 `figure.pptx`，可独立复制。
PPTX 由本项目 PowerPoint COM 工作流生成，含原生文本框、形状、连线和独立照片；已嵌入字体并设置淡入切换。
PPTD 与对应 scene.json 对象逐一映射，供跨工具编辑；主交付以在 PowerPoint 中检查过的 PPTX 为准。

- [图一项目](fig01_study_pipeline/figure.pptd)
- [图二项目](fig02_image_edit_workflow/figure.pptd)
- [图三项目](fig03_lora_t2i_workflow/figure.pptd)

绘图源：上级目录 `revise_first_three.py`、`scene.json`、`build_figures.ps1`。
重新运行 COM 绘图后，运行上级目录 `package_first_three.py` 更新此项目。
