# Figure 1: v5 study pipeline

`draw_fig1.py` generates the vector master `main_pipeline_v5.svg` and the PDF used by the paper at `fig1_pipeline.pdf` in this folder. It does not use `paper/make_figures.py`.

The v4 source drafts are archived in `../archive/drafts/`. The D arm is planned and shown dashed. `dev61` enters development evaluation only, never training. Remove D's pending styling after its dataset and results are verified.

Regenerate from the repository root with the bundled Python (the project `.venv` currently lacks ReportLab):

```powershell
& 'C:\Users\Reed\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' 'D:\yolo\paper\figures\fig01\draw_fig1.py'
```
